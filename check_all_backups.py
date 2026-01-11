"""
Check all possible backup locations for lost data
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_file_products(filepath):
    """Check how many products are in a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            products = data.get('products', [])
            return len(products), data.get('total_products', 0)
    except:
        return None, None

def main():
    print("=" * 70)
    print("COMPREHENSIVE BACKUP SEARCH")
    print("=" * 70)
    print()
    
    # Check current directory
    current_dir = Path('.')
    target_size = 1400000  # ~1.4 MB for 2,829 products (estimated)
    
    print("1. Checking all JSON files in current directory:")
    print("-" * 70)
    json_files = list(current_dir.glob('*.json'))
    found_large = False
    
    for json_file in sorted(json_files, key=lambda x: x.stat().st_size, reverse=True):
        size = json_file.stat().st_size
        count, total = check_file_products(json_file)
        size_kb = size / 1024
        
        if count:
            status = "✅" if size > target_size else "❌"
            print(f"{status} {json_file.name}")
            print(f"   Size: {size_kb:.2f} KB")
            print(f"   Products: {count} (field: {total})")
            print(f"   Modified: {datetime.fromtimestamp(json_file.stat().st_mtime)}")
            if size > target_size:
                found_large = True
                print(f"   ⚠️ THIS FILE MIGHT CONTAIN YOUR LOST DATA!")
            print()
    
    # Check backups directory
    print("\n2. Checking backups directory:")
    print("-" * 70)
    backups_dir = current_dir / 'backups'
    if backups_dir.exists():
        backup_files = list(backups_dir.glob('*.json'))
        if backup_files:
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_size, reverse=True):
                size = backup_file.stat().st_size
                count, total = check_file_products(backup_file)
                size_kb = size / 1024
                if count:
                    status = "✅" if size > target_size else "❌"
                    print(f"{status} {backup_file.name}")
                    print(f"   Size: {size_kb:.2f} KB")
                    print(f"   Products: {count} (field: {total})")
                    print(f"   Modified: {datetime.fromtimestamp(backup_file.stat().st_mtime)}")
                    if size > target_size:
                        found_large = True
                        print(f"   ⚠️ THIS FILE MIGHT CONTAIN YOUR LOST DATA!")
                    print()
        else:
            print("   No backup files found")
    else:
        print("   Backups directory does not exist")
        print("   (This is normal - backup system was just added)")
    
    # Check temp files
    print("\n3. Checking temporary files:")
    print("-" * 70)
    tmp_files = list(current_dir.glob('*.tmp'))
    if tmp_files:
        for tmp_file in tmp_files:
            size = tmp_file.stat().st_size
            size_kb = size / 1024
            print(f"   {tmp_file.name}: {size_kb:.2f} KB")
            if size > target_size:
                print(f"   ⚠️ THIS TEMP FILE MIGHT CONTAIN YOUR LOST DATA!")
    else:
        print("   No temporary files found")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if not found_large:
        print("❌ No files found with ~1.4 MB size (expected for 2,829 products)")
        print()
        print("The lost data is likely:")
        print("  - Overwritten when scraper restarted")
        print("  - Not saved before the restart")
        print("  - Lost due to the bug that was just fixed")
        print()
        print("RECOMMENDATION:")
        print("  Try Windows Previous Versions (see RECOVERY_GUIDE.md)")
        print("  Right-click the JSON file → Properties → Previous Versions tab")
    else:
        print("✅ Found potential backup file(s) with large size!")
        print("   Check the files marked above")
    
    print()
    print("The backup system is now active and will prevent future data loss.")

if __name__ == '__main__':
    main()

