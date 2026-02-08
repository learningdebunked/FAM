"""
Walmart Product Scraper
Scrapes processed food products from Walmart.com
"""

import asyncio
import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper, APIBasedScraper
import logging

logger = logging.getLogger(__name__)


class WalmartScraper(BaseScraper):
    """Scraper for Walmart.com products"""
    
    # Walmart's internal API endpoints (discovered through browser inspection)
    SEARCH_API = "https://www.walmart.com/orchestra/home/graphql"
    
    # Processed food categories to scrape
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/browse/food/beverages/976759_976782"},
        {"name": "Snacks", "url": "/browse/food/snacks-cookies-chips/976759_976787"},
        {"name": "Breakfast & Cereal", "url": "/browse/food/breakfast-cereal/976759_976783"},
        {"name": "Candy", "url": "/browse/food/candy/976759_1096070"},
        {"name": "Condiments", "url": "/browse/food/condiments-sauces-spices/976759_976794"},
        {"name": "Canned Goods", "url": "/browse/food/canned-goods/976759_976785"},
        {"name": "Frozen Foods", "url": "/browse/food/frozen/976759_976791"},
        {"name": "Dairy & Eggs", "url": "/browse/food/dairy-eggs/976759_976784"},
        {"name": "Deli", "url": "/browse/food/deli/976759_976793"},
        {"name": "Bakery & Bread", "url": "/browse/food/bakery-bread/976759_976779"},
    ]
    
    def __init__(self):
        super().__init__("Walmart", "https://www.walmart.com")
        
    async def get_categories(self) -> List[Dict[str, str]]:
        """Get Walmart food categories"""
        return [
            {"name": cat["name"], "url": f"{self.base_url}{cat['url']}"}
            for cat in self.FOOD_CATEGORIES
        ]
    
    async def get_products_in_category(self, category_url: str,
                                       max_products: int = 100) -> List[Dict]:
        """Get products from a Walmart category page"""
        products = []
        page = 1
        
        while len(products) < max_products:
            # Fetch category page
            url = f"{category_url}?page={page}"
            html = await self._fetch_page(url)
            
            if not html:
                break
            
            soup = self._parse_html(html)
            
            # Find product items - Walmart uses data attributes
            product_elements = soup.select('[data-item-id]')
            
            if not product_elements:
                # Try alternative selectors
                product_elements = soup.select('.search-result-gridview-item')
            
            if not product_elements:
                # Try finding JSON data in script tags
                products_from_json = self._extract_products_from_json(html)
                if products_from_json:
                    products.extend(products_from_json[:max_products - len(products)])
                break
            
            for elem in product_elements:
                if len(products) >= max_products:
                    break
                    
                product = self._parse_product_card(elem)
                if product:
                    products.append(product)
            
            # Check if there's a next page
            next_page = soup.select_one('[aria-label="Next Page"]')
            if not next_page or len(product_elements) == 0:
                break
                
            page += 1
        
        return products
    
    def _extract_products_from_json(self, html: str) -> List[Dict]:
        """Extract product data from embedded JSON in page"""
        products = []
        
        # Look for __NEXT_DATA__ or similar JSON blobs
        patterns = [
            r'__NEXT_DATA__\s*=\s*({.*?})\s*</script>',
            r'window\.__WML_REDUX_INITIAL_STATE__\s*=\s*({.*?});',
            r'"itemStacks":\s*(\[.*?\])',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    products = self._parse_json_products(data)
                    if products:
                        break
                except json.JSONDecodeError:
                    continue
        
        return products
    
    def _parse_json_products(self, data: Dict) -> List[Dict]:
        """Parse products from JSON data structure"""
        products = []
        
        # Navigate through possible data structures
        items = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common paths
            if 'props' in data:
                page_props = data.get('props', {}).get('pageProps', {})
                items = page_props.get('initialData', {}).get('searchResult', {}).get('itemStacks', [])
            elif 'searchResult' in data:
                items = data.get('searchResult', {}).get('itemStacks', [])
            elif 'items' in data:
                items = data.get('items', [])
        
        for item_stack in items:
            if isinstance(item_stack, dict) and 'items' in item_stack:
                for item in item_stack['items']:
                    product = self._parse_json_product(item)
                    if product:
                        products.append(product)
            elif isinstance(item_stack, dict):
                product = self._parse_json_product(item_stack)
                if product:
                    products.append(product)
        
        return products
    
    def _parse_json_product(self, item: Dict) -> Optional[Dict]:
        """Parse a single product from JSON"""
        try:
            product_id = item.get('usItemId') or item.get('id')
            name = item.get('name') or item.get('title')
            
            if not product_id or not name:
                return None
            
            # Get price
            price_info = item.get('priceInfo', {}) or item.get('price', {})
            price = None
            if isinstance(price_info, dict):
                price = price_info.get('currentPrice', {}).get('price')
                if not price:
                    price = price_info.get('price')
            elif isinstance(price_info, (int, float)):
                price = price_info
            
            # Get image
            image_info = item.get('imageInfo', {}) or item.get('image', {})
            image_url = None
            if isinstance(image_info, dict):
                image_url = image_info.get('thumbnailUrl') or image_info.get('url')
            elif isinstance(image_info, str):
                image_url = image_info
            
            return {
                'external_id': str(product_id),
                'name': name,
                'brand': item.get('brand'),
                'price': price,
                'image_url': image_url,
                'url': f"{self.base_url}/ip/{product_id}",
                'barcode': item.get('upc') or item.get('gtin'),
            }
        except Exception as e:
            logger.error(f"Error parsing JSON product: {e}")
            return None
    
    def _parse_product_card(self, element) -> Optional[Dict]:
        """Parse a product card HTML element"""
        try:
            # Get product ID
            product_id = element.get('data-item-id')
            
            # Get name
            name_elem = element.select_one('[data-automation-id="product-title"]')
            if not name_elem:
                name_elem = element.select_one('.product-title-link')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            # Get price
            price_elem = element.select_one('[data-automation-id="product-price"]')
            if not price_elem:
                price_elem = element.select_one('.price-main')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self._parse_price(price_text)
            
            # Get image
            img_elem = element.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            # Get link
            link_elem = element.select_one('a[href*="/ip/"]')
            product_url = link_elem.get('href') if link_elem else None
            if product_url and not product_url.startswith('http'):
                product_url = f"{self.base_url}{product_url}"
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'image_url': image_url,
                'url': product_url or f"{self.base_url}/ip/{product_id}",
            }
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        """Get detailed product information from product page"""
        html = await self._fetch_page(product_url)
        
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        # Try to extract from JSON first
        product_data = self._extract_product_json(html)
        
        if product_data:
            return product_data
        
        # Fall back to HTML parsing
        return self._parse_product_page(soup, product_url)
    
    def _extract_product_json(self, html: str) -> Optional[Dict]:
        """Extract product details from embedded JSON"""
        # Look for product data in script tags
        patterns = [
            r'__NEXT_DATA__\s*=\s*({.*?})\s*</script>',
            r'"product":\s*({.*?})\s*,\s*"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return self._parse_product_detail_json(data)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _parse_product_detail_json(self, data: Dict) -> Optional[Dict]:
        """Parse detailed product info from JSON"""
        try:
            # Navigate to product data
            product = None
            
            if 'props' in data:
                product = data.get('props', {}).get('pageProps', {}).get('initialData', {}).get('data', {}).get('product', {})
            elif 'product' in data:
                product = data.get('product', {})
            
            if not product:
                return None
            
            # Extract basic info
            result = {
                'external_id': product.get('usItemId'),
                'name': product.get('name'),
                'brand': product.get('brand'),
                'barcode': product.get('upc') or product.get('gtin13'),
                'description': product.get('shortDescription'),
                'image_url': product.get('imageInfo', {}).get('thumbnailUrl'),
                'price': product.get('priceInfo', {}).get('currentPrice', {}).get('price'),
            }
            
            # Extract ingredients
            ingredients_text = None
            nutrition_data = {}
            
            # Look in product attributes
            id_ml_info = product.get('idmlMap', {})
            if id_ml_info:
                # Ingredients
                ingredients_section = id_ml_info.get('Ingredients', {})
                if ingredients_section:
                    ingredients_text = ingredients_section.get('values', [{}])[0].get('value', '')
                
                # Nutrition
                nutrition_section = id_ml_info.get('Nutrition Facts', {})
                if nutrition_section:
                    nutrition_data = self._parse_nutrition_from_idml(nutrition_section)
            
            # Alternative: look in specifications
            specs = product.get('specifications', [])
            for spec in specs:
                if spec.get('name', '').lower() == 'ingredients':
                    ingredients_text = spec.get('value', '')
                elif 'nutrition' in spec.get('name', '').lower():
                    # Parse nutrition from spec
                    pass
            
            result['ingredients_text'] = ingredients_text
            result['ingredients'] = self._parse_ingredients(ingredients_text) if ingredients_text else []
            result['nutrition'] = nutrition_data
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing product detail JSON: {e}")
            return None
    
    def _parse_nutrition_from_idml(self, nutrition_section: Dict) -> Dict:
        """Parse nutrition data from Walmart's IDML format"""
        nutrition = {}
        
        values = nutrition_section.get('values', [])
        for item in values:
            name = item.get('name', '').lower()
            value = item.get('value', '')
            
            # Map common nutrition fields
            mappings = {
                'calories': 'calories',
                'total fat': 'total_fat',
                'saturated fat': 'saturated_fat',
                'trans fat': 'trans_fat',
                'cholesterol': 'cholesterol',
                'sodium': 'sodium',
                'total carbohydrate': 'total_carbohydrates',
                'dietary fiber': 'dietary_fiber',
                'total sugars': 'total_sugars',
                'added sugars': 'added_sugars',
                'protein': 'protein',
                'vitamin d': 'vitamin_d',
                'calcium': 'calcium',
                'iron': 'iron',
                'potassium': 'potassium',
            }
            
            for key, field in mappings.items():
                if key in name:
                    nutrition[field] = self._parse_nutrition_value(value)
                    break
        
        return nutrition
    
    def _parse_product_page(self, soup, product_url: str) -> Optional[Dict]:
        """Parse product details from HTML"""
        try:
            # Get product name
            name_elem = soup.select_one('h1[itemprop="name"]')
            if not name_elem:
                name_elem = soup.select_one('.prod-ProductTitle')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            # Get product ID from URL
            match = re.search(r'/ip/[^/]+/(\d+)', product_url)
            product_id = match.group(1) if match else None
            
            # Get brand
            brand_elem = soup.select_one('[itemprop="brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            # Get price
            price_elem = soup.select_one('[itemprop="price"]')
            price = None
            if price_elem:
                price = self._parse_price(price_elem.get('content') or price_elem.get_text())
            
            # Get image
            img_elem = soup.select_one('[data-testid="hero-image"] img')
            image_url = img_elem.get('src') if img_elem else None
            
            # Get ingredients
            ingredients_text = None
            ingredients_section = soup.select_one('[data-testid="ingredients-content"]')
            if ingredients_section:
                ingredients_text = ingredients_section.get_text(strip=True)
            else:
                # Try finding in specifications
                specs = soup.select('.specification-row')
                for spec in specs:
                    label = spec.select_one('.specification-label')
                    if label and 'ingredient' in label.get_text().lower():
                        value = spec.select_one('.specification-value')
                        if value:
                            ingredients_text = value.get_text(strip=True)
                            break
            
            # Get nutrition facts
            nutrition = {}
            nutrition_table = soup.select_one('.nutrition-facts-table')
            if nutrition_table:
                rows = nutrition_table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        if 'calorie' in name:
                            nutrition['calories'] = self._parse_nutrition_value(value)
                        elif 'total fat' in name:
                            nutrition['total_fat'] = self._parse_nutrition_value(value)
                        # ... add more mappings
            
            return {
                'external_id': product_id,
                'name': name,
                'brand': brand,
                'price': price,
                'image_url': image_url,
                'url': product_url,
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': nutrition,
            }
            
        except Exception as e:
            logger.error(f"Error parsing product page: {e}")
            return None


# Factory function
def create_walmart_scraper() -> WalmartScraper:
    """Create a Walmart scraper instance"""
    return WalmartScraper()
