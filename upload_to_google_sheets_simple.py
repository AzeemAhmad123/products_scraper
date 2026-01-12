"""
Simple script to upload Walmart products to Google Sheets
Creates a NEW spreadsheet if you don't have one
"""
import json
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import sys
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_credentials(credentials_file: str):
    """Get OAuth credentials"""
    token_file = 'token.pickle'
    creds = None
    
    # Load existing token if available
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Could not load existing token: {str(e)}")
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("=" * 70)
            print("GOOGLE AUTHENTICATION")
            print("=" * 70)
            print("\nA browser window will open.")
            print("Please sign in with your Google account and authorize the app.")
            print("\nPress Enter to continue...")
            input()
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        print("✓ Token saved for future use")
    
    return creds

def load_products(json_file: str):
    """Load all products from JSON file"""
    print(f"\nLoading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    print(f"✓ Loaded {len(products)} products")
    return products

def create_new_spreadsheet_and_upload(products: list, spreadsheet_name: str = None, sheet_name: str = None, credentials_file: str = None):
    """Create a new Google Spreadsheet and upload products"""
    
    if credentials_file is None:
        credentials_file = 'client_secret_1043911085470-45uf75uncmrvpdlfkvaih6kq05laqjmp.apps.googleusercontent.com.json'
    
    if spreadsheet_name is None:
        spreadsheet_name = f"Walmart Scraped Products {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    if sheet_name is None:
        sheet_name = "Products"
    
    print("\n" + "=" * 70)
    print("UPLOADING TO GOOGLE SHEETS")
    print("=" * 70)
    
    print(f"\nAuthenticating with Google Sheets...")
    creds = get_credentials(credentials_file)
    client = gspread.authorize(creds)
    print("✓ Authenticated successfully")
    
    print(f"\nCreating new spreadsheet: {spreadsheet_name}")
    try:
        spreadsheet = client.create(spreadsheet_name)
        spreadsheet_id = spreadsheet.id
        print(f"✓ Created spreadsheet with ID: {spreadsheet_id}")
        print(f"✓ Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    except Exception as e:
        print(f"✗ Error creating spreadsheet: {str(e)}")
        return False
    
    # Use the first worksheet (default Sheet1)
    worksheet = spreadsheet.sheet1
    worksheet.update_title(sheet_name)
    print(f"✓ Using worksheet: {sheet_name}")
    
    # Prepare headers
    headers = [
        'Product Name',
        'Found',
        'Walmart Product Name',
        'Walmart Price',
        'Walmart Brand',
        'Walmart Size',
        'In Stock',
        'Walmart URL',
        'Scraped At'
    ]
    
    print(f"\nUploading {len(products)} products...")
    
    # Clear and add headers
    worksheet.clear()
    worksheet.append_row(headers)
    
    # Prepare and upload data in batches
    batch_size = 100
    rows = []
    
    for product in products:
        row = [
            product.get('product_name', ''),
            'Yes' if product.get('found') else 'No',
            product.get('walmart_product_name', ''),
            product.get('walmart_price', ''),
            product.get('walmart_brand', ''),
            product.get('walmart_size', ''),
            'Yes' if product.get('walmart_in_stock') else 'No',
            product.get('walmart_url', ''),
            product.get('scraped_at', '')
        ]
        rows.append(row)
    
    # Upload in batches
    uploaded = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        worksheet.append_rows(batch)
        uploaded += len(batch)
        print(f"  Uploaded {uploaded}/{len(rows)} products...")
    
    print(f"\n" + "=" * 70)
    print("✅ UPLOAD COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Successfully uploaded {len(products)} products")
    print(f"\n📊 Spreadsheet URL:")
    print(f"   https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print(f"\n📋 Sheet name: {sheet_name}")
    print(f"\nYou can now open the spreadsheet in your browser!")
    
    return True

def main():
    """Main function"""
    print("=" * 70)
    print("UPLOAD WALMART PRODUCTS TO GOOGLE SHEETS")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Create a NEW Google Spreadsheet")
    print("  2. Upload all your scraped products")
    print("  3. Give you the link to access it")
    print()
    
    # Use default names (can be modified if needed)
    spreadsheet_name = None  # Will use default with timestamp
    sheet_name = None  # Will use "Products"
    
    # Load products
    json_file = 'walmart_scraped_products_20260109_074637.json'
    products = load_products(json_file)
    
    if not products:
        print("No products to upload!")
        return
    
    # Create spreadsheet and upload
    create_new_spreadsheet_and_upload(products, spreadsheet_name, sheet_name)

if __name__ == '__main__':
    main()

