"""
Generic Scrapers for International Grocery Retailers
Provides scrapers for UK, EU, Australia, Asia, and Middle East retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class TescoScraper(BaseScraper):
    """Scraper for Tesco.com (UK)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/groceries/en-GB/shop/drinks/all"},
        {"name": "Food Cupboard", "url": "/groceries/en-GB/shop/food-cupboard/all"},
        {"name": "Frozen Food", "url": "/groceries/en-GB/shop/frozen-food/all"},
        {"name": "Fresh Food", "url": "/groceries/en-GB/shop/fresh-food/all"},
        {"name": "Bakery", "url": "/groceries/en-GB/shop/bakery/all"},
        {"name": "Dairy & Chilled", "url": "/groceries/en-GB/shop/dairy-and-chilled/all"},
    ]
    
    def __init__(self):
        super().__init__("Tesco", "https://www.tesco.com")
    
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
            items = soup.select('[data-auto="product-tile"]')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_tesco_card(item)
                if product:
                    products.append(product)
            
            page += 1
            if len(items) < 24:
                break
        
        return products
    
    def _parse_tesco_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/products/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/products/(\d+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-auto="product-tile--title"]')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-auto="price-value"]')
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
            logger.error(f"Error parsing Tesco card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'/products/(\d+)', product_url)
            product_id = match.group(1) if match else None
            
            # Get ingredients
            ingredients_text = None
            ing_section = soup.select_one('[id*="ingredients"]')
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            # Get nutrition
            nutrition = {}
            nutrition_table = soup.select_one('.nutrition-table')
            if nutrition_table:
                rows = nutrition_table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        field = cells[0].get_text(strip=True).lower()
                        value = self._parse_nutrition_value(cells[1].get_text())
                        if 'energy' in field and 'kcal' in field:
                            nutrition['calories'] = value
                        elif 'fat' in field and 'saturate' not in field:
                            nutrition['total_fat'] = value
                        elif 'saturate' in field:
                            nutrition['saturated_fat'] = value
                        elif 'carbohydrate' in field:
                            nutrition['total_carbohydrates'] = value
                        elif 'sugar' in field:
                            nutrition['total_sugars'] = value
                        elif 'protein' in field:
                            nutrition['protein'] = value
                        elif 'salt' in field:
                            nutrition['sodium'] = value
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': nutrition,
                'currency': 'GBP',
            }
        except Exception as e:
            logger.error(f"Error parsing Tesco product: {e}")
            return None


