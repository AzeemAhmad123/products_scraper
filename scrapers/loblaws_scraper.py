"""
Loblaws.ca scraper
"""
import re
import logging
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.product import Product
from config import LOBLAWS_BASE_URL

logger = logging.getLogger(__name__)


class LoblawsScraper(BaseScraper):
    """Scraper for Loblaws.ca"""
    
    def __init__(self):
        super().__init__(LOBLAWS_BASE_URL, 'loblaws')
    
    def search_products(self, query: str, max_results: int = 50) -> List[Product]:
        """Search for products on Loblaws.ca"""
        products = []
        try:
            search_url = f"{self.base_url}/search?search-bar={quote(query)}"
            logger.info(f"Searching Loblaws for: {query}")
            
            soup = self._get_page(search_url, use_selenium=True)
            if not soup:
                return products
            
            # Wait for dynamic content
            import time
            time.sleep(3)
            
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Loblaws product selectors
            product_selectors = [
                '[data-testid="product-card"]',
                '[class*="product-card"]',
                '[class*="ProductCard"]',
                'div[class*="product-item"]',
                'article[class*="product"]',
                'a[href*="/products/"]'
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
            logger.error(f"Error searching Loblaws: {str(e)}")
        
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
                         element.select_one('[class*="Price"]') or
                         element.select_one('span[class*="currency"]'))
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Extract image
            img_elem = (element.select_one('img[src]') or
                       element.select_one('img[data-src]') or
                       element.select_one('img[data-lazy-src]'))
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or 
                           img_elem.get('data-src') or 
                           img_elem.get('data-lazy-src'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract brand
            brand_elem = (element.select_one('[class*="brand"]') or
                         element.select_one('[data-testid="brand"]'))
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            if not brand and name:
                words = name.split()
                if words and words[0][0].isupper() and len(words[0]) > 2:
                    brand = words[0]
            
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
        
        price_patterns = [
            r'\$\s*(\d+\.\d{2})',
            r'\$\s*(\d+)',
            r'(\d+\.\d{2})\s*\$',
            r'(\d+\.\d{2})',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text)
            if match:
                try:
                    price = float(match.group(1))
                    if 0.5 <= price <= 1000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def get_product_details(self, product_url: str) -> Optional[Product]:
        """Get detailed product information from product page"""
        try:
            soup = self._get_page(product_url, use_selenium=True)
            if not soup:
                return None
            
            import time
            time.sleep(2)
            
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract details (similar to Walmart scraper)
            name_elem = (soup.select_one('h1[data-testid="product-name"]') or
                        soup.select_one('h1[class*="name"]') or
                        soup.select_one('h1[class*="title"]') or
                        soup.select_one('h1'))
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            price_elem = (soup.select_one('[data-testid="price"]') or
                         soup.select_one('[class*="price"]') or
                         soup.select_one('[itemprop="price"]'))
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            img_elem = (soup.select_one('img[data-testid="product-image"]') or
                       soup.select_one('img[class*="product-image"]') or
                       soup.select_one('img[itemprop="image"]'))
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or img_elem.get('data-src'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            desc_elem = (soup.select_one('[data-testid="product-description"]') or
                        soup.select_one('[class*="description"]') or
                        soup.select_one('[itemprop="description"]'))
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            brand_elem = (soup.select_one('[data-testid="brand"]') or
                         soup.select_one('[class*="brand"]') or
                         soup.select_one('[itemprop="brand"]'))
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            return Product(
                name=name,
                price=price,
                image_url=image_url,
                product_url=product_url,
                description=description,
                brand=brand,
                source=self.source_name
            )
            
        except Exception as e:
            logger.error(f"Error getting product details from {product_url}: {str(e)}")
            return None



