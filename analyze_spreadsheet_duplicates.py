"""
Analyze duplicates and unique products in WebsiteScrapper 2.ods
"""
import pandas as pd
import sys
from collections import Counter

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("SPREADSHEET DUPLICATE ANALYSIS")
print("=" * 70)
print()

# Load spreadsheet
print("Loading spreadsheet: WebsiteScrapper 2.ods")
df = pd.read_excel('WebsiteScrapper 2.ods', engine='odf')
print(f"Total rows in spreadsheet: {len(df):,}")
print()

# Find product column
product_column = 'Product'
if product_column not in df.columns:
    # Try to find it
    for col in df.columns:
        if 'product' in col.lower() or 'name' in col.lower():
            product_column = col
            break
    if product_column not in df.columns:
        product_column = df.columns[0]

print(f"Using product column: '{product_column}'")
print()

# Clean product names (remove empty, strip whitespace)
df['Product_Clean'] = df[product_column].astype(str).str.strip()
df = df[df['Product_Clean'] != '']
df = df[df['Product_Clean'] != 'nan']

print(f"Rows with valid product names: {len(df):,}")
print()

# Count unique products
unique_products = df['Product_Clean'].nunique()
duplicate_rows = len(df) - unique_products

print("=" * 70)
print("RESULTS")
print("=" * 70)
print()
print(f"Total rows: {len(df):,}")
print(f"Unique products: {unique_products:,}")
print(f"Duplicate rows: {duplicate_rows:,}")
print()

# Calculate percentage
if len(df) > 0:
    duplicate_percentage = (duplicate_rows / len(df)) * 100
    unique_percentage = (unique_products / len(df)) * 100
    print(f"Unique products: {unique_percentage:.1f}%")
    print(f"Duplicate rows: {duplicate_percentage:.1f}%")
    print()

# Find products with most duplicates
print("=" * 70)
print("TOP 20 PRODUCTS WITH MOST DUPLICATES")
print("=" * 70)
print()

product_counts = Counter(df['Product_Clean'])
duplicates_only = {name: count for name, count in product_counts.items() if count > 1}
sorted_duplicates = sorted(duplicates_only.items(), key=lambda x: x[1], reverse=True)

if sorted_duplicates:
    print(f"Products with duplicates: {len(duplicates_only):,}")
    print(f"Total duplicate entries: {sum(count - 1 for count in duplicates_only.values()):,}")
    print()
    print("Top 20 most duplicated products:")
    print()
    for i, (product_name, count) in enumerate(sorted_duplicates[:20], 1):
        print(f"{i:2}. {product_name[:60]:<60} - {count} times ({count - 1} duplicates)")
else:
    print("No duplicate products found!")
    print()

# Summary
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print(f"✓ Total rows in spreadsheet: {len(df):,}")
print(f"✓ Unique products to scrape: {unique_products:,}")
print(f"✓ Duplicate rows (will be skipped): {duplicate_rows:,}")
print()
print("The scraper will:")
print(f"  - Process {unique_products:,} unique products")
print(f"  - Skip {duplicate_rows:,} duplicate rows automatically")
print(f"  - Save only unique products to JSON file")
print()

