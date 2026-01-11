"""
Base scraper class with common functionality
Uses undetected-chromedriver to avoid bot detection
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import requests

from config import USER_AGENT, REQUEST_DELAY_SECONDS, HEADLESS_BROWSER, BROWSER_TIMEOUT
from models.product import Product

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, base_url: str, source_name: str):
        self.base_url = base_url
        self.source_name = source_name
        self.driver: Optional[uc.Chrome] = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
    
    def _get_driver(self) -> uc.Chrome:
        """Initialize and return an undetected Chrome WebDriver to avoid bot detection"""
        if self.driver is None:
            options = uc.ChromeOptions()
            
            if HEADLESS_BROWSER:
                options.add_argument('--headless=new')
            else:
                # Non-headless mode is better for avoiding detection
                options.add_argument('--start-maximized')
            
            # Additional options for better stealth
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={USER_AGENT}')
            
            # Use undetected-chromedriver (automatically handles bot detection)
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                use_subprocess=True
            )
            self.driver.set_page_load_timeout(BROWSER_TIMEOUT)
            
            # Set window size
            if not HEADLESS_BROWSER:
                self.driver.set_window_size(1920, 1080)
            
            logger.info(f"Initialized undetected Chrome driver for {self.source_name}")
        return self.driver
    
    def _close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            try:
            self.driver.quit()
            except:
                pass
            self.driver = None
    
    def _recreate_driver(self):
        """Recreate the Chrome driver (useful when blocked)"""
        self._close_driver()
        return self._get_driver()
    
    def _get_page(self, url: str, use_selenium: bool = False) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object"""
        try:
            if use_selenium:
                driver = self._get_driver()
                driver.get(url)
                # Wait longer for page to load and avoid bot detection
                time.sleep(REQUEST_DELAY_SECONDS + 2)
                
                # Scroll a bit to simulate human behavior
                driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                html = driver.page_source
                current_url = driver.current_url
                
                # Only skip if URL actually contains "blocked" - this means we're truly blocked
                # Don't skip for warnings in page content, continue scraping
                is_actually_blocked = "blocked" in current_url.lower()
                
                if is_actually_blocked:
                    logger.warning(f"Actually blocked - URL contains 'blocked': {current_url}")
                    logger.warning("Skipping this product and continuing to next...")
                    return None
                
                # Log warnings but continue scraping
                has_warning = (
                    "robot" in html.lower() or 
                    "captcha" in html.lower() or 
                    "not robots" in html.lower() or
                    "verify your identity" in html.lower() or
                    "press & hold" in html.lower() or
                    "press and hold" in html.lower() or
                    "we like real shoppers" in html.lower()
                )
                
                if has_warning:
                    logger.warning(f"Bot detection warning on {url} - but continuing to scrape...")
                    # Continue anyway - try to extract data
            else:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                html = response.text
            
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _delay(self):
        """Add delay between requests"""
        time.sleep(REQUEST_DELAY_SECONDS)
    
    @abstractmethod
    def search_products(self, query: str, max_results: int = 50) -> List[Product]:
        """Search for products by query string"""
        pass
    
    @abstractmethod
    def get_product_details(self, product_url: str) -> Optional[Product]:
        """Get detailed information about a specific product"""
        pass
    
    def cleanup(self):
        """Clean up resources"""
        self._close_driver()
        self.session.close()

