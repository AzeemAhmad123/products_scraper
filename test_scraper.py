"""
Test script for local testing of the scraper
"""
import json
import logging
from scrapers.walmart_scraper import WalmartScraper
from scrapers.metro_scraper import MetroScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_walmart_scraper():
    """Test Walmart scraper with a simple query"""
    logger.info("Testing Walmart scraper...")
    scraper = WalmartScraper()
    
    try:
        # Test search
        products = scraper.search_products('milk', max_results=5)
        logger.info(f"Found {len(products)} products")
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.name}")
            print(f"   Price: ${product.price}")
            print(f"   URL: {product.product_url}")
            print(f"   Image: {product.image_url}")
        
        return products
    finally:
        scraper.cleanup()


def test_metro_scraper():
    """Test Metro scraper with a simple query"""
    logger.info("Testing Metro scraper...")
    scraper = MetroScraper()
    
    try:
        # Test search
        products = scraper.search_products('milk', max_results=5)
        logger.info(f"Found {len(products)} products")
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.name}")
            print(f"   Price: ${product.price}")
            print(f"   URL: {product.product_url}")
            print(f"   Image: {product.image_url}")
        
        return products
    finally:
        scraper.cleanup()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Grocery Scrapers")
    print("=" * 60)
    
    print("\n1. Testing Walmart.ca scraper...")
    walmart_products = test_walmart_scraper()
    
    print("\n" + "=" * 60)
    print("\n2. Testing Metro.ca scraper...")
    metro_products = test_metro_scraper()
    
    print("\n" + "=" * 60)
    print("\nTest Summary:")
    print(f"Walmart products found: {len(walmart_products)}")
    print(f"Metro products found: {len(metro_products)}")
    print("=" * 60)



