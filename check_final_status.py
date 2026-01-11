import json

with open('walmart_scraped_products_20260109_074637.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data.get('products', [])
print("Final Status:")
print(f"  Total products: {len(products)}")
print(f"  Products found: {data.get('products_found', 0)}")
print(f"  Last updated: {data.get('scraped_at', 'N/A')}")

