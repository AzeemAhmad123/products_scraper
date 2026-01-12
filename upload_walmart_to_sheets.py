"""
Upload Walmart scraped products to Google Sheets in a new sheet
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
            print("Starting OAuth flow...")
            print("A browser window will open. Please authorize the application.")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        print("Token saved for future use")
    
    return creds

def load_products(json_file: str):
    """Load all products from JSON file"""
    print(f"Loading products from {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    products = data.get('products', [])
    print(f"Loaded {len(products)} products")
    return products

def upload_to_sheets(products: list, spreadsheet_id: str, sheet_name: str = None, credentials_file: str = None):
    """Upload products to a new sheet in existing Google Spreadsheet"""
    
    if credentials_file is None:
        credentials_file = 'client_secret_1043911085470-45uf75uncmrvpdlfkvaih6kq05laqjmp.apps.googleusercontent.com.json'
    
    if sheet_name is None:
        sheet_name = f"Walmart Products {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"\nAuthenticating with Google Sheets...")
    creds = get_credentials(credentials_file)
    client = gspread.authorize(creds)
    
    print(f"\nOpening spreadsheet: {spreadsheet_id}")
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except Exception as e:
        print(f"Error opening spreadsheet: {str(e)}")
        print("Please check the spreadsheet ID and ensure you have access to it.")
        return False
    
    # Create new worksheet
    print(f"\nCreating new worksheet: {sheet_name}")
    try:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=len(products) + 100, cols=15)
        print(f"Created worksheet: {sheet_name}")
    except Exception as e:
        print(f"Error creating worksheet: {str(e)}")
        return False
    
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
    
    # Add headers
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
    
    print(f"\n✅ Successfully uploaded {len(products)} products to Google Sheets!")
    print(f"\nSpreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
    print(f"Sheet name: {sheet_name}")
    
    return True

def main():
    """Main function"""
    print("=" * 70)
    print("UPLOAD WALMART PRODUCTS TO GOOGLE SHEETS")
    print("=" * 70)
    print()
    
    # Get spreadsheet ID from user
    spreadsheet_id = input("Enter Google Spreadsheet ID (from the URL): ").strip()
    if not spreadsheet_id:
        print("Error: Spreadsheet ID is required!")
        return
    
    # Optional: Get sheet name
    sheet_name = input("Enter sheet name (or press Enter for default): ").strip()
    if not sheet_name:
        sheet_name = None
    
    # Load products
    json_file = 'walmart_scraped_products_20260109_074637.json'
    products = load_products(json_file)
    
    if not products:
        print("No products to upload!")
        return
    
    # Upload to sheets
    upload_to_sheets(products, spreadsheet_id, sheet_name)

if __name__ == '__main__':
    main()

