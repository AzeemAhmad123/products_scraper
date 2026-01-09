"""
Store registry - manages all grocery store scrapers
"""
from typing import Dict, Type, Optional
from scrapers.base_scraper import BaseScraper
from scrapers.walmart_scraper import WalmartScraper
from scrapers.metro_scraper import MetroScraper
from scrapers.loblaws_scraper import LoblawsScraper
from scrapers.sobeys_scraper import SobeysScraper
from scrapers.foodbasics_scraper import FoodBasicsScraper

# Store registry mapping - all stores (flexible for adding more)
STORE_SCRAPERS: Dict[str, Type[BaseScraper]] = {
    'walmart': WalmartScraper,
    'metro': MetroScraper,
    'loblaws': LoblawsScraper,
    'sobeys': SobeysScraper,
    'foodbasics': FoodBasicsScraper,  # Added based on client spreadsheet
    # Additional stores will be added step by step as client provides them
    # 'nofrills': NoFrillsScraper,
    # 'realcanadiansuperstore': RealCanadianSuperstoreScraper,
    # 'freshco': FreshCoScraper,
    # 'longos': LongosScraper,
    # 'fortinos': FortinosScraper,
}

def get_scraper(store_name: str) -> Optional[BaseScraper]:
    """Get a scraper instance for a store"""
    scraper_class = STORE_SCRAPERS.get(store_name.lower())
    if scraper_class:
        return scraper_class()
    return None

def get_all_store_names() -> list:
    """Get list of all available store names"""
    return list(STORE_SCRAPERS.keys())

def register_scraper(store_name: str, scraper_class: Type[BaseScraper]):
    """Register a new scraper"""
    STORE_SCRAPERS[store_name.lower()] = scraper_class

