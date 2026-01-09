"""Test product detail extraction from a specific product URL"""
from scrapers.walmart_scraper import WalmartScraper
import json

# Test with the exact product from your screenshot
product_url = "https://www.walmart.ca/en/ip/Natrel-Fine-filtered-2-Milk/10220384"

print("=" * 70)
print("Testing Product Detail Extraction")
print("=" * 70)
print(f"\nProduct URL: {product_url}\n")

scraper = WalmartScraper()
try:
    print("Fetching product details...")
    product = scraper.get_product_details(product_url)
    
    if product:
        print("\n" + "=" * 70)
        print("EXTRACTED PRODUCT DETAILS:")
        print("=" * 70)
        print(f"Name: {product.name}")
        print(f"Price: ${product.price}" if product.price else "Price: Not found")
        print(f"Brand: {product.brand}" if product.brand else "Brand: Not found")
        print(f"Size: {product.size}" if product.size else "Size: Not found")
        print(f"Image URL: {product.image_url[:80]}..." if product.image_url else "Image: Not found")
        print(f"Description: {product.description[:100]}..." if product.description else "Description: Not found")
        print(f"In Stock: {product.in_stock}")
        print("=" * 70)
        
        # Save to JSON
        product_dict = product.to_dict()
        with open('test_product_details.json', 'w', encoding='utf-8') as f:
            json.dump(product_dict, f, indent=2, default=str)
        print("\nSaved to: test_product_details.json")
    else:
        print("\n❌ Failed to extract product details")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    scraper.cleanup()



