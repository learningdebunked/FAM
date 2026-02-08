"""
North America Grocery Scrapers
Scrapers for USA and Canada grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class KrogerScraper(BaseScraper):
    """Scraper for Kroger.com (USA - largest supermarket chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/pl/beverages/06"},
        {"name": "Snacks", "url": "/pl/snacks/07"},
        {"name": "Breakfast", "url": "/pl/breakfast/08"},
        {"name": "Candy", "url": "/pl/candy/09"},
        {"name": "Canned Goods", "url": "/pl/canned-goods/10"},
        {"name": "Condiments", "url": "/pl/condiments-sauces/11"},
        {"name": "Frozen", "url": "/pl/frozen/04"},
        {"name": "Dairy", "url": "/pl/dairy/01"},
    ]
    
    def __init__(self):
        super().__init__("Kroger", "https://www.kroger.com")
    
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
            
            page_products = self._extract_kroger_products(html)
            if not page_products:
                break
            
            products.extend(page_products)
            page += 1
        
        return products[:max_products]
    
    def _extract_kroger_products(self, html: str) -> List[Dict]:
        products = []
        soup = self._parse_html(html)
        
        # Try to find product cards
        items = soup.select('[data-testid="product-card"]')
        if not items:
            items = soup.select('.ProductCard')
        
        for item in items:
            try:
                link = item.select_one('a[href*="/p/"]')
                if not link:
                    continue
                
                href = link.get('href', '')
                match = re.search(r'/p/([^/]+)/(\d+)', href)
                product_id = match.group(2) if match else None
                
                name_elem = item.select_one('[data-testid="product-title"]')
                if not name_elem:
                    name_elem = item.select_one('.ProductDescription-truncated')
                name = name_elem.get_text(strip=True) if name_elem else None
                
                if not product_id or not name:
                    continue
                
                price_elem = item.select_one('[data-testid="product-price"]')
                price = self._parse_price(price_elem.get_text()) if price_elem else None
                
                img_elem = item.select_one('img')
                image_url = img_elem.get('src') if img_elem else None
                
                products.append({
                    'external_id': product_id,
                    'name': name,
                    'price': price,
                    'currency': 'USD',
                    'image_url': image_url,
                    'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
                })
            except Exception as e:
                logger.error(f"Error parsing Kroger product: {e}")
        
        return products
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/p/[^/]+/(\d+)', product_url)
            product_id = match.group(1) if match else None
            
            # Get ingredients
            ingredients_text = None
            ing_section = soup.select_one('[data-testid="product-ingredients"]')
            if not ing_section:
                ing_section = soup.find(text=re.compile(r'ingredients', re.I))
                if ing_section:
                    ing_section = ing_section.find_parent()
            
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            # Get nutrition
            nutrition = self._parse_nutrition_table(soup)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'USD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': nutrition,
            }
        except Exception as e:
            logger.error(f"Error parsing Kroger product details: {e}")
            return None
    
    def _parse_nutrition_table(self, soup) -> Dict:
        nutrition = {}
        table = soup.select_one('.NutritionLabel')
        if table:
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True).lower()
                    value = self._parse_nutrition_value(cells[1].get_text())
                    if 'calorie' in name:
                        nutrition['calories'] = value
                    elif 'total fat' in name:
                        nutrition['total_fat'] = value
                    elif 'sodium' in name:
                        nutrition['sodium'] = value
                    elif 'carbohydrate' in name:
                        nutrition['total_carbohydrates'] = value
                    elif 'protein' in name:
                        nutrition['protein'] = value
        return nutrition


class CostcoScraper(BaseScraper):
    """Scraper for Costco.com (USA - warehouse club)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/c/grocery-household/beverages"},
        {"name": "Snacks", "url": "/c/grocery-household/snacks-candy-nuts"},
        {"name": "Breakfast", "url": "/c/grocery-household/breakfast"},
        {"name": "Pantry", "url": "/c/grocery-household/pantry"},
        {"name": "Frozen", "url": "/c/grocery-household/frozen-food"},
    ]
    
    def __init__(self):
        super().__init__("Costco", "https://www.costco.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        offset = 0
        
        while len(products) < max_products:
            url = f"{category_url}?offset={offset}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-tile')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_costco_card(item)
                if product:
                    products.append(product)
            
            offset += 24
        
        return products
    
    def _parse_costco_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*=".product."]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'\.product\.(\d+)\.html', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.description')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            img_elem = element.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'USD',
                'image_url': image_url,
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Costco card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'\.product\.(\d+)\.html', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            specs = soup.select('.product-info-specs tr')
            for spec in specs:
                label = spec.select_one('th')
                if label and 'ingredient' in label.get_text().lower():
                    value = spec.select_one('td')
                    if value:
                        ingredients_text = value.get_text(strip=True)
                        break
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'USD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Costco product: {e}")
            return None


class SafewayScraper(BaseScraper):
    """Scraper for Safeway.com (USA)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/shop/aisles/beverages.3132.html"},
        {"name": "Snacks", "url": "/shop/aisles/snacks-candy.3124.html"},
        {"name": "Breakfast", "url": "/shop/aisles/breakfast.3108.html"},
        {"name": "Canned Goods", "url": "/shop/aisles/canned-goods-soups.3110.html"},
        {"name": "Frozen", "url": "/shop/aisles/frozen.3114.html"},
    ]
    
    def __init__(self):
        super().__init__("Safeway", "https://www.safeway.com")
    
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
            items = soup.select('.product-item')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_safeway_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_safeway_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/shop/product-details"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'\.(\d+)\.html', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'USD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Safeway card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'\.(\d+)\.html', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            ing_section = soup.select_one('.product-ingredients')
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'USD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Safeway product: {e}")
            return None


class PublixScraper(BaseScraper):
    """Scraper for Publix.com (USA - Southeast)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/shop/beverages"},
        {"name": "Snacks", "url": "/shop/snacks"},
        {"name": "Breakfast", "url": "/shop/breakfast"},
        {"name": "Canned Goods", "url": "/shop/canned-goods"},
        {"name": "Frozen", "url": "/shop/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Publix", "https://www.publix.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-card')
        
        for item in items[:max_products]:
            product = self._parse_publix_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_publix_card(self, element) -> Optional[Dict]:
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
                'currency': 'USD',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Publix card: {e}")
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
            ing_section = soup.select_one('.ingredients')
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'USD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Publix product: {e}")
            return None


class LoblawsScraper(BaseScraper):
    """Scraper for Loblaws.ca (Canada - largest grocery chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/food/drinks/c/27985"},
        {"name": "Snacks", "url": "/food/pantry/snacks/c/27998"},
        {"name": "Breakfast", "url": "/food/pantry/breakfast-foods/c/27994"},
        {"name": "Canned Goods", "url": "/food/pantry/canned-food/c/27995"},
        {"name": "Frozen", "url": "/food/frozen/c/27986"},
    ]
    
    def __init__(self):
        super().__init__("Loblaws", "https://www.loblaws.ca")
    
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
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_loblaws_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_loblaws_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/p/([^/]+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-testid="product-title"]')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-testid="product-price"]')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'CAD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Loblaws card: {e}")
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
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CAD',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Loblaws product: {e}")
            return None


# Factory functions
def create_kroger_scraper() -> KrogerScraper:
    return KrogerScraper()

def create_costco_scraper() -> CostcoScraper:
    return CostcoScraper()

def create_safeway_scraper() -> SafewayScraper:
    return SafewayScraper()

def create_publix_scraper() -> PublixScraper:
    return PublixScraper()

def create_loblaws_scraper() -> LoblawsScraper:
    return LoblawsScraper()
