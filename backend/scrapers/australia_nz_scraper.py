"""
Australia & New Zealand Grocery Scrapers
Scrapers for Australian and New Zealand grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class ColesScraper(BaseScraper):
    """Scraper for Coles (Australia - 2nd largest)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/browse/drinks"},
        {"name": "Pantry", "url": "/browse/pantry"},
        {"name": "Snacks", "url": "/browse/snacks-confectionery"},
        {"name": "Frozen", "url": "/browse/frozen"},
        {"name": "Dairy", "url": "/browse/dairy-eggs-fridge"},
        {"name": "Bakery", "url": "/browse/bakery"},
    ]
    
    def __init__(self):
        super().__init__("Coles", "https://www.coles.com.au")
    
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
            items = soup.select('[data-testid="product-tile"]')
            
            if not items:
                items = soup.select('.product-tile')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_coles_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_coles_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-testid="product-title"]')
            if not name_elem:
                name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-testid="product-price"]')
            if not price_elem:
                price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'AUD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Coles card: {e}")
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
            ing_section = soup.select_one('[data-testid="ingredients"]')
            if not ing_section:
                ing_section = soup.find(text=re.compile(r'ingredients', re.I))
                if ing_section:
                    ing_section = ing_section.find_parent()
            
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'AUD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Coles product: {e}")
            return None


class IGAScraper(BaseScraper):
    """Scraper for IGA (Australia - independent grocers)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/drinks"},
        {"name": "Pantry", "url": "/pantry"},
        {"name": "Snacks", "url": "/snacks"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("IGA", "https://www.iga.com.au")
    
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
            product = self._parse_iga_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_iga_card(self, element) -> Optional[Dict]:
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
                'currency': 'AUD',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing IGA card: {e}")
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
                'currency': 'AUD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing IGA product: {e}")
            return None


# ==================== New Zealand Scrapers ====================

class CountdownScraper(BaseScraper):
    """Scraper for Countdown (New Zealand - Woolworths NZ)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/shop/browse/drinks"},
        {"name": "Pantry", "url": "/shop/browse/pantry"},
        {"name": "Snacks", "url": "/shop/browse/snacks-sweets"},
        {"name": "Frozen", "url": "/shop/browse/frozen"},
        {"name": "Dairy", "url": "/shop/browse/fridge-deli"},
    ]
    
    def __init__(self):
        super().__init__("Countdown", "https://www.countdown.co.nz")
    
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
            items = soup.select('[data-testid="product-card"]')
            
            if not items:
                items = soup.select('.product-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_countdown_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_countdown_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-testid="product-title"]')
            if not name_elem:
                name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-testid="product-price"]')
            if not price_elem:
                price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'NZD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Countdown card: {e}")
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
                'currency': 'NZD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Countdown product: {e}")
            return None


class PaknSaveScraper(BaseScraper):
    """Scraper for PAK'nSAVE (New Zealand - discount)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/shop/category/drinks"},
        {"name": "Pantry", "url": "/shop/category/pantry"},
        {"name": "Snacks", "url": "/shop/category/snacks"},
        {"name": "Frozen", "url": "/shop/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("PAKnSAVE", "https://www.paknsave.co.nz")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-card, .fs-product-card')
        
        for item in items[:max_products]:
            product = self._parse_paknsave_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_paknsave_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name, .fs-product-card__title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price, .fs-product-card__price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'NZD',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing PAK'nSAVE card: {e}")
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
                'currency': 'NZD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing PAK'nSAVE product: {e}")
            return None


class NewWorldScraper(BaseScraper):
    """Scraper for New World (New Zealand - premium)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/shop/category/drinks"},
        {"name": "Pantry", "url": "/shop/category/pantry"},
        {"name": "Snacks", "url": "/shop/category/snacks"},
        {"name": "Frozen", "url": "/shop/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("New World", "https://www.newworld.co.nz")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-card, .fs-product-card')
        
        for item in items[:max_products]:
            product = self._parse_newworld_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_newworld_card(self, element) -> Optional[Dict]:
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
                'currency': 'NZD',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing New World card: {e}")
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
                'currency': 'NZD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing New World product: {e}")
            return None


# Factory functions
def create_coles_scraper() -> ColesScraper:
    return ColesScraper()

def create_iga_scraper() -> IGAScraper:
    return IGAScraper()

def create_countdown_scraper() -> CountdownScraper:
    return CountdownScraper()

def create_paknsave_scraper() -> PaknSaveScraper:
    return PaknSaveScraper()

def create_newworld_scraper() -> NewWorldScraper:
    return NewWorldScraper()
