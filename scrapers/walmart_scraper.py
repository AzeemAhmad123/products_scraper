"""
Walmart.ca scraper
"""
import re
import logging
from typing import List, Optional
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from models.product import Product
from config import WALMART_BASE_URL

logger = logging.getLogger(__name__)


class WalmartScraper(BaseScraper):
    """Scraper for Walmart.ca"""
    
    def __init__(self):
        super().__init__(WALMART_BASE_URL, 'walmart')
    
    def search_products(self, query: str, max_results: int = 50) -> List[Product]:
        """Search for products on Walmart.ca"""
        products = []
        try:
            # Walmart search URL
            search_url = f"{self.base_url}/search?q={quote(query)}"
            logger.info(f"Searching Walmart for: {query}")
            
            soup = self._get_page(search_url, use_selenium=True)
            if not soup:
                return products
            
            # Find product containers - Walmart uses various selectors
            # Try multiple selectors as Walmart's structure may vary
            product_selectors = [
                '[data-testid="product-tile"]',
                '[data-automation="product-tile"]',
                'div[class*="product-tile"]',
                'div[class*="ProductTile"]',
                'article[class*="product"]'
            ]
            
            product_elements = []
            for selector in product_selectors:
                product_elements = soup.select(selector)
                if product_elements:
                    logger.info(f"Found {len(product_elements)} products using selector: {selector}")
                    break
            
            if not product_elements:
                # Fallback: look for any links that might be products
                product_elements = soup.select('a[href*="/ip/"]')
                logger.info(f"Fallback: Found {len(product_elements)} potential product links")
            
            for element in product_elements[:max_results]:
                try:
                    product = self._parse_product_element(element, soup)
                    if product:
                        # Always try to get full details from product page for better accuracy
                        # Especially if price seems wrong (too low) or missing
                        should_fetch_details = (
                            not product.price or 
                            product.price < 1.0 or  # Suspiciously low price
                            not product.description or
                            not product.image_url
                        )
                        
                        if should_fetch_details and product.product_url:
                            logger.info(f"Fetching details from product page: {product.name[:50]}")
                            detailed_product = self.get_product_details(product.product_url)
                            if detailed_product:
                                # Update with detailed info (prefer detailed version)
                                if detailed_product.price:
                                    product.price = detailed_product.price
                                if detailed_product.description:
                                    product.description = detailed_product.description
                                if detailed_product.brand:
                                    product.brand = detailed_product.brand
                                if detailed_product.image_url:
                                    product.image_url = detailed_product.image_url
                                if detailed_product.size:
                                    product.size = detailed_product.size
                                self._delay()  # Be respectful
                        
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error parsing product element: {str(e)}")
                    continue
            
            self._delay()
            
        except Exception as e:
            logger.error(f"Error searching Walmart: {str(e)}")
        
        return products
    
    def _parse_product_element(self, element, soup: BeautifulSoup) -> Optional[Product]:
        """Parse a product element from search results"""
        try:
            # Extract product URL
            link = element.find('a', href=True)
            if not link:
                # If element itself is a link
                if element.name == 'a' and element.get('href'):
                    link = element
                else:
                    return None
            
            product_url = link.get('href', '')
            if not product_url.startswith('http'):
                product_url = urljoin(self.base_url, product_url)
            
            # Clean up URL (remove tracking parameters)
            if '?' in product_url and 'rd=' in product_url:
                # Extract the actual product URL from tracking link
                import urllib.parse
                parsed = urllib.parse.urlparse(product_url)
                if 'rd=' in parsed.query:
                    rd_param = urllib.parse.parse_qs(parsed.query).get('rd', [])
                    if rd_param:
                        product_url = urllib.parse.unquote(rd_param[0])
            
            # Extract product name - try multiple selectors
            name_elem = (element.select_one('[data-testid="product-title"]') or 
                        element.select_one('[data-automation="product-title"]') or
                        element.select_one('h2, h3, h4') or
                        element.select_one('[class*="title"]') or
                        element.select_one('[class*="name"]') or
                        element.select_one('span[class*="product-title"]') or
                        link)
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            if not name or name == 'Unknown Product' or len(name) < 3:
                return None
            
            # Extract price - try multiple selectors
            price_elem = (element.select_one('[data-testid="price"]') or
                         element.select_one('[data-automation="price"]') or
                         element.select_one('span[class*="price"]') or
                         element.select_one('div[class*="price"]') or
                         element.select_one('[class*="Price"]') or
                         element.select_one('span[class*="currency"]') or
                         element.select_one('[itemprop="price"]'))
            price = self._extract_price(price_elem.get_text() if price_elem else '')
            
            # Also try to find price in text content (but be more careful)
            if not price:
                element_text = element.get_text()
                # Look for price patterns like $4.47 (with dollar sign and decimal)
                price_match = re.search(r'\$\s*(\d+\.\d{2})', element_text)
                if price_match:
                    try:
                        price = float(price_match.group(1))
                        if not (0.5 <= price <= 1000):
                            price = None
                    except:
                        pass
            
            # Extract image - try multiple selectors
            img_elem = (element.select_one('img[src]') or
                       element.select_one('img[data-src]') or
                       element.select_one('img[data-lazy-src]') or
                       element.select_one('img[data-original]'))
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or 
                           img_elem.get('data-src') or 
                           img_elem.get('data-lazy-src') or
                           img_elem.get('data-original'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract brand - try multiple selectors
            brand_elem = (element.select_one('[class*="brand"]') or
                         element.select_one('[data-testid="brand"]') or
                         element.select_one('[data-automation="brand"]') or
                         element.select_one('span[class*="Brand"]'))
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            # Try to extract brand from product name (first word if capitalized)
            if not brand and name:
                words = name.split()
                if words and words[0][0].isupper() and len(words[0]) > 2:
                    # Common brands
                    potential_brand = words[0]
                    if potential_brand.lower() not in ['the', 'a', 'an', 'this', 'that']:
                        brand = potential_brand
            
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
        
        # Look for price patterns: $4.47, 4.47, $4, etc.
        # But avoid matching single digits or very small numbers (likely from product names)
        price_patterns = [
            r'\$\s*(\d+\.\d{2})',  # $4.47
            r'\$\s*(\d+)',         # $4
            r'(\d+\.\d{2})\s*\$',  # 4.47$
            r'(\d+\.\d{2})',       # 4.47 (standalone)
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, price_text)
            if match:
                try:
                    price = float(match.group(1))
                    # Only accept reasonable prices (between $0.50 and $1000)
                    if 0.5 <= price <= 1000:
                        return price
                except ValueError:
                    continue
        
        # Fallback: try to extract any number with decimal
        price_text_clean = re.sub(r'[^\d.,]', '', price_text)
        if '.' in price_text_clean:
            try:
                price = float(price_text_clean.replace(',', ''))
                if 0.5 <= price <= 1000:
                    return price
            except ValueError:
                pass
        
        return None
    
    def get_product_details(self, product_url: str) -> Optional[Product]:
        """Get detailed product information from product page"""
        try:
            soup = self._get_page(product_url, use_selenium=True)
            if not soup:
                return None
            
            # Wait a bit for dynamic content
            import time
            time.sleep(2)
            
            # Refresh soup after dynamic content loads
            if self.driver:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract product name - try multiple selectors
            name_elem = (soup.select_one('h1[data-testid="product-title"]') or
                        soup.select_one('h1[data-automation="product-title"]') or
                        soup.select_one('h1[class*="product-title"]') or
                        soup.select_one('h1[class*="ProductTitle"]') or
                        soup.select_one('h1'))
            name = name_elem.get_text(strip=True) if name_elem else 'Unknown Product'
            
            # Extract price - Walmart shows price in various formats
            price_elem = (soup.select_one('span[data-automation="product-price"]') or
                         soup.select_one('[data-testid="price"]') or
                         soup.select_one('span[class*="price"]') or
                         soup.select_one('div[class*="price"]') or
                         soup.select_one('[itemprop="price"]') or
                         soup.select_one('span[class*="currency"]'))
            
            price_text = price_elem.get_text(strip=True) if price_elem else ''
            price = self._extract_price(price_text)
            
            # Also search in page text for price pattern
            if not price:
                page_text = soup.get_text()
                # Look for patterns like "$4.47" or "Price: $4.47"
                price_match = re.search(r'(?:price|cost)[\s:]*\$?\s*(\d+\.?\d{0,2})', page_text, re.IGNORECASE)
                if price_match:
                    try:
                        price = float(price_match.group(1))
                    except:
                        pass
            
            # Extract original price if on sale
            original_price_elem = (soup.select_one('[class*="original-price"]') or
                                  soup.select_one('[class*="was-price"]') or
                                  soup.select_one('[class*="strike"]') or
                                  soup.select_one('span[class*="regular-price"]'))
            original_price = self._extract_price(original_price_elem.get_text() if original_price_elem else '')
            
            # Extract image - try multiple selectors
            img_elem = (soup.select_one('img[data-testid="product-image"]') or
                       soup.select_one('img[data-automation="product-image"]') or
                       soup.select_one('img[class*="product-image"]') or
                       soup.select_one('img[class*="ProductImage"]') or
                       soup.select_one('img[itemprop="image"]'))
            image_url = None
            if img_elem:
                image_url = (img_elem.get('src') or 
                           img_elem.get('data-src') or 
                           img_elem.get('data-lazy-src') or
                           img_elem.get('data-original'))
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Extract description - "About this item" section
            desc_elem = (soup.select_one('[data-testid="product-description"]') or
                        soup.select_one('[data-automation="product-description"]') or
                        soup.select_one('div[class*="description"]') or
                        soup.select_one('div[class*="about-this-item"]') or
                        soup.select_one('ul[class*="description"]') or
                        soup.select_one('[itemprop="description"]'))
            description = None
            if desc_elem:
                # Get all list items or paragraphs
                desc_items = desc_elem.select('li, p')
                if desc_items:
                    description = ' '.join([item.get_text(strip=True) for item in desc_items])
                else:
                    description = desc_elem.get_text(strip=True)
            
            # Extract brand - try multiple selectors
            brand_elem = (soup.select_one('[data-testid="brand"]') or
                         soup.select_one('[data-automation="brand"]') or
                         soup.select_one('span[class*="brand"]') or
                         soup.select_one('div[class*="brand"]') or
                         soup.select_one('[itemprop="brand"]'))
            brand = brand_elem.get_text(strip=True) if brand_elem else None
            
            # Extract brand from "At a glance" table if available
            if not brand:
                glance_table = soup.select_one('table, div[class*="at-a-glance"]')
                if glance_table:
                    rows = glance_table.select('tr, div[class*="row"]')
                    for row in rows:
                        text = row.get_text()
                        if 'brand' in text.lower():
                            brand = text.split(':')[-1].strip() if ':' in text else None
                            break
            
            # Extract size/unit from product name or page
            size = None
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(L|ml|g|kg|oz|lb)', name, re.IGNORECASE)
            if size_match:
                size = f"{size_match.group(1)}{size_match.group(2)}"
            
            # Check stock status
            stock_elem = (soup.select_one('[class*="out-of-stock"]') or
                         soup.select_one('[class*="unavailable"]') or
                         soup.select_one('span[class*="sold-out"]'))
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

