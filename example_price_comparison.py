"""
Example: How to search for a specific product and compare prices
"""
from scraper import GroceryScraper
from api.price_comparison_api import PriceComparisonAPI

def example_search_and_compare():
    """Example: Search for a product and compare prices"""
    
    # Method 1: Search and scrape in one go
    print("=" * 60)
    print("Method 1: Search and scrape a product")
    print("=" * 60)
    
    scraper = GroceryScraper(use_mongodb=True)
    try:
        # Search for "Milk 2L Nestle" across all stores
        results = scraper.search_product_across_stores("Milk 2L Nestle", max_results_per_store=10)
        
        print(f"\nFound {results['total']} products:")
        print(f"  Walmart: {results['walmart']['count']}")
        print(f"  Metro: {results['metro']['count']}")
        
        if results.get('price_comparison'):
            comp = results['price_comparison']
            if comp.get('found'):
                best = comp.get('best_price', {})
                print(f"\nBest Price: ${best.get('price')} at {best.get('store')}")
                print(f"Price Range: ${comp.get('price_range', {}).get('lowest')} - ${comp.get('price_range', {}).get('highest')}")
    finally:
        scraper.cleanup()
    
    # Method 2: Query existing data from MongoDB
    print("\n" + "=" * 60)
    print("Method 2: Query prices from database")
    print("=" * 60)
    
    api = PriceComparisonAPI()
    try:
        # Get best price
        best = api.get_best_price("Milk 2L Nestle")
        if best:
            print(f"\nBest Price: ${best['price']} at {best['source']}")
            print(f"Product: {best['name']}")
            print(f"URL: {best['product_url']}")
        
        # Compare all prices
        comparison = api.compare_prices("Milk 2L Nestle")
        if comparison.get('found'):
            print(f"\nPrice Comparison:")
            print(f"  Total stores: {comparison['total_stores']}")
            print(f"  Total products: {comparison['total_products']}")
            print(f"  Lowest: ${comparison['price_range']['lowest']}")
            print(f"  Highest: ${comparison['price_range']['highest']}")
            print(f"  Average: ${comparison['price_range']['average']:.2f}")
            
            print(f"\nAll prices:")
            for product in comparison['all_prices'][:5]:  # Show top 5
                print(f"  ${product['price']:6.2f} - {product['source']:10s} - {product['name']}")
    finally:
        api.close()


if __name__ == '__main__':
    example_search_and_compare()



