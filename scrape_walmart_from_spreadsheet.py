"""
Script to scrape Walmart for products from the spreadsheet
Reads product names from WebsiteScrapper 2.ods, searches Walmart, and saves results
"""
import pandas as pd
import json
import logging
from datetime import datetime
from typing import List, Dict
from scrapers.walmart_scraper import WalmartScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_products_from_spreadsheet(file_path: str) -> pd.DataFrame:
    """Load products from the spreadsheet"""
    logger.info(f"Loading products from {file_path}")
    df = pd.read_excel(file_path, engine='odf')
    logger.info(f"Loaded {len(df)} products from spreadsheet")
    return df


def search_walmart_for_product(scraper: WalmartScraper, product_name: str, max_results: int = 5) -> Dict:
    """Search Walmart for a specific product and return best match"""
    try:
        logger.info(f"Searching Walmart for: {product_name}")
        
        # Ensure driver is initialized
        if not scraper.driver:
            scraper._get_driver()
        
        products = scraper.search_products(product_name, max_results=max_results)
        
        if not products:
            return {
                'product_name': product_name,
                'found': False,
                'walmart_url': None,
                'walmart_price': None,
                'walmart_product_name': None
            }
        
        # Get the first product (best match)
        best_product = products[0]
        
        # If we don't have price, try to get details from product page
        if not best_product.price and best_product.product_url:
            logger.info(f"Fetching details for: {best_product.name}")
            try:
                detailed = scraper.get_product_details(best_product.product_url)
                if detailed and detailed.price:
                    best_product = detailed
            except Exception as e:
                logger.warning(f"Could not get details: {str(e)}")
        
        return {
            'product_name': product_name,
            'found': True,
            'walmart_url': best_product.product_url,
            'walmart_price': best_product.price,
            'walmart_product_name': best_product.name,
            'walmart_brand': best_product.brand,
            'walmart_size': best_product.size,
            'walmart_in_stock': best_product.in_stock,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching for {product_name}: {str(e)}")
        return {
            'product_name': product_name,
            'found': False,
            'error': str(e),
            'walmart_url': None,
            'walmart_price': None
        }


def get_already_processed_products(output_file: str = None) -> set:
    """Get set of products that have already been processed"""
    import glob
    processed = set()
    
    # First check the main output file if specified
    if output_file:
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for product in data.get('products', []):
                    processed.add(product.get('product_name'))
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"Could not read {output_file}: {str(e)}")
    
    # Also check existing batch files
    batch_files = glob.glob("walmart_batch_*.json")
    
    for batch_file in batch_files:
        try:
            with open(batch_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for product in data.get('products', []):
                    processed.add(product.get('product_name'))
        except:
            pass
    
    return processed


def load_existing_results(output_file: str) -> List[Dict]:
    """Load existing results from output file"""
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('products', [])
    except FileNotFoundError:
        return []
    except Exception as e:
        logger.warning(f"Could not load existing results: {str(e)}")
        return []


def save_to_output_file(results: List[Dict], output_file: str):
    """Save all results to the main output file"""
    output_data = {
        'scraped_at': datetime.utcnow().isoformat(),
        'total_products': len(results),
        'products_found': sum(1 for r in results if r.get('found')),
        'products': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file} ({len(results)} products)")


def load_row_numbers_from_file(row_numbers_file: str) -> set:
    """Load row numbers from a text file"""
    row_numbers = set()
    try:
        with open(row_numbers_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        row_numbers.add(int(line))
                    except ValueError:
                        pass
        logger.info(f"Loaded {len(row_numbers)} row numbers from {row_numbers_file}")
    except FileNotFoundError:
        logger.warning(f"Row numbers file not found: {row_numbers_file}")
    return row_numbers


def scrape_all_products_from_spreadsheet(
    spreadsheet_path: str, 
    batch_size: int = 100,
    start_from: int = 0,
    resume: bool = True,
    output_file: str = 'walmart_scraped_products_20260109_074637.json',
    row_numbers_file: str = None
):
    """Scrape Walmart for all products in spreadsheet in batches"""
    
    # Load existing results
    existing_results = load_existing_results(output_file)
    existing_product_names = {p.get('product_name') for p in existing_results if p.get('product_name')}
    all_results = existing_results.copy()
    
    # Load products
    df = load_products_from_spreadsheet(spreadsheet_path)
    
    # Filter by row numbers if provided
    if row_numbers_file:
        row_numbers = load_row_numbers_from_file(row_numbers_file)
        if row_numbers:
            # Filter dataframe to only include specified rows (row numbers are 1-indexed)
            df = df.iloc[[i for i in range(len(df)) if (i + 1) in row_numbers]].copy()
            logger.info(f"Filtered to {len(df)} rows based on row numbers file")
    
    # Get unique product names
    product_names = df['Product'].unique().tolist()
    
    logger.info(f"Total unique products in spreadsheet: {len(product_names)}")
    logger.info(f"Existing results in {output_file}: {len(existing_results)} products")
    
    # Start from specified index first (before resume check)
    if start_from > 0:
        product_names = product_names[start_from:]
        logger.info(f"Starting from index {start_from}, {len(product_names)} products remaining")
    
    # Get already processed products if resuming
    if resume:
        processed = get_already_processed_products(output_file)
        logger.info(f"Already processed: {len(processed)} products")
        # Filter out already processed
        original_count = len(product_names)
        product_names = [p for p in product_names if p not in processed]
        logger.info(f"Remaining to process: {len(product_names)} products (skipped {original_count - len(product_names)} already processed)")
    
    if not product_names:
        logger.info("All products already processed!")
        return
    
    # Calculate number of batches
    total_batches = (len(product_names) + batch_size - 1) // batch_size
    logger.info(f"Will process in {total_batches} batches of {batch_size} products each")
    logger.info(f"Results will be saved to: {output_file}")
    
    import time
    
    # Process in batches
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(product_names))
        batch_products = product_names[start_idx:end_idx]
        
        logger.info("\n" + "=" * 70)
        logger.info(f"BATCH {batch_num + 1}/{total_batches}")
        logger.info(f"Processing products {start_idx + 1} to {end_idx} (of {len(product_names)})")
        logger.info("=" * 70)
        
        batch_results = []
        
        # Process each product in this batch
        for i, product_name in enumerate(batch_products, 1):
            global_idx = start_idx + i
            logger.info(f"\n[Batch {batch_num + 1}, Product {i}/{len(batch_products)}] [{global_idx}/{len(product_names)}] Processing: {product_name}")
            
            # Create new scraper for each product
            scraper = WalmartScraper()
            try:
                result = search_walmart_for_product(scraper, product_name)
                batch_results.append(result)
                
                # Update all_results and save immediately
                # Remove existing entry if present
                all_results = [r for r in all_results if r.get('product_name') != product_name]
                all_results.append(result)
                save_to_output_file(all_results, output_file)
                
                # Log result
                if result.get('found'):
                    logger.info(f"  ✓ Found: ${result.get('walmart_price')} - {result.get('walmart_product_name', '')[:50]}")
                else:
                    logger.info(f"  ✗ Not found")
                    
            except Exception as e:
                logger.error(f"Failed to process {product_name}: {str(e)}")
                error_result = {
                    'product_name': product_name,
                    'found': False,
                    'error': str(e),
                    'walmart_url': None,
                    'walmart_price': None
                }
                batch_results.append(error_result)
                # Update all_results
                all_results = [r for r in all_results if r.get('product_name') != product_name]
                all_results.append(error_result)
                save_to_output_file(all_results, output_file)
            finally:
                try:
                    scraper.cleanup()
                except:
                    pass
            
            # Add delay between searches
            time.sleep(5)
        
        # Print batch summary
        found_count = sum(1 for r in batch_results if r.get('found'))
        logger.info("\n" + "-" * 70)
        logger.info(f"Batch {batch_num + 1} Complete:")
        logger.info(f"  Products processed: {len(batch_results)}")
        logger.info(f"  Products found: {found_count}")
        logger.info(f"  Products not found: {len(batch_results) - found_count}")
        logger.info(f"  Total in output file: {len(all_results)} products")
        logger.info("-" * 70)
        
        # If not last batch, wait a bit before next batch
        if batch_num < total_batches - 1:
            logger.info(f"\nWaiting 10 seconds before starting next batch...")
            time.sleep(10)
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("ALL BATCHES COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Total batches processed: {total_batches}")
    logger.info(f"Total products processed: {len(product_names)}")
    logger.info(f"Total products in {output_file}: {len(all_results)}")
    logger.info(f"Products found: {sum(1 for r in all_results if r.get('found'))}")
    logger.info("=" * 70)


def save_batch_results(results: List[Dict], output_file: str, batch_num: int, total_batches: int):
    """Save batch results to JSON file"""
    output_data = {
        'batch_number': batch_num,
        'total_batches': total_batches,
        'scraped_at': datetime.utcnow().isoformat(),
        'products_in_batch': len(results),
        'products_found': sum(1 for r in results if r.get('found')),
        'products': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"Batch {batch_num} saved to {output_file}")


def save_results(results: List[Dict], output_file: str):
    """Save results to JSON file"""
    output_data = {
        'scraped_at': datetime.utcnow().isoformat(),
        'total_products': len(results),
        'products_found': sum(1 for r in results if r.get('found')),
        'products': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Walmart for products from spreadsheet in batches')
    parser.add_argument('--spreadsheet', type=str, default='WebsiteScrapper 2.ods',
                       help='Path to spreadsheet file')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of products per batch (default: 100)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from product index (default: 0, use 3 to skip first 3)')
    parser.add_argument('--no-resume', action='store_true',
                       help='Do not resume - process all products from start')
    parser.add_argument('--output-file', type=str, default='walmart_scraped_products_20260109_074637.json',
                       help='Output file to save results (default: walmart_scraped_products_20260109_074637.json)')
    parser.add_argument('--row-numbers-file', type=str, default=None,
                       help='Path to file containing row numbers to scrape (one per line)')
    
    args = parser.parse_args()
    
    scrape_all_products_from_spreadsheet(
        spreadsheet_path=args.spreadsheet,
        batch_size=args.batch_size,
        start_from=args.start_from,
        resume=not args.no_resume,
        output_file=args.output_file,
        row_numbers_file=args.row_numbers_file
    )

