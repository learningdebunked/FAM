"""
Base Scraper Class for FAM Product Data Pipeline
Provides common functionality for all retailer scrapers
"""

import asyncio
import aiohttp
import random
import re
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all retailer scrapers"""
    
    # Default headers to mimic browser requests
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Rate limiting settings
    MIN_DELAY = 1.0  # Minimum delay between requests (seconds)
    MAX_DELAY = 3.0  # Maximum delay between requests (seconds)
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5.0
    
    def __init__(self, retailer_name: str, base_url: str):
        self.retailer_name = retailer_name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.products_scraped = 0
        self.products_failed = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.DEFAULT_HEADERS)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply rate limiting between requests"""
        delay = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
        await asyncio.sleep(delay)
    
    async def _fetch_page(self, url: str, params: Dict = None, 
                         headers: Dict = None) -> Optional[str]:
        """Fetch a page with retry logic"""
        merged_headers = {**self.DEFAULT_HEADERS, **(headers or {})}
        
        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()
                
                async with self.session.get(
                    url, 
                    params=params, 
                    headers=merged_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Rate limited
                        logger.warning(f"Rate limited on {url}, waiting...")
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    elif response.status == 403:  # Forbidden
                        logger.error(f"Access forbidden for {url}")
                        return None
                    else:
                        logger.warning(f"Got status {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on {url}, attempt {attempt + 1}")
            except aiohttp.ClientError as e:
                logger.error(f"Client error on {url}: {e}")
            
            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)
        
        return None
    
    async def _fetch_json(self, url: str, params: Dict = None,
                         headers: Dict = None) -> Optional[Dict]:
        """Fetch JSON data from an API endpoint"""
        merged_headers = {
            **self.DEFAULT_HEADERS, 
            'Accept': 'application/json',
            **(headers or {})
        }
        
        for attempt in range(self.MAX_RETRIES):
            try:
                await self._rate_limit()
                
                async with self.session.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    else:
                        logger.warning(f"Got status {response.status} for {url}")
                        
            except Exception as e:
                logger.error(f"Error fetching JSON from {url}: {e}")
            
            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY)
        
        return None
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'html.parser')
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep commas for ingredients
        text = text.strip()
        return text
    
    def _parse_price(self, price_text: str) -> Optional[float]:
        """Parse price from text"""
        if not price_text:
            return None
        # Extract numbers from price text
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
    
    def _parse_ingredients(self, ingredients_text: str) -> List[str]:
        """Parse ingredients text into a list"""
        if not ingredients_text:
            return []
        
        # Clean the text
        text = self._clean_text(ingredients_text)
        
        # Remove common prefixes
        prefixes = ['ingredients:', 'contains:', 'made with:']
        for prefix in prefixes:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Split by common delimiters
        # Handle nested parentheses by temporarily replacing them
        # Simple split by comma, handling parentheses
        ingredients = []
        current = ""
        paren_depth = 0
        
        for char in text:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
                if current.strip():
                    ingredients.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            ingredients.append(current.strip())
        
        # Clean each ingredient
        cleaned = []
        for ing in ingredients:
            ing = ing.strip()
            # Remove percentage values
            ing = re.sub(r'\d+\.?\d*%', '', ing).strip()
            # Remove leading numbers/bullets
            ing = re.sub(r'^[\d\.\-\*]+\s*', '', ing).strip()
            if ing and len(ing) > 1:
                cleaned.append(ing)
        
        return cleaned
    
    def _parse_nutrition_value(self, text: str) -> Optional[float]:
        """Parse a nutrition value from text (e.g., '10g' -> 10.0)"""
        if not text:
            return None
        match = re.search(r'([\d,]+\.?\d*)', text.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    @abstractmethod
    async def get_categories(self) -> List[Dict[str, str]]:
        """Get list of product categories to scrape
        
        Returns:
            List of dicts with 'name' and 'url' keys
        """
        pass
    
    @abstractmethod
    async def get_products_in_category(self, category_url: str, 
                                       max_products: int = 100) -> List[Dict]:
        """Get products from a category page
        
        Args:
            category_url: URL of the category page
            max_products: Maximum number of products to fetch
            
        Returns:
            List of product dicts with basic info (id, name, url, price, image)
        """
        pass
    
    @abstractmethod
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        """Get detailed product information including ingredients and nutrition
        
        Args:
            product_url: URL of the product page
            
        Returns:
            Dict with full product details or None if failed
        """
        pass
    
    async def scrape_all(self, max_products_per_category: int = 100,
                        categories: List[str] = None) -> List[Dict]:
        """Scrape all products from the retailer
        
        Args:
            max_products_per_category: Max products to scrape per category
            categories: Optional list of category names to scrape (None = all)
            
        Returns:
            List of all scraped products
        """
        all_products = []
        
        logger.info(f"Starting scrape for {self.retailer_name}")
        
        # Get categories
        category_list = await self.get_categories()
        
        if categories:
            category_list = [c for c in category_list if c['name'] in categories]
        
        logger.info(f"Found {len(category_list)} categories to scrape")
        
        for category in category_list:
            logger.info(f"Scraping category: {category['name']}")
            
            try:
                # Get products in category
                products = await self.get_products_in_category(
                    category['url'], 
                    max_products_per_category
                )
                
                logger.info(f"Found {len(products)} products in {category['name']}")
                
                # Get details for each product
                for product in products:
                    try:
                        details = await self.get_product_details(product['url'])
                        if details:
                            details['category'] = category['name']
                            all_products.append(details)
                            self.products_scraped += 1
                        else:
                            self.products_failed += 1
                    except Exception as e:
                        logger.error(f"Error getting product details: {e}")
                        self.products_failed += 1
                        
            except Exception as e:
                logger.error(f"Error scraping category {category['name']}: {e}")
        
        logger.info(f"Scrape complete. Scraped: {self.products_scraped}, Failed: {self.products_failed}")
        
        return all_products


class APIBasedScraper(BaseScraper):
    """Base class for scrapers that use retailer APIs instead of HTML scraping"""
    
    def __init__(self, retailer_name: str, base_url: str, api_base_url: str):
        super().__init__(retailer_name, base_url)
        self.api_base_url = api_base_url
    
    async def _api_request(self, endpoint: str, params: Dict = None,
                          headers: Dict = None) -> Optional[Dict]:
        """Make an API request"""
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        return await self._fetch_json(url, params, headers)
