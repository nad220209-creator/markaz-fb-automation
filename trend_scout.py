import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

TARGET_CATEGORIES = [
    "Baby Suit",
    "Women Handbag",
    "Girl Skincare Beauty Kit Serum",
    "Shoes",
    "Women Unstitched Lawn Suit"
]

def fetch_url_for_category(category):
    print(f"Scouting Markaz catalog for category: '{category}'...")
    search_url = f"https://www.markaz.app/shop?search={requests.utils.quote(category)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    return "https://www.markaz.app" + href if href.startswith("/") else href
    except Exception as e:
        print(f"Notice searching category '{category}': {e}")
        
    # Fallback default product URL if catalog search fails
    return "https://www.markaz.app/shop/product/men-s-unstitched-wash-and-wear-plain-suit/743822"

def get_single_trending_product():
    """Returns one rotational category and product URL for scheduled runs."""
    current_hour = datetime.utcnow().hour
    hour_to_index = {3: 0, 7: 1, 11: 2, 15: 3, 19: 4}
    idx = hour_to_index.get(current_hour, datetime.utcnow().day % len(TARGET_CATEGORIES))
    category = TARGET_CATEGORIES[idx]
    print(f"Rotational Scheduled Mode -> Selected category: '{category}'")
    return category, fetch_url_for_category(category)

def get_all_trending_products():
    """Returns all 5 categories and their product URLs for manual runs."""
    print("Manual Trigger Mode -> Scouting all 5 categories simultaneously...")
    category_urls = {}
    for category in TARGET_CATEGORIES:
        url = fetch_url_for_category(category)
        category_urls[category] = url
        print(f"-> Discovered URL for {category}: {url}")
    return category_urls
