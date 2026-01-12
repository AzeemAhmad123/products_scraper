"""
Script to upload found products from walmart_scraped_products_20260109_074637.json to Google Sheets
Only uploads products where found: true
"""
import json
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Sheets API scope
# Only use Drive scope if creating new spreadsheets
SCOPES_SHEETS_ONLY = ['https://www.googleapis.com/auth/spreadsheets']
SCOPES_WITH_DRIVE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def detect_credential_type(credentials_file: str):
    """Detect if credentials file is service account or OAuth client"""
    try:
        with open(credentials_file, 'r') as f:
            data = json.load(f)
        
        if 'type' in data and data['type'] == 'service_account':
            return 'service_account'
        elif 'installed' in data or 'web' in data:
            return 'oauth'
        else:
            # Try to determine by structure
            if 'private_key' in data:
                return 'service_account'
            elif 'client_secret' in str(data):
                return 'oauth'
            else:
                raise ValueError("Cannot determine credential type")
    except Exception as e:
        logger.error(f"Error reading credentials file: {str(e)}")
        raise

def get_oauth_credentials(credentials_file: str, use_drive: bool = False):
    """Get OAuth credentials (with token storage)"""
    scopes = SCOPES_WITH_DRIVE if use_drive else SCOPES_SHEETS_ONLY
    token_file = 'token.pickle'
    creds = None
    
    # Load existing token if available
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            logger.warning(f"Could not load existing token: {str(e)}")
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token...")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        
        # Save token for next time
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        logger.info("Token saved for future use")
    
    return creds

def get_google_sheets_client(credentials_file: str, use_drive: bool = False):
    """Initialize Google Sheets client using either service account or OAuth credentials"""
    try:
        cred_type = detect_credential_type(credentials_file)
        logger.info(f"Detected credential type: {cred_type}")
        
        if cred_type == 'service_account':
            scopes = SCOPES_WITH_DRIVE if use_drive else SCOPES_SHEETS_ONLY
            creds = ServiceAccountCredentials.from_service_account_file(credentials_file, scopes=scopes)
        else:
            creds = get_oauth_credentials(credentials_file, use_drive=use_drive)
        
        client = gspread.authorize(creds)
        logger.info("Successfully authenticated with Google Sheets API")
        return client
    except Exception as e:
        logger.error(f"Error authenticating with Google Sheets: {str(e)}")
        raise

def load_products_from_json(json_file: str):
    """Load products from JSON file and filter for found products only"""
    logger.info(f"Loading products from {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter only products where found: true
    found_products = [p for p in data.get('products', []) if p.get('found') == True]
    
    logger.info(f"Total products in file: {len(data.get('products', []))}")
    logger.info(f"Found products (found=true): {len(found_products)}")
    
    return found_products

def upload_to_google_sheets(products: list, spreadsheet_id: str = None, spreadsheet_name: str = 'Walmart Scraped Products', worksheet_name: str = 'Walmart Products', credentials_file: str = 'walmart-scraper-project-82db0cf1ae60.json'):
    """Upload products to Google Sheets"""
    try:
        # Initialize client (only need Drive API if creating new spreadsheet)
        need_drive = spreadsheet_id is None
        client = get_google_sheets_client(credentials_file, use_drive=need_drive)
        
        # Open existing spreadsheet or create new one
        if spreadsheet_id:
            logger.info(f"Opening spreadsheet: {spreadsheet_id}")
            spreadsheet = client.open_by_key(spreadsheet_id)
        else:
            logger.info(f"Creating new spreadsheet: {spreadsheet_name}")
            try:
                spreadsheet = client.create(spreadsheet_name)
                spreadsheet_id = spreadsheet.id
                logger.info(f"Created spreadsheet with ID: {spreadsheet_id}")
            except Exception as e:
                logger.error(f"Failed to create spreadsheet. Google Drive API may need to be enabled.")
                logger.error(f"Error: {str(e)}")
                logger.info("Please provide an existing spreadsheet ID using --spreadsheet-id")
                raise
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            logger.info(f"Using existing worksheet: {worksheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            logger.info(f"Creating new worksheet: {worksheet_name}")
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        
        # Prepare headers
        headers = [
            'Product Name',
            'Walmart Product Name',
            'Price',
            'Brand',
            'Size',
            'In Stock',
            'URL',
            'Scraped At'
        ]
        
        # Clear existing data and add headers
        worksheet.clear()
        worksheet.append_row(headers)
        logger.info("Headers added")
        
        # Prepare data rows
        rows = []
        for product in products:
            row = [
                product.get('product_name', ''),
                product.get('walmart_product_name', ''),
                product.get('walmart_price', ''),
                product.get('walmart_brand', ''),
                product.get('walmart_size', ''),
                'Yes' if product.get('walmart_in_stock') else 'No',
                product.get('walmart_url', ''),
                product.get('scraped_at', '')
            ]
            rows.append(row)
        
        # Upload data in batches (Google Sheets API limit is 10000 cells per request)
        batch_size = 100
        total_uploaded = 0
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            worksheet.append_rows(batch)
            total_uploaded += len(batch)
            logger.info(f"Uploaded {total_uploaded}/{len(rows)} products...")
        
        logger.info(f"Successfully uploaded {len(rows)} products to Google Sheets!")
        logger.info(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error uploading to Google Sheets: {str(e)}")
        raise

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload found products to Google Sheets')
    parser.add_argument('--json-file', type=str, default='walmart_scraped_products_20260109_074637.json',
                       help='JSON file with scraped products')
    parser.add_argument('--spreadsheet-id', type=str, default=None,
                       help='Google Sheets spreadsheet ID (from the URL). If not provided, a new spreadsheet will be created.')
    parser.add_argument('--spreadsheet-name', type=str, default='Walmart Scraped Products',
                       help='Name for new spreadsheet (if creating new one)')
    parser.add_argument('--worksheet-name', type=str, default='Walmart Products',
                       help='Name of the worksheet (default: Walmart Products)')
    parser.add_argument('--credentials', type=str, default='client_secret_1043911085470-45uf75uncmrvpdlfkvaih6kq05laqjmp.apps.googleusercontent.com.json',
                       help='Path to Google OAuth credentials JSON file')
    
    args = parser.parse_args()
    
    # Load products
    products = load_products_from_json(args.json_file)
    
    if not products:
        logger.warning("No found products to upload!")
        return
    
    # Upload to Google Sheets
    upload_to_google_sheets(
        products=products,
        spreadsheet_id=args.spreadsheet_id,
        spreadsheet_name=args.spreadsheet_name,
        worksheet_name=args.worksheet_name,
        credentials_file=args.credentials
    )

if __name__ == '__main__':
    main()

