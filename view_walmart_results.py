"""View Walmart scraping results in a readable format"""
import json
import glob
import os

# Find the most recent result file
result_files = glob.glob("walmart_scraped_products_*.json")
if result_files:
    latest = max(result_files, key=os.path.getctime)
    print(f"Showing results from: {latest}\n")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("WALMART SCRAPING RESULTS")
    print("=" * 80)
    print(f"Total Products Searched: {data['total_products']}")
    print(f"Products Found: {data['products_found']}")
    print(f"Scraped At: {data['scraped_at']}")
    print("=" * 80)
    
    print("\nPRODUCT DETAILS:")
    print("-" * 80)
    
    for i, product in enumerate(data['products'], 1):
        print(f"\n{i}. {product['product_name']}")
        print("-" * 80)
        
        if product.get('found'):
            print(f"   [FOUND] on Walmart")
            print(f"   Walmart Product: {product.get('walmart_product_name', 'N/A')}")
            print(f"   Price: ${product.get('walmart_price', 'N/A')}")
            print(f"   Brand: {product.get('walmart_brand', 'N/A')}")
            print(f"   Size: {product.get('walmart_size', 'N/A')}")
            print(f"   In Stock: {product.get('walmart_in_stock', 'N/A')}")
            print(f"   URL: {product.get('walmart_url', 'N/A')[:70]}...")
        else:
            print(f"   [NOT FOUND] on Walmart")
            if product.get('error'):
                print(f"   Error: {product['error']}")
    
    print("\n" + "=" * 80)
else:
    print("No result files found. Run scrape_walmart_from_spreadsheet.py first!")

