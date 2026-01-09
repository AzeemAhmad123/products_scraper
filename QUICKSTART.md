# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Test Locally (No MongoDB Required)

Test the scrapers without setting up MongoDB:

```bash
python test_scraper.py
```

This will test both Walmart and Metro scrapers with a simple "milk" search.

## Step 3: Run a Test Scrape

Run a limited scrape and save to JSON (no MongoDB needed):

```bash
python scraper.py --test --once --no-db
```

This will:
- Search for 3 product categories (milk, bread, eggs)
- Save results to a JSON file
- Not require MongoDB

Check the generated `scraped_products_*.json` file to see the results.

## Step 4: Full Scrape (Optional)

Once testing works, run a full scrape:

```bash
python scraper.py --once --no-db
```

This searches for 15 common grocery items from both sites.

## Step 5: Set Up MongoDB (For Production)

1. Install MongoDB or use MongoDB Atlas
2. Create a `.env` file:
   ```
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB_NAME=grocery_scraper
   SCRAPE_INTERVAL_HOURS=3
   ```
3. Run with MongoDB:
   ```bash
   python scraper.py --once
   ```

## Step 6: Schedule Automatic Scraping

Run with automatic scheduling (every 3 hours):

```bash
python scraper.py
```

Press Ctrl+C to stop.

## Troubleshooting

### Chrome/ChromeDriver Issues
- Make sure Chrome browser is installed
- The `webdriver-manager` package will auto-download ChromeDriver
- If issues persist, try updating Chrome browser

### Website Changes
- If scrapers stop working, the website structure may have changed
- Check the logs in `scraper.log` for errors
- You may need to update the CSS selectors in the scraper files

### MongoDB Connection Issues
- If MongoDB is not running, use `--no-db` flag
- Results will still be saved to JSON files
- Check MongoDB connection string in `.env` file

## Next Steps

1. Test locally first with `--test --once --no-db`
2. Verify the JSON output looks correct
3. Set up MongoDB when ready for production
4. Deploy and schedule regular scraping



