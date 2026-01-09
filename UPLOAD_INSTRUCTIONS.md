# Upload Products to Google Sheets - Instructions

## Option 1: Use Existing Spreadsheet (Recommended)

If you already have a Google Sheet, you need to:

1. **Get the Spreadsheet ID** from the URL:
   - Open your Google Sheet
   - The URL looks like: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part

2. **Share the spreadsheet** with the service account email:
   - Email: `metro-price-scraper@walmart-scraper-project.iam.gserviceaccount.com`
   - Give it "Editor" access

3. **Run the upload script:**
   ```bash
   python upload_to_google_sheets.py --spreadsheet-id YOUR_SPREADSHEET_ID
   ```

## Option 2: Create New Spreadsheet

If you want to create a new spreadsheet:

1. **Enable Google Drive API:**
   - Visit: https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project=1043911085470
   - Click "Enable"

2. **Run the upload script:**
   ```bash
   python upload_to_google_sheets.py
   ```

## What the Script Does

- Reads `walmart_scraped_products_20260109_074637.json`
- Filters for products where `found: true` (only found products)
- Uploads to Google Sheets with columns:
  - Product Name
  - Walmart Product Name
  - Price
  - Brand
  - Size
  - In Stock
  - URL
  - Scraped At

## Current Status

- Found products ready to upload: 114 products
- Script is ready to run once you provide spreadsheet ID or enable Drive API

