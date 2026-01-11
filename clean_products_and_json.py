"""
Script to:
1. Remove products from spreadsheet that are in the JSON file
2. Remove duplicate products from spreadsheet
3. Remove duplicate products from JSON file
4. Save cleaned files
"""
import pandas as pd
import json
from datetime import datetime
from collections import OrderedDict

def load_json_products(json_file: str) -> set:
    """Load product names from JSON file"""
    print(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = set()
    for product in data.get('products', []):
        product_name = product.get('product_name', '').strip()
        if product_name:
            products.add(product_name)
    
    print(f"Found {len(products)} unique products in JSON file")
    return products

def remove_duplicates_from_json(json_file: str, output_file: str = None):
    """Remove duplicate products from JSON file, keeping first occurrence"""
    if output_file is None:
        output_file = json_file.replace('.json', '_cleaned.json')
    
    print(f"\nCleaning JSON file: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seen_products = set()
    unique_products = []
    duplicates_removed = 0
    
    for product in data.get('products', []):
        product_name = product.get('product_name', '').strip()
        if product_name and product_name not in seen_products:
            seen_products.add(product_name)
            unique_products.append(product)
        elif product_name:
            duplicates_removed += 1
    
    # Update data
    cleaned_data = {
        'scraped_at': data.get('scraped_at', datetime.now().isoformat()),
        'total_products': len(unique_products),
        'products_found': sum(1 for p in unique_products if p.get('found')),
        'products': unique_products,
        'cleaned_at': datetime.now().isoformat(),
        'duplicates_removed': duplicates_removed
    }
    
    # Save cleaned JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, default=str)
    
    print(f"  Original products: {len(data.get('products', []))}")
    print(f"  Unique products: {len(unique_products)}")
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Saved to: {output_file}")
    
    return cleaned_data, duplicates_removed

def clean_spreadsheet(
    spreadsheet_path: str,
    json_products: set,
    duplicate_row_numbers: list = None,
    output_file: str = None
):
    """Remove products from spreadsheet that are in JSON or are duplicates"""
    if output_file is None:
        output_file = spreadsheet_path.replace('.ods', '_cleaned.ods')
    
    print(f"\nCleaning spreadsheet: {spreadsheet_path}")
    
    # Load spreadsheet
    df = pd.read_excel(spreadsheet_path, engine='odf')
    original_count = len(df)
    print(f"  Original rows: {original_count}")
    
    # Add row numbers (1-indexed for Excel compatibility)
    df['Row_Number'] = range(1, len(df) + 1)
    
    # Find product column
    product_column = None
    for col in df.columns:
        if 'product' in col.lower() or 'name' in col.lower():
            product_column = col
            break
    
    if product_column is None:
        product_column = df.columns[0]
    
    print(f"  Using product column: {product_column}")
    
    # Track rows to remove
    rows_to_remove = set()
    
    # 1. Remove rows that match products in JSON
    json_matches = 0
    for idx, row in df.iterrows():
        product_name = str(row[product_column]).strip() if pd.notna(row[product_column]) else ""
        if product_name in json_products:
            rows_to_remove.add(idx)
            json_matches += 1
    
    print(f"  Rows matching JSON products: {json_matches}")
    
    # 2. Remove duplicate rows (if duplicate_row_numbers provided)
    duplicate_matches = 0
    if duplicate_row_numbers:
        # Convert row numbers to 0-indexed
        duplicate_indices = {row_num - 1 for row_num in duplicate_row_numbers if row_num > 0}
        for idx in duplicate_indices:
            if idx < len(df) and idx not in rows_to_remove:
                rows_to_remove.add(idx)
                duplicate_matches += 1
        
        print(f"  Duplicate rows to remove: {duplicate_matches}")
    
    # Remove rows
    df_cleaned = df.drop(index=rows_to_remove).reset_index(drop=True)
    
    # Remove the Row_Number column we added
    if 'Row_Number' in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=['Row_Number'])
    
    final_count = len(df_cleaned)
    removed_count = original_count - final_count
    
    print(f"  Final rows: {final_count}")
    print(f"  Total rows removed: {removed_count}")
    
    # Save cleaned spreadsheet
    df_cleaned.to_excel(output_file, engine='odf', index=False)
    print(f"  Saved to: {output_file}")
    
    return df_cleaned, removed_count

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean products from spreadsheet and JSON')
    parser.add_argument('--spreadsheet', type=str, default='WebsiteScrapper 2.ods',
                       help='Path to spreadsheet file')
    parser.add_argument('--json', type=str, default='walmart_scraped_products_20260109_074637.json',
                       help='Path to JSON file')
    parser.add_argument('--duplicates-file', type=str, default='duplicate_product_row_numbers.txt',
                       help='Path to file with duplicate row numbers')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("CLEANING PRODUCTS AND JSON FILE")
    print("=" * 70)
    
    # 1. Load products from JSON
    json_products = load_json_products(args.json)
    
    # 2. Remove duplicates from JSON
    cleaned_json, json_duplicates = remove_duplicates_from_json(args.json)
    
    # 3. Load duplicate row numbers if file exists
    duplicate_row_numbers = []
    try:
        with open(args.duplicates_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        duplicate_row_numbers.append(int(line))
                    except ValueError:
                        pass
        print(f"\nLoaded {len(duplicate_row_numbers)} duplicate row numbers from {args.duplicates_file}")
    except FileNotFoundError:
        print(f"\nDuplicate row numbers file not found: {args.duplicates_file}")
        print("  Will only remove products that match JSON file")
    
    # 4. Clean spreadsheet
    cleaned_df, removed_rows = clean_spreadsheet(
        args.spreadsheet,
        json_products,
        duplicate_row_numbers
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"JSON File:")
    print(f"  Duplicates removed: {json_duplicates}")
    print(f"  Cleaned file: {args.json.replace('.json', '_cleaned.json')}")
    print(f"\nSpreadsheet:")
    print(f"  Rows removed: {removed_rows}")
    print(f"  Remaining rows: {len(cleaned_df)}")
    print(f"  Cleaned file: {args.spreadsheet.replace('.ods', '_cleaned.ods')}")
    print("=" * 70)

if __name__ == '__main__':
    main()

