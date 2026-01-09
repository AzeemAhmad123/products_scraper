# Implementation Plan for 10-Store Scraper

## Phase 1: Anti-Bot Setup ✅
- [x] Add `undetected-chromedriver` to requirements
- [x] Update `base_scraper.py` to use undetected-chromedriver
- [x] Test with existing stores (Walmart, Metro)

## Phase 2: Store Configuration ✅
- [x] Add all 10 store URLs to config.py
- [x] Add "Nestle Coffee Mate" to search list
- [x] Create store configuration structure

## Phase 3: Create Store Scrapers (In Progress)
For each store, create a scraper similar to `walmart_scraper.py`:

### Priority 1 (Most Popular):
- [ ] `loblaws_scraper.py` - Loblaws.ca
- [ ] `sobeys_scraper.py` - Sobeys.com
- [ ] `nofrills_scraper.py` - No Frills

### Priority 2:
- [ ] `realcanadiansuperstore_scraper.py` - Real Canadian Superstore
- [ ] `freshco_scraper.py` - FreshCo
- [ ] `foodbasics_scraper.py` - Food Basics

### Priority 3:
- [ ] `longos_scraper.py` - Longo's
- [ ] `fortinos_scraper.py` - Fortinos

## Phase 4: Multi-Store Integration
- [ ] Update `GroceryScraper` class to handle all 10 stores
- [ ] Create store factory/registry pattern
- [ ] Update `search_product_across_stores()` to query all stores

## Phase 5: Price Comparison Logic
- [ ] Function: `get_prices_for_product(product_name)` - Returns prices from all stores
- [ ] Function: `compare_list_prices(shopping_list)` - Best stores for entire list
- [ ] Function: `get_best_store_for_list(shopping_list)` - Single store or multi-store recommendation

## Phase 6: MongoDB Schema
Update schema to support:
- Product name (normalized)
- Prices from all 10 stores (array or separate fields)
- Store availability
- Last updated per store
- Price history (optional)

## Phase 7: API Endpoints for App
- [ ] `GET /api/products/{name}/prices` - All store prices for a product
- [ ] `GET /api/products/{name}/best-price` - Best price and store
- [ ] `POST /api/lists/compare` - Compare entire shopping list
- [ ] `GET /api/lists/{list_id}/recommendations` - Store recommendations

## Testing Strategy
1. Test undetected-chromedriver with "Nestle Coffee Mate" on Walmart
2. Test with Metro
3. Test with one new store (Loblaws)
4. Scale to all 10 stores
5. Test price comparison functions
6. Test MongoDB storage and retrieval

## Estimated Timeline
- Phase 1-2: ✅ Complete
- Phase 3: 2-3 days (creating 8 new scrapers)
- Phase 4: 1 day
- Phase 5: 1 day
- Phase 6: 1 day
- Phase 7: 1-2 days

**Total: ~1 week for full implementation**



