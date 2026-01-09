"""
Example: How to integrate the scraper with your Pantry List app backend

This shows how your app backend can query the scraped data and return it to your mobile app.
"""

from api.price_comparison_api import PriceComparisonAPI
import json

# Initialize the API (your backend would do this once at startup)
api = PriceComparisonAPI()

def get_product_prices_for_app(product_name: str):
    """
    This is what your app backend endpoint would look like.
    When user types "Milk 2L Nestle" in the app, this function is called.
    """
    
    # Get price comparison
    comparison = api.compare_prices(product_name, max_age_hours=24)
    
    if not comparison.get('found'):
        return {
            'success': False,
            'message': 'Product not found',
            'product_name': product_name
        }
    
    # Format response for your mobile app
    response = {
        'success': True,
        'product_name': product_name,
        'best_price': {
            'price': comparison['best_price']['price'],
            'store': comparison['best_price']['store'],
            'store_display_name': comparison['best_price']['store'].title(),  # "Walmart" or "Metro"
            'product_url': comparison['best_price']['product_url'],
            'product_name': comparison['best_price']['name']
        },
        'price_range': comparison['price_range'],
        'all_stores': []
    }
    
    # Add all store options
    for store_name, products in comparison['stores'].items():
        for product in products:
            response['all_stores'].append({
                'store': store_name,
                'store_display_name': store_name.title(),
                'price': product['price'],
                'product_name': product['name'],
                'product_url': product['product_url'],
                'image_url': product.get('image_url'),
                'in_stock': product.get('in_stock', True)
            })
    
    # Sort by price (lowest first)
    response['all_stores'].sort(key=lambda x: x['price'] or float('inf'))
    
    return response


def get_best_price_simple(product_name: str):
    """
    Simple function - just returns the best price.
    Use this when user just wants to know where to buy cheapest.
    """
    best = api.get_best_price(product_name)
    
    if not best:
        return {
            'success': False,
            'message': 'Product not found'
        }
    
    return {
        'success': True,
        'product_name': product_name,
        'best_price': best['price'],
        'store': best['source'],
        'store_display_name': best['source'].title(),
        'product_url': best['product_url'],
        'product_name_full': best['name']
    }


# Example: Flask/FastAPI endpoint structure
"""
# If using Flask:
@app.route('/api/products/search', methods=['GET'])
def search_product():
    product_name = request.args.get('name')
    result = get_product_prices_for_app(product_name)
    return jsonify(result)

# If using FastAPI:
@app.get('/api/products/search')
def search_product(name: str):
    return get_product_prices_for_app(name)
"""


if __name__ == '__main__':
    # Test the functions
    print("=" * 70)
    print("Testing App Integration")
    print("=" * 70)
    
    # Test 1: Search for a product
    print("\n1. Searching for 'milk':")
    result = get_product_prices_for_app("milk")
    
    if result['success']:
        print(f"\n[OK] Found {len(result['all_stores'])} options")
        print(f"   Best Price: ${result['best_price']['price']} at {result['best_price']['store_display_name']}")
        print(f"\n   All prices:")
        for store in result['all_stores'][:5]:  # Show top 5
            print(f"     ${store['price']:6.2f} - {store['store_display_name']:10s} - {store['product_name'][:40]}")
    else:
        print(f"X {result['message']}")
    
    # Test 2: Simple best price
    print("\n" + "=" * 70)
    print("2. Getting best price for 'milk':")
    best = get_best_price_simple("milk")
    
    if best['success']:
        print(f"\n[OK] Best Price: ${best['best_price']} at {best['store_display_name']}")
        print(f"   Product: {best['product_name_full']}")
        print(f"   URL: {best['product_url']}")
    else:
        print(f"X {best['message']}")
    
    print("\n" + "=" * 70)
    print("Example JSON Response for your app:")
    print("=" * 70)
    print(json.dumps(result if result['success'] else best, indent=2))
    
    api.close()

