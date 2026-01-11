# Two-Computer Scraping Setup Guide

## Overview
You have **7,258 remaining unique products** to scrape, split into two files for parallel scraping on two computers.

## Files Created

1. **`unique_unscraped_rows_computer1.txt`** - 5,247 products (for Computer 1)
2. **`unique_unscraped_rows_computer2.txt`** - 5,248 products (for Computer 2)

## Setup Instructions

### Option 1: Shared Network Drive (Recommended)
If both computers can access the same network drive or cloud folder:

**Computer 1:**
```bash
python scrape_walmart_parallel.py --spreadsheet "WebsiteScrapper 2.ods" --row-numbers-file "unique_unscraped_rows_computer1.txt" --workers 2 --output-file "walmart_scraped_products_20260109_074637.json"
```

**Computer 2:**
```bash
python scrape_walmart_parallel.py --spreadsheet "WebsiteScrapper 2.ods" --row-numbers-file "unique_unscraped_rows_computer2.txt" --workers 2 --output-file "walmart_scraped_products_20260109_074637.json"
```

**Benefits:**
- Both computers save to the same file
- Duplicate prevention works automatically
- No merging needed
- Real-time progress tracking

### Option 2: Separate Files (Then Merge)
If computers cannot share files:

**Computer 1:**
```bash
python scrape_walmart_parallel.py --spreadsheet "WebsiteScrapper 2.ods" --row-numbers-file "unique_unscraped_rows_computer1.txt" --workers 2 --output-file "walmart_scraped_products_computer1.json"
```

**Computer 2:**
```bash
python scrape_walmart_parallel.py --spreadsheet "WebsiteScrapper 2.ods" --row-numbers-file "unique_unscraped_rows_computer2.txt" --workers 2 --output-file "walmart_scraped_products_computer2.json"
```

**After both finish, merge the files:**
```bash
python merge_results_from_two_computers.py
```

## Important Notes

1. **Copy Required Files to Both Computers:**
   - `scrape_walmart_parallel.py`
   - `WebsiteScrapper 2.ods`
   - `unique_unscraped_rows_computer1.txt` (to Computer 1)
   - `unique_unscraped_rows_computer2.txt` (to Computer 2)
   - `scrapers/` folder (entire folder)
   - `config.py`
   - All dependencies installed

2. **Duplicate Prevention:**
   - The scraper automatically prevents duplicates
   - Uses `product_name` as unique key
   - If both computers scrape the same product, the last one wins

3. **Backup System:**
   - Both computers will create backups automatically
   - Backups stored in `backups/` directory
   - Last 20 backups kept automatically

4. **Progress Tracking:**
   - Each computer will skip already-scraped products
   - Check the JSON file to see progress
   - Total products will increase as scraping progresses

## Verification

After setup, verify on each computer:
```bash
python -c "import json; f=open('walmart_scraped_products_20260109_074637.json','r',encoding='utf-8'); data=json.load(f); print(f'Total products: {len(data.get(\"products\",[]))}')"
```

## Troubleshooting

**If computers can't access shared file:**
- Use Option 2 (separate files)
- Merge files when both are done
- The merge script handles duplicates automatically

**If you see conflicts:**
- The duplicate prevention system handles this
- Last write wins (both are valid, just one is kept)
- No data loss occurs

## Expected Results

- **Computer 1:** Will scrape ~5,247 products
- **Computer 2:** Will scrape ~5,248 products
- **Total:** ~7,258 unique products (some overlap is normal)
- **Final:** ~7,658 unique products total (including the 400 already scraped)

