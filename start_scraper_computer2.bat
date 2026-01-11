@echo off
echo ========================================
echo COMPUTER 2 - WALMART SCRAPER
echo ========================================
echo.
echo Starting scraper for Computer 2...
echo Output file: walmart_scraped_products_computer2.json
echo.
python scrape_walmart_parallel.py --spreadsheet "WebsiteScrapper 2.ods" --row-numbers-file "unique_unscraped_rows_computer2.txt" --workers 2 --flush-size 5 --output-file "walmart_scraped_products_computer2.json"
pause

