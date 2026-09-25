import os
import requests
from PIL import Image
import numpy as np

def scrape_products(keyword, max_items=3):
    """
    Returns product items for the given keyword. 
    Using sample high-demand data for testing your Google Drive & AI pipeline.
    """
    print(f"🔍 Scraping trending products for category: {keyword}")
    
    # Create sample local placeholder images to test the full upload pipeline
    os.makedirs("/tmp/sample_imgs", exist_ok=True)
    sample_img_path = "/tmp/sample_imgs/sample_product.jpg"
    
    # Generate a simple test image if it doesn't exist
    if not os.path.exists(sample_img_path):
        img = Image.new('RGB', (800, 800), color=(73, 109, 137))
        img.save(sample_img_path)

    # Targeted sample data matching your high-demand categories
    mock_catalog = {
        "shoes": [
            {
                "id": "shoe_001",
                "title": "Men's Stylish Casual Walking Sneakers Shoes",
                "price": "2199",
                "description": "Comfortable sole, premium quality mesh material, perfect for daily wear.",
                "image_paths": [sample_img_path]
            }
        ],
        "bag": [
            {
                "id": "bag_001",
                "title": "Women Luxury PU Leather Crossbody Shoulder Bag",
                "price": "1850",
                "description": "Trendy design with multiple spacious compartments and durable gold chain strap.",
                "image_paths": [sample_img_path]
            }
        ],
        "seasonal": [
            {
                "id": "seasonal_001",
                "title": "Winter Stitched Dhanak 2-Piece Suit for Women",
                "price": "2499",
                "description": "Warm winter fabric, elegant embroidery, ready-to-wear stitched collection.",
                "image_paths": [sample_img_path]
            }
        ]
    }

    # Match keyword to mock catalog category
    selected_products = []
    kw_lower = keyword.lower()
    if "shoe" in kw_lower:
        selected_products = mock_catalog["shoes"]
    elif "bag" in kw_lower:
        selected_products = mock_catalog["bag"]
    else:
        selected_products = mock_catalog["seasonal"]

    return selected_products[:max_items]
