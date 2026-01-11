"""
Recover products from scraped_rows.json and merge with main JSON file
"""
import json
from datetime import datetime

# Load scraped_rows.json
print("Loading scraped_rows.json...")
with open('scraped_rows.json', 'r', encoding='utf-8') as f:
    scraped_rows_data = json.load(f)

rows = scraped_rows_data.get('rows', [])
print(f"Found {len(rows)} rows in scraped_rows.json")

# Load existing main JSON file
print("Loading main JSON file...")
try:
    with open('walmart_scraped_products_20260109_074637.json', 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    existing_products = {p.get('product_name'): p for p in main_data.get('products', [])}
    print(f"Found {len(existing_products)} existing products in main JSON")
except Exception as e:
    print(f"Error loading main JSON: {e}")
    existing_products = {}

# Convert scraped_rows to main format and merge
recovered_count = 0
for row in rows:
    if row.get('found'):
        product_name = row.get('product_name')
        if product_name and product_name not in existing_products:
            # Convert row format to main format
            product = {
                'product_name': product_name,
                'found': True,
                'walmart_url': row.get('walmart_url'),
                'walmart_price': row.get('walmart_price'),
                'walmart_product_name': None,  # Not in scraped_rows format
                'walmart_brand': None,
                'walmart_size': None,
                'walmart_in_stock': None,
                'scraped_at': datetime.now().isoformat()
            }
            existing_products[product_name] = product
            recovered_count += 1

print(f"\nRecovered {recovered_count} additional products from scraped_rows.json")
print(f"Total products after recovery: {len(existing_products)}")

# Save recovered data
output_data = {
    'scraped_at': datetime.now().isoformat(),
    'total_products': len(existing_products),
    'products_found': sum(1 for p in existing_products.values() if p.get('found')),
    'products': list(existing_products.values()),
    'recovered_from': 'scraped_rows.json',
    'recovered_at': datetime.now().isoformat(),
    'recovered_count': recovered_count
}

# Create backup first
import shutil
import os
backup_file = 'walmart_scraped_products_20260109_074637_backup_before_recovery.json'
if os.path.exists('walmart_scraped_products_20260109_074637.json'):
    shutil.copy2('walmart_scraped_products_20260109_074637.json', backup_file)
    print(f"\nCreated backup: {backup_file}")

# Save recovered file
output_file = 'walmart_scraped_products_20260109_074637.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"\nSaved recovered data to {output_file}")
print(f"   Total products: {len(existing_products)}")
print(f"   Products found: {output_data['products_found']}")

