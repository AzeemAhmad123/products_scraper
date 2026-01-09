# Price Comparison Guide

## Overview

This scraper now supports **price comparison across multiple stores**. You can search for a specific product (e.g., "Milk 2L Nestle") and get prices from Walmart.ca and Metro.ca, then compare them to find the best deal.

## How It Works

### 1. Product Name Normalization

The system normalizes product names to match the same product across different stores:
- Removes special characters and extra spaces
- Converts to lowercase for comparison
- Handles variations in naming (e.g., "Nestle Milk 2L" vs "Milk 2L Nestle")

### 2. Price Comparison

When you search for a product:
1. The scraper searches both Walmart and Metro
2. Products are stored in MongoDB with normalized names
3. The system matches products across stores
4. Prices are compared and sorted (lowest first)

### 3. MongoDB Storage

Products are stored with:
- Original product name
- Normalized name (for matching)
- Price, brand, size, etc.
- Source store (walmart/metro)
- Timestamp

## Usage Examples

### Command Line: Search for a Product

```bash
# Search for "Milk 2L Nestle" and compare prices
python scraper.py --search "Milk 2L Nestle" --once
```

Output:
- Searches Walmart and Metro
- Shows best price
- Saves to MongoDB
- Creates JSON file with results

### Python API: Use in Your App Backend

```python
from api.price_comparison_api import PriceComparisonAPI

api = PriceComparisonAPI()

# Get the best price
best = api.get_best_price("Milk 2L Nestle")
if best:
    print(f"Best price: ${best['price']} at {best['source']}")
    print(f"URL: {best['product_url']}")

# Compare all prices
comparison = api.compare_prices("Milk 2L Nestle")
print(f"Lowest: ${comparison['price_range']['lowest']}")
print(f"Highest: ${comparison['price_range']['highest']}")
print(f"Average: ${comparison['price_range']['average']}")

# Get all prices sorted
prices = api.get_product_prices("Milk 2L Nestle")
for product in prices:
    print(f"${product['price']} - {product['source']} - {product['name']}")
```

### Example Response Structure

```json
{
  "product_name": "Milk 2L Nestle",
  "found": true,
  "total_stores": 2,
  "total_products": 5,
  "best_price": {
    "price": 4.99,
    "store": "walmart",
    "product_url": "https://www.walmart.ca/...",
    "name": "Nestle Milk 2L"
  },
  "price_range": {
    "lowest": 4.99,
    "highest": 6.49,
    "average": 5.74
  },
  "stores": {
    "walmart": [
      {"name": "...", "price": 4.99, ...},
      {"name": "...", "price": 5.49, ...}
    ],
    "metro": [
      {"name": "...", "price": 5.99, ...},
      {"name": "...", "price": 6.49, ...}
    ]
  }
}
```

## Integration with Your App

### Step 1: Set Up MongoDB

Make sure MongoDB is running and configured in `.env`:
```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=grocery_scraper
```

### Step 2: Run the Scraper

Schedule the scraper to run every 3 hours:
```bash
python scraper.py
```

Or run it manually:
```bash
python scraper.py --search "Product Name" --once
```

### Step 3: Use the API in Your Backend

In your app's backend (Flask, Django, FastAPI, etc.):

```python
from api.price_comparison_api import PriceComparisonAPI

# Initialize API
api = PriceComparisonAPI()

# Endpoint: Get best price for a product
@app.route('/api/products/best-price')
def get_best_price():
    product_name = request.args.get('name')
    best = api.get_best_price(product_name)
    return jsonify(best)

# Endpoint: Compare prices
@app.route('/api/products/compare')
def compare_prices():
    product_name = request.args.get('name')
    comparison = api.compare_prices(product_name)
    return jsonify(comparison)
```

### Step 4: Display in Your App

When a user types a product name in your app:
1. Send request to your backend: `GET /api/products/compare?name=Milk 2L Nestle`
2. Backend queries MongoDB using the API
3. Return price comparison data
4. Display in app: "Best price: $4.99 at Walmart"

## Workflow

1. **Scraping** (every 3 hours):
   - Scraper searches for products
   - Saves to MongoDB with normalized names
   - Updates existing products with new prices

2. **User Search** (real-time):
   - User types product name in app
   - App queries MongoDB via API
   - Returns best price and comparison
   - Shows user where to buy

3. **Data Freshness**:
   - Only prices from last 24 hours are used (configurable)
   - Older data is ignored for accuracy

## Adding More Stores

To add more stores (e.g., Loblaws, Sobeys):

1. Create new scraper: `scrapers/loblaws_scraper.py`
2. Add to `GroceryScraper` class in `scraper.py`
3. The price comparison will automatically include the new store

## Testing

Test the price comparison:
```bash
# Search for a product
python scraper.py --search "Milk 2L Nestle" --once

# Test the API
python api/price_comparison_api.py

# Run example
python example_price_comparison.py
```

## Notes

- Product matching uses fuzzy matching - same products with slightly different names will be matched
- Prices are sorted automatically (lowest first)
- Only in-stock items are included in comparisons
- Data freshness: Only prices from last 24 hours are used (configurable via `max_age_hours`)



