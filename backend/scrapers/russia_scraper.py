"""
Russia Grocery Scrapers
Scrapers for major Russian grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class MagnitScraper(BaseScraper):
    """Scraper for Magnit (Магнит - Russia's largest retailer)"""
    
    FOOD_CATEGORIES = [
        {"name": "Напитки", "url": "/catalog/napitki"},
        {"name": "Снеки", "url": "/catalog/sneki"},
        {"name": "Завтраки", "url": "/catalog/zavtraki"},
        {"name": "Бакалея", "url": "/catalog/bakaleya"},
        {"name": "Заморозка", "url": "/catalog/zamorozka"},
    ]
    
    def __init__(self):
        super().__init__("Magnit", "https://magnit.ru")
    
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
            items = soup.select('.product-card, .catalog-item')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_magnit_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_magnit_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-card__title, .catalog-item__title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-card__price, .catalog-item__price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'RUB',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Magnit card: {e}")
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
            # Russian: Состав (sostav)
            ing_section = soup.find(text=re.compile(r'состав|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'RUB',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Magnit product: {e}")
            return None


class X5RetailScraper(BaseScraper):
    """Scraper for X5 Retail Group (Pyaterochka/Пятёрочка - Russia)"""
    
    FOOD_CATEGORIES = [
        {"name": "Напитки", "url": "/catalog/napitki"},
        {"name": "Снеки", "url": "/catalog/sneki"},
        {"name": "Завтраки", "url": "/catalog/zavtraki"},
        {"name": "Бакалея", "url": "/catalog/bakaleya"},
        {"name": "Заморозка", "url": "/catalog/zamorozka"},
    ]
    
    def __init__(self):
        super().__init__("Pyaterochka", "https://5ka.ru")
    
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
            items = soup.select('.product-card, .product-item')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_x5_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_x5_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-card__title, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-card__price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'RUB',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing X5 card: {e}")
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
            ing_section = soup.find(text=re.compile(r'состав|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'RUB',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing X5 product: {e}")
            return None


class LentaScraper(BaseScraper):
    """Scraper for Lenta (Лента - Russia hypermarket chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Напитки", "url": "/catalog/napitki"},
        {"name": "Снеки", "url": "/catalog/sneki"},
        {"name": "Завтраки", "url": "/catalog/zavtraki"},
        {"name": "Бакалея", "url": "/catalog/bakaleya"},
        {"name": "Заморозка", "url": "/catalog/zamorozka"},
    ]
    
    def __init__(self):
        super().__init__("Lenta", "https://lenta.com")
    
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
            items = soup.select('.product-card, .sku-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_lenta_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_lenta_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.sku-card__title, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.sku-card__price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'RUB',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Lenta card: {e}")
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
            ing_section = soup.find(text=re.compile(r'состав|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'RUB',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Lenta product: {e}")
            return None


class PerekrestokScraper(BaseScraper):
    """Scraper for Perekrestok (Перекрёсток - X5 premium chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Напитки", "url": "/cat/napitki"},
        {"name": "Снеки", "url": "/cat/sneki"},
        {"name": "Завтраки", "url": "/cat/zavtraki"},
        {"name": "Бакалея", "url": "/cat/bakaleya"},
        {"name": "Заморозка", "url": "/cat/zamorozka"},
    ]
    
    def __init__(self):
        super().__init__("Perekrestok", "https://www.perekrestok.ru")
    
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
            items = soup.select('.product-card, .product-item')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_perekrestok_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_perekrestok_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-card__title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-card__price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'RUB',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Perekrestok card: {e}")
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
            ing_section = soup.find(text=re.compile(r'состав|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'RUB',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Perekrestok product: {e}")
            return None


# Factory functions
def create_magnit_scraper() -> MagnitScraper:
    return MagnitScraper()

def create_pyaterochka_scraper() -> X5RetailScraper:
    return X5RetailScraper()

def create_lenta_scraper() -> LentaScraper:
    return LentaScraper()

def create_perekrestok_scraper() -> PerekrestokScraper:
    return PerekrestokScraper()
