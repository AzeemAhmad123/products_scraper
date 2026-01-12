"""
Google Sheets uploader module for automatically uploading new products
"""
import gspread
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Configuration
SPREADSHEET_ID = '1gQ78uBRQPYOavjxp4yMpTXxXBQmKY3eoSCUaHC4Ntzg'
SHEET_NAME = 'Products'
CREDENTIALS_FILE = 'client_secret_1043911085470-45uf75uncmrvpdlfkvaih6kq05laqjmp.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.pickle'

# Cache for already uploaded products (to avoid duplicates)
_uploaded_products_cache: Set[str] = set()
_cache_initialized = False

def get_credentials():
    """Get OAuth credentials"""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            logger.warning(f"Could not load existing token: {str(e)}")
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired Google token...")
                creds.refresh(Request())
            except Exception as e:
                logger.warning(f"Could not refresh token: {str(e)}")
                creds = None
        
        if not creds:
            logger.warning("Google Sheets authentication required. Skipping upload for now.")
            return None
        
        # Save token for next time
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            logger.warning(f"Could not save token: {str(e)}")
    
    return creds

def initialize_uploaded_products_cache():
    """Initialize cache with products already in Google Sheets"""
    global _uploaded_products_cache, _cache_initialized
    
    if _cache_initialized:
        return
    
    try:
        creds = get_credentials()
        if not creds:
            _cache_initialized = True
            return
        
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Get all product names from column A (skip header)
        all_values = worksheet.col_values(1)
        if len(all_values) > 1:  # Has header + data
            _uploaded_products_cache = set(all_values[1:])  # Skip header
            logger.info(f"Initialized cache with {len(_uploaded_products_cache)} products from Google Sheets")
        else:
            logger.info("Google Sheets is empty, starting fresh")
        
        _cache_initialized = True
    except Exception as e:
        logger.warning(f"Could not initialize Google Sheets cache: {str(e)}")
        _cache_initialized = True  # Mark as initialized to avoid retrying

def upload_new_products_to_sheets(new_products: List[Dict], spreadsheet_id: str = None, sheet_name: str = None):
    """
    Upload only new products to Google Sheets
    Returns number of products uploaded
    """
    if not new_products:
        return 0
    
    spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
    sheet_name = sheet_name or SHEET_NAME
    
    try:
        # Initialize cache if not done
        if not _cache_initialized:
            initialize_uploaded_products_cache()
        
        # Filter out products already uploaded
        products_to_upload = []
        for product in new_products:
            product_name = product.get('product_name', '').strip()
            if product_name and product_name not in _uploaded_products_cache:
                products_to_upload.append(product)
                _uploaded_products_cache.add(product_name)
        
        if not products_to_upload:
            logger.debug(f"No new products to upload to Google Sheets (all {len(new_products)} already uploaded)")
            return 0
        
        # Get credentials
        creds = get_credentials()
        if not creds:
            logger.warning("Cannot upload to Google Sheets: No valid credentials")
            return 0
        
        # Connect to Google Sheets
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Prepare rows
        rows = []
        for product in products_to_upload:
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
        batch_size = 100
        uploaded = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            worksheet.append_rows(batch)
            uploaded += len(batch)
        
        logger.info(f"📊 Uploaded {uploaded} new products to Google Sheets")
        return uploaded
        
    except Exception as e:
        logger.error(f"Error uploading to Google Sheets: {str(e)}")
        # Don't raise - allow scraper to continue even if upload fails
        return 0

