"""
Parallel scraper for Walmart products with queue-based saving
- Runs 5 Chrome browsers in parallel
- Queues results and flushes every 5 products
- Saves immediately to prevent data loss
"""
import pandas as pd
import json
import logging
import time
import threading
import random
import shutil
import os
from datetime import datetime
from typing import List, Dict, Set
from queue import Queue
from scrapers.walmart_scraper import WalmartScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe lock for JSON file operations
json_lock = threading.Lock()
queue_lock = threading.Lock()

def load_products_from_spreadsheet(file_path: str) -> pd.DataFrame:
    """Load products from the spreadsheet"""
    logger.info(f"Loading products from {file_path}")
    df = pd.read_excel(file_path, engine='odf')
    logger.info(f"Loaded {len(df)} products from spreadsheet")
    return df

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

def load_existing_results(output_file: str) -> List[Dict]:
    """Load existing results from output file with retry logic"""
    max_retries = 3
    retry_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                products = data.get('products', [])
                if products:
                    logger.debug(f"Loaded {len(products)} existing products from {output_file}")
                return products
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"CRITICAL: Failed to load existing results after {max_retries} attempts. File may be corrupted!")
                # Try to load from backup if available
                backup_dir = os.path.join(os.path.dirname(output_file) or '.', 'backups')
                if os.path.exists(backup_dir):
                    backup_files = sorted(
                        [f for f in os.listdir(backup_dir) 
                         if f.startswith(os.path.splitext(os.path.basename(output_file))[0]) and f.endswith('.json')],
                        reverse=True
                    )
                    if backup_files:
                        latest_backup = os.path.join(backup_dir, backup_files[0])
                        logger.warning(f"Attempting to load from backup: {latest_backup}")
                        try:
                            with open(latest_backup, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                products = data.get('products', [])
                                logger.warning(f"Loaded {len(products)} products from backup instead!")
                                return products
                        except:
                            pass
                return []
        except Exception as e:
            logger.error(f"Error loading existing results (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                logger.error(f"CRITICAL: Failed to load existing results after {max_retries} attempts!")
                return []

def create_backup(output_file: str, max_backups: int = 20):
    """Create a backup of the output file before overwriting"""
    try:
        if os.path.exists(output_file):
            # Create backup directory if it doesn't exist
            backup_dir = os.path.join(os.path.dirname(output_file) or '.', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.basename(output_file)
            name_without_ext = os.path.splitext(base_name)[0]
            backup_file = os.path.join(backup_dir, f"{name_without_ext}_backup_{timestamp}.json")
            
            # Copy file to backup
            shutil.copy2(output_file, backup_file)
            logger.info(f"📦 Backup created: {backup_file}")
            
            # Clean up old backups (keep only last max_backups)
            backup_files = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith(name_without_ext) and f.endswith('.json')],
                reverse=True
            )
            for old_backup in backup_files[max_backups:]:
                old_backup_path = os.path.join(backup_dir, old_backup)
                try:
                    os.remove(old_backup_path)
                    logger.debug(f"Removed old backup: {old_backup}")
                except Exception as e:
                    logger.warning(f"Could not remove old backup {old_backup}: {str(e)}")
            
            return backup_file
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
    return None

def save_results_thread_safe(results: List[Dict], output_file: str):
    """Thread-safe function to save results to JSON file with automatic backup"""
    with json_lock:
        try:
            # Create backup before overwriting (only if file exists and has content)
            existing_count_before = 0
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        existing_count_before = len(existing_data.get('products', []))
                        if existing_count_before > 0:
                            create_backup(output_file)
                            logger.debug(f"Backup created before save (existing: {existing_count_before} products)")
                except Exception as e:
                    logger.warning(f"Could not read file for backup: {str(e)}")
            
            # Load existing results with retry logic
            existing_results = load_existing_results(output_file)
            
            # CRITICAL SAFETY CHECK: If we had products before but loaded none, something is wrong!
            if existing_count_before > 0 and len(existing_results) == 0:
                logger.error(f"⚠️ CRITICAL WARNING: File had {existing_count_before} products but loaded 0! This would cause data loss!")
                logger.error("⚠️ Attempting to recover from backup...")
                # Try to load from latest backup
                backup_dir = os.path.join(os.path.dirname(output_file) or '.', 'backups')
                if os.path.exists(backup_dir):
                    backup_files = sorted(
                        [f for f in os.listdir(backup_dir) 
                         if f.startswith(os.path.splitext(os.path.basename(output_file))[0]) and f.endswith('.json')],
                        reverse=True
                    )
                    if backup_files:
                        latest_backup = os.path.join(backup_dir, backup_files[0])
                        try:
                            with open(latest_backup, 'r', encoding='utf-8') as f:
                                backup_data = json.load(f)
                                existing_results = backup_data.get('products', [])
                                logger.warning(f"✅ Recovered {len(existing_results)} products from backup: {latest_backup}")
                        except Exception as e:
                            logger.error(f"Failed to load from backup: {str(e)}")
                
                # If still no results and we had products before, ABORT the save to prevent data loss
                if len(existing_results) == 0 and existing_count_before > 0:
                    logger.error(f"❌ ABORTING SAVE to prevent data loss! File had {existing_count_before} products but cannot load them!")
                    logger.error("❌ Please check the file manually or restore from backup!")
                    return
            
            # Create a dictionary to avoid duplicates (by product_name)
            results_dict = {r.get('product_name'): r for r in existing_results}
            original_dict_size = len(results_dict)
            
            # Update with new results
            new_count = 0
            for result in results:
                product_name = result.get('product_name')
                if product_name:
                    if product_name not in results_dict:
                        new_count += 1
                    results_dict[product_name] = result
            
            # Convert back to list
            all_results = list(results_dict.values())
            
            # Final safety check: ensure we're not losing data
            if original_dict_size > 0 and len(all_results) < original_dict_size:
                logger.error(f"⚠️ WARNING: Would lose {original_dict_size - len(all_results)} products! Aborting save!")
                return
            
            # Save to file
            output_data = {
                'scraped_at': datetime.now().isoformat(),
                'total_products': len(all_results),
                'products_found': sum(1 for r in all_results if r.get('found')),
                'products': all_results
            }
            
            # Write to temporary file first, then rename (atomic write)
            temp_file = output_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            # Atomic rename
            if os.path.exists(output_file):
                os.replace(temp_file, output_file)
            else:
                os.rename(temp_file, output_file)
            
            logger.info(f"✅ Saved {len(results)} products ({new_count} new) to {output_file} (Total: {len(all_results)})")
        except Exception as e:
            logger.error(f"❌ Error saving results: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

def search_walmart_for_product(scraper: WalmartScraper, product_name: str, max_results: int = 20) -> Dict:
    """Search Walmart for a specific product and return best match (lowest price if multiple matches)"""
    try:
        logger.info(f"🔎 [START] Searching Walmart for: {product_name}")
        
        # Ensure driver is initialized
        if not scraper.driver:
            scraper._get_driver()
        
        # Search for more products to find best match
        logger.info(f"🔎 [CALLING] search_products for: {product_name}")
        products = scraper.search_products(product_name, max_results=max_results)
        logger.info(f"🔎 [RETURNED] search_products completed for: {product_name}")
        
        # Check if we got None (blocked)
        if products is None:
            logger.warning(f"⚠ search_products returned None (blocked) for: {product_name}")
            return None
        
        logger.info(f"📦 search_products returned {len(products) if products else 0} products for: {product_name}")
        
        if not products:
            logger.warning(f"⚠ No products returned from search for: {product_name}")
            return {
                'product_name': product_name,
                'found': False,
                'walmart_url': None,
                'walmart_price': None,
                'walmart_product_name': None,
                'scraped_at': datetime.now().isoformat()
            }
        
        # Log all products found
        for i, p in enumerate(products[:5]):  # Log first 5
            logger.info(f"  Product {i+1}: {p.name[:60] if p.name else 'NO NAME'} - ${p.price if p.price else 'NO PRICE'}")
        
        # Normalize search terms for matching - filter out very short words
        search_terms = [term.lower().strip() for term in product_name.split() if len(term) > 2]
        # Also try the full search phrase as one term
        if len(product_name) > 3:
            search_terms.append(product_name.lower().strip())
        logger.info(f"🔍 Search terms: {search_terms}")
        
        # Filter products where search terms appear in product name
        matching_products = []
        for product in products:
            if not product.name or product.name == 'Unknown Product':
                continue
            
            product_name_lower = product.name.lower()
            
            # Check if search terms appear in product name
            # Method 1: Check if at least one significant term matches
            matching_terms = sum(1 for term in search_terms if term in product_name_lower and len(term) > 3)
            match_ratio = matching_terms / len(search_terms) if search_terms else 0
            
            # Method 2: Check if the full search phrase (or significant part) appears
            full_phrase_match = False
            if len(product_name) > 5:
                # Check if main words (excluding very short ones) appear
                main_words = [w for w in product_name.lower().split() if len(w) > 3]
                if main_words:
                    main_words_in_product = sum(1 for w in main_words if w in product_name_lower)
                    if main_words_in_product >= len(main_words) * 0.6:  # At least 60% of main words
                        full_phrase_match = True
                        match_ratio = max(match_ratio, 0.8)  # Boost match ratio
            
            # Accept if: at least 20% of terms match OR full phrase matches OR at least one significant term OR any term matches
            # Much more lenient - accept products if they have any relevance
            if match_ratio >= 0.2 or full_phrase_match or matching_terms > 0 or any(term in product_name_lower for term in search_terms if len(term) > 2):
                matching_products.append((product, match_ratio, product.price or float('inf')))
                logger.info(f"  ✓ Match ({match_ratio*100:.0f}%): {product.name[:60]} - ${product.price if product.price else 'N/A'}")
            else:
                logger.debug(f"  ✗ No match ({match_ratio*100:.0f}%): {product.name[:60]}")
        
        # If no products match search terms, but we have products from search, use the first one
        # This handles cases where Walmart returns relevant products but names don't match exactly
        if not matching_products:
            if products and len(products) > 0:
                # Use the first product from search results (Walmart's best match)
                logger.warning(f"No products matched search terms exactly, but using Walmart's first result: {products[0].name[:60]}")
                best_product = products[0]
                # Skip to detail scraping
            else:
                logger.warning(f"No products found matching search terms: {search_terms}")
                return {
                    'product_name': product_name,
                    'found': False,
                    'walmart_url': None,
                    'walmart_price': None,
                    'walmart_product_name': None,
                    'scraped_at': datetime.now().isoformat()
                }
        else:
            # Sort by: 1) Match ratio (higher is better), 2) Price (lower is better)
            # This finds the best matching product with lowest price
            matching_products.sort(key=lambda x: (-x[1], x[2]))  # Negative match_ratio for descending
            
            # Get the best match (highest match ratio, then lowest price)
            best_product, match_ratio, _ = matching_products[0]
            logger.info(f"Selected best match ({match_ratio*100:.0f}% match): {best_product.name[:60]} - ${best_product.price if best_product.price else 'N/A'}")
            
            # If there are multiple products with same match ratio, prefer the one with lowest price
            same_ratio_products = [p for p in matching_products if abs(p[1] - match_ratio) < 0.1]
            if len(same_ratio_products) > 1:
                # Sort by price (lowest first)
                same_ratio_products.sort(key=lambda x: x[2])
                best_product, match_ratio, _ = same_ratio_products[0]
                logger.info(f"Selected lowest price from {len(same_ratio_products)} similar matches: {best_product.name[:60]} - ${best_product.price if best_product.price else 'N/A'}")
        
        # ALWAYS try to fetch full details from product page
        # This is critical - the details page has more accurate data
        if best_product.product_url:
            logger.info(f"🔍 Scraping full product details from page: {best_product.name[:50]}")
            logger.info(f"   URL: {best_product.product_url}")
            try:
                # Try to get details - this should wait for page to load and try many selectors
                detailed = scraper.get_product_details(best_product.product_url)
                
                # Check if we got blocked (only skip if actually blocked)
                if detailed is None:
                    # Check if URL shows blocked
                    if scraper.driver:
                        check_url = scraper.driver.current_url
                        if "blocked" in check_url.lower():
                            logger.warning(f"⚠ Actually blocked when scraping product page, skipping product entirely")
                            return None
                    # Not actually blocked, just failed to parse - use search result data
                    logger.warning(f"⚠ Could not extract details from product page (not blocked), using search result data")
                    logger.info(f"   Search result - Name: {best_product.name[:50]}, Price: ${best_product.price}")
                else:
                    # We got detailed product - check if it's valid
                    if detailed and detailed.name and detailed.name != 'Unknown Product' and len(detailed.name) > 3:
                        # Prefer detailed product - it has more complete data
                        best_product = detailed
                        logger.info(f"✓✓ Successfully scraped complete details: ${best_product.price} - {best_product.name[:50]}")
                    elif detailed and detailed.name and len(detailed.name) > 3:
                        # We got a name but maybe missing price - still use it
                        best_product = detailed
                        logger.info(f"✓ Scraped details (price may be missing): {best_product.name[:50]}")
                    elif detailed and detailed.price:
                        # If we got price from details page, update search result
                        best_product.price = detailed.price
                        if detailed.brand:
                            best_product.brand = detailed.brand
                        if detailed.size:
                            best_product.size = detailed.size
                        if detailed.in_stock is not None:
                            best_product.in_stock = detailed.in_stock
                        logger.info(f"✓ Updated with details page data: ${best_product.price}")
                    else:
                        logger.warning(f"⚠ Detailed product returned but invalid, using search result data")
            except Exception as e:
                logger.error(f"❌ Exception scraping details: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.warning(f"   Using search result data instead")
        
        # Ensure we have at least basic data - but be more lenient
        # Only require that we have a name and URL - price can be None
        if not best_product.name or best_product.name == 'Unknown Product' or len(best_product.name) < 2:
            logger.warning(f"Product name is missing or invalid for: {product_name}")
            return {
                'product_name': product_name,
                'found': False,
                'walmart_url': None,
                'walmart_price': None,
                'walmart_product_name': None,
                'scraped_at': datetime.now().isoformat()
            }
        
        # Save product even if price is missing - we have name and URL which means we found it
        logger.info(f"✅ FINAL: Scraped product: {best_product.name[:60]} - Price: ${best_product.price if best_product.price else 'N/A'}")
        logger.info(f"✅ Returning found=True for: {product_name}")
        result_dict = {
            'product_name': product_name,
            'found': True,  # Always True if we have name and URL
            'walmart_url': best_product.product_url,
            'walmart_price': best_product.price,  # Can be None
            'walmart_product_name': best_product.name,
            'walmart_brand': best_product.brand,
            'walmart_size': best_product.size,
            'walmart_in_stock': best_product.in_stock,
            'scraped_at': datetime.now().isoformat()
        }
        logger.info(f"✅ Result dict created: found={result_dict.get('found')}, price={result_dict.get('walmart_price')}")
        return result_dict
        
    except Exception as e:
        logger.error(f"❌ [EXCEPTION] Error searching for {product_name}: {str(e)}")
        import traceback
        logger.error(f"❌ [TRACEBACK]: {traceback.format_exc()}")
        # Check if it's a session error - if so, return None to trigger browser recreation
        error_str = str(e).lower()
        if 'invalid session' in error_str or 'session' in error_str or 'no such window' in error_str:
            logger.warning(f"⚠ Session lost for {product_name}, returning None to trigger browser recreation")
            return None
        # For other errors, return a dict with found=False
        return {
            'product_name': product_name,
            'found': False,
            'error': str(e),
            'walmart_url': None,
            'walmart_price': None,
            'walmart_product_name': None,
            'scraped_at': datetime.now().isoformat()
        }

def queue_manager(queue: Queue, output_file: str, flush_size: int = 5):
    """Manages the result queue and flushes when it reaches flush_size"""
    buffer = []
    
    while True:
        try:
            # Get result from queue (with timeout to check if we should exit)
            try:
                result = queue.get(timeout=1)
            except:
                # If queue is empty and we have items in buffer, flush them
                if buffer:
                    logger.info(f"Flushing {len(buffer)} products from buffer...")
                    save_results_thread_safe(buffer, output_file)
                    buffer = []
                continue
            
            # Check if it's a stop signal
            if result is None:
                # Flush remaining buffer before stopping
                if buffer:
                    logger.info(f"Final flush: {len(buffer)} products")
                    save_results_thread_safe(buffer, output_file)
                    buffer = []
                break
            
            # Add to buffer
            buffer.append(result)
            
            # Flush when buffer reaches flush_size
            if len(buffer) >= flush_size:
                logger.info(f"Queue reached {flush_size} products, flushing...")
                save_results_thread_safe(buffer, output_file)
                buffer = []
            
            queue.task_done()
            
        except Exception as e:
            logger.error(f"Error in queue manager: {str(e)}")
            # Save buffer immediately on error to prevent data loss
            if buffer:
                save_results_thread_safe(buffer, output_file)
                buffer = []

def worker_thread(worker_id: int, product_queue: Queue, result_queue: Queue, output_file: str):
    """Worker thread that processes products"""
    scraper = None
    consecutive_blocks = 0  # Track consecutive blocks
    max_consecutive_blocks = 3  # Recreate browser after 3 consecutive blocks
    
    try:
        scraper = WalmartScraper()
        logger.info(f"Worker {worker_id} started")
        
        while True:
            try:
                # Get product from queue
                product_name = product_queue.get(timeout=1)
            except:
                # Queue is empty, check if we should continue
                continue
            
            # Check for stop signal
            if product_name is None:
                break
            
            try:
                # Search for product
                result = search_walmart_for_product(scraper, product_name)
                
                # Check if result is None (blocked/bot detection)
                if result is None:
                    consecutive_blocks += 1
                    logger.warning(f"[Worker {worker_id}] ⚠ Blocked/Bot detection for: {product_name} - Skipping and continuing (Consecutive blocks: {consecutive_blocks})")
                    
                    # If too many consecutive blocks, recreate the browser
                    if consecutive_blocks >= max_consecutive_blocks:
                        logger.warning(f"[Worker {worker_id}] 🔄 Too many consecutive blocks ({consecutive_blocks}), recreating Chrome browser...")
                        try:
                            # Close old browser
                            if scraper.driver:
                                scraper._close_driver()
                            # Wait a bit to let IP "cool down" (randomized between 30-60 seconds)
                            wait_time = random.randint(30, 60)
                            logger.info(f"[Worker {worker_id}] ⏳ Waiting {wait_time} seconds before recreating browser...")
                            time.sleep(wait_time)
                            # Recreate driver (fresh browser instance)
                            scraper._recreate_driver()
                            consecutive_blocks = 0  # Reset counter
                            logger.info(f"[Worker {worker_id}] ✅ Browser recreated successfully")
                        except Exception as e:
                            logger.error(f"[Worker {worker_id}] Error recreating browser: {str(e)}")
                            # Still reset counter to avoid infinite loop
                            consecutive_blocks = 0
                    
                    continue
                
                # Safety check: Ensure result is a dict (not None)
                if result is None or not isinstance(result, dict):
                    consecutive_blocks += 1
                    logger.warning(f"[Worker {worker_id}] ⚠ Invalid result (None or not dict) for: {product_name} - Treating as blocked (Consecutive blocks: {consecutive_blocks})")
                    if consecutive_blocks >= max_consecutive_blocks:
                        logger.warning(f"[Worker {worker_id}] 🔄 Too many consecutive blocks ({consecutive_blocks}), recreating Chrome browser...")
                        try:
                            if scraper.driver:
                                scraper._close_driver()
                            wait_time = random.randint(30, 60)
                            logger.info(f"[Worker {worker_id}] ⏳ Waiting {wait_time} seconds before recreating browser...")
                            time.sleep(wait_time)
                            scraper._recreate_driver()
                            consecutive_blocks = 0
                            logger.info(f"[Worker {worker_id}] ✅ Browser recreated successfully")
                        except Exception as e:
                            logger.error(f"[Worker {worker_id}] Error recreating browser: {str(e)}")
                            consecutive_blocks = 0
                    continue
                
                # Reset consecutive blocks counter on success
                consecutive_blocks = 0
                
                # Debug: Log what we got (result is guaranteed to be a dict here)
                product_name_short = (result.get('walmart_product_name') or '')[:50] if result.get('walmart_product_name') else 'N/A'
                logger.info(f"[Worker {worker_id}] Result for {product_name}: found={result.get('found')}, price={result.get('walmart_price')}, name={product_name_short}")
                
                # Only add to result queue if product was found
                if result.get('found'):
                    result_queue.put(result)
                    logger.info(f"[Worker {worker_id}] ✓ QUEUED: ${result.get('walmart_price')} - {product_name_short}")
                else:
                    logger.info(f"[Worker {worker_id}] ✗ Not found: {product_name} (not saved to JSON)")
                    # Reset consecutive blocks on successful search (even if product not found)
                    consecutive_blocks = 0
                
            except Exception as e:
                logger.error(f"[Worker {worker_id}] Error processing {product_name}: {str(e)}")
                import traceback
                logger.error(f"[Worker {worker_id}] Traceback: {traceback.format_exc()}")
                # Don't add error results to queue - only save found products
                logger.info(f"[Worker {worker_id}] Error result not saved (only found products are saved)")
            finally:
                product_queue.task_done()
                # Random delay between products (2-5 seconds) to avoid detection
                delay = random.uniform(2, 5)
                time.sleep(delay)
    
    except Exception as e:
        logger.error(f"Worker {worker_id} error: {str(e)}")
    finally:
        if scraper:
            try:
                scraper.cleanup()
            except:
                pass
        logger.info(f"Worker {worker_id} finished")

def scrape_parallel(
    spreadsheet_path: str,
    row_numbers_file: str = None,
    num_workers: int = 2,
    output_file: str = 'walmart_scraped_products_20260109_074637.json',
    flush_size: int = 5
):
    """Scrape products in parallel with multiple Chrome browsers"""
    
    logger.info("=" * 70)
    logger.info("PARALLEL WALMART SCRAPER")
    logger.info("=" * 70)
    logger.info(f"Workers (Chrome browsers): {num_workers}")
    logger.info(f"Queue flush size: {flush_size}")
    logger.info(f"Output file: {output_file}")
    logger.info("=" * 70)
    
    # Load existing results
    existing_results = load_existing_results(output_file)
    existing_product_names = {p.get('product_name') for p in existing_results if p.get('product_name')}
    logger.info(f"Existing results: {len(existing_results)} products")
    
    # Load spreadsheet
    df = load_products_from_spreadsheet(spreadsheet_path)
    
    # Filter by row numbers if provided
    if row_numbers_file:
        row_numbers = load_row_numbers_from_file(row_numbers_file)
        if row_numbers:
            df = df.iloc[[i for i in range(len(df)) if (i + 1) in row_numbers]].copy()
            logger.info(f"Filtered to {len(df)} rows based on row numbers file")
    
    # Get product names
    product_names = df['Product'].unique().tolist()
    
    # Filter out already processed products
    original_count = len(product_names)
    product_names = [p for p in product_names if p not in existing_product_names]
    logger.info(f"Products to process: {len(product_names)} (skipped {original_count - len(product_names)} already processed)")
    
    if not product_names:
        logger.info("All products already processed!")
        return
    
    # Create queues
    product_queue = Queue()
    result_queue = Queue()
    
    # Add products to queue
    for product_name in product_names:
        product_queue.put(product_name)
    
    # Start queue manager thread
    queue_thread = threading.Thread(target=queue_manager, args=(result_queue, output_file, flush_size), daemon=True)
    queue_thread.start()
    logger.info("Queue manager started")
    
    # Start worker threads
    workers = []
    for i in range(num_workers):
        worker = threading.Thread(target=worker_thread, args=(i + 1, product_queue, result_queue, output_file), daemon=True)
        worker.start()
        workers.append(worker)
        logger.info(f"Worker {i + 1} started")
        time.sleep(1)  # Stagger worker starts
    
    logger.info(f"\nProcessing {len(product_names)} products with {num_workers} workers...")
    logger.info("Chrome browsers should be visible now!\n")
    
    # Wait for all products to be processed
    product_queue.join()
    logger.info("All products processed, waiting for workers to finish...")
    
    # Wait a bit for workers to finish
    time.sleep(5)
    
    # Signal workers to stop
    for _ in range(num_workers):
        product_queue.put(None)
    
    # Wait for workers to finish
    for worker in workers:
        worker.join(timeout=10)
    
    # Signal queue manager to stop
    result_queue.put(None)
    queue_thread.join(timeout=5)
    
    # Final save
    final_results = load_existing_results(output_file)
    logger.info("\n" + "=" * 70)
    logger.info("SCRAPING COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"Total products processed: {len(product_names)}")
    logger.info(f"Total products in {output_file}: {len(final_results)}")
    logger.info(f"Products found: {sum(1 for r in final_results if r.get('found'))}")
    logger.info("=" * 70)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Parallel Walmart scraper')
    parser.add_argument('--spreadsheet', type=str, default='WebsiteScrapper 2.ods',
                       help='Path to spreadsheet file')
    parser.add_argument('--row-numbers-file', type=str, default='unique_unscraped_rows.txt',
                       help='Path to file containing row numbers to scrape')
    parser.add_argument('--workers', type=int, default=2,
                       help='Number of parallel workers (Chrome browsers)')
    parser.add_argument('--flush-size', type=int, default=5,
                       help='Number of products to queue before flushing to JSON')
    parser.add_argument('--output-file', type=str, default='walmart_scraped_products_20260109_074637.json',
                       help='Output file to save results')
    
    args = parser.parse_args()
    
    scrape_parallel(
        spreadsheet_path=args.spreadsheet,
        row_numbers_file=args.row_numbers_file,
        num_workers=args.workers,
        output_file=args.output_file,
        flush_size=args.flush_size
    )

