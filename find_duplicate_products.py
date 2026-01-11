"""
Script to find all duplicate products in WebsiteScrapper 2.ods
"""
import pandas as pd
import json
from datetime import datetime
from collections import defaultdict

def find_duplicate_products(spreadsheet_path: str = 'WebsiteScrapper 2.ods'):
    """Find all duplicate products in the spreadsheet"""
    
    print(f"Loading spreadsheet: {spreadsheet_path}")
    df = pd.read_excel(spreadsheet_path, engine='odf')
    
    print(f"Total rows in spreadsheet: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Find the product column (could be 'Product' or similar)
    product_column = None
    for col in df.columns:
        if 'product' in col.lower() or 'name' in col.lower():
            product_column = col
            break
    
    if product_column is None:
        # Try first column
        product_column = df.columns[0]
        print(f"Using first column as product column: {product_column}")
    else:
        print(f"Using product column: {product_column}")
    
    # Add row numbers (1-indexed for Excel compatibility)
    df['Row_Number'] = range(1, len(df) + 1)
    
    # Find duplicates based on product name
    # Group by product name and collect row numbers
    product_groups = defaultdict(list)
    
    for idx, row in df.iterrows():
        product_name = str(row[product_column]).strip() if pd.notna(row[product_column]) else ""
        if product_name:  # Only add non-empty products
            product_groups[product_name].append({
                'row_number': int(row['Row_Number']),
                'index': int(idx)
            })
    
    # Find duplicates (products that appear more than once)
    duplicates = {}
    duplicate_row_numbers = []
    
    for product_name, rows in product_groups.items():
        if len(rows) > 1:
            duplicates[product_name] = {
                'count': len(rows),
                'rows': rows,
                'row_numbers': [r['row_number'] for r in rows]
            }
            duplicate_row_numbers.extend([r['row_number'] for r in rows])
    
    # Sort duplicate row numbers
    duplicate_row_numbers = sorted(set(duplicate_row_numbers))
    
    # Create summary
    summary = {
        'analysis_date': datetime.now().isoformat(),
        'spreadsheet_path': spreadsheet_path,
        'total_rows': len(df),
        'total_unique_products': len(product_groups),
        'total_duplicate_products': len(duplicates),
        'total_duplicate_rows': len(duplicate_row_numbers),
        'duplicate_row_numbers': duplicate_row_numbers,
        'duplicates': duplicates
    }
    
    # Print summary
    print("\n" + "=" * 70)
    print("DUPLICATE PRODUCTS ANALYSIS")
    print("=" * 70)
    print(f"Total rows in spreadsheet: {summary['total_rows']}")
    print(f"Total unique products: {summary['total_unique_products']}")
    print(f"Products with duplicates: {summary['total_duplicate_products']}")
    print(f"Total rows with duplicates: {summary['total_duplicate_rows']}")
    print("=" * 70)
    
    # Print top 20 duplicates
    print("\nTop 20 Most Duplicated Products:")
    print("-" * 70)
    sorted_duplicates = sorted(duplicates.items(), key=lambda x: x[1]['count'], reverse=True)
    for i, (product_name, info) in enumerate(sorted_duplicates[:20], 1):
        print(f"{i}. {product_name[:60]}")
        print(f"   Appears {info['count']} times in rows: {info['row_numbers']}")
    
    if len(sorted_duplicates) > 20:
        print(f"\n... and {len(sorted_duplicates) - 20} more duplicate products")
    
    # Save to JSON file
    output_file = 'duplicate_products_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\nDetailed analysis saved to: {output_file}")
    
    # Save duplicate row numbers to text file
    row_numbers_file = 'duplicate_product_row_numbers.txt'
    with open(row_numbers_file, 'w', encoding='utf-8') as f:
        f.write("# Row numbers in WebsiteScrapper 2.ods that contain duplicate products\n")
        for row_num in duplicate_row_numbers:
            f.write(f"{row_num}\n")
    
    print(f"Duplicate row numbers saved to: {row_numbers_file}")
    
    # Create a detailed CSV of duplicates
    csv_file = 'duplicate_products_details.csv'
    duplicate_rows_data = []
    for product_name, info in duplicates.items():
        for row_info in info['rows']:
            row_idx = row_info['index']
            row_data = df.iloc[row_idx].to_dict()
            row_data['duplicate_count'] = info['count']
            row_data['is_duplicate'] = True
            duplicate_rows_data.append(row_data)
    
    if duplicate_rows_data:
        duplicate_df = pd.DataFrame(duplicate_rows_data)
        duplicate_df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"Detailed duplicate products saved to: {csv_file}")
    
    return summary

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Find duplicate products in spreadsheet')
    parser.add_argument('--spreadsheet', type=str, default='WebsiteScrapper 2.ods',
                       help='Path to spreadsheet file')
    
    args = parser.parse_args()
    
    find_duplicate_products(args.spreadsheet)

