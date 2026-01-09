"""
Configuration settings for the grocery scraper
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'grocery_scraper')

# Scraping Configuration
SCRAPE_INTERVAL_HOURS = int(os.getenv('SCRAPE_INTERVAL_HOURS', '3'))
REQUEST_DELAY_SECONDS = float(os.getenv('REQUEST_DELAY_SECONDS', '2.0'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# Site URLs - Top 10 Canadian Grocery Stores
WALMART_BASE_URL = 'https://www.walmart.ca'
METRO_BASE_URL = 'https://www.metro.ca'
LOBLAWS_BASE_URL = 'https://www.loblaws.ca'
SOBEYS_BASE_URL = 'https://www.sobeys.com'
NOFRILLS_BASE_URL = 'https://www.nofrills.ca'
REAL_CANADIAN_SUPERSTORE_BASE_URL = 'https://www.realcanadiansuperstore.ca'
FRESHCO_BASE_URL = 'https://www.freshco.com'
FOOD_BASICS_BASE_URL = 'https://www.foodbasics.ca'
LONGOS_BASE_URL = 'https://www.longos.com'
FORTINOS_BASE_URL = 'https://www.fortinos.ca'

# Default stores to scrape (can be configured)
DEFAULT_STORES = [
    'walmart',
    'metro',
    'loblaws',
    'sobeys',
    'nofrills',
    'realcanadiansuperstore',
    'freshco',
    'foodbasics',
    'longos',
    'fortinos'
]

# User Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Selenium Configuration
# Set to False for better results (less bot detection), but browser will be visible
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'False').lower() == 'true'
BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', '30'))

