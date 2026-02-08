#!/usr/bin/env python3
"""
FAM Data Pipeline CLI
Command-line interface for running the grocery scraping pipeline
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.pipeline import DataPipeline, ScraperRegistry
from database.db_manager import get_db


def list_retailers():
    """List all available retailers"""
    print("\n" + "="*60)
    print("AVAILABLE RETAILERS")
    print("="*60)
    
    db = get_db()
    retailers = db.get_retailers()
    
    # Group by region
    by_region = {}
    for r in retailers:
        region = r['region']
        if region not in by_region:
            by_region[region] = []
        by_region[region].append(r)
    
    for region, retailers_list in sorted(by_region.items()):
        print(f"\n{region}:")
        for r in retailers_list:
            scraper_available = "✓" if r['name'] in ScraperRegistry.SCRAPERS else "○"
            last_scraped = r['last_scraped_at'] or "Never"
            print(f"  [{scraper_available}] {r['name']} ({r['country']}) - Last scraped: {last_scraped}")
    
    print("\n✓ = Scraper implemented, ○ = Scraper not yet implemented")
    print("\nImplemented scrapers:", ", ".join(ScraperRegistry.list_available()))


def show_stats():
    """Show database statistics"""
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    db = get_db()
    stats = db.get_stats()
    
    print(f"\nTotal Products: {stats['total_products']}")
    print(f"Products with Ingredients: {stats['products_with_ingredients']}")
    print(f"Products with Nutrition: {stats['products_with_nutrition']}")
    print(f"Analyzed Products: {stats['analyzed_products']}")
    
    print("\nProducts by Retailer:")
    for retailer, count in sorted(stats['products_by_retailer'].items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {retailer}: {count}")


async def run_pipeline(retailers=None, max_products=50, analyze=True, alternatives=True):
    """Run the scraping pipeline"""
    pipeline = DataPipeline()
    await pipeline.run_full_pipeline(
        retailers=retailers,
        max_products_per_category=max_products,
        analyze=analyze,
        generate_alternatives=alternatives
    )


def main():
    parser = argparse.ArgumentParser(
        description='FAM Data Pipeline - Scrape grocery products for the Food-as-Medicine app',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available retailers
  python run_pipeline.py --list
  
  # Show database statistics
  python run_pipeline.py --stats
  
  # Run pipeline for all implemented scrapers
  python run_pipeline.py --run
  
  # Run pipeline for specific retailers
  python run_pipeline.py --run --retailers Walmart Target
  
  # Run with custom product limit
  python run_pipeline.py --run --retailers Walmart --max-products 100
  
  # Run without analysis (scrape only)
  python run_pipeline.py --run --no-analyze
        """
    )
    
    parser.add_argument('--list', action='store_true', help='List available retailers')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--run', action='store_true', help='Run the scraping pipeline')
    parser.add_argument('--retailers', nargs='+', help='Specific retailers to scrape')
    parser.add_argument('--max-products', type=int, default=50, help='Max products per category (default: 50)')
    parser.add_argument('--no-analyze', action='store_true', help='Skip ingredient analysis')
    parser.add_argument('--no-alternatives', action='store_true', help='Skip alternatives generation')
    
    args = parser.parse_args()
    
    if args.list:
        list_retailers()
    elif args.stats:
        show_stats()
    elif args.run:
        print("\n" + "="*60)
        print("FAM DATA PIPELINE")
        print("="*60)
        
        if args.retailers:
            # Validate retailers
            available = ScraperRegistry.list_available()
            invalid = [r for r in args.retailers if r not in available]
            if invalid:
                print(f"\nError: No scraper available for: {', '.join(invalid)}")
                print(f"Available scrapers: {', '.join(available)}")
                sys.exit(1)
        
        asyncio.run(run_pipeline(
            retailers=args.retailers,
            max_products=args.max_products,
            analyze=not args.no_analyze,
            alternatives=not args.no_alternatives
        ))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
