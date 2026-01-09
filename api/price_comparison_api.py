"""
API functions for price comparison - can be used by your app backend
"""
import logging
from typing import Optional, Dict, Any, List
from database.mongodb_handler import MongoDBHandler

logger = logging.getLogger(__name__)


class PriceComparisonAPI:
    """API for price comparison functionality"""
    
    def __init__(self):
        self.db_handler = MongoDBHandler()
    
    def get_product_prices(self, product_name: str, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get prices for a product across all stores
        Returns list of products sorted by price (lowest first)
        
        Example:
            api = PriceComparisonAPI()
            prices = api.get_product_prices("Milk 2L Nestle")
        """
        if not self.db_handler.is_connected():
            logger.warning("MongoDB not connected")
            return []
        
        return self.db_handler.find_product_prices(product_name, max_age_hours)
    
    def get_best_price(self, product_name: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Get the best (lowest) price for a product
        
        Returns:
            {
                'name': 'Product name',
                'price': 4.99,
                'source': 'walmart',
                'product_url': 'https://...',
                'image_url': 'https://...',
                ...
            }
        """
        if not self.db_handler.is_connected():
            return None
        
        return self.db_handler.get_best_price(product_name, max_age_hours)
    
    def compare_prices(self, product_name: str, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Compare prices for a product across all stores
        
        Returns:
            {
                'product_name': 'Milk 2L Nestle',
                'found': True,
                'total_stores': 2,
                'total_products': 5,
                'best_price': {
                    'price': 4.99,
                    'store': 'walmart',
                    'product_url': 'https://...',
                    'name': 'Nestle Milk 2L'
                },
                'price_range': {
                    'lowest': 4.99,
                    'highest': 6.49,
                    'average': 5.74
                },
                'stores': {
                    'walmart': [...],
                    'metro': [...]
                },
                'all_prices': [...]
            }
        """
        if not self.db_handler.is_connected():
            return {
                'product_name': product_name,
                'found': False,
                'error': 'MongoDB not connected'
            }
        
        return self.db_handler.compare_prices(product_name, max_age_hours)
    
    def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for products by name (fuzzy search)
        """
        if not self.db_handler.is_connected():
            return []
        
        return self.db_handler.search_products(query, limit)
    
    def close(self):
        """Close database connection"""
        if self.db_handler:
            self.db_handler.close()


# Example usage
if __name__ == '__main__':
    api = PriceComparisonAPI()
    
    try:
        # Example: Get best price for a product
        product = "Milk 2L Nestle"
        print(f"\nSearching for: {product}")
        
        # Get best price
        best = api.get_best_price(product)
        if best:
            print(f"\nBest Price: ${best['price']} at {best['source']}")
            print(f"Product: {best['name']}")
            print(f"URL: {best['product_url']}")
        else:
            print("Product not found")
        
        # Compare all prices
        comparison = api.compare_prices(product)
        if comparison.get('found'):
            print(f"\nPrice Comparison:")
            print(f"  Stores: {comparison['total_stores']}")
            print(f"  Products: {comparison['total_products']}")
            print(f"  Lowest: ${comparison['price_range']['lowest']}")
            print(f"  Highest: ${comparison['price_range']['highest']}")
            print(f"  Average: ${comparison['price_range']['average']:.2f}")
            
            print(f"\nPrices by store:")
            for store, products in comparison['stores'].items():
                print(f"  {store.upper()}:")
                for p in products[:3]:  # Show top 3
                    print(f"    - ${p['price']}: {p['name']}")
    finally:
        api.close()



