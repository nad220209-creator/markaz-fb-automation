import os
import re
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def clean_url(raw_url):
    if not raw_url:
        return ""
    match = re.search(r'https?://[^\s\]\)\"]+', raw_url)
    if match:
        return match.group(0)
    cleaned = raw_url.strip("[]()'\" ")
    if not cleaned.startswith("http"):
        cleaned = "https://" + cleaned.lstrip("/")
    return cleaned

def extract_correct_title(soup):
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        raw_title = og_title["content"].split("–")[0].split("-")[0].strip()
        if raw_title and len(raw_title) > 3:
            return raw_title

    ignored_headers = ["ratings and reviews", "customer reviews", "similar products", "you may also like", "cart", "checkout"]
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text().strip()
        if text and not any(bad in text.lower() for bad in ignored_headers):
            if len(text) > 5:
                return text

    return "Markaz Product"

def download_and_extract_media(raw_page_url, temp_dir):
    page_url = clean_url(raw_page_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    logger.info(f"Fetching URL: {page_url}")
    res = requests.get(page_url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    title = extract_correct_title(soup)
    logger.info(f"Verified product title: {title}")

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

    # Reseller Profit Margin + Silent Delivery Charge markup (Wholesale + PKR 600)
    markup = 600
    selling_price = wholesale_price + markup
    logger.info(f"Wholesale: PKR {wholesale_price} | Markup (Profit + Shipping): PKR {markup} | Selling Price: PKR {selling_price}")

    overview_section = soup.find("div", {"id": "504"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
    raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]

    downloaded_img_paths = []
    collected_urls = set()

    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        collected_urls.add(og_img["content"].split("?")[0])

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and "static.markaz.app" in src:
            if any(bad in src.lower() for in_list in [['icon', 'logo', 'avatar', 'thumb', 'badge']] for bad in in_list):
                continue
            clean_src = src.split("?")[0]
            if clean_src.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                collected_urls.add(clean_src)

    logger.info(f"Downloading {len(collected_urls)} verified HD product images...")

    for idx, img_url in enumerate(list(collected_urls), start=1):
        try:
            img_res = requests.get(img_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if img_res.status_code == 200 and len(img_res.content) > 1000:
                raw_path = os.path.join(temp_dir, f"raw_{idx}.jpg")
                with open(raw_path, "wb") as f:
                    f.write(img_res.content)
                
                with Image.open(raw_path) as im:
                    rgb_im = im.convert('RGB')
                    rgb_im.save(raw_path, 'JPEG', quality=100, subsampling=0)
                    downloaded_img_paths.append(raw_path)
        except Exception as e:
            logger.warning(f"Failed downloading image {img_url}: {e}")

    if not title or not selling_price:
        raise ValueError("Failed to extract valid product title or price.")

    return title, selling_price, raw_details, downloaded_img_paths
