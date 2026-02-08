"""
Africa Grocery Scrapers
Scrapers for South Africa and other African grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class ShopriteScraper(BaseScraper):
    """Scraper for Shoprite (South Africa - largest retailer in Africa)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks-confectionery"},
        {"name": "Breakfast", "url": "/breakfast"},
        {"name": "Pantry", "url": "/pantry"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Shoprite", "https://www.shoprite.co.za")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        page = 1
        
        while len(products) < max_products:
            url = f"{category_url}?page={page}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-item, .product-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_shoprite_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_shoprite_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-name, .product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-price, .price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'ZAR',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Shoprite card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/product/([^/]+)', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'ZAR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Shoprite product: {e}")
            return None


class PicknPayScraper(BaseScraper):
    """Scraper for Pick n Pay (South Africa)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks"},
        {"name": "Breakfast", "url": "/breakfast"},
        {"name": "Pantry", "url": "/pantry"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Pick n Pay", "https://www.pnp.co.za")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        page = 1
        
        while len(products) < max_products:
            url = f"{category_url}?page={page}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-item, .product-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_pnp_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_pnp_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'ZAR',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Pick n Pay card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1]
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'ZAR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Pick n Pay product: {e}")
            return None


class CheckersScraper(BaseScraper):
    """Scraper for Checkers (South Africa - Shoprite Group)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks"},
        {"name": "Breakfast", "url": "/breakfast"},
        {"name": "Pantry", "url": "/pantry"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Checkers", "https://www.checkers.co.za")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item')
        
        for item in items[:max_products]:
            product = self._parse_checkers_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_checkers_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'ZAR',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Checkers card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1]
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'ZAR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Checkers product: {e}")
            return None


class WoolworthsSAScraper(BaseScraper):
    """Scraper for Woolworths South Africa (premium retailer)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/food/beverages"},
        {"name": "Snacks", "url": "/food/snacks"},
        {"name": "Breakfast", "url": "/food/breakfast"},
        {"name": "Pantry", "url": "/food/pantry"},
        {"name": "Frozen", "url": "/food/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Woolworths SA", "https://www.woolworths.co.za")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        page = 1
        
        while len(products) < max_products:
            url = f"{category_url}?page={page}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-item, .product-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_woolworths_sa_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_woolworths_sa_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'ZAR',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Woolworths SA card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1]
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'ZAR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Woolworths SA product: {e}")
            return None


# Factory functions
def create_shoprite_scraper() -> ShopriteScraper:
    return ShopriteScraper()

def create_picknpay_scraper() -> PicknPayScraper:
    return PicknPayScraper()

def create_checkers_scraper() -> CheckersScraper:
    return CheckersScraper()

def create_woolworths_sa_scraper() -> WoolworthsSAScraper:
    return WoolworthsSAScraper()
