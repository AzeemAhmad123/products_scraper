# Grocery Web Scraper

A web scraping tool to extract product details from Walmart.ca and Metro.ca for the Pantry List app.

## Features

- Scrapes product details from Walmart.ca and Metro.ca
- **Price comparison across stores** - Find the best price for any product
- **Product matching** - Automatically matches same products across different stores
- Stores data in MongoDB with normalized product names
- Automated scheduling (every 3 hours or nightly)
- Local testing support before production deployment
- Saves results to JSON files for local testing without MongoDB
- **API for your app** - Easy integration with your Pantry List app backend

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Chrome/Chromium

The scraper uses Selenium with Chrome. Make sure Chrome is installed on your system. The `webdriver-manager` package will automatically download the appropriate ChromeDriver.

### 3. Configure Environment (Optional)

Create a `.env` file (copy from `.env.example`):
```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=grocery_scraper
SCRAPE_INTERVAL_HOURS=3
REQUEST_DELAY_SECONDS=2.0
HEADLESS_BROWSER=True
```

**Note:** MongoDB is optional. The scraper will save results to JSON files even without MongoDB.

### 4. MongoDB Setup (Optional, for production)

If you want to use MongoDB:
- Install MongoDB locally or use MongoDB Atlas
- Update `MONGODB_URI` in `.env` file
- The scraper will automatically connect and create indexes

## Usage

### Search for a Specific Product (Price Comparison)

Search for a specific product and compare prices across stores:
```bash
python scraper.py --search "Milk 2L Nestle" --once
```

This will:
- Search for the product on Walmart and Metro
- Save results to MongoDB
- Show price comparison with best price
- Save results to JSON file

### Quick Test (Individual Scrapers)

Test each scraper individually:
```bash
python test_scraper.py
```

### Local Testing (Limited Queries, No Scheduling)

Test with a few product categories:
```bash
python scraper.py --test --once --no-db
```

This will:
- Run a limited set of queries (3 categories)
- Save results to JSON file
- Skip MongoDB (use `--no-db` flag)
- Exit after completion

### Run Once (Full Scrape, No Scheduling)

Run a full scrape once and exit:
```bash
python scraper.py --once
```

Or without MongoDB:
```bash
python scraper.py --once --no-db
```

### Production Mode (Scheduled Scraping)

Run with automatic scheduling (every 3 hours by default):
```bash
python scraper.py
```

Or specify custom interval:
```bash
python scraper.py --interval 6
```

This will:
- Run immediately
- Then schedule runs every N hours
- Continue running until stopped (Ctrl+C)

## Command Line Options

- `--search "Product Name"` - Search for a specific product and compare prices
- `--test` - Run in test mode (limited queries for faster testing)
- `--once` - Run once and exit (no scheduling)
- `--no-db` - Skip MongoDB, save to JSON only
- `--interval N` - Set hours between scrapes (default: 3)

## Using the Price Comparison API in Your App

The `api/price_comparison_api.py` module provides functions your app backend can use:

```python
from api.price_comparison_api import PriceComparisonAPI

api = PriceComparisonAPI()

# Get best price for a product
best = api.get_best_price("Milk 2L Nestle")
# Returns: {'price': 4.99, 'source': 'walmart', 'product_url': '...', ...}

# Compare all prices
comparison = api.compare_prices("Milk 2L Nestle")
# Returns: {
#   'best_price': {...},
#   'price_range': {'lowest': 4.99, 'highest': 6.49, 'average': 5.74},
#   'stores': {'walmart': [...], 'metro': [...]},
#   ...
# }

# Get all prices sorted by price
prices = api.get_product_prices("Milk 2L Nestle")
# Returns: List of products sorted by price (lowest first)
```

See `example_price_comparison.py` for a complete example.

## Project Structure

```
.
├── scraper.py                 # Main orchestration script
├── test_scraper.py           # Test script for individual scrapers
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py       # Base scraper class
│   ├── walmart_scraper.py    # Walmart.ca scraper
│   └── metro_scraper.py      # Metro.ca scraper
├── models/
│   └── product.py            # Product data model
└── database/
    ├── __init__.py
    └── mongodb_handler.py    # MongoDB integration
```

## Data Structure

Each product contains:
- `name` - Product name
- `price` - Current price
- `original_price` - Original price (if on sale)
- `image_url` - Product image URL
- `product_url` - Link to product page
- `description` - Product description
- `brand` - Brand name
- `size` - Product size/weight
- `unit` - Unit of measurement
- `category` - Product category
- `in_stock` - Stock availability
- `source` - 'walmart' or 'metro'
- `scraped_at` - Timestamp of scraping

## Output

Results are saved to:
- **JSON files**: `scraped_products_YYYYMMDD_HHMMSS.json` (always created)
- **MongoDB**: `grocery_scraper.products` collection (if MongoDB is configured)

## Testing Locally

1. **Test individual scrapers:**
   ```bash
   python test_scraper.py
   ```

2. **Test full scraper without MongoDB:**
   ```bash
   python scraper.py --test --once --no-db
   ```

3. **Check the JSON output file** to verify data structure

4. **Test with MongoDB** (if installed):
   ```bash
   python scraper.py --test --once
   ```

## Production Deployment

1. Set up MongoDB (local or cloud)
2. Update `.env` with production MongoDB URI
3. Run with scheduling:
   ```bash
   python scraper.py
   ```
4. Or use a process manager like `systemd` or `supervisord` to keep it running

## Notes

- The scraper includes delays between requests to be respectful to the websites
- Both sites may have anti-scraping measures; the scraper uses Selenium to handle JavaScript
- Website structures may change; scrapers may need updates if selectors change
- Always check robots.txt and terms of service before scraping

