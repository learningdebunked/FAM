"""
Middle East Grocery Scrapers
Scrapers for UAE, Dubai, Saudi Arabia, Turkey grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class LuluHypermarketScraper(BaseScraper):
    """Scraper for Lulu Hypermarket (UAE/GCC - largest hypermarket chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks-confectionery"},
        {"name": "Breakfast", "url": "/breakfast-spreads"},
        {"name": "Grocery", "url": "/grocery"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Lulu Hypermarket", "https://www.luluhypermarket.com/en-ae")
    
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
            items = soup.select('.product-item, .product-box')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_lulu_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_lulu_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/p/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-name, .product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-price, .price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            img_elem = element.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'AED',
                'image_url': image_url,
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Lulu card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/p/([^/]+)', product_url)
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
                'currency': 'AED',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Lulu product: {e}")
            return None


class SpinneysScraper(BaseScraper):
    """Scraper for Spinneys (UAE/Lebanon - premium supermarket)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks-confectionery"},
        {"name": "Breakfast", "url": "/breakfast"},
        {"name": "Pantry", "url": "/pantry"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Spinneys", "https://www.spinneys.com")
    
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
                product = self._parse_spinneys_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_spinneys_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'AED',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Spinneys card: {e}")
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
                'currency': 'AED',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Spinneys product: {e}")
            return None


class ChoithramsScraper(BaseScraper):
    """Scraper for Choithrams (UAE - supermarket chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/beverages"},
        {"name": "Snacks", "url": "/snacks"},
        {"name": "Breakfast", "url": "/breakfast"},
        {"name": "Grocery", "url": "/grocery"},
        {"name": "Frozen", "url": "/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Choithrams", "https://www.choithrams.com")
    
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
            product = self._parse_choithrams_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_choithrams_card(self, element) -> Optional[Dict]:
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
                'currency': 'AED',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Choithrams card: {e}")
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
                'currency': 'AED',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Choithrams product: {e}")
            return None


# ==================== Turkey Scrapers ====================

class MigrosTurkeyScraper(BaseScraper):
    """Scraper for Migros (Turkey - largest supermarket chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "İçecekler", "url": "/icecekler"},
        {"name": "Atıştırmalık", "url": "/atistirmalik"},
        {"name": "Kahvaltılık", "url": "/kahvaltilik"},
        {"name": "Temel Gıda", "url": "/temel-gida"},
        {"name": "Donuk Gıda", "url": "/donuk-gida"},
    ]
    
    def __init__(self):
        super().__init__("Migros Turkey", "https://www.migros.com.tr")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        page = 1
        
        while len(products) < max_products:
            url = f"{category_url}?sayfa={page}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-card, .mdc-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_migros_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_migros_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/urun/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/urun/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-name, .mdc-card__title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-price, .price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'TRY',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Migros card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/urun/([^/]+)', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            # Turkish: İçindekiler
            ing_section = soup.find(text=re.compile(r'içindekiler|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'TRY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Migros product: {e}")
            return None


class BIMScraper(BaseScraper):
    """Scraper for BIM (Turkey - discount supermarket)"""
    
    FOOD_CATEGORIES = [
        {"name": "İçecekler", "url": "/icecekler"},
        {"name": "Atıştırmalık", "url": "/atistirmalik"},
        {"name": "Kahvaltılık", "url": "/kahvaltilik"},
        {"name": "Temel Gıda", "url": "/temel-gida"},
    ]
    
    def __init__(self):
        super().__init__("BIM", "https://www.bim.com.tr")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .urun-item')
        
        for item in items[:max_products]:
            product = self._parse_bim_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_bim_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name, .urun-adi')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price, .fiyat')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'TRY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing BIM card: {e}")
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
            ing_section = soup.find(text=re.compile(r'içindekiler|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'TRY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing BIM product: {e}")
            return None


class A101Scraper(BaseScraper):
    """Scraper for A101 (Turkey - discount supermarket)"""
    
    FOOD_CATEGORIES = [
        {"name": "İçecekler", "url": "/icecek"},
        {"name": "Atıştırmalık", "url": "/atistirmalik"},
        {"name": "Kahvaltılık", "url": "/kahvaltilik"},
        {"name": "Temel Gıda", "url": "/temel-gida"},
    ]
    
    def __init__(self):
        super().__init__("A101", "https://www.a101.com.tr")
    
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
            product = self._parse_a101_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_a101_card(self, element) -> Optional[Dict]:
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
                'currency': 'TRY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing A101 card: {e}")
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
            ing_section = soup.find(text=re.compile(r'içindekiler|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'TRY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing A101 product: {e}")
            return None


# Factory functions
def create_lulu_scraper() -> LuluHypermarketScraper:
    return LuluHypermarketScraper()

def create_spinneys_scraper() -> SpinneysScraper:
    return SpinneysScraper()

def create_choithrams_scraper() -> ChoithramsScraper:
    return ChoithramsScraper()

def create_migros_turkey_scraper() -> MigrosTurkeyScraper:
    return MigrosTurkeyScraper()

def create_bim_scraper() -> BIMScraper:
    return BIMScraper()

def create_a101_scraper() -> A101Scraper:
    return A101Scraper()
