"""
MongoDB handler for storing scraped products
"""
import logging
from typing import List, Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from datetime import datetime, timedelta

from config import MONGODB_URI, MONGODB_DB_NAME
from models.product import Product
from utils.product_matcher import normalize_product_name

logger = logging.getLogger(__name__)


class MongoDBHandler:
    """Handles MongoDB operations for product storage"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client[MONGODB_DB_NAME]
            self.collection = self.db['products']
            
            # Create indexes for better query performance
            self.collection.create_index([('name', 'text')])  # Text search index
            self.collection.create_index([('source', 1), ('product_url', 1)], unique=True)  # Unique constraint
            self.collection.create_index([('scraped_at', -1)])  # For sorting by date
            self.collection.create_index([('normalized_name', 1)])  # For product matching
            self.collection.create_index([('price', 1)])  # For price sorting
            
            logger.info(f"Connected to MongoDB: {MONGODB_DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.client = None
            self.db = None
            self.collection = None
    
    def is_connected(self) -> bool:
        """Check if MongoDB connection is active"""
        if not self.client:
            return False
        try:
            self.client.server_info()
            return True
        except:
            return False
    
    def insert_product(self, product: Product) -> bool:
        """Insert a single product into MongoDB"""
        if not self.is_connected():
            logger.warning("MongoDB not connected. Skipping insert.")
            return False
        
        try:
            product_dict = product.to_dict()
            # Add normalized name for matching
            product_dict['normalized_name'] = normalize_product_name(product.name)
            # Use upsert to update if product already exists
            self.collection.update_one(
                {'source': product.source, 'product_url': product.product_url},
                {'$set': product_dict},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error inserting product {product.name}: {str(e)}")
            return False
    
    def insert_products(self, products: List[Product]) -> int:
        """Insert multiple products into MongoDB"""
        if not self.is_connected():
            logger.warning("MongoDB not connected. Skipping insert.")
            return 0
        
        inserted_count = 0
        for product in products:
            if self.insert_product(product):
                inserted_count += 1
        
        logger.info(f"Inserted {inserted_count}/{len(products)} products into MongoDB")
        return inserted_count
    
    def search_products(self, query: str, limit: int = 50) -> List[dict]:
        """Search for products by name"""
        if not self.is_connected():
            logger.warning("MongoDB not connected. Cannot search.")
            return []
        
        try:
            # Text search
            results = list(self.collection.find(
                {'$text': {'$search': query}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})]).limit(limit))
            
            # Fallback to regex if text search returns nothing
            if len(results) == 0:
                results = list(self.collection.find(
                    {'name': {'$regex': query, '$options': 'i'}}
                ).limit(limit))
            
            return results
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    def get_product_count(self, source: Optional[str] = None) -> int:
        """Get total number of products in database"""
        if not self.is_connected():
            return 0
        
        try:
            if source:
                return self.collection.count_documents({'source': source})
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Error getting product count: {str(e)}")
            return 0
    
    def find_product_prices(self, product_name: str, max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Find prices for a specific product across all stores
        Returns list of products with prices, sorted by price (lowest first)
        """
        if not self.is_connected():
            logger.warning("MongoDB not connected. Cannot search.")
            return []
        
        try:
            normalized = normalize_product_name(product_name)
            
            # Find products matching the normalized name
            # Also search by original name for flexibility
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Search using text search and normalized name
            query = {
                '$or': [
                    {'normalized_name': {'$regex': normalized, '$options': 'i'}},
                    {'name': {'$regex': product_name, '$options': 'i'}},
                    {'$text': {'$search': product_name}}
                ],
                'scraped_at': {'$gte': cutoff_time},  # Only recent data
                'price': {'$ne': None, '$gt': 0},  # Must have valid price
                'in_stock': True  # Only in-stock items
            }
            
            results = list(self.collection.find(query).sort('price', 1))
            
            # Remove _id for cleaner output
            for result in results:
                result.pop('_id', None)
            
            return results
        except Exception as e:
            logger.error(f"Error finding product prices: {str(e)}")
            return []
    
    def get_best_price(self, product_name: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Get the best (lowest) price for a product across all stores
        Returns the product with the lowest price, or None if not found
        """
        products = self.find_product_prices(product_name, max_age_hours)
        if products:
            return products[0]  # Already sorted by price
        return None
    
    def compare_prices(self, product_name: str, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Compare prices for a product across all stores
        Returns comparison data with best price, all prices, etc.
        """
        products = self.find_product_prices(product_name, max_age_hours)
        
        if not products:
            return {
                'product_name': product_name,
                'found': False,
                'stores': [],
                'best_price': None,
                'price_range': None
            }
        
        # Group by store
        stores = {}
        for product in products:
            source = product.get('source', 'unknown')
            if source not in stores:
                stores[source] = []
            stores[source].append(product)
        
        # Get best price
        best = products[0] if products else None
        prices = [p['price'] for p in products if p.get('price')]
        
        return {
            'product_name': product_name,
            'found': True,
            'total_stores': len(stores),
            'total_products': len(products),
            'best_price': {
                'price': best['price'] if best else None,
                'store': best.get('source') if best else None,
                'product_url': best.get('product_url') if best else None,
                'name': best.get('name') if best else None
            },
            'price_range': {
                'lowest': min(prices) if prices else None,
                'highest': max(prices) if prices else None,
                'average': sum(prices) / len(prices) if prices else None
            },
            'stores': stores,
            'all_prices': products
        }
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

