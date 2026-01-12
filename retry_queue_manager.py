"""
Retry queue manager for blocked/skipped products
"""
import json
import os
import logging
from typing import List, Set, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

RETRY_QUEUE_FILE = 'retry_queue.json'
MAX_RETRY_ATTEMPTS = 3

def load_retry_queue() -> Dict[str, int]:
    """Load retry queue from file"""
    if not os.path.exists(RETRY_QUEUE_FILE):
        return {}
    
    try:
        with open(RETRY_QUEUE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('products', {})
    except Exception as e:
        logger.warning(f"Could not load retry queue: {str(e)}")
        return {}

def save_retry_queue(retry_queue: Dict[str, int]):
    """Save retry queue to file"""
    try:
        data = {
            'last_updated': datetime.now().isoformat(),
            'products': retry_queue
        }
        with open(RETRY_QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save retry queue: {str(e)}")

def add_to_retry_queue(product_name: str, retry_queue: Dict[str, int], lock):
    """Add product to retry queue"""
    with lock:
        current_attempts = retry_queue.get(product_name, 0)
        if current_attempts < MAX_RETRY_ATTEMPTS:
            retry_queue[product_name] = current_attempts + 1
            logger.info(f"📋 Added to retry queue: {product_name} (attempt {retry_queue[product_name]}/{MAX_RETRY_ATTEMPTS})")
        else:
            logger.warning(f"⚠️ Max retries reached for {product_name}, removing from queue")

def remove_from_retry_queue(product_name: str, retry_queue: Dict[str, int], lock):
    """Remove product from retry queue (successfully scraped)"""
    with lock:
        if product_name in retry_queue:
            del retry_queue[product_name]
            logger.info(f"✅ Removed from retry queue (successfully scraped): {product_name}")

def get_retry_queue_products(retry_queue: Dict[str, int]) -> List[str]:
    """Get list of products to retry"""
    return [product for product, attempts in retry_queue.items() if attempts < MAX_RETRY_ATTEMPTS]

def clear_retry_queue(retry_queue: Dict[str, int], lock):
    """Clear all products from retry queue"""
    with lock:
        retry_queue.clear()
        logger.info("Cleared retry queue")


