"""Show location of JSON files"""
import os
import glob

print("=" * 70)
print("JSON FILE LOCATION")
print("=" * 70)

# Find all Walmart JSON files
json_files = glob.glob("walmart_scraped_products_*.json")
json_files.sort(key=os.path.getmtime, reverse=True)  # Most recent first

if json_files:
    print(f"\nFound {len(json_files)} JSON file(s):\n")
    
    for i, file in enumerate(json_files, 1):
        file_path = os.path.abspath(file)
        file_size = os.path.getsize(file)
        mod_time = os.path.getmtime(file)
        from datetime import datetime
        mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{i}. {file}")
        print(f"   Full Path: {file_path}")
        print(f"   Size: {file_size} bytes")
        print(f"   Modified: {mod_time_str}")
        print()
    
    print(f"\nMost Recent File:")
    print(f"  {os.path.abspath(json_files[0])}")
    print("\n" + "=" * 70)
else:
    print("\nNo JSON files found!")
    print("Run: python scrape_walmart_from_spreadsheet.py --limit 5")
    print("=" * 70)


