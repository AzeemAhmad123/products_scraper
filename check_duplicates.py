import json
from collections import Counter

# Load JSON file
with open('walmart_scraped_products_20260109_074637.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data.get('products', [])
product_names = [p.get('product_name') for p in products if p.get('product_name')]

# Count occurrences
counts = Counter(product_names)
duplicates = {name: count for name, count in counts.items() if count > 1}

print(f"Total products in JSON: {len(products)}")
print(f"Unique product names: {len(set(product_names))}")
print(f"Duplicate products: {len(products) - len(set(product_names))}")
print(f"\nProducts with duplicates: {len(duplicates)}")
print(f"Total duplicate entries: {sum(count - 1 for count in counts.values() if count > 1)}")

if duplicates:
    print("\nTop 10 most duplicated products:")
    for name, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {count} times")
else:
    print("\nNo duplicate products found!")

