"""
Target Product Scraper
Scrapes processed food products from Target.com
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class TargetScraper(BaseScraper):
    """Scraper for Target.com products"""
    
    # Target API endpoints
    REDSKY_API = "https://redsky.target.com/redsky_aggregations/v1"
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/c/beverages-grocery/-/N-5xt0r"},
        {"name": "Snacks", "url": "/c/chips-snacks-grocery/-/N-5xsy4"},
        {"name": "Breakfast & Cereal", "url": "/c/breakfast-cereal-grocery/-/N-5xt0e"},
        {"name": "Candy", "url": "/c/candy-grocery/-/N-5xt0a"},
        {"name": "Frozen Foods", "url": "/c/frozen-foods-grocery/-/N-5xszd"},
        {"name": "Dairy", "url": "/c/dairy-grocery/-/N-5xszf"},
        {"name": "Pantry", "url": "/c/pantry-grocery/-/N-5xszg"},
        {"name": "Deli", "url": "/c/deli-grocery/-/N-5xszh"},
    ]
    
    def __init__(self):
        super().__init__("Target", "https://www.target.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        """Get Target food categories"""
        return [
            {"name": cat["name"], "url": f"{self.base_url}{cat['url']}"}
            for cat in self.FOOD_CATEGORIES
        ]
    
    async def get_products_in_category(self, category_url: str,
                                       max_products: int = 100) -> List[Dict]:
        """Get products from a Target category page"""
        products = []
        offset = 0
        count = 24  # Products per page
        
        while len(products) < max_products:
            html = await self._fetch_page(f"{category_url}?Nao={offset}")
            
            if not html:
                break
            
            # Try to extract from JSON in page
            page_products = self._extract_products_from_page(html)
            
            if not page_products:
                break
            
            products.extend(page_products)
            offset += count
            
            if len(page_products) < count:
                break
        
        return products[:max_products]
    
    def _extract_products_from_page(self, html: str) -> List[Dict]:
        """Extract products from Target page"""
        products = []
        
        # Look for __TGT_DATA__ or similar
        patterns = [
            r'__TGT_DATA__\s*=\s*({.*?});?\s*</script>',
            r'"search":\s*({.*?"products".*?})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    products = self._parse_target_products(data)
                    if products:
                        break
                except json.JSONDecodeError:
                    continue
        
        # Fallback to HTML parsing
        if not products:
            soup = self._parse_html(html)
            product_cards = soup.select('[data-test="product-card"]')
            
            for card in product_cards:
                product = self._parse_product_card(card)
                if product:
                    products.append(product)
        
        return products
    
    def _parse_target_products(self, data: Dict) -> List[Dict]:
        """Parse products from Target JSON data"""
        products = []
        
        # Navigate to products array
        items = []
        if '__PRELOADED_QUERIES__' in data:
            queries = data.get('__PRELOADED_QUERIES__', {})
            for key, value in queries.items():
                if 'search' in str(key).lower():
                    items = value.get('data', {}).get('search', {}).get('products', [])
                    break
        elif 'search' in data:
            items = data.get('search', {}).get('products', [])
        elif 'products' in data:
            items = data.get('products', [])
        
        for item in items:
            try:
                tcin = item.get('tcin') or item.get('item', {}).get('tcin')
                name = item.get('title') or item.get('item', {}).get('product_description', {}).get('title')
                
                if not tcin or not name:
                    continue
                
                price_info = item.get('price', {})
                price = price_info.get('current_retail') or price_info.get('reg_retail')
                
                image_info = item.get('images', {}) or item.get('item', {}).get('enrichment', {}).get('images', {})
                image_url = image_info.get('primary_image_url') if isinstance(image_info, dict) else None
                
                products.append({
                    'external_id': str(tcin),
                    'name': name,
                    'brand': item.get('brand') or item.get('item', {}).get('product_description', {}).get('brand'),
                    'price': price,
                    'image_url': image_url,
                    'url': f"{self.base_url}/p/-/A-{tcin}",
                })
            except Exception as e:
                logger.error(f"Error parsing Target product: {e}")
                continue
        
        return products
    
    def _parse_product_card(self, element) -> Optional[Dict]:
        """Parse a product card HTML element"""
        try:
            link = element.select_one('a[href*="/p/"]')
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/A-(\d+)', href)
            product_id = match.group(1) if match else None
            
            name_elem = element.select_one('[data-test="product-title"]')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not product_id or not name:
                return None
            
            price_elem = element.select_one('[data-test="current-price"]')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            img_elem = element.select_one('img')
            image_url = img_elem.get('src') if img_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'image_url': image_url,
                'url': f"{self.base_url}{href}" if not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Target product card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        """Get detailed product information"""
        html = await self._fetch_page(product_url)
        
        if not html:
            return None
        
        # Extract TCIN from URL
        match = re.search(r'/A-(\d+)', product_url)
        tcin = match.group(1) if match else None
        
        # Try JSON extraction first
        product_data = self._extract_product_json(html, tcin)
        
        if product_data:
            return product_data
        
        # Fallback to HTML parsing
        return self._parse_product_page(html, product_url, tcin)
    
    def _extract_product_json(self, html: str, tcin: str) -> Optional[Dict]:
        """Extract product details from JSON"""
        match = re.search(r'__TGT_DATA__\s*=\s*({.*?});?\s*</script>', html, re.DOTALL)
        
        if not match:
            return None
        
        try:
            data = json.loads(match.group(1))
            
            # Find product in preloaded queries
            product = None
            queries = data.get('__PRELOADED_QUERIES__', {})
            
            for key, value in queries.items():
                if 'pdp' in str(key).lower() or 'product' in str(key).lower():
                    product = value.get('data', {}).get('product', {})
                    if product:
                        break
            
            if not product:
                return None
            
            # Extract details
            item = product.get('item', {})
            desc = item.get('product_description', {})
            
            result = {
                'external_id': tcin,
                'name': desc.get('title'),
                'brand': desc.get('brand'),
                'description': desc.get('downstream_description'),
                'barcode': item.get('primary_barcode'),
                'price': product.get('price', {}).get('current_retail'),
                'image_url': item.get('enrichment', {}).get('images', {}).get('primary_image_url'),
                'url': f"{self.base_url}/p/-/A-{tcin}",
            }
            
            # Get ingredients
            ingredients_text = None
            nutrition_data = {}
            
            # Look in product labels
            labels = item.get('product_labels', [])
            for label in labels:
                if label.get('label_type') == 'ingredients':
                    ingredients_text = label.get('value')
                elif label.get('label_type') == 'nutrition_facts':
                    nutrition_data = self._parse_nutrition_label(label.get('value', ''))
            
            # Alternative: look in wellness info
            wellness = item.get('wellness', {})
            if not ingredients_text:
                ingredients_text = wellness.get('ingredients')
            
            result['ingredients_text'] = ingredients_text
            result['ingredients'] = self._parse_ingredients(ingredients_text) if ingredients_text else []
            result['nutrition'] = nutrition_data
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting Target product JSON: {e}")
            return None
    
    def _parse_nutrition_label(self, label_text: str) -> Dict:
        """Parse nutrition facts from label text"""
        nutrition = {}
        
        patterns = {
            'calories': r'calories[:\s]+(\d+)',
            'total_fat': r'total fat[:\s]+([\d.]+)',
            'saturated_fat': r'saturated fat[:\s]+([\d.]+)',
            'trans_fat': r'trans fat[:\s]+([\d.]+)',
            'sodium': r'sodium[:\s]+([\d.]+)',
            'total_carbohydrates': r'total carbohydrate[s]?[:\s]+([\d.]+)',
            'dietary_fiber': r'dietary fiber[:\s]+([\d.]+)',
            'total_sugars': r'total sugars?[:\s]+([\d.]+)',
            'protein': r'protein[:\s]+([\d.]+)',
        }
        
        label_lower = label_text.lower()
        for field, pattern in patterns.items():
            match = re.search(pattern, label_lower)
            if match:
                try:
                    nutrition[field] = float(match.group(1))
                except ValueError:
                    pass
        
        return nutrition
    
    def _parse_product_page(self, html: str, product_url: str, tcin: str) -> Optional[Dict]:
        """Parse product page HTML"""
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('[data-test="product-title"]')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            brand_elem = soup.select_one('[data-test="product-brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            price_elem = soup.select_one('[data-test="product-price"]')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            img_elem = soup.select_one('[data-test="product-image"] img')
            image_url = img_elem.get('src') if img_elem else None
            
            # Get ingredients
            ingredients_text = None
            ingredients_section = soup.select_one('[data-test="ingredientsContent"]')
            if ingredients_section:
                ingredients_text = ingredients_section.get_text(strip=True)
            
            return {
                'external_id': tcin,
                'name': name,
                'brand': brand,
                'price': price,
                'image_url': image_url,
                'url': product_url,
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Target product page: {e}")
            return None


def create_target_scraper() -> TargetScraper:
    """Create a Target scraper instance"""
    return TargetScraper()
