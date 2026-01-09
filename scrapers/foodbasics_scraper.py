"""
FoodBasics.ca scraper
Based on client requirements from spreadsheet
"""
import re
import logging
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.product import Product
from config import FOOD_BASICS_BASE_URL

logger = logging.getLogger(__name__)


class FoodBasicsScraper(BaseScraper):
    """Scraper for FoodBasics.ca - matches spreadsheet structure"""
    
    def __init__(self):
        super().__init__(FOOD_BASICS_BASE_URL, 'foodbasics')
    
    def search_products(self, query: str, max_results: int = 50) -> List[Product]:
        """Search for products on FoodBasics.ca"""
        products = []
        try:
            search_url = f"{self.base_url}/search?q={quote(query)}"
            logger.info(f"Searching FoodBasics for: {query}")
            
            soup = self._get_page(search_url, use_selenium=True)
            if not soup:
                return products
            
            import time
            time.sleep(3)
            
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # FoodBasics product selectors
            product_selectors = [
                '[data-testid="product-card"]',
                '[class*="product-card"]',
                '[class*="ProductCard"]',
                'div[class*="product-item"]',
                'article[class*="product"]',
                'a[href*="/aisles/"]'
            ]
            
            product_elements = []
            for selector in product_selectors:
                product_elements = soup.select(selector)
                if product_elements:
                    logger.info(f"Found {len(product_elements)} products using selector: {selector}")
                    break
            
            for element in product_elements[:max_results]:
                try:
                    product = self._parse_product_element(element, soup)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing product element: {str(e)}")
                    continue
            
            self._delay()
            
        except Exception as e:
            logger.error(f"Error searching FoodBasics: {str(e)}")
        
        return products
    
    def _parse_product_element(self, element, soup: BeautifulSoup) -> Optional[Product]:
        """Parse a product element from search results"""
        try:
            link = element.find('a', href=True)
            if not link:
                if element.name == 'a' and element.get('href'):
                    link = element
                else:
                    return None
            
            product_url = link.get('href', '')
            if not product_url.startswith('http'):
                product_url = urljoin(self.base_url, product_url)
            
            # Extract product name
            name_elem = (element.select_one('[data-testid="product-name"]') or
                        element.select_one('[class*="name"]') or
                        element.select_one('[class*="title"]') or
                        element.select_one('h2, h3, h4') or
                        link)
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            if not name or name == 'Unknown Product' or len(name) < 3:
                return None
            
            # Extract price
            price_elem = (element.select_one('[data-testid="price"]') or
                         element.select_one('[class*="price"]') or
                         element.select_one('[class*="Price"]'))
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Extract sale information
            is_on_sale = False
            original_price = None
            sale_price = None
            
            # Check for sale indicators
            sale_elem = (element.select_one('[class*="sale"]') or
                        element.select_one('[class*="on-sale"]') or
                        element.select_one('[class*="discount"]'))
            
            if sale_elem or 'sale' in element.get_text().lower():
                is_on_sale = True
                # Try to find original price
                original_price_elem = (element.select_one('[class*="original-price"]') or
                                     element.select_one('[class*="was-price"]') or
                                     element.select_one('[class*="regular-price"]'))
                if original_price_elem:
                    original_price = self._extract_price(original_price_elem.get_text())
                sale_price = price
            
            # Extract image
            img_elem = (element.select_one('img[src]') or
                       element.select_one('img[data-src]'))
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or img_elem.get('data-src'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract brand
            brand_elem = element.select_one('[class*="brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            if not brand and name:
                words = name.split()
                if words and words[0][0].isupper() and len(words[0]) > 2:
                    brand = words[0]
            
            # Extract size from name or element
            size = None
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(L|ml|g|kg|oz|lb|un|pieces?)', name, re.IGNORECASE)
            if size_match:
                size = f"{size_match.group(1)}{size_match.group(2)}"
            
            return Product(
                name=name,
                price=price,
                original_price=original_price,
                sale_price=sale_price,
                is_on_sale=is_on_sale,
                image_url=image_url,
                product_url=product_url,
                brand=brand,
                size=size,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing product element: {str(e)}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text"""
        if not price_text:
            return None
        
        price_patterns = [
            r'\$\s*(\d+\.\d{2})',
            r'\$\s*(\d+)',
            r'(\d+\.\d{2})\s*\$',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text)
            if match:
                try:
                    price = float(match.group(1))
                    if 0.01 <= price <= 10000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def get_product_details(self, product_url: str) -> Optional[Product]:
        """Get detailed product information from product page including categories and SKU"""
        try:
            soup = self._get_page(product_url, use_selenium=True)
            if not soup:
                return None
            
            import time
            time.sleep(2)
            
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract product name
            name_elem = (soup.select_one('h1[data-testid="product-name"]') or
                        soup.select_one('h1[class*="name"]') or
                        soup.select_one('h1[class*="title"]') or
                        soup.select_one('h1'))
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            # Extract price
            price_elem = (soup.select_one('[data-testid="price"]') or
                         soup.select_one('[class*="price"]') or
                         soup.select_one('[itemprop="price"]'))
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Extract sale information
            is_on_sale = False
            original_price = None
            sale_price = None
            
            sale_indicator = (soup.select_one('[class*="sale"]') or
                            soup.select_one('[class*="on-sale"]'))
            if sale_indicator:
                is_on_sale = True
                original_price_elem = (soup.select_one('[class*="original-price"]') or
                                     soup.select_one('[class*="was-price"]'))
                if original_price_elem:
                    original_price = self._extract_price(original_price_elem.get_text())
                sale_price = price
            
            # Extract categories from breadcrumbs or URL
            # FoodBasics URLs often contain category path: /aisles/category1/category2/category3/product
            categories = self._extract_categories_from_url(product_url, soup)
            
            # Extract SKU
            sku = self._extract_sku(soup, product_url)
            
            # Extract other details
            img_elem = soup.select_one('img[class*="product-image"]') or soup.select_one('img[itemprop="image"]')
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or img_elem.get('data-src'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            desc_elem = soup.select_one('[class*="description"]') or soup.select_one('[itemprop="description"]')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            brand_elem = soup.select_one('[class*="brand"]') or soup.select_one('[itemprop="brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            size_elem = soup.select_one('[class*="size"]')
            size = size_elem.get_text(strip=True) if size_elem else None
            
            # Extract size from name if not found
            if not size:
                size_match = re.search(r'(\d+(?:\.\d+)?)\s*(L|ml|g|kg|oz|lb|un|pieces?)', name, re.IGNORECASE)
                if size_match:
                    size = f"{size_match.group(1)}{size_match.group(2)}"
            
            # Check stock
            stock_elem = soup.select_one('[class*="out-of-stock"]') or soup.select_one('[class*="unavailable"]')
            in_stock = stock_elem is None
            
            return Product(
                name=name,
                price=price,
                original_price=original_price,
                sale_price=sale_price,
                is_on_sale=is_on_sale,
                image_url=image_url,
                product_url=product_url,
                description=description,
                brand=brand,
                size=size,
                master_category=categories.get('master_category'),
                main_category=categories.get('main_category'),
                category_2nd=categories.get('category_2nd'),
                category_3rd=categories.get('category_3rd'),
                sku=sku,
                in_stock=in_stock,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error getting product details from {product_url}: {str(e)}")
            return None
    
    def _extract_categories_from_url(self, url: str, soup: BeautifulSoup) -> dict:
        """Extract category hierarchy from URL or breadcrumbs"""
        categories = {
            'master_category': None,
            'main_category': None,
            'category_2nd': None,
            'category_3rd': None
        }
        
        # Try to extract from breadcrumbs
        breadcrumb_elem = soup.select_one('[class*="breadcrumb"]') or soup.select_one('nav[aria-label*="breadcrumb"]')
        if breadcrumb_elem:
            breadcrumbs = breadcrumb_elem.select('a, span')
            breadcrumb_texts = [b.get_text(strip=True) for b in breadcrumbs if b.get_text(strip=True)]
            # Map breadcrumbs to category levels (adjust based on actual structure)
            if len(breadcrumb_texts) >= 4:
                categories['master_category'] = breadcrumb_texts[0] if len(breadcrumb_texts) > 0 else None
                categories['main_category'] = breadcrumb_texts[1] if len(breadcrumb_texts) > 1 else None
                categories['category_2nd'] = breadcrumb_texts[2] if len(breadcrumb_texts) > 2 else None
                categories['category_3rd'] = breadcrumb_texts[3] if len(breadcrumb_texts) > 3 else None
        
        # Fallback: Extract from URL path
        # FoodBasics URLs: /aisles/category1/category2/category3/product
        if '/aisles/' in url:
            url_parts = url.split('/aisles/')[1].split('/')
            if len(url_parts) >= 3:
                categories['category_2nd'] = url_parts[0].replace('-', ' ').title() if len(url_parts) > 0 else None
                categories['category_3rd'] = url_parts[1].replace('-', ' ').title() if len(url_parts) > 1 else None
        
        return categories
    
    def _extract_sku(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract SKU from product page or URL"""
        # Try to find SKU in page
        sku_elem = (soup.select_one('[class*="sku"]') or
                   soup.select_one('[data-testid="sku"]') or
                   soup.select_one('[itemprop="sku"]'))
        if sku_elem:
            sku_text = sku_elem.get_text(strip=True)
            # Extract numbers
            sku_match = re.search(r'(\d+)', sku_text)
            if sku_match:
                return sku_match.group(1)
        
        # Try to extract from URL (FoodBasics URLs often end with /p/SKU)
        if '/p/' in url:
            sku_match = re.search(r'/p/(\d+)', url)
            if sku_match:
                return sku_match.group(1)
        
        return None



