import os
import tempfile
import json
import re
import requests
from bs4 import BeautifulSoup
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

CATEGORY_NAME = "Baby Suit"
SEARCH_QUERY = "Newborn Baby Suit Cotton Set"
FALLBACK_URL = "https://www.markaz.app/shop/product/baby-suit-set-soft-blended-3-pcs-newborn/96520"
HISTORY_FILE = "processed_history.json"

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

def get_single_product():
    encoded_query = requests.utils.quote(SEARCH_QUERY)
    search_url = f"https://www.markaz.app/shop?search={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Searching Markaz live for: '{SEARCH_QUERY}'...")
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
                    if len(title) > 3:
                        if {"title": title, "url": full_url} not in candidates:
                            candidates.append({"title": title, "url": full_url})
    except Exception as e:
        print(f"Search error: {e}")

    processed_urls = load_history()
    fresh_candidates = [c for c in candidates if c["url"] not in processed_urls]
    
    if not fresh_candidates:
        if candidates:
            fresh_candidates = candidates
        else:
            print("Search yielded no items. Using verified fallback baby product URL.")
            return FALLBACK_URL

    selected = fresh_candidates[0]
    processed_urls.append(selected["url"])
    save_history(processed_urls)

    print(f"Selected Product -> Title: '{selected['title']}' | URL: {selected['url']}")
    return selected["url"]

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print(f"=== TESTING CATEGORY: {CATEGORY_NAME} ===")
    temp_dir = tempfile.mkdtemp()
    
    try:
        product_url = get_single_product()

        title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
        print(f"Title: {title} | Selling Price: PKR {selling_price} | Images: {len(image_paths)}")

        copy_dict = generate_copy(title, selling_price, raw_details)
        clean_file_title = sanitize_filename(f"{CATEGORY_NAME}_{title}")
        local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
        
        build_pdf(f"[{CATEGORY_NAME.upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path, product_url=product_url)
        upload_pdf(local_pdf_path, clean_file_title)
        print(f"SUCCESS: {CATEGORY_NAME} PDF generated and uploaded with source link!")
        
    except Exception as e:
        print(f"ERROR in baby suit test: {e}")

if __name__ == "__main__":
    main()
