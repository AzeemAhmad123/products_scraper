"""
Remove all products with found: false from the JSON file
"""
import json
from datetime import datetime

def remove_not_found_products(json_file: str):
    """Remove products where found is False"""
    
    print(f"Loading JSON file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data.get('products', []))
    print(f"Original products: {original_count}")
    
    # Filter out products where found is False
    found_products = [p for p in data.get('products', []) if p.get('found', False) is True]
    removed_count = original_count - len(found_products)
    
    print(f"Products with found: true: {len(found_products)}")
    print(f"Products removed (found: false): {removed_count}")
    
    # Update the data
    cleaned_data = {
        'scraped_at': data.get('scraped_at', datetime.now().isoformat()),
        'total_products': len(found_products),
        'products_found': len(found_products),  # All remaining products are found
        'products': found_products,
        'cleaned_at': datetime.now().isoformat(),
        'removed_not_found': removed_count
    }
    
    # Save back to the same file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, default=str)
    
    print(f"\nCleaned JSON saved to: {json_file}")
    print(f"Removed {removed_count} products with found: false")
    print(f"Kept {len(found_products)} products with found: true")
    
    return cleaned_data

if __name__ == '__main__':
    import sys
    
    json_file = 'walmart_scraped_products_20260109_074637.json'
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    remove_not_found_products(json_file)


