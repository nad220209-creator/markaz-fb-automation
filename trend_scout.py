import os
import requests
from bs4 import BeautifulSoup

# Define your 5 target categories for the Punjab elite under-35 demographic
TARGET_CATEGORIES = [
    "Baby Suit",
    "Women Handbag",
    "Girl Skincare Beauty Kit Serum",
    "Shoes",
    "Women Unstitched Lawn Suit"
]

def get_products_for_all_categories():
    category_urls = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    for category in TARGET_CATEGORIES:
        print(f"Scouting Markaz catalog for trending items in category: '{category}'...")
        search_url = f"https://www.markaz.app/shop?search={requests.utils.quote(category)}"
        
        product_url = None
        try:
            res = requests.get(search_url, headers=headers, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/product/" in href:
                        product_url = "https://www.markaz.app" + href if href.startswith("/") else href
                        break
        except Exception as e:
            print(f"Notice searching category '{category}': {e}")
            
        if product_url:
            category_urls[category] = product_url
            print(f"-> Discovered URL for {category}: {product_url}")
        else:
            print(f"-> Warning: Could not find live URL for {category}, skipping.")
            
    return category_urls
