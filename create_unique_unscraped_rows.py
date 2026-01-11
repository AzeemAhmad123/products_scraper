"""
Create a file listing row numbers of unique products that haven't been scraped yet
"""
import pandas as pd
import json

def main():
    # Load JSON products
    print("Loading products from JSON file...")
    with open('walmart_scraped_products_20260109_074637.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    json_products = {p['product_name'].strip() for p in json_data['products']}
    print(f"  Found {len(json_products)} products in JSON file")
    
    # Load duplicate row numbers
    print("\nLoading duplicate row numbers...")
    duplicate_row_numbers = set()
    try:
        with open('duplicate_product_row_numbers.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        duplicate_row_numbers.add(int(line))
                    except ValueError:
                        pass
        print(f"  Found {len(duplicate_row_numbers)} duplicate row numbers")
    except FileNotFoundError:
        print("  No duplicate row numbers file found")
    
    # Load original spreadsheet
    print("\nLoading original spreadsheet...")
    df = pd.read_excel('WebsiteScrapper 2.ods', engine='odf')
    print(f"  Total rows: {len(df)}")
    
    # Find product column
    product_column = None
    for col in df.columns:
        if 'product' in col.lower() or 'name' in col.lower():
            product_column = col
            break
    if product_column is None:
        product_column = df.columns[0]
    
    print(f"  Using product column: {product_column}")
    
    # Find unique, unscraped rows
    print("\nIdentifying unique, unscraped rows...")
    unique_unscraped_rows = []
    
    for idx, row in df.iterrows():
        row_number = idx + 1  # 1-indexed for Excel compatibility
        product_name = str(row[product_column]).strip() if pd.notna(row[product_column]) else ""
        
        # Skip if empty product name
        if not product_name:
            continue
        
        # Check if it's a duplicate
        if row_number in duplicate_row_numbers:
            continue
        
        # Check if it's already scraped (in JSON)
        if product_name in json_products:
            continue
        
        # This row is unique and not scraped
        unique_unscraped_rows.append(row_number)
    
    # Sort the row numbers
    unique_unscraped_rows.sort()
    
    print(f"  Found {len(unique_unscraped_rows)} unique, unscraped rows")
    
    # Save to file
    output_file = 'unique_unscraped_rows.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Row numbers in WebsiteScrapper 2.ods that are:\n")
        f.write("#   1. Unique (not duplicates)\n")
        f.write("#   2. Not yet scraped (not in JSON file)\n")
        f.write(f"# Total rows: {len(unique_unscraped_rows)}\n")
        f.write(f"# Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for row_num in unique_unscraped_rows:
            f.write(f"{row_num}\n")
    
    print(f"\nSaved to: {output_file}")
    
    # Also create a summary
    summary_file = 'unique_unscraped_summary.json'
    summary = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'total_rows': len(unique_unscraped_rows),
        'spreadsheet_total_rows': len(df),
        'json_products_count': len(json_products),
        'duplicate_rows_count': len(duplicate_row_numbers),
        'rows': unique_unscraped_rows[:100]  # First 100 as sample
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to: {summary_file}")
    
    # Print statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total rows in spreadsheet: {len(df)}")
    print(f"Rows already scraped (in JSON): {len(json_products)}")
    print(f"Duplicate rows: {len(duplicate_row_numbers)}")
    print(f"Unique, unscraped rows: {len(unique_unscraped_rows)}")
    print("=" * 70)

if __name__ == '__main__':
    main()

