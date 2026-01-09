# How to Use Scraper Results in Your App

## Where Results Are Stored

### 1. JSON Files (Local Testing)
Results are saved to JSON files in the project directory:
- Format: `product_search_[product_name]_[timestamp].json`
- Example: `product_search_milk_20260108_184945.json`

### 2. MongoDB (Production)
When MongoDB is connected, results are stored in:
- Database: `grocery_scraper` (configurable)
- Collection: `products`
- Each product has: name, price, store, URL, image, etc.

## How Your App Gets Results

### Step 1: Scraper Runs (Background)
The scraper runs every 3 hours and saves products to MongoDB:
```bash
python scraper.py  # Runs every 3 hours automatically
```

### Step 2: User Searches in App
When user types a product name in your Pantry List app:

1. **App sends request to your backend:**
   ```
   GET /api/products/search?name=Milk%202L%20Nestle
   ```

2. **Your backend queries MongoDB:**
   ```python
   from api.price_comparison_api import PriceComparisonAPI
   
   api = PriceComparisonAPI()
   comparison = api.compare_prices("Milk 2L Nestle")
   ```

3. **Backend returns JSON to app:**
   ```json
   {
     "success": true,
     "product_name": "Milk 2L Nestle",
     "best_price": {
       "price": 4.99,
       "store": "walmart",
       "store_display_name": "Walmart",
       "product_url": "https://www.walmart.ca/...",
       "product_name": "Nestle Milk 2L"
     },
     "price_range": {
       "lowest": 4.99,
       "highest": 6.49,
       "average": 5.74
     },
     "all_stores": [
       {
         "store": "walmart",
         "price": 4.99,
         "product_name": "Nestle Milk 2L",
         "product_url": "https://...",
         "in_stock": true
       },
       {
         "store": "metro",
         "price": 5.99,
         "product_name": "Nestle Milk 2L",
         "product_url": "https://...",
         "in_stock": true
       }
     ]
   }
   ```

4. **App displays results:**
   - Show best price: "Best Price: $4.99 at Walmart"
   - Show all options: List all stores with prices
   - Link to product: User can click to go to store website

## Example Backend Code

### Flask Example
```python
from flask import Flask, request, jsonify
from api.price_comparison_api import PriceComparisonAPI

app = Flask(__name__)
api = PriceComparisonAPI()

@app.route('/api/products/search', methods=['GET'])
def search_product():
    product_name = request.args.get('name', '')
    
    if not product_name:
        return jsonify({'success': False, 'message': 'Product name required'}), 400
    
    comparison = api.compare_prices(product_name)
    
    if not comparison.get('found'):
        return jsonify({
            'success': False,
            'message': 'Product not found',
            'product_name': product_name
        })
    
    # Format for app
    response = {
        'success': True,
        'product_name': product_name,
        'best_price': {
            'price': comparison['best_price']['price'],
            'store': comparison['best_price']['store'],
            'store_display_name': comparison['best_price']['store'].title(),
            'product_url': comparison['best_price']['product_url'],
            'product_name': comparison['best_price']['name']
        },
        'price_range': comparison['price_range'],
        'all_stores': []
    }
    
    # Add all stores
    for store_name, products in comparison['stores'].items():
        for product in products:
            response['all_stores'].append({
                'store': store_name,
                'store_display_name': store_name.title(),
                'price': product['price'],
                'product_name': product['name'],
                'product_url': product['product_url'],
                'image_url': product.get('image_url'),
                'in_stock': product.get('in_stock', True)
            })
    
    # Sort by price
    response['all_stores'].sort(key=lambda x: x['price'] or float('inf'))
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
```

### FastAPI Example
```python
from fastapi import FastAPI, Query
from api.price_comparison_api import PriceComparisonAPI

app = FastAPI()
api = PriceComparisonAPI()

@app.get('/api/products/search')
def search_product(name: str = Query(..., description="Product name to search")):
    comparison = api.compare_prices(name)
    
    if not comparison.get('found'):
        return {
            'success': False,
            'message': 'Product not found',
            'product_name': name
        }
    
    # Format response (same as Flask example above)
    # ...
    
    return response
```

## App Display Example

### In Your Mobile App (React Native / Flutter / etc.)

```javascript
// When user types product name
async function searchProduct(productName) {
  const response = await fetch(
    `https://your-backend.com/api/products/search?name=${encodeURIComponent(productName)}`
  );
  const data = await response.json();
  
  if (data.success) {
    // Show best price
    showBestPrice(data.best_price);
    
    // Show all options
    showAllStores(data.all_stores);
  } else {
    showNotFound();
  }
}

function showBestPrice(bestPrice) {
  // Display: "Best Price: $4.99 at Walmart"
  // With link to product_url
}

function showAllStores(stores) {
  // Display list:
  // - Walmart: $4.99 [Link]
  // - Metro: $5.99 [Link]
  // Sorted by price (lowest first)
}
```

## Current Test Results

Right now, results are saved to:
- **JSON file**: `product_search_milk_20260108_184945.json`
- **MongoDB**: Not connected yet (use `--no-db` flag for testing)

To see current results:
```bash
python show_results.py
```

## Next Steps

1. **Set up MongoDB** (for production):
   - Install MongoDB or use MongoDB Atlas
   - Update `.env` file with connection string
   - Run scraper: `python scraper.py --search "milk" --once`

2. **Create backend API**:
   - Use the example code above
   - Deploy to your server
   - Connect to MongoDB

3. **Update your app**:
   - Add API call to search products
   - Display results with prices
   - Show "Best Price" prominently
   - Link to store websites

4. **Schedule scraping**:
   - Run `python scraper.py` to start automatic scraping every 3 hours
   - Products will be updated in MongoDB
   - Your app will always have fresh prices



