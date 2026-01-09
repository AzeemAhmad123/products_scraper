"""
Batch scraper runner - automatically processes in batches and restarts
"""
import subprocess
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_batch_scraper():
    """Run the batch scraper continuously"""
    logger.info("=" * 70)
    logger.info("BATCH SCRAPER RUNNER")
    logger.info("=" * 70)
    logger.info("This will run the scraper in batches of 100 products")
    logger.info("Each batch will be saved automatically")
    logger.info("The script will continue until all products are processed")
    logger.info("=" * 70)
    
    # Run the scraper
    # It will automatically handle batching and saving
    try:
        result = subprocess.run(
            [sys.executable, 'scrape_walmart_from_spreadsheet.py', 
             '--batch-size', '100', 
             '--start-from', '3'],
            check=False
        )
        
        if result.returncode == 0:
            logger.info("\nScraping completed successfully!")
        else:
            logger.warning(f"\nScraping ended with code: {result.returncode}")
            logger.info("Check the logs for details")
            
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")


if __name__ == '__main__':
    run_batch_scraper()

