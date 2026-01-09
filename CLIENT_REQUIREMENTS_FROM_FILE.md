# Client Requirements - Based on Spreadsheet Analysis

## File Analysis
- **Total Products**: 11,448 products
- **Store**: FoodBasics (example/template)
- **Purpose**: This appears to be a template showing the data structure the client wants

## Required Data Fields

Based on the spreadsheet columns, the client wants to scrape:

### 1. Store Information
- **Store** - Store name (e.g., FoodBasics, Walmart, Metro, etc.)

### 2. Category Hierarchy (4 Levels)
- **Master Category** - Top level (e.g., "Dairy & Eggs", "Fruits & Vegetables")
- **Main Category** - Second level (e.g., "dairy and eggs", "fruits and vegetables")
- **2nd Level** - Third level (e.g., "milk cream butter", "fruits")
- **3rd Level** - Fourth level (e.g., "salted butter", "banana")

### 3. Product Information
- **Product** - Full product name
- **URL** - Direct link to product page
- **Brand** - Product brand name
- **Size** - Product size/weight (e.g., "454 g", "2 L", "12 un")
- **Price per unit** - Current price
- **On Sale?** - Yes/No indicator
- **Original Price** - Regular price (if on sale)
- **Sale Price** - Discounted price (if on sale)
- **In stock** - Stock availability (Yes/No)
- **SKU** - Product SKU/barcode

## What This Means

### Current System vs. Required System

**What We Have:**
- ✅ Product name
- ✅ URL
- ✅ Brand (sometimes)
- ✅ Size (sometimes)
- ✅ Price
- ✅ In stock status
- ❌ Category hierarchy (missing)
- ❌ Sale information (Original Price vs Sale Price)
- ❌ SKU (missing)

### What We Need to Add

1. **Category Extraction**
   - Need to extract 4-level category hierarchy from product pages
   - Store: Master Category > Main Category > 2nd Level > 3rd Level

2. **Sale Information**
   - Detect if product is on sale
   - Extract original price
   - Extract sale price
   - Currently we only get current price

3. **SKU Extraction**
   - Extract product SKU/barcode from product pages

4. **Enhanced Product Model**
   - Update Product model to include:
     - Category hierarchy
     - Sale status
     - Original price
     - SKU

## Implementation Plan

### Phase 1: Update Product Model
- Add category fields (master_category, main_category, category_2nd, category_3rd)
- Add sale fields (is_on_sale, original_price, sale_price)
- Add SKU field

### Phase 2: Update Scrapers
- Extract category hierarchy from product pages
- Detect sale status and extract both prices
- Extract SKU from product pages

### Phase 3: Update MongoDB Schema
- Store all new fields
- Index categories for filtering

### Phase 4: Update API
- Return category information
- Return sale information
- Return SKU

## Example Data Structure

```json
{
  "store": "FoodBasics",
  "master_category": "Dairy & Eggs",
  "main_category": "dairy and eggs",
  "category_2nd": "milk cream butter",
  "category_3rd": "salted butter",
  "product": "Salted Butter",
  "url": "https://www.foodbasics.ca/...",
  "brand": "SELECTION",
  "size": "454 g",
  "price_per_unit": 5.89,
  "on_sale": false,
  "original_price": null,
  "sale_price": null,
  "in_stock": true,
  "sku": "59749894784"
}
```

## Next Steps

1. ✅ Understand requirements (DONE)
2. ⏳ Update Product model with new fields
3. ⏳ Update scrapers to extract categories, sale info, SKU
4. ⏳ Test with FoodBasics (since that's in the template)
5. ⏳ Apply to all 10 stores

## Questions for Client

1. Do they want to scrape ALL products from each store, or just search for specific products?
2. Should we scrape by category (browse categories) or by search?
3. How often should categories be updated?
4. Is the FoodBasics data a template, or do they want us to scrape FoodBasics specifically?



