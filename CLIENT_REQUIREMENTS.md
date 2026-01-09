# Client Requirements Summary

## Product to Scrape
- **Nestle Coffee Mate** - Added to search list
- Alternative search: "Coffee Mate"

## Stores to Scrape (10 Canadian Grocery Stores)
1. **Walmart.ca** ✅ (Already implemented)
2. **Metro.ca** ✅ (Already implemented)
3. **Loblaws.ca** (To be implemented)
4. **Sobeys.com** (To be implemented)
5. **No Frills** (To be implemented)
6. **Real Canadian Superstore** (To be implemented)
7. **FreshCo.com** (To be implemented)
8. **Food Basics** (To be implemented)
9. **Longo's** (To be implemented)
10. **Fortinos** (To be implemented)

## Use Cases

### Use Case 1: Show Prices Below Each Item
- User adds items to their list
- For each item, show prices from all 10 stores below it
- User can see where to buy each item cheapest

### Use Case 2: Complete List Price Comparison
- User finishes their shopping list
- System shows where they can get the cheapest price for their entire list
- May suggest going to multiple stores for best overall savings

## Technical Requirements

### Anti-Bot Solution
- ✅ Using `undetected-chromedriver` (free, no API needed)
- Replaces regular Selenium to avoid bot detection
- Makes browser look like a real human user

### Data Storage
- MongoDB backend
- Store product prices from all 10 stores
- Support price comparison queries

### Data Structure Needed
For each product (e.g., "Nestle Coffee Mate"):
- Product name
- Price from each store (10 prices)
- Store names
- Product URLs
- Images (if available)
- Last updated timestamp

## Implementation Status

- ✅ Base scraper updated to use undetected-chromedriver
- ✅ "Nestle Coffee Mate" added to search list
- ✅ Configuration for 10 stores added
- ⏳ Individual store scrapers (8 remaining stores)
- ⏳ Multi-store price comparison logic
- ⏳ MongoDB integration for storing all store prices

## Next Steps

1. Test undetected-chromedriver with Walmart and Metro
2. Create scrapers for remaining 8 stores
3. Update main scraper to handle all 10 stores
4. Create price comparison functions for:
   - Single product across all stores
   - Entire shopping list across all stores
5. MongoDB schema for storing multi-store prices



