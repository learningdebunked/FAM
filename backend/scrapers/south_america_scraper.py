"""
South America Grocery Scrapers
Scrapers for Brazil, Argentina, Chile, Colombia grocery retailers
"""

import re
import json
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)


class CencosudScraper(BaseScraper):
    """Scraper for Cencosud (Chile - Jumbo, Santa Isabel)"""
    
    FOOD_CATEGORIES = [
        {"name": "Bebidas", "url": "/bebidas"},
        {"name": "Snacks", "url": "/snacks-y-dulces"},
        {"name": "Desayuno", "url": "/desayuno"},
        {"name": "Despensa", "url": "/despensa"},
        {"name": "Congelados", "url": "/congelados"},
    ]
    
    def __init__(self):
        super().__init__("Cencosud", "https://www.jumbo.cl")
    
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
            items = soup.select('.product-item, .vtex-product-summary')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_cencosud_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_cencosud_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p"]')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name, .vtex-product-summary-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1].replace('/p', '') if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price, .vtex-product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'CLP',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Cencosud card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1].replace('/p', '')
            
            ingredients_text = None
            ing_section = soup.select_one('.product-ingredients, [data-specification="Ingredientes"]')
            if ing_section:
                ingredients_text = ing_section.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'CLP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Cencosud product: {e}")
            return None


class GrupoExitoScraper(BaseScraper):
    """Scraper for Grupo Éxito (Colombia - largest retailer)"""
    
    FOOD_CATEGORIES = [
        {"name": "Bebidas", "url": "/mercado/bebidas"},
        {"name": "Snacks", "url": "/mercado/snacks-dulces"},
        {"name": "Desayuno", "url": "/mercado/desayuno-lonchera"},
        {"name": "Despensa", "url": "/mercado/despensa"},
        {"name": "Congelados", "url": "/mercado/congelados"},
    ]
    
    def __init__(self):
        super().__init__("Grupo Exito", "https://www.exito.com")
    
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
            items = soup.select('.vtex-product-summary, .product-card')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_exito_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_exito_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p"]')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.vtex-product-summary-name, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1].replace('/p', '') if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.vtex-product-price, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'COP',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Exito card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1].replace('/p', '')
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredientes', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'COP',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Exito product: {e}")
            return None


class PaoDeAcucarScraper(BaseScraper):
    """Scraper for Pão de Açúcar (Brazil - GPA)"""
    
    FOOD_CATEGORIES = [
        {"name": "Bebidas", "url": "/bebidas"},
        {"name": "Biscoitos e Snacks", "url": "/biscoitos-e-snacks"},
        {"name": "Matinais", "url": "/matinais"},
        {"name": "Mercearia", "url": "/mercearia"},
        {"name": "Congelados", "url": "/congelados"},
    ]
    
    def __init__(self):
        super().__init__("Pao de Acucar", "https://www.paodeacucar.com")
    
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
            items = soup.select('.product-card, .vtex-product-summary')
            
            if not items:
                break
            
            for item in items:
                if len(products) >= max_products:
                    break
                product = self._parse_pda_card(item)
                if product:
                    products.append(product)
            
            page += 1
        
        return products
    
    def _parse_pda_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a[href*="/p"]')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = href.split('/')[-1].replace('/p', '') if href else name.replace(' ', '-')
            
            price_elem = element.select_one('.product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'BRL',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Pao de Acucar card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            product_id = product_url.split('/')[-1].replace('/p', '')
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredientes', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'BRL',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Pao de Acucar product: {e}")
            return None


class CotoScraper(BaseScraper):
    """Scraper for Coto (Argentina)"""
    
    FOOD_CATEGORIES = [
        {"name": "Bebidas", "url": "/bebidas"},
        {"name": "Snacks", "url": "/almacen/snacks"},
        {"name": "Desayuno", "url": "/almacen/desayuno"},
        {"name": "Almacen", "url": "/almacen"},
        {"name": "Congelados", "url": "/congelados"},
    ]
    
    def __init__(self):
        super().__init__("Coto", "https://www.cotodigital3.com.ar")
    
    async def get_categories(self) -> List[Dict[str, str]]:
        return [{"name": c["name"], "url": f"{self.base_url}{c['url']}"} for c in self.FOOD_CATEGORIES]
    
    async def get_products_in_category(self, category_url: str, max_products: int = 100) -> List[Dict]:
        products = []
        html = await self._fetch_page(category_url)
        if not html:
            return products
        
        soup = self._parse_html(html)
        items = soup.select('.product_info_container, .product-item')
        
        for item in items[:max_products]:
            product = self._parse_coto_card(item)
            if product:
                products.append(product)
        
        return products
    
    def _parse_coto_card(self, element) -> Optional[Dict]:
        try:
            link = element.select_one('a')
            if not link:
                return None
            
            href = link.get('href', '')
            name_elem = element.select_one('.descrip_full, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            if not name:
                return None
            
            product_id = re.search(r'(\d+)', href).group(1) if re.search(r'(\d+)', href) else name.replace(' ', '-')
            
            price_elem = element.select_one('.atg_store_newPrice, .product-price')
            price = self._parse_price(price_elem.get_text()) if price_elem else None
            
            return {
                'external_id': product_id,
                'name': name,
                'price': price,
                'currency': 'ARS',
                'url': f"{self.base_url}{href}" if href and not href.startswith('http') else href,
            }
        except Exception as e:
            logger.error(f"Error parsing Coto card: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict]:
        html = await self._fetch_page(product_url)
        if not html:
            return None
        
        soup = self._parse_html(html)
        
        try:
            name_elem = soup.select_one('h1, .product-name')
            name = name_elem.get_text(strip=True) if name_elem else None
            
            match = re.search(r'(\d+)', product_url)
            product_id = match.group(1) if match else None
            
            ingredients_text = None
            ing_section = soup.find(text=re.compile(r'ingredientes', re.I))
            if ing_section:
                parent = ing_section.find_parent()
                if parent:
                    ingredients_text = parent.get_text(strip=True)
            
            return {
                'external_id': product_id,
                'name': name,
                'url': product_url,
                'currency': 'ARS',
                'ingredients_text': ingredients_text,
                'ingredients': self._parse_ingredients(ingredients_text) if ingredients_text else [],
                'nutrition': {},
            }
        except Exception as e:
            logger.error(f"Error parsing Coto product: {e}")
            return None


# Factory functions
def create_cencosud_scraper() -> CencosudScraper:
    return CencosudScraper()

def create_grupo_exito_scraper() -> GrupoExitoScraper:
    return GrupoExitoScraper()

def create_pao_de_acucar_scraper() -> PaoDeAcucarScraper:
    return PaoDeAcucarScraper()

def create_coto_scraper() -> CotoScraper:
    return CotoScraper()
