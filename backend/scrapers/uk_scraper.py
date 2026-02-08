"""
UK Grocery Scrapers
Scrapers for United Kingdom grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class SainsburysScraper(BaseScraper):
    """Scraper for Sainsbury's (UK - 2nd largest)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/shop/gb/groceries/drinks"},
        {"name": "Food Cupboard", "url": "/shop/gb/groceries/food-cupboard"},
        {"name": "Frozen", "url": "/shop/gb/groceries/frozen"},
        {"name": "Fresh Food", "url": "/shop/gb/groceries/fresh-food"},
        {"name": "Bakery", "url": "/shop/gb/groceries/bakery"},
    ]
    
    def __init__(self):
        super().__init__("Sainsburys", "https://www.sainsburys.co.uk")
    
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
            items = soup.select('[data-test-id="product-tile"]')
            
            if not items:
                items = soup.select('.product-tile')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_sainsburys_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_sainsburys_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-test-id="product-tile-description"]')
            if not name_elem:
                name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-test-id="product-tile-price"]')
            if not price_elem:
                price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            img_elem = element.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'GBP',
                'image_url': image_url,
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Sainsburys card: {e}")
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
            ing_section = soup.select_one('[id*="ingredients"]')
            if not ing_section:
                ing_section = soup.find(text=re.compile(r'ingredients', re.I))
                if ing_section:
                    ing_section = ing_section.find_parent()
            
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            nutrition = self._parse_nutrition(soup)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'GBP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': nutrition,
            }
        except Exception as e:
            logger.error(f"Error parsing Sainsburys product: {e}")
            return None
    
    def _parse_nutrition(self, soup) -> Dict:
        nutrition = {}
        table = soup.select_one('.nutrition-table, [data-test-id="nutrition-table"]')
        if table:
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td, th')
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True).lower()
                    value = self._parse_nutrition_value(cells[1].get_text())
                    if 'energy' in name and 'kcal' in name:
                        nutrition['calories'] = value
                    elif 'fat' in name and 'saturate' not in name:
                        nutrition['total_fat'] = value
                    elif 'saturate' in name:
                        nutrition['saturated_fat'] = value
                    elif 'carbohydrate' in name:
                        nutrition['total_carbohydrates'] = value
                    elif 'sugar' in name:
                        nutrition['total_sugars'] = value
                    elif 'protein' in name:
                        nutrition['protein'] = value
                    elif 'salt' in name:
                        nutrition['sodium'] = value
        return nutrition


class ASDASScraper(BaseScraper):
    """Scraper for ASDA (UK - Walmart owned)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/groceries/drinks"},
        {"name": "Food Cupboard", "url": "/groceries/food-cupboard"},
        {"name": "Frozen", "url": "/groceries/frozen"},
        {"name": "Fresh Food", "url": "/groceries/fresh-food"},
        {"name": "Bakery", "url": "/groceries/bakery"},
    ]
    
    def __init__(self):
        super().__init__("ASDA", "https://groceries.asda.com")
    
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
            items = soup.select('[data-auto-id="product"]')
            
            if not items:
                items = soup.select('.co-product')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_asda_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_asda_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/product/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/product/(\d+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-auto-id="product-title"]')
            if not name_elem:
                name_elem = element.select_one('.co-product__title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-auto-id="product-price"]')
            if not price_elem:
                price_elem = element.select_one('.co-product__price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'GBP',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing ASDA card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/product/(\d+)', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            ing_section = soup.select_one('[data-auto-id="ingredients"]')
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
                'currency': 'GBP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing ASDA product: {e}")
            return None


class MorrisonsScraper(BaseScraper):
    """Scraper for Morrisons (UK)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/browse/drinks"},
        {"name": "Food Cupboard", "url": "/browse/food-cupboard"},
        {"name": "Frozen", "url": "/browse/frozen"},
        {"name": "Fresh", "url": "/browse/fresh"},
        {"name": "Bakery", "url": "/browse/bakery"},
    ]
    
    def __init__(self):
        super().__init__("Morrisons", "https://groceries.morrisons.com")
    
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
            items = soup.select('[data-test="fop-item"]')
            
            if not items:
                items = soup.select('.product-tile')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_morrisons_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_morrisons_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/products/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/products/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-test="fop-title"]')
            if not name_elem:
                name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-test="fop-price"]')
            if not price_elem:
                price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'GBP',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Morrisons card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/products/([^/]+)', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            ing_section = soup.select_one('[data-test="ingredients"]')
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
                'currency': 'GBP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Morrisons product: {e}")
            return None


class WaitroseScraper(BaseScraper):
    """Scraper for Waitrose (UK - premium)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/ecom/shop/browse/groceries/drinks"},
        {"name": "Food Cupboard", "url": "/ecom/shop/browse/groceries/food_cupboard"},
        {"name": "Frozen", "url": "/ecom/shop/browse/groceries/frozen"},
        {"name": "Fresh", "url": "/ecom/shop/browse/groceries/fresh_and_chilled"},
        {"name": "Bakery", "url": "/ecom/shop/browse/groceries/bakery"},
    ]
    
    def __init__(self):
        super().__init__("Waitrose", "https://www.waitrose.com")
    
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
            items = soup.select('[data-testid="product-pod"]')
            
            if not items:
                items = soup.select('.product-pod')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_waitrose_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_waitrose_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/products/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/products/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-testid="product-pod-title"]')
            if not name_elem:
                name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-testid="product-pod-price"]')
            if not price_elem:
                price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'GBP',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Waitrose card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/products/([^/]+)', product_url)
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
                'currency': 'GBP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Waitrose product: {e}")
            return None


class IcelandScraper(BaseScraper):
    """Scraper for Iceland (UK - frozen foods specialist)"""
    
    FOOD_CATEGORIES = [
        {"name": "Frozen Food", "url": "/frozen"},
        {"name": "Drinks", "url": "/drinks"},
        {"name": "Food Cupboard", "url": "/food-cupboard"},
        {"name": "Chilled", "url": "/chilled"},
    ]
    
    def __init__(self):
        super().__init__("Iceland", "https://www.iceland.co.uk")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-tile')
        
        for item in items[:max_products]:
            product = self._parse_iceland_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_iceland_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/p/([^/]+)', href)
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
                'currency': 'GBP',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Iceland card: {e}")
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
            ing_section = soup.find(text=re.compile(r'ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'GBP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Iceland product: {e}")
            return None


# Factory functions
def create_sainsburys_scraper() -> SainsburysScraper:
    return SainsburysScraper()

def create_asda_scraper() -> ASDASScraper:
    return ASDASScraper()

def create_morrisons_scraper() -> MorrisonsScraper:
    return MorrisonsScraper()

def create_waitrose_scraper() -> WaitroseScraper:
    return WaitroseScraper()

def create_iceland_scraper() -> IcelandScraper:
    return IcelandScraper()
