"""
Merge results from two computers into one JSON file
"""
import json
import sys
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("MERGE RESULTS FROM TWO COMPUTERS")
print("=" * 70)
print()

# Main file (from computer 1)
main_file = 'walmart_scraped_products_computer1.json'

# File from computer 2 (default path, can be changed)
other_file_default = 'walmart_scraped_products_computer2.json'
other_file = input(f"Enter the path to Computer 2's JSON file (default: {other_file_default}): ").strip()
if not other_file:
    other_file = other_file_default

if not other_file:
    print("No file provided. Exiting.")
    sys.exit(0)

print()
print(f"1. Loading main file: {main_file}")
try:
    with open(main_file, 'r', encoding='utf-8') as f:
        main_data = json.load(f)
    main_products = main_data.get('products', [])
    print(f"   Products in main file: {len(main_products)}")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

print()
print(f"2. Loading other computer's file: {other_file}")
try:
    with open(other_file, 'r', encoding='utf-8') as f:
        other_data = json.load(f)
    other_products = other_data.get('products', [])
    print(f"   Products in other file: {len(other_products)}")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

print()
print("3. Merging products...")
# Create dictionary keyed by product_name to avoid duplicates
merged_dict = {}

# Add products from main file
for product in main_products:
    product_name = product.get('product_name')
    if product_name:
        merged_dict[product_name] = product

# Add products from other file (will overwrite if duplicate, but that's OK)
added_count = 0
for product in other_products:
    product_name = product.get('product_name')
    if product_name:
        if product_name not in merged_dict:
            added_count += 1
        merged_dict[product_name] = product

merged_products = list(merged_dict.values())
print(f"   Merged products: {len(merged_products)}")
print(f"   New products added: {added_count}")
print(f"   Duplicates handled: {len(main_products) + len(other_products) - len(merged_products)}")
print()

# Create backup
import shutil
import os
backup_file = main_file.replace('.json', '_backup_before_merge.json')
if os.path.exists(main_file):
    shutil.copy2(main_file, backup_file)
    print(f"4. Created backup: {backup_file}")
    print()

# Save merged results to main file
merged_output_file = 'walmart_scraped_products_20260109_074637.json'
print("5. Saving merged results...")
output_data = {
    'scraped_at': datetime.now().isoformat(),
    'total_products': len(merged_products),
    'products_found': sum(1 for r in merged_products if r.get('found')),
    'merged_from': [main_file, other_file],
    'merged_at': datetime.now().isoformat(),
    'products': merged_products
}

with open(merged_output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, default=str)

print(f"   Saved to: {merged_output_file}")
print()

print("=" * 70)
print("MERGE COMPLETE!")
print("=" * 70)
print(f"Total products: {len(merged_products)}")
print(f"Products found: {output_data['products_found']}")
print(f"New products added: {added_count}")
print()

