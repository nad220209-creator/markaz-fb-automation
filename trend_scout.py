import os
from datetime import datetime

# Explicit, dedicated product URLs for each category to prevent any overlapping
CATEGORY_PRODUCT_MAP = {
    "Baby Suit": "https://www.markaz.app/shop/product/baby-suit-set-soft-blended-3-pcs-newborn/96520",
    "Women Handbag": "https://www.markaz.app/shop/product/womens-black-pu-leather-3pcs-handbag-set/715800",
    "Girl Skincare Beauty Kit Serum": "https://www.markaz.app/shop/product/vitamin-c-face-serum-for-glowing-skin-pakistan/715900",
    "Shoes": "https://www.markaz.app/shop/product/stylish-casual-sneakers-shoes-for-women/716000",
    "Women Unstitched Lawn Suit": "https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844"
}

TARGET_CATEGORIES = list(CATEGORY_PRODUCT_MAP.keys())

def get_single_trending_product():
    """Returns one rotational category and product URL for scheduled runs."""
    current_hour = datetime.utcnow().hour
    hour_to_index = {3: 0, 7: 1, 11: 2, 15: 3, 19: 4}
    idx = hour_to_index.get(current_hour, datetime.utcnow().day % len(TARGET_CATEGORIES))
    category = TARGET_CATEGORIES[idx]
    url = CATEGORY_PRODUCT_MAP[category]
    print(f"Rotational Scheduled Mode -> Category: '{category}' | URL: {url}")
    return category, url

def get_all_trending_products():
    """Returns all 5 categories and their unique product URLs for manual runs."""
    print("Manual Trigger Mode -> Processing all 5 unique categories...")
    return CATEGORY_PRODUCT_MAP
