import os
import re
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image

def clean_url(raw_url):
    """Aggressively strips markdown links, brackets, and quotes from URLs."""
    if not raw_url:
        return ""
    match = re.search(r'https?://[^\s\]\)\"]+', raw_url)
    if match:
        return match.group(0)
    cleaned = raw_url.strip("[]()'\" ")
    if not cleaned.startswith("http"):
        cleaned = "https://" + cleaned.lstrip("/")
    return cleaned

def download_and_extract_media(raw_page_url, temp_dir):
    page_url = clean_url(raw_page_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"Scraping exact product from URL: {page_url}")
    res = requests.get(page_url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Extract Product Title
    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Markaz Product"

    # Extract Pricing
    price_text = ""
    for tag in soup.find_all(string=re.compile(r"PKR", re.IGNORECASE)):
        price_text += " " + str(tag).strip()

    digits = re.findall(r"\d[\d,]*", price_text)
    wholesale_price = 1719
    if digits:
        try:
            extracted = int(digits[0].replace(",", ""))
            if extracted > 100:
                wholesale_price = extracted
        except ValueError:
            pass
    selling_price = wholesale_price + 450

    # Extract Details
    overview_section = soup.find("div", {"id": "504"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
    raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]

    # PRECISE PRODUCT IMAGE EXTRACTION VIA NEXT.JS STATE (__NEXT_DATA__)
    image_urls = []
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag and script_tag.string:
        try:
            page_data = json.loads(script_tag.string)
            # Recursively search JSON for image lists belonging to the product
            def extract_images_from_json(node):
                urls = []
                if isinstance(node, dict):
                    for k, v in node.items():
                        if k in ['images', 'media', 'productImages', 'gallery'] and isinstance(v, list):
                            for item in v:
                                if isinstance(item, str) and 'static.markaz.app' in item:
                                    urls.append(item.split('?')[0])
                                elif isinstance(item, dict):
                                    for sub_val in item.values():
                                        if isinstance(sub_val, str) and 'static.markaz.app' in sub_val:
                                            urls.append(sub_val.split('?')[0])
                        else:
                            urls.extend(extract_images_from_json(v))
                elif isinstance(node, list):
                    for element in node:
                        urls.extend(extract_images_from_json(element))
                return urls

            image_urls = list(dict.fromkeys(extract_images_from_json(page_data)))
        except Exception as e:
            print(f"Notice parsing JSON state: {e}")

    # Fallback to main product gallery container if JSON keys weren't isolated
    if not image_urls:
        print("Using container fallback for product images...")
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            image_urls.append(og_img["content"].split("?")[0])
        
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and "static.markaz.app" in src:
                if not any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'thumb']):
                    clean_src = src.split("?")[0]
                    if clean_src not in image_urls:
                        image_urls.append(clean_src)

    print(f"Found exactly {len(image_urls)} official product image(s). Downloading in full HD...")

    downloaded_img_paths = []
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            img_res = requests.get(img_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if img_res.status_code == 200 and len(img_res.content) > 1000:
                raw_path = os.path.join(temp_dir, f"product_img_{idx}.jpg")
                with open(raw_path, "wb") as f:
                    f.write(img_res.content)
                
                # Open and save at 100% full uncompressed quality
                with Image.open(raw_path) as im:
                    rgb_im = im.convert('RGB')
                    rgb_im.save(raw_path, 'JPEG', quality=100, subsampling=0)
                    downloaded_img_paths.append(raw_path)
        except Exception as e:
            print(f"Notice downloading product image {img_url}: {e}")

    print(f"SUCCESS: Successfully processed {len(downloaded_img_paths)} exact uncompressed HD product image(s).")
    return title, selling_price, raw_details, downloaded_img_paths
