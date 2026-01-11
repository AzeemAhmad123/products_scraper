"""
Split remaining unique products into two files for parallel scraping on two computers
"""
import pandas as pd
import json
import sys
import os

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("SPLITTING PRODUCTS FOR TWO COMPUTERS")
print("=" * 70)
print()

# Load spreadsheet
spreadsheet_path = 'WebsiteScrapper 2.ods'
print(f"1. Loading spreadsheet: {spreadsheet_path}")
try:
    df = pd.read_excel(spreadsheet_path, engine='odf')
    print(f"   Total rows: {len(df)}")
    print(f"   Unique products: {df['Product'].nunique()}")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Load already scraped products
json_file = 'walmart_scraped_products_20260109_074637.json'
print(f"2. Loading already scraped products: {json_file}")
try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scraped_products = data.get('products', [])
    scraped_names = {p.get('product_name') for p in scraped_products if p.get('product_name')}
    print(f"   Already scraped: {len(scraped_names)} products")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    scraped_names = set()
    print()

# Get unique products from spreadsheet
print("3. Getting unique products from spreadsheet...")
unique_products = df['Product'].unique().tolist()
print(f"   Unique products in spreadsheet: {len(unique_products)}")

# Filter out already scraped
remaining_products = [p for p in unique_products if p not in scraped_names]
print(f"   Remaining to scrape: {len(remaining_products)}")
print()

if len(remaining_products) == 0:
    print("All products already scraped!")
    sys.exit(0)

# Get row numbers for remaining products
print("4. Finding row numbers for remaining products...")
remaining_rows = []
for idx, row in df.iterrows():
    product_name = row['Product']
    if product_name in remaining_products:
        # Row numbers are 1-indexed in the file format
        remaining_rows.append(idx + 1)

print(f"   Found {len(remaining_rows)} rows for remaining products")
print()

# Split into two equal parts
print("5. Splitting into two files...")
total = len(remaining_rows)
half = total // 2

computer1_rows = remaining_rows[:half]
computer2_rows = remaining_rows[half:]

print(f"   Computer 1: {len(computer1_rows)} products (rows {min(computer1_rows) if computer1_rows else 0} to {max(computer1_rows) if computer1_rows else 0})")
print(f"   Computer 2: {len(computer2_rows)} products (rows {min(computer2_rows) if computer2_rows else 0} to {max(computer2_rows) if computer2_rows else 0})")
print()

# Save to files
file1 = 'unique_unscraped_rows_computer1.txt'
file2 = 'unique_unscraped_rows_computer2.txt'

print(f"6. Saving to files...")
with open(file1, 'w', encoding='utf-8') as f:
    for row_num in computer1_rows:
        f.write(f"{row_num}\n")

with open(file2, 'w', encoding='utf-8') as f:
    for row_num in computer2_rows:
        f.write(f"{row_num}\n")

print(f"   Created: {file1} ({len(computer1_rows)} rows)")
print(f"   Created: {file2} ({len(computer2_rows)} rows)")
print()

# Verify no overlap
overlap = set(computer1_rows) & set(computer2_rows)
if overlap:
    print(f"   WARNING: Found {len(overlap)} overlapping rows!")
else:
    print(f"   Verified: No overlapping rows between the two files")
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total remaining products: {len(remaining_products)}")
print(f"Computer 1 file: {file1} ({len(computer1_rows)} products)")
print(f"Computer 2 file: {file2} ({len(computer2_rows)} products)")
print()
print("INSTRUCTIONS:")
print("=" * 70)
print("Computer 1:")
print(f"  python scrape_walmart_parallel.py --spreadsheet \"WebsiteScrapper 2.ods\" --row-numbers-file \"{file1}\" --workers 2 --output-file \"walmart_scraped_products_20260109_074637.json\"")
print()
print("Computer 2:")
print(f"  python scrape_walmart_parallel.py --spreadsheet \"WebsiteScrapper 2.ods\" --row-numbers-file \"{file2}\" --workers 2 --output-file \"walmart_scraped_products_20260109_074637.json\"")
print()
print("NOTE: Both computers will save to the same JSON file.")
print("The duplicate prevention system will ensure no conflicts!")
print("=" * 70)