class WoolworthsScraper(BaseScraper):
    """Scraper for Woolworths.com.au (Australia)"""
    
    FOOD_CATEGORIES = [
        {"name": "Drinks", "url": "/shop/browse/drinks"},
        {"name": "Pantry", "url": "/shop/browse/pantry"},
        {"name": "Snacks & Confectionery", "url": "/shop/browse/snacks-confectionery"},
        {"name": "Freezer", "url": "/shop/browse/freezer"},
        {"name": "Dairy Eggs & Fridge", "url": "/shop/browse/dairy-eggs-fridge"},
        {"name": "Bakery", "url": "/shop/browse/bakery"},
    ]
    
    def __init__(self):
        super().__init__("Woolworths", "https://www.woolworths.com.au")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        page = 1
        
        while len(products) < max_products:
            url = f"{category_url}?pageNumber={page}"
            html = await self._fetch_page(url)
            if not html:
                break
            
            soup = self._parse_html(html)
            items = soup.select('.product-tile-v2')
            
            if not items:
                # Try JSON extraction
                json_products = self._extract_woolworths_json(html)
                if json_products:
                    products.extend(json_products[:max_products - len(products)])
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_woolworths_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _extract_woolworths_json(self, html: str) -> List[Dict]:
        products = []
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                items = data.get('search', {}).get('products', [])
                for item in items:
                    products.append({
                        'external_id': str(item.get('stockcode')),
                        'name': item.get('name'),
                        'brand': item.get('brand'),
                        'price': item.get('price'),
                        'currency': 'AUD',
                        'image_url': item.get('mediumImageFile'),
                        'url': f"{self.base_url}/shop/productdetails/{item.get('stockcode')}",
                        'barcode': item.get('barcode'),
                    })
            except json.JSONDecodeError:
                pass
        return products
    
    def _parse_woolworths_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/productdetails/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/productdetails/(\d+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('.product-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('.price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'AUD',
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Woolworths card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        # Try JSON extraction
        match = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.*?});', html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                product = data.get('product', {}).get('details', {})
                
                return {
                    'external_id': str(product.get('stockcode')),
                    'name': product.get('name'),
                    'brand': product.get('brand'),
                    'barcode': product.get('barcode'),
                    'price': product.get('price'),
                    'currency': 'AUD',
                    'url': product_url,
                    'ingredients_text': product.get('ingredients'),
                    'ingredients': self._parse_ingredients(product.get('ingredients', '')),
                    'nutrition': self._parse_woolworths_nutrition(product.get('nutritionalInformation', [])),
                }
            except Exception as e:
                logger.error(f"Error parsing Woolworths JSON: {e}")
        
        return None
    
    def _parse_woolworths_nutrition(self, nutrition_info: List) -> Dict:
        nutrition = {}
        for item in nutrition_info:
            name = item.get('name', '').lower()
            value = self._parse_nutrition_value(item.get('value'))
            
            if 'energy' in name and 'kj' not in name:
                nutrition['calories'] = value
            elif 'fat' in name and 'saturated' not in name:
                nutrition['total_fat'] = value
            elif 'saturated' in name:
                nutrition['saturated_fat'] = value
            elif 'carbohydrate' in name:
                nutrition['total_carbohydrates'] = value
            elif 'sugar' in name:
                nutrition['total_sugars'] = value
            elif 'protein' in name:
                nutrition['protein'] = value
            elif 'sodium' in name:
                nutrition['sodium'] = value
        
        return nutrition


class CarrefourScraper(BaseScraper):
    """Scraper for Carrefour (France/UAE)"""
    
    def __init__(self, region: str = "fr"):
        self.region = region
        if region == "uae":
            base_url = "https://www.carrefouruae.com"
            self.FOOD_CATEGORIES = [
                {"name": "Food Cupboard", "url": "/mafuae/en/c/NFUAE1100000"},
                {"name": "Beverages", "url": "/mafuae/en/c/NFUAE1200000"},
                {"name": "Frozen", "url": "/mafuae/en/c/NFUAE1500000"},
                {"name": "Dairy", "url": "/mafuae/en/c/NFUAE1300000"},
            ]
        else:
            base_url = "https://www.carrefour.fr"
            self.FOOD_CATEGORIES = [
                {"name": "Epicerie", "url": "/r/epicerie-sucree"},
                {"name": "Boissons", "url": "/r/boissons"},
                {"name": "Surgeles", "url": "/r/surgeles"},
                {"name": "Produits Laitiers", "url": "/r/produits-laitiers-oeufs-fromages"},
            ]
        
        super().__init__(f"Carrefour {'UAE' if region == 'uae' else 'France'}", base_url)
    
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
                product = self._parse_carrefour_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_carrefour_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/p/([^/]+)', href)
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
            
            currency = 'AED' if self.region == 'uae' else 'EUR'
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': currency,
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Carrefour card: {e}")
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
            
            # Get ingredients
            ingredients_text = None
            ing_section = soup.select_one('[data-testid="ingredients"]')
            if not ing_section:
                ing_section = soup.find(text=re.compile(r'ingr[eé]dients?', re.I))
                if ing_section:
                    ing_section = ing_section.find_parent()
            
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            currency = 'AED' if self.region == 'uae' else 'EUR'
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': currency,
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Carrefour product: {e}")
            return None


# Factory functions
def create_tesco_scraper() -> TescoScraper:
    return TescoScraper()

def create_woolworths_scraper() -> WoolworthsScraper:
    return WoolworthsScraper()

def create_carrefour_scraper(region: str = "fr") -> CarrefourScraper:
    return CarrefourScraper(region)
