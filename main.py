import os
import tempfile
import json
import re
import datetime
import requests
from bs4 import BeautifulSoup
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

HISTORY_FILE = "processed_history.json"

CATEGORIES = [
    {
        "name": "Women Handbag",
        "query": "Womens Handbag Shoulder Bag",
        "fallback_url": "https://www.markaz.app/shop/product/womens-stylish-handbag-shoulder-bag/715000",
        "required_keywords": ["bag", "handbag", "purse", "shoulder", "satchel", "tote"],
        "positive_keywords": ["women", "womens", "ladies", "girl", "female"],
        "forbidden_keywords": ["men", "mens", "boy", "gents", "male"]
    },
    {
        "name": "Baby Suit",
        "query": "Newborn Baby Suit Cotton Set",
        "fallback_url": "https://www.markaz.app/shop/product/baby-suit-set-soft-blended-3-pcs-newborn/96520",
        "required_keywords": ["baby", "newborn", "infant", "kids", "romper", "toddler"],
        "positive_keywords": ["suit", "romper", "set", "dress", "kurta", "bodysuit", "frock", "cotton"],
        "forbidden_keywords": ["tablet", "lcd", "writing", "toy", "educational", "game", "men", "mens", "women", "womens", "fabric", "boski", "gents", "lawn"]
    },
    {
        "name": "Girl Skincare Beauty Kit Serum",
        "query": "Vitamin C Face Serum Skincare Kit",
        "fallback_url": "https://www.markaz.app/shop/product/vitamin-c-face-serum-for-glowing-skin-pakistan/715900",
        "required_keywords": ["serum", "face", "skin", "cream", "kit", "vitamin", "glow", "beauty", "cleanser", "lotion"],
        "positive_keywords": [],
        "forbidden_keywords": ["shoe", "shoes", "bag", "handbag", "suit", "shirt", "pant", "watch", "toy"]
    },
    {
        "name": "Mens Shoes",
        "query": "Mens Casual Sneakers Shoes",
        "fallback_url": "https://www.markaz.app/shop/product/mens-blue-slip-on-walking-sneakers-size-40-45/692757",
        "required_keywords": ["shoe", "shoes", "sneaker", "sneakers", "slip-on", "boot", "boots", "footwear"],
        "positive_keywords": ["men", "mens", "boy", "boys", "gents"],
        "forbidden_keywords": ["women", "womens", "ladies", "girl", "girls"]
    },
    {
        "name": "Womens Shoes",
        "query": "Womens Casual Sneakers Khussa",
        "fallback_url": "https://www.markaz.app/shop/product/womens-stylish-casual-sneakers-pakistan/715700",
        "required_keywords": ["shoe", "shoes", "sneaker", "sneakers", "khussa", "sandal", "heel", "pumps", "footwear"],
        "positive_keywords": ["women", "womens", "ladies", "girl", "girls", "female"],
        "forbidden_keywords": ["men", "mens", "boy", "boys", "gents"]
    },
    {
        "name": "Women Unstitched Lawn Suit",
        "query": "Women Unstitched Lawn Suit Printed",
        "fallback_url": "https://www.markaz.app/shop/product/womens-printed-unstitched-lawn-suit-pakistan/715500",
        "required_keywords": ["lawn", "suit", "unstitched", "printed", "3-piece", "2-piece", "kurti", "cotton"],
        "positive_keywords": [],
        "forbidden_keywords": ["shoe", "shoes", "bag", "handbag", "serum", "watch", "toy", "men", "mens"]
    }
]

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history_list):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_list, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def process_category(cat):
    print(f"\n--- PROCESSING CATEGORY: {cat['name']} ---")
    encoded_query = requests.utils.quote(cat["query"])
    search_url = f"https://www.markaz.app/shop?search={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    candidates = []
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    full_url = ("https://www.markaz.app" + href if href.startswith("/") else href).split("?")[0]
                    title = a.get_text().strip()
                    title_lower = title.lower()
                    
                    has_required = any(kw in title_lower for kw in cat["required_keywords"])
                    has_positive = True if not cat["positive_keywords"] else any(kw in title_lower for kw in cat["positive_keywords"])
                    has_forbidden = any(kw in title_lower for kw in cat["forbidden_keywords"])
                    
                    if len(title) > 3 and has_required and has_positive and not has_forbidden:
                        if {"title": title, "url": full_url} not in candidates:
                            candidates.append({"title": title, "url": full_url})
    except Exception as e:
        print(f"Search error for {cat['name']}: {e}")

    processed_urls = load_history()
    fresh_candidates = [c for c in candidates if c["url"] not in processed_urls]
    
    product_url = ""
    if not fresh_candidates:
        if candidates:
            fresh_candidates = candidates
        else:
            print(f"No strict candidates for {cat['name']}. Using verified fallback URL.")
            product_url = cat["fallback_url"]

    if not product_url:
        selected = fresh_candidates[0]
        product_url = selected["url"]
        processed_urls.append(product_url)
        save_history(processed_urls)

    print(f"Selected Product URL: {product_url}")
    
    temp_dir = tempfile.mkdtemp()
    title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
    copy_dict = generate_copy(title, selling_price, raw_details)
    clean_file_title = sanitize_filename(f"{cat['name']}_{title}")
    local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
    
    build_pdf(f"[{cat['name'].upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path, product_url=product_url)
    upload_pdf(local_pdf_path, clean_file_title)
    print(f"SUCCESS: {cat['name']} PDF generated and uploaded!")

def main():
    run_all = os.environ.get("RUN_ALL", "false").lower() == "true"
    
    if run_all:
        print("--- MANUAL RUN: Processing ALL Categories ---")
        for cat in CATEGORIES:
            process_category(cat)
    else:
        print("--- AUTOMATED SCHEDULE RUN: Processing ONE Category ---")
        current_hour = datetime.datetime.utcnow().hour
        cat_index = current_hour % len(CATEGORIES)
        selected_cat = CATEGORIES[cat_index]
        process_category(selected_cat)

if __name__ == "__main__":
    main()
