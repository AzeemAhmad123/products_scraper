"""
Main scraper script with scheduling support
"""
import argparse
import logging
import sys
import time
import json
from datetime import datetime
from typing import List, Optional

import schedule

from scrapers.store_registry import get_scraper, get_all_store_names, STORE_SCRAPERS
from database.mongodb_handler import MongoDBHandler
from config import SCRAPE_INTERVAL_HOURS, DEFAULT_STORES
from models.product import Product
from utils.product_matcher import normalize_product_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GroceryScraper:
    """Main scraper orchestrator - handles all stores"""
    
    def __init__(self, use_mongodb: bool = True, stores: Optional[List[str]] = None):
        """
        Initialize scraper for specified stores
        
        Args:
            use_mongodb: Whether to use MongoDB
            stores: List of store names to use (defaults to all available stores)
        """
        self.stores = stores or get_all_store_names()
        self.scrapers = {}
        
        # Initialize scrapers for requested stores
        for store_name in self.stores:
            scraper = get_scraper(store_name)
            if scraper:
                self.scrapers[store_name] = scraper
                logger.info(f"Initialized scraper for: {store_name}")
            else:
                logger.warning(f"No scraper available for: {store_name}")
        
        self.db_handler = MongoDBHandler() if use_mongodb else None
        self.use_mongodb = use_mongodb
    
    def scrape_common_products(self, test_mode: bool = False) -> dict:
        """Scrape common grocery products from all stores"""
        # Common grocery items to search for
        search_queries = [
            'milk',
            'bread',
            'eggs',
            'chicken',
            'bananas',
            'apples',
            'rice',
            'pasta',
            'cheese',
            'yogurt',
            'cereal',
            'coffee',
            'sugar',
            'flour',
            'butter',
            'Nestle Coffee Mate',  # Added per client requirements
            'Coffee Mate'  # Alternative search term
        ]
        
        if test_mode:
            search_queries = search_queries[:3]  # Limit for testing
        
        all_products = []
        results = {}
        
        # Initialize results structure for all stores
        for store_name in self.stores:
            results[store_name] = {'count': 0, 'products': []}
        results['total'] = 0
        results['timestamp'] = datetime.utcnow().isoformat()
        
        logger.info(f"Starting scrape for {len(search_queries)} product categories across {len(self.stores)} stores")
        
        # Scrape each store
        for store_name, scraper in self.scrapers.items():
            logger.info("=" * 50)
            logger.info(f"Scraping {store_name.upper()}")
            logger.info("=" * 50)
            
            store_products = []
            for query in search_queries:
                try:
                    logger.info(f"Searching {store_name} for: {query}")
                    products = scraper.search_products(query, max_results=10)
                    store_products.extend(products)
                    logger.info(f"Found {len(products)} products for '{query}' on {store_name}")
                    time.sleep(2)  # Be respectful with delays
                except Exception as e:
                    logger.error(f"Error scraping {store_name} for '{query}': {str(e)}")
            
            results[store_name]['count'] = len(store_products)
            results[store_name]['products'] = [p.to_dict() for p in store_products]
            all_products.extend(store_products)
        
        results['total'] = len(all_products)
        
        # Save to MongoDB if enabled
        if self.use_mongodb and self.db_handler and self.db_handler.is_connected():
            logger.info(f"Saving {len(all_products)} products to MongoDB...")
            saved_count = self.db_handler.insert_products(all_products)
            results['saved_to_db'] = saved_count
            logger.info(f"Saved {saved_count} products to MongoDB")
        else:
            logger.info("MongoDB not available. Products not saved to database.")
            results['saved_to_db'] = 0
        
        # Save to JSON file for local testing
        output_file = f"scraped_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")
        
        return results
    
    def search_product_across_stores(self, product_name: str, max_results_per_store: int = 10) -> dict:
        """
        Search for a specific product across all stores and compare prices
        Example: search_product_across_stores("Milk 2L Nestle")
        """
        logger.info(f"Searching for '{product_name}' across all stores...")
        
        all_products = []
        results = {
            'query': product_name,
            'total': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Initialize results for all stores
        for store_name in self.stores:
            results[store_name] = {'count': 0, 'products': []}
        
        # Search all stores
        for store_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Searching {store_name} for: {product_name}")
                store_products = scraper.search_products(product_name, max_results=max_results_per_store)
                results[store_name]['count'] = len(store_products)
                results[store_name]['products'] = [p.to_dict() for p in store_products]
                all_products.extend(store_products)
                logger.info(f"Found {len(store_products)} products on {store_name}")
            except Exception as e:
                logger.error(f"Error searching {store_name}: {str(e)}")
        
        results['total'] = len(all_products)
        
        # Save to MongoDB if enabled
        if self.use_mongodb and self.db_handler and self.db_handler.is_connected():
            logger.info(f"Saving {len(all_products)} products to MongoDB...")
            saved_count = self.db_handler.insert_products(all_products)
            results['saved_to_db'] = saved_count
            
            # Get price comparison
            comparison = self.db_handler.compare_prices(product_name)
            results['price_comparison'] = comparison
            logger.info(f"Price comparison: Best price ${comparison.get('best_price', {}).get('price')} at {comparison.get('best_price', {}).get('store')}")
        else:
            results['saved_to_db'] = 0
            results['price_comparison'] = None
        
        # Save to JSON file
        output_file = f"product_search_{normalize_product_name(product_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_file}")
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        for store_name, scraper in self.scrapers.items():
            try:
                scraper.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {store_name} scraper: {str(e)}")
        
        if self.db_handler:
            self.db_handler.close()


