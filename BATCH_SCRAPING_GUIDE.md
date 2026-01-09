# Batch Scraping Guide

## How It Works

The scraper now processes products in **batches of 100**:

1. **Loads all products** from spreadsheet
2. **Skips already processed** products (checks existing batch files)
3. **Processes 100 products** at a time
4. **Saves each batch** to a separate JSON file
5. **Automatically continues** to next batch
6. **Stops when all products are done**

## File Structure

Each batch is saved as:
- `walmart_batch_001_20260109_074637.json` (Batch 1)
- `walmart_batch_002_20260109_080000.json` (Batch 2)
- `walmart_batch_003_20260109_081500.json` (Batch 3)
- etc.

## Running the Scraper

### Start from Product 4 (Skip first 3 already done)
```bash
python scrape_walmart_from_spreadsheet.py --batch-size 100 --start-from 3
```

### Start from beginning (all products)
```bash
python scrape_walmart_from_spreadsheet.py --batch-size 100
```

### Custom batch size
```bash
python scrape_walmart_from_spreadsheet.py --batch-size 50
```

## Resume Feature

The scraper automatically:
- ✅ Checks existing batch files
- ✅ Skips already processed products
- ✅ Continues from where it left off

**If script stops/crashes:**
- Just run it again with same command
- It will automatically skip processed products
- Continues from next batch

## Progress Tracking

Each batch file contains:
- Batch number
- Total batches
- Products in batch
- Products found
- Full product data

## Estimated Time

- **Per product**: ~10-15 seconds (with delays)
- **Per batch (100 products)**: ~15-25 minutes
- **Total (11,448 products)**: ~30-50 hours (can run overnight)

## Monitoring

Watch the console output:
- Shows current batch number
- Shows progress within batch
- Shows found/not found status
- Saves automatically after each batch

## Stopping and Resuming

**To stop:** Press Ctrl+C
**To resume:** Run the same command again
- It will skip already processed products
- Continue from next batch

## Output Files

All batch files are saved in the project folder:
```
walmart_batch_001_*.json
walmart_batch_002_*.json
walmart_batch_003_*.json
...
```

Each file is independent - you can process them separately or combine later.

