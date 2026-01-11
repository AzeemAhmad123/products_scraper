"""
Verify that cleaned files don't contain products from JSON or duplicates
"""
import pandas as pd
import json

# Load JSON products
with open('walmart_scraped_products_20260109_074637.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)
json_products = {p['product_name'].strip() for p in json_data['products']}

# Load cleaned spreadsheet
df = pd.read_excel('WebsiteScrapper 2_cleaned.ods', engine='odf')

# Find product column
product_column = None
for col in df.columns:
    if 'product' in col.lower() or 'name' in col.lower():
        product_column = col
        break
if product_column is None:
    product_column = df.columns[0]

print("=" * 70)
print("VERIFICATION REPORT")
print("=" * 70)

# Check for JSON products in cleaned spreadsheet
spreadsheet_products = set()
json_matches_in_spreadsheet = []
for idx, row in df.iterrows():
    product_name = str(row[product_column]).strip() if pd.notna(row[product_column]) else ""
    if product_name:
        spreadsheet_products.add(product_name)
        if product_name in json_products:
            json_matches_in_spreadsheet.append((idx + 1, product_name))

print(f"\nCleaned Spreadsheet:")
print(f"  Total rows: {len(df)}")
print(f"  Unique products: {len(spreadsheet_products)}")
print(f"  Products matching JSON: {len(json_matches_in_spreadsheet)}")

if json_matches_in_spreadsheet:
    print(f"\n  WARNING: Found {len(json_matches_in_spreadsheet)} products from JSON still in spreadsheet:")
    for row_num, product in json_matches_in_spreadsheet[:10]:
        print(f"    Row {row_num}: {product}")
else:
    print("  [OK] No products from JSON found in cleaned spreadsheet")

# Check for duplicates in cleaned spreadsheet
from collections import Counter
product_counts = Counter()
for idx, row in df.iterrows():
    product_name = str(row[product_column]).strip() if pd.notna(row[product_column]) else ""
    if product_name:
        product_counts[product_name] += 1

duplicates = {k: v for k, v in product_counts.items() if v > 1}
print(f"\n  Duplicates in cleaned spreadsheet: {len(duplicates)}")

if duplicates:
    print(f"  WARNING: Found {len(duplicates)} duplicate products:")
    for product, count in list(duplicates.items())[:10]:
        print(f"    {product}: {count} times")
else:
    print("  [OK] No duplicates found in cleaned spreadsheet")

# Check cleaned JSON
with open('walmart_scraped_products_20260109_074637_cleaned.json', 'r', encoding='utf-8') as f:
    cleaned_json = json.load(f)

json_product_names = [p['product_name'].strip() for p in cleaned_json['products']]
json_duplicates = {k: v for k, v in Counter(json_product_names).items() if v > 1}

print(f"\nCleaned JSON:")
print(f"  Total products: {len(cleaned_json['products'])}")
print(f"  Unique products: {len(set(json_product_names))}")
print(f"  Duplicates: {len(json_duplicates)}")

if json_duplicates:
    print(f"  WARNING: Found duplicates in cleaned JSON")
else:
    print("  [OK] No duplicates in cleaned JSON")

print("\n" + "=" * 70)