def run_scraper(test_mode: bool = False, use_mongodb: bool = True):
    """Run the scraper once"""
    scraper = GroceryScraper(use_mongodb=use_mongodb)
    try:
        results = scraper.scrape_common_products(test_mode=test_mode)
        logger.info("=" * 50)
        logger.info("Scraping completed!")
        logger.info(f"Total products scraped: {results['total']}")
        for store_name in self.stores:
            if store_name in results:
                logger.info(f"  - {store_name.title()}: {results[store_name]['count']}")
        if 'saved_to_db' in results:
            logger.info(f"  - Saved to DB: {results['saved_to_db']}")
        logger.info("=" * 50)
        return results
    finally:
        scraper.cleanup()


def schedule_scraper(interval_hours: int = 3, use_mongodb: bool = True):
    """Schedule the scraper to run periodically"""
    logger.info(f"Scheduling scraper to run every {interval_hours} hours")
    
    # Schedule the job
    schedule.every(interval_hours).hours.do(run_scraper, test_mode=False, use_mongodb=use_mongodb)
    
    # Run once immediately
    logger.info("Running initial scrape...")
    run_scraper(test_mode=False, use_mongodb=use_mongodb)
    
    # Keep running
    logger.info("Scraper scheduled. Waiting for next run...")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user")


def search_product(product_name: str, use_mongodb: bool = True):
    """Search for a specific product across all stores"""
    scraper = GroceryScraper(use_mongodb=use_mongodb)
    try:
        results = scraper.search_product_across_stores(product_name)
        logger.info("=" * 50)
        logger.info("Product search completed!")
        logger.info(f"Product: {product_name}")
        logger.info(f"Total products found: {results['total']}")
        logger.info(f"  - Walmart: {results['walmart']['count']}")
        logger.info(f"  - Metro: {results['metro']['count']}")
        
        if results.get('price_comparison'):
            comp = results['price_comparison']
            if comp.get('found'):
                best = comp.get('best_price', {})
                logger.info(f"Best price: ${best.get('price')} at {best.get('store')}")
                logger.info(f"Price range: ${comp.get('price_range', {}).get('lowest')} - ${comp.get('price_range', {}).get('highest')}")
        
        logger.info("=" * 50)
        return results
    finally:
        scraper.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Grocery Web Scraper for Walmart.ca and Metro.ca')
    parser.add_argument('--test', action='store_true', help='Run in test mode (limited queries)')
    parser.add_argument('--once', action='store_true', help='Run once and exit (no scheduling)')
    parser.add_argument('--no-db', action='store_true', help='Skip MongoDB (save to JSON only)')
    parser.add_argument('--interval', type=int, default=SCRAPE_INTERVAL_HOURS, 
                       help=f'Hours between scrapes (default: {SCRAPE_INTERVAL_HOURS})')
    parser.add_argument('--search', type=str, help='Search for a specific product (e.g., "Milk 2L Nestle")')
    
    args = parser.parse_args()
    
    use_mongodb = not args.no_db
    
    # If --search is provided, search for that product
    if args.search:
        search_product(args.search, use_mongodb=use_mongodb)
    elif args.once:
        # Run once and exit
        run_scraper(test_mode=args.test, use_mongodb=use_mongodb)
    else:
        # Schedule recurring runs
        schedule_scraper(interval_hours=args.interval, use_mongodb=use_mongodb)


if __name__ == '__main__':
    main()

