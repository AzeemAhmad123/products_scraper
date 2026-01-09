"""
Product name normalization and matching utilities
"""
import re
from typing import Optional, Tuple


def normalize_product_name(name: str) -> str:
    """
    Normalize product name for matching across stores
    Removes extra spaces, converts to lowercase, removes special chars
    """
    if not name:
        return ""
    
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove common prefixes/suffixes that stores might add
    normalized = re.sub(r'\s*(\(.*?\)|\[.*?\])', '', normalized)  # Remove brackets
    normalized = re.sub(r'\s*-\s*', ' ', normalized)  # Normalize dashes
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    # Remove special characters but keep alphanumeric and spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    return normalized.strip()


def extract_brand_and_product(name: str) -> Tuple[Optional[str], str]:
    """
    Extract brand name and product name from full product name
    Returns: (brand, product_name)
    """
    if not name:
        return None, ""
    
    # Common brand patterns
    brand_patterns = [
        r'^(nestle|nestlé)\s+',
        r'^(kellogg\'?s?)\s+',
        r'^(kraft)\s+',
        r'^(coca.?cola|pepsi)\s+',
        r'^(campbell\'?s?)\s+',
        r'^(heinz)\s+',
        r'^(unilever)\s+',
        r'^(danone|dannon)\s+',
        r'^(general.?mills)\s+',
        r'^(conagra)\s+',
    ]
    
    name_lower = name.lower()
    for pattern in brand_patterns:
        match = re.match(pattern, name_lower, re.IGNORECASE)
        if match:
            brand = match.group(1).title()
            product = name[match.end():].strip()
            return brand, product
    
    # Try to extract brand from common patterns
    # Format: "Brand Product Name"
    words = name.split()
    if len(words) > 1:
        # First word might be brand if it's capitalized
        if words[0][0].isupper() and len(words[0]) > 2:
            potential_brand = words[0]
            product = ' '.join(words[1:])
            return potential_brand, product
    
    return None, name


def extract_size_and_unit(name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract size and unit from product name
    Returns: (size, unit)
    Examples: "Milk 2L" -> ("2", "L"), "Bread 500g" -> ("500", "g")
    """
    if not name:
        return None, None
    
    # Pattern: number followed by unit (L, ml, g, kg, oz, lb, etc.)
    patterns = [
        (r'(\d+\.?\d*)\s*(ml|milliliter|millilitre)', 'ml'),
        (r'(\d+\.?\d*)\s*(l|liter|litre)', 'L'),
        (r'(\d+\.?\d*)\s*(g|gram|grams)', 'g'),
        (r'(\d+\.?\d*)\s*(kg|kilogram|kilograms)', 'kg'),
        (r'(\d+\.?\d*)\s*(oz|ounce|ounces)', 'oz'),
        (r'(\d+\.?\d*)\s*(lb|pound|pounds)', 'lb'),
        (r'(\d+)\s*(pack|packs|ct|count)', 'pack'),
    ]
    
    name_lower = name.lower()
    for pattern, unit in patterns:
        match = re.search(pattern, name_lower, re.IGNORECASE)
        if match:
            size = match.group(1)
            return size, unit
    
    return None, None


def products_match(product1_name: str, product2_name: str, threshold: float = 0.8) -> bool:
    """
    Check if two product names likely refer to the same product
    Uses normalized names and simple similarity
    """
    norm1 = normalize_product_name(product1_name)
    norm2 = normalize_product_name(product2_name)
    
    if not norm1 or not norm2:
        return False
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Check if one contains the other (for partial matches)
    if norm1 in norm2 or norm2 in norm1:
        # Calculate similarity
        shorter = min(len(norm1), len(norm2))
        longer = max(len(norm1), len(norm2))
        if shorter / longer >= threshold:
            return True
    
    # Word-based matching
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return False
    
    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    similarity = intersection / union if union > 0 else 0
    
    return similarity >= threshold

