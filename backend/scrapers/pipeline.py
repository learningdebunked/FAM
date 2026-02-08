"""
FAM Data Pipeline Orchestrator
Manages the entire scraping, storage, and analysis pipeline
"""

import asyncio
import sys
import os
from typing import List, Dict, Optional, Type
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import get_db, DatabaseManager
from scrapers.base_scraper import BaseScraper
# US
from scrapers.walmart_scraper import WalmartScraper
from scrapers.target_scraper import TargetScraper
from scrapers.north_america_scraper import KrogerScraper, CostcoScraper, SafewayScraper, PublixScraper, LoblawsScraper
# South America
from scrapers.south_america_scraper import CencosudScraper, GrupoExitoScraper, PaoDeAcucarScraper, CotoScraper
# UK
from scrapers.generic_scraper import TescoScraper
from scrapers.uk_scraper import SainsburysScraper, ASDASScraper, MorrisonsScraper, WaitroseScraper, IcelandScraper
# Europe
from scrapers.generic_scraper import CarrefourScraper
# Australia/NZ
from scrapers.generic_scraper import WoolworthsScraper
from scrapers.australia_nz_scraper import ColesScraper, IGAScraper, CountdownScraper, PaknSaveScraper, NewWorldScraper
# Asia
from scrapers.asia_scraper import FairPriceScraper, BigBazaarScraper, DMartScraper, AeonScraper, EMartScraper, LotteMartScraper
# China
from scrapers.china_scraper import FreshippoScraper, RTMartScraper, YonghuiScraper, WumartScraper
# Middle East & Turkey
from scrapers.middle_east_scraper import LuluHypermarketScraper, SpinneysScraper, ChoithramsScraper, MigrosTurkeyScraper, BIMScraper, A101Scraper
# Russia
from scrapers.russia_scraper import MagnitScraper, X5RetailScraper, LentaScraper, PerekrestokScraper
# Africa
from scrapers.africa_scraper import ShopriteScraper, PicknPayScraper, CheckersScraper, WoolworthsSAScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperRegistry:
    """Registry of available scrapers"""
    
    SCRAPERS: Dict[str, Type[BaseScraper]] = {
        # ==================== North America ====================
        'Walmart': WalmartScraper,
        'Target': TargetScraper,
        'Kroger': KrogerScraper,
        'Costco': CostcoScraper,
        'Safeway': SafewayScraper,
        'Publix': PublixScraper,
        'Loblaws': LoblawsScraper,  # Canada
        
        # ==================== South America ====================
        'Cencosud': CencosudScraper,  # Chile
        'Grupo Exito': GrupoExitoScraper,  # Colombia
        'Pao de Acucar': PaoDeAcucarScraper,  # Brazil
        'Coto': CotoScraper,  # Argentina
        
        # ==================== UK ====================
        'Tesco': TescoScraper,
        'Sainsburys': SainsburysScraper,
        'ASDA': ASDASScraper,
        'Morrisons': MorrisonsScraper,
        'Waitrose': WaitroseScraper,
        'Iceland': IcelandScraper,
        
        # ==================== Europe ====================
        'Carrefour': CarrefourScraper,  # France
        
        # ==================== Australia/NZ ====================
        'Woolworths': WoolworthsScraper,  # Australia
        'Coles': ColesScraper,  # Australia
        'IGA': IGAScraper,  # Australia
        'Countdown': CountdownScraper,  # New Zealand
        'PAKnSAVE': PaknSaveScraper,  # New Zealand
        'New World': NewWorldScraper,  # New Zealand
        
        # ==================== Asia ====================
        'FairPrice': FairPriceScraper,  # Singapore
        'Big Bazaar': BigBazaarScraper,  # India
        'DMart': DMartScraper,  # India
        'Aeon': AeonScraper,  # Japan
        'E-Mart': EMartScraper,  # South Korea
        'Lotte Mart': LotteMartScraper,  # South Korea
        
        # ==================== China ====================
        'Freshippo': FreshippoScraper,  # Alibaba
        'RT-Mart': RTMartScraper,
        'Yonghui': YonghuiScraper,
        'Wumart': WumartScraper,
        
        # ==================== Middle East ====================
        'Lulu Hypermarket': LuluHypermarketScraper,  # UAE
        'Spinneys': SpinneysScraper,  # UAE
        'Choithrams': ChoithramsScraper,  # UAE
        
        # ==================== Turkey ====================
        'Migros Turkey': MigrosTurkeyScraper,
        'BIM': BIMScraper,
        'A101': A101Scraper,
        
        # ==================== Russia ====================
        'Magnit': MagnitScraper,
        'Pyaterochka': X5RetailScraper,
        'Lenta': LentaScraper,
        'Perekrestok': PerekrestokScraper,
        
        # ==================== Africa ====================
        'Shoprite': ShopriteScraper,  # South Africa
        'Pick n Pay': PicknPayScraper,  # South Africa
        'Checkers': CheckersScraper,  # South Africa
        'Woolworths SA': WoolworthsSAScraper,  # South Africa
    }
    
    @classmethod
    def get_scraper(cls, retailer_name: str) -> Optional[BaseScraper]:
        """Get scraper instance for a retailer"""
        scraper_class = cls.SCRAPERS.get(retailer_name)
        if scraper_class:
            if retailer_name == 'Carrefour UAE':
                return CarrefourScraper(region='uae')
            return scraper_class()
        return None
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List available scrapers"""
        return list(cls.SCRAPERS.keys())


class DataPipeline:
    """
    Main data pipeline orchestrator for FAM
    
    Pipeline stages:
    1. Scrape products from retailers
    2. Parse and normalize data
    3. Store in local database
    4. Analyze ingredients against risk database
    5. Generate alternatives mappings
    """
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or get_db()
        self.stats = {
            'total_scraped': 0,
            'total_stored': 0,
            'total_analyzed': 0,
            'errors': []
        }
    
    async def run_full_pipeline(self, 
                                retailers: List[str] = None,
                                max_products_per_category: int = 50,
                                analyze: bool = True,
                                generate_alternatives: bool = True):
        """
        Run the complete data pipeline
        
        Args:
            retailers: List of retailer names to scrape (None = all)
            max_products_per_category: Max products per category
            analyze: Whether to analyze products after scraping
            generate_alternatives: Whether to generate alternatives
        """
        logger.info("=" * 60)
        logger.info("Starting FAM Data Pipeline")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Get retailers to scrape
        if retailers is None:
            db_retailers = self.db.get_retailers()
            retailers = [r['name'] for r in db_retailers if r['name'] in ScraperRegistry.SCRAPERS]
        
        logger.info(f"Retailers to scrape: {retailers}")
        
        # Stage 1: Scrape products
        for retailer_name in retailers:
            await self._scrape_retailer(retailer_name, max_products_per_category)
        
        # Stage 2: Analyze products
        if analyze:
            await self._analyze_all_products()
        
        # Stage 3: Generate alternatives
        if generate_alternatives:
            await self._generate_alternatives()
        
        # Print summary
        elapsed = (datetime.now() - start_time).total_seconds()
        self._print_summary(elapsed)
    
    async def _scrape_retailer(self, retailer_name: str, max_products: int):
        """Scrape products from a single retailer"""
        logger.info(f"\n{'='*40}")
        logger.info(f"Scraping: {retailer_name}")
        logger.info(f"{'='*40}")
        
        scraper = ScraperRegistry.get_scraper(retailer_name)
        if not scraper:
            logger.warning(f"No scraper available for {retailer_name}")
            return
        
        # Get retailer ID from database
        retailer = self.db.get_retailer_by_name(retailer_name)
        if not retailer:
            logger.error(f"Retailer {retailer_name} not found in database")
            return
        
        retailer_id = retailer['id']
        
        # Create scrape job
        job_id = self.db.create_scrape_job(retailer_id)
        
        try:
            async with scraper:
                products = await scraper.scrape_all(max_products_per_category=max_products)
                
                logger.info(f"Scraped {len(products)} products from {retailer_name}")
                
                # Store products
                stored_count = 0
                for product in products:
                    try:
                        product_id = self._store_product(retailer_id, product)
                        if product_id:
                            stored_count += 1
                    except Exception as e:
                        logger.error(f"Error storing product: {e}")
                        self.stats['errors'].append(str(e))
                
                self.stats['total_scraped'] += len(products)
                self.stats['total_stored'] += stored_count
                
                # Update job status
                self.db.update_scrape_job(
                    job_id,
                    status='completed',
                    total_products=len(products),
                    scraped_products=stored_count,
                    failed_products=len(products) - stored_count
                )
                
                # Update retailer last scraped
                self.db.update_retailer_last_scraped(retailer_id)
                
        except Exception as e:
            logger.error(f"Error scraping {retailer_name}: {e}")
            self.stats['errors'].append(f"{retailer_name}: {str(e)}")
            self.db.update_scrape_job(job_id, status='failed', error_message=str(e))
    
    def _store_product(self, retailer_id: int, product: Dict) -> Optional[int]:
        """Store a product and its related data"""
        if not product.get('name'):
            return None
        
        # Get or create category
        category_id = None
        if product.get('category'):
            # Simple category lookup - could be enhanced
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM categories WHERE name = ?",
                    (product['category'],)
                )
                row = cursor.fetchone()
                if row:
                    category_id = row['id']
        
        # Insert product
        product_data = {
            'retailer_id': retailer_id,
            'external_id': product.get('external_id'),
            'barcode': product.get('barcode'),
            'name': product.get('name'),
            'brand': product.get('brand'),
            'category_id': category_id,
            'description': product.get('description'),
            'image_url': product.get('image_url'),
            'price': product.get('price'),
            'currency': product.get('currency', 'USD'),
            'serving_size': product.get('serving_size'),
            'product_url': product.get('url'),
            'is_processed': True,
        }
        
        product_id = self.db.insert_product(product_data)
        
        # Insert ingredients
        if product.get('ingredients_text') or product.get('ingredients'):
            self.db.insert_ingredients(
                product_id,
                product.get('ingredients_text', ''),
                product.get('ingredients', [])
            )
        
        # Insert nutrition
        if product.get('nutrition'):
            self.db.insert_nutrition(product_id, product['nutrition'])
        
        return product_id
    
    async def _analyze_all_products(self):
        """Analyze all products that haven't been analyzed"""
        logger.info("\n" + "="*40)
        logger.info("Analyzing products")
        logger.info("="*40)
        
        # Get risk ingredients from database
        risk_ingredients = self.db.get_risk_ingredients()
        risk_map = {r['canonical_name'].lower(): r for r in risk_ingredients}
        
        # Get products without analysis
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.id, p.name, i.parsed_ingredients
                FROM products p
                LEFT JOIN ingredients i ON p.id = i.product_id
                LEFT JOIN product_analysis pa ON p.id = pa.product_id
                WHERE pa.id IS NULL AND i.parsed_ingredients IS NOT NULL
                LIMIT 1000
            """)
            products = cursor.fetchall()
        
        logger.info(f"Found {len(products)} products to analyze")
        
        for product in products:
            try:
                import json
                ingredients = json.loads(product['parsed_ingredients']) if product['parsed_ingredients'] else []
                
                analysis = self._analyze_product(ingredients, risk_map)
                
                self.db.save_product_analysis(product['id'], analysis)
                self.stats['total_analyzed'] += 1
                
            except Exception as e:
                logger.error(f"Error analyzing product {product['id']}: {e}")
    
    def _analyze_product(self, ingredients: List[str], risk_map: Dict) -> Dict:
        """Analyze a product's ingredients against risk database"""
        flagged = []
        risk_score = 0
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Check against risk ingredients
            for risk_name, risk_info in risk_map.items():
                if risk_name in ingredient_lower:
                    flagged.append({
                        'ingredient': ingredient,
                        'canonical_name': risk_info['canonical_name'],
                        'risk_level': risk_info['risk_level'],
                        'category': risk_info['category'],
                        'affected_profiles': risk_info['affected_profiles'],
                    })
                    
                    # Add to risk score
                    if risk_info['risk_level'] == 'high':
                        risk_score += 25
                    elif risk_info['risk_level'] == 'medium':
                        risk_score += 15
                    elif risk_info['risk_level'] == 'low':
                        risk_score += 5
                    break
        
        risk_score = min(risk_score, 100)
        overall_score = 100 - risk_score
        
        # Determine risk level
        if overall_score >= 80:
            risk_level = 'safe'
        elif overall_score >= 60:
            risk_level = 'low'
        elif overall_score >= 40:
            risk_level = 'medium'
        elif overall_score >= 20:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return {
            'overall_score': overall_score,
            'risk_level': risk_level,
            'flagged_ingredients': flagged,
            'total_ingredients': len(ingredients),
            'flagged_count': len(flagged),
        }
    
    async def _generate_alternatives(self):
        """Generate healthy alternatives for products"""
        logger.info("\n" + "="*40)
        logger.info("Generating alternatives")
        logger.info("="*40)
        
        # Get products with high risk scores
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.id, p.name, p.category_id, pa.overall_score, pa.risk_level
                FROM products p
                JOIN product_analysis pa ON p.id = pa.product_id
                WHERE pa.risk_level IN ('medium', 'high', 'critical')
                LIMIT 500
            """)
            risky_products = cursor.fetchall()
        
        logger.info(f"Found {len(risky_products)} products needing alternatives")
        
        for product in risky_products:
            # Find healthier alternatives in same category
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT p.id, p.name, pa.overall_score
                    FROM products p
                    JOIN product_analysis pa ON p.id = pa.product_id
                    WHERE p.category_id = ?
                    AND pa.overall_score > ?
                    AND p.id != ?
                    ORDER BY pa.overall_score DESC
                    LIMIT 5
                """, (product['category_id'], product['overall_score'], product['id']))
                alternatives = cursor.fetchall()
            
            for alt in alternatives:
                score_improvement = alt['overall_score'] - product['overall_score']
                self.db.save_alternative(
                    product['id'],
                    alt['id'],
                    f"Healthier option with {score_improvement:.0f} point improvement",
                    score_improvement
                )
    
    def _print_summary(self, elapsed_seconds: float):
        """Print pipeline summary"""
        logger.info("\n" + "="*60)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*60)
        logger.info(f"Total products scraped: {self.stats['total_scraped']}")
        logger.info(f"Total products stored: {self.stats['total_stored']}")
        logger.info(f"Total products analyzed: {self.stats['total_analyzed']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")
        logger.info(f"Time elapsed: {elapsed_seconds:.1f} seconds")
        
        if self.stats['errors']:
            logger.info("\nErrors encountered:")
            for error in self.stats['errors'][:10]:
                logger.info(f"  - {error}")
        
        # Print database stats
        db_stats = self.db.get_stats()
        logger.info("\nDatabase Statistics:")
        logger.info(f"  Total products: {db_stats['total_products']}")
        logger.info(f"  Products with ingredients: {db_stats['products_with_ingredients']}")
        logger.info(f"  Products with nutrition: {db_stats['products_with_nutrition']}")
        logger.info(f"  Analyzed products: {db_stats['analyzed_products']}")


async def run_pipeline(retailers: List[str] = None, max_products: int = 50):
    """Convenience function to run the pipeline"""
    pipeline = DataPipeline()
    await pipeline.run_full_pipeline(
        retailers=retailers,
        max_products_per_category=max_products
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='FAM Data Pipeline')
    parser.add_argument('--retailers', nargs='+', help='Retailers to scrape')
    parser.add_argument('--max-products', type=int, default=50, help='Max products per category')
    parser.add_argument('--no-analyze', action='store_true', help='Skip analysis')
    parser.add_argument('--no-alternatives', action='store_true', help='Skip alternatives generation')
    
    args = parser.parse_args()
    
    pipeline = DataPipeline()
    asyncio.run(pipeline.run_full_pipeline(
        retailers=args.retailers,
        max_products_per_category=args.max_products,
        analyze=not args.no_analyze,
        generate_alternatives=not args.no_alternatives
    ))
