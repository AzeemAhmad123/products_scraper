"""Quick script to display scraper results"""
import json
import glob
import os

# Find the most recent result file
result_files = glob.glob("product_search_*.json")
if result_files:
    latest = max(result_files, key=os.path.getctime)
    print(f"Showing results from: {latest}\n")
    
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 70)
    print(f"Search Query: {data['query']}")
    print("=" * 70)
    
    print(f"\nWALMART ({data['walmart']['count']} products):")
    print("-" * 70)
    for i, p in enumerate(data['walmart']['products'][:10], 1):
        price_str = f"${p['price']:.2f}" if p.get('price') else "Price N/A"
        print(f"{i:2d}. {p['name'][:55]:55s} {price_str:>10s}")
        if p.get('product_url'):
            print(f"    URL: {p['product_url'][:65]}")
    
    print(f"\nMETRO ({data['metro']['count']} products):")
    print("-" * 70)
    for i, p in enumerate(data['metro']['products'][:10], 1):
        price_str = f"${p['price']:.2f}" if p.get('price') else "Price N/A"
        print(f"{i:2d}. {p['name'][:55]:55s} {price_str:>10s}")
        if p.get('product_url'):
            print(f"    URL: {p['product_url'][:65]}")
    
    print("\n" + "=" * 70)
    print(f"Total: {data['total']} products found")
    print("=" * 70)
else:
    print("No result files found. Run the scraper first!")



