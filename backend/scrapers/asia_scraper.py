"""
Asia Grocery Scrapers
Scrapers for Singapore, India, Japan, Korea grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class FairPriceScraper(BaseScraper):
    """Scraper for FairPrice (Singapore - NTUC)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks-confectionery"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Canned Food", "url": "/category/canned-food"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("FairPrice", "https://www.fairprice.com.sg")
    
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
                product = self._parse_fairprice_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_fairprice_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-testid="product-name"]')
            if not name_elem:
                name_elem = element.select_one('.product-name')
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
                'currency': 'SGD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing FairPrice card: {e}")
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
                'currency': 'SGD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing FairPrice product: {e}")
            return None


class BigBazaarScraper(BaseScraper):
    """Scraper for Big Bazaar (India - Future Group)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks-branded-foods"},
        {"name": "Breakfast", "url": "/breakfast-dairy"},
        {"name": "Staples", "url": "/staples"},
        {"name": "Frozen", "url": "/frozen-food"},
    ]
    
    def __init__(self):
        super().__init__("Big Bazaar", "https://www.bigbazaar.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .product-card')
        
        for item in items[:max_products]:
            product = self._parse_bigbazaar_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_bigbazaar_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name, .product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price, .price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'INR',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Big Bazaar card: {e}")
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
                'currency': 'INR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Big Bazaar product: {e}")
            return None


class DMartScraper(BaseScraper):
    """Scraper for DMart (India - Avenue Supermarts)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks-namkeen"},
        {"name": "Breakfast", "url": "/breakfast-cereals"},
        {"name": "Grocery", "url": "/grocery-staples"},
        {"name": "Frozen", "url": "/frozen-food"},
    ]
    
    def __init__(self):
        super().__init__("DMart", "https://www.dmart.in")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .product-card')
        
        for item in items[:max_products]:
            product = self._parse_dmart_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_dmart_card(self, element) -> Optional[Dict]:
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
                'currency': 'INR',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing DMart card: {e}")
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
                'currency': 'INR',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing DMart product: {e}")
            return None


class AeonScraper(BaseScraper):
    """Scraper for Aeon (Japan - largest retailer)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Aeon", "https://www.aeon.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .product-card')
        
        for item in items[:max_products]:
            product = self._parse_aeon_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_aeon_card(self, element) -> Optional[Dict]:
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
                'currency': 'JPY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Aeon card: {e}")
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
            # Japanese: 原材料 (genzairyou)
            ing_section = soup.find(text=re.compile(r'原材料|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'JPY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Aeon product: {e}")
            return None


class EMartScraper(BaseScraper):
    """Scraper for E-Mart (South Korea - largest retailer)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("E-Mart", "https://emart.ssg.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .cunit_prod')
        
        for item in items[:max_products]:
            product = self._parse_emart_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_emart_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.title, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = re.search(r'itemId=(\d+)', href)
            product_id = product_id.group(1) if product_id else name.replace(' ', '-')
            
            price_elem = element.select_one('.price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'KRW',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing E-Mart card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1, .cdtl_info_tit')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'itemId=(\d+)', product_url)
            product_id = match.group(1) if match else product_url.split('/')[-1]
            
            ingredients_text = None
            # Korean: 원재료 (wonjaeryo)
            ing_section = soup.find(text=re.compile(r'원재료|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'KRW',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing E-Mart product: {e}")
            return None


class LotteMartScraper(BaseScraper):
    """Scraper for Lotte Mart (South Korea)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Lotte Mart", "https://www.lottemart.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .prd_item')
        
        for item in items[:max_products]:
            product = self._parse_lottemart_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_lottemart_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.prd_name, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.prd_price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'KRW',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Lotte Mart card: {e}")
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
            ing_section = soup.find(text=re.compile(r'원재료|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'KRW',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Lotte Mart product: {e}")
            return None


# Factory functions
def create_fairprice_scraper() -> FairPriceScraper:
    return FairPriceScraper()

def create_bigbazaar_scraper() -> BigBazaarScraper:
    return BigBazaarScraper()

def create_dmart_scraper() -> DMartScraper:
    return DMartScraper()

def create_aeon_scraper() -> AeonScraper:
    return AeonScraper()

def create_emart_scraper() -> EMartScraper:
    return EMartScraper()

def create_lottemart_scraper() -> LotteMartScraper:
    return LotteMartScraper()
