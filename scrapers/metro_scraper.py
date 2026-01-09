"""
Metro.ca scraper
"""
import re
import logging
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.product import Product
from config import METRO_BASE_URL

logger = logging.getLogger(__name__)


class MetroScraper(BaseScraper):
    """Scraper for Metro.ca"""
    
    def __init__(self):
        super().__init__(METRO_BASE_URL, 'metro')
    
    def search_products(self, query: str, max_results: int = 50) -> List[Product]:
        """Search for products on Metro.ca"""
        products = []
        try:
            # Metro search URL - may need to adjust based on actual site structure
            search_url = f"{self.base_url}/en/online/search?q={quote(query)}"
            logger.info(f"Searching Metro for: {query}")
            
            # Metro likely uses JavaScript, so use Selenium
            soup = self._get_page(search_url, use_selenium=True)
            if not soup:
                return products
            
            # Wait a bit for dynamic content to load
            import time
            time.sleep(3)
            
            # Refresh soup after dynamic content loads
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find product containers - Metro uses various selectors
            product_selectors = [
                '[data-testid="product-card"]',
                '[class*="product-card"]',
                '[class*="ProductCard"]',
                'div[class*="product-item"]',
                'article[class*="product"]'
            ]
            
            product_elements = []
            for selector in product_selectors:
                product_elements = soup.select(selector)
                if product_elements:
                    logger.info(f"Found {len(product_elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                # Fallback: look for any product-like containers
                product_elements = soup.select('div[class*="item"], a[href*="/product"]')
                logger.info(f"Fallback: Found {len(product_elements)} potential product elements")
            
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
            logger.error(f"Error searching Metro: {str(e)}")
        
        return products
    
    def _parse_product_element(self, element, soup: BeautifulSoup) -> Optional[Product]:
        """Parse a product element from search results"""
        try:
            # Extract product URL
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
            name_elem = element.select_one('[data-testid="product-name"], [class*="name"], [class*="title"], h2, h3, h4')
            if not name_elem:
                name_elem = link
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            if not name or name == 'Unknown Product':
                return None
            
            # Extract price
            price_elem = element.select_one('[data-testid="price"], [class*="price"], [class*="Price"]')
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Extract image
            img_elem = element.select_one('img[src], img[data-src], img[data-lazy-src]')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract brand if available
            brand_elem = element.select_one('[class*="brand"], [data-testid="brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            return Product(
                name=name,
                price=price,
                image_url=image_url,
                product_url=product_url,
                brand=brand,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error parsing product element: {str(e)}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract number
        price_text = re.sub(r'[^\d.,]', '', price_text)
        price_text = price_text.replace(',', '')
        
        try:
            return float(price_text)
        except ValueError:
            return None
    
    def get_product_details(self, product_url: str) -> Optional[Product]:
        """Get detailed product information from product page"""
        try:
            soup = self._get_page(product_url, use_selenium=True)
            if not soup:
                return None
            
            # Wait for dynamic content
            import time
            time.sleep(2)
            
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract product name
            name_elem = soup.select_one('h1[data-testid="product-name"], h1[class*="name"], h1[class*="title"], h1')
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            # Extract price
            price_elem = soup.select_one('[data-testid="price"], [class*="price"], [class*="Price"]')
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Extract original price if on sale
            original_price_elem = soup.select_one('[class*="original-price"], [class*="was-price"], [class*="regular-price"]')
            original_price = self._extract_price(original_price_elem.get_text() if original_price_elem else '')
            
            # Extract image
            img_elem = soup.select_one('img[data-testid="product-image"], img[class*="product-image"], img[class*="main-image"]')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract description
            desc_elem = soup.select_one('[data-testid="product-description"], [class*="description"]')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract brand
            brand_elem = soup.select_one('[data-testid="brand"], [class*="brand"]')
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            # Extract size/unit
            size_elem = soup.select_one('[class*="size"], [class*="unit"], [class*="weight"]')
            size = size_elem.get_text(strip=True) if size_elem else None
            
            # Check stock status
            stock_elem = soup.select_one('[class*="out-of-stock"], [class*="unavailable"], [class*="not-available"]')
            in_stock = stock_elem is None
            
            return Product(
                name=name,
                price=price,
                original_price=original_price,
                image_url=image_url,
                product_url=product_url,
                description=description,
                brand=brand,
                size=size,
                in_stock=in_stock,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error getting product details from {product_url}: {str(e)}")
            return None

