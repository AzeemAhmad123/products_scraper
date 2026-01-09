"""
Product data model for scraped grocery items
"""
from datetime import datetime
from typing import Optional, Dict, Any


class Product:
    """Represents a grocery product from any source with full details"""
    
    def __init__(
        self,
        name: str,
        price: Optional[float] = None,
        original_price: Optional[float] = None,
        sale_price: Optional[float] = None,
        is_on_sale: bool = False,
        image_url: Optional[str] = None,
        product_url: Optional[str] = None,
        description: Optional[str] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        unit: Optional[str] = None,
        category: Optional[str] = None,
        # Category hierarchy (4 levels as per client requirements)
        master_category: Optional[str] = None,
        main_category: Optional[str] = None,
        category_2nd: Optional[str] = None,
        category_3rd: Optional[str] = None,
        # Additional fields
        sku: Optional[str] = None,
        in_stock: bool = True,
        source: str = 'unknown',
        scraped_at: Optional[datetime] = None
    ):
        self.name = name
        self.price = price  # Current price (sale_price if on sale, otherwise regular price)
        self.original_price = original_price  # Regular price before sale
        self.sale_price = sale_price  # Price when on sale
        self.is_on_sale = is_on_sale
        self.image_url = image_url
        self.product_url = product_url
        self.description = description
        self.brand = brand
        self.size = size
        self.unit = unit
        self.category = category  # Keep for backward compatibility
        # Category hierarchy
        self.master_category = master_category
        self.main_category = main_category
        self.category_2nd = category_2nd
        self.category_3rd = category_3rd
        # Additional fields
        self.sku = sku
        self.in_stock = in_stock
        self.source = source
        self.scraped_at = scraped_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary for MongoDB storage"""
        return {
            'name': self.name,
            'price': self.price,  # Current price (price_per_unit in spreadsheet)
            'original_price': self.original_price,
            'sale_price': self.sale_price,
            'is_on_sale': self.is_on_sale,
            'image_url': self.image_url,
            'product_url': self.product_url,
            'description': self.description,
            'brand': self.brand,
            'size': self.size,
            'unit': self.unit,
            'category': self.category,  # Backward compatibility
            # Category hierarchy (matching spreadsheet structure)
            'master_category': self.master_category,
            'main_category': self.main_category,
            'category_2nd': self.category_2nd,
            'category_3rd': self.category_3rd,
            # Additional fields
            'sku': self.sku,
            'in_stock': self.in_stock,
            'source': self.source,
            'scraped_at': self.scraped_at,
            'created_at': datetime.utcnow()
        }
    
    def __repr__(self):
        return f"Product(name='{self.name}', price={self.price}, source='{self.source}')"

