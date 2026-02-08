"""
China Grocery Scrapers
Scrapers for major Chinese grocery retailers and e-commerce platforms
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class FreshippoScraper(BaseScraper):
    """Scraper for Freshippo/Hema (盒马鲜生 - Alibaba's grocery chain)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Freshippo", "https://www.freshhema.com")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .goods-item')
        
        for item in items[:max_products]:
            product = self._parse_freshippo_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_freshippo_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.goods-name, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.goods-price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'CNY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Freshippo card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1, .goods-title')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1]
            
            ingredients_text = None
            # Chinese: 配料表 (pèiliào biǎo) or 成分 (chéngfèn)
            ing_section = soup.find(text=re.compile(r'配料|成分|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CNY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Freshippo product: {e}")
            return None


class RTMartScraper(BaseScraper):
    """Scraper for RT-Mart (大润发 - Sun Art Retail)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("RT-Mart", "https://www.rt-mart.com.cn")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .goods-item')
        
        for item in items[:max_products]:
            product = self._parse_rtmart_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_rtmart_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name, .goods-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1] if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price, .goods-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'CNY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing RT-Mart card: {e}")
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
            ing_section = soup.find(text=re.compile(r'配料|成分|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CNY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing RT-Mart product: {e}")
            return None


class YonghuiScraper(BaseScraper):
    """Scraper for Yonghui Superstores (永辉超市)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Yonghui", "https://www.yonghui.com.cn")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product-item, .goods-item')
        
        for item in items[:max_products]:
            product = self._parse_yonghui_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_yonghui_card(self, element) -> Optional[Dict]:
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
                'currency': 'CNY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Yonghui card: {e}")
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
            ing_section = soup.find(text=re.compile(r'配料|成分|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CNY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Yonghui product: {e}")
            return None


class WumartScraper(BaseScraper):
    """Scraper for Wumart (物美超市)"""
    
    FOOD_CATEGORIES = [
        {"name": "Beverages", "url": "/category/beverages"},
        {"name": "Snacks", "url": "/category/snacks"},
        {"name": "Breakfast", "url": "/category/breakfast"},
        {"name": "Grocery", "url": "/category/grocery"},
        {"name": "Frozen", "url": "/category/frozen"},
    ]
    
    def __init__(self):
        super().__init__("Wumart", "https://www.wumart.com")
    
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
            product = self._parse_wumart_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_wumart_card(self, element) -> Optional[Dict]:
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
                'currency': 'CNY',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Wumart card: {e}")
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
            ing_section = soup.find(text=re.compile(r'配料|成分|ingredients', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CNY',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Wumart product: {e}")
            return None


# Factory functions
def create_freshippo_scraper() -> FreshippoScraper:
    return FreshippoScraper()

def create_rtmart_scraper() -> RTMartScraper:
    return RTMartScraper()

def create_yonghui_scraper() -> YonghuiScraper:
    return YonghuiScraper()

def create_wumart_scraper() -> WumartScraper:
    return WumartScraper()
