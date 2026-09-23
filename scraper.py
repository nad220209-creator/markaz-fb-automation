import os
import re
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image
import google.generativeai as genai

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

def find_in_stock_alternative(soup, current_url):
    """Uses Gemini AI to pick the best in-stock alternative from Markaz 'Similar products' if item is out of stock."""
    text_content = soup.get_text()
    if "out of stock" not in text_content.lower():
        return current_url # Product is live and in stock!

    logger.warning("Product is OUT OF STOCK. Scanning for in-stock similar alternatives...")
    alternatives = []
    
    # Extract similar products listed on the page
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/product/" in href:
            full_url = "https://www.markaz.app" + href if href.startswith("/") else href
            title = a.get_text().strip()
            if len(title) > 5 and full_url != current_url:
                alternatives.append({"title": title, "url": full_url})

    if not alternatives:
        return current_url

    # Use Gemini AI to pick the highest demand alternative
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            genai.configure(api_key=str(api_key).strip("[]'\" "))
            candidate_titles = [f"{i}. {alt['title']}" for i, alt in enumerate(alternatives[:15])]
            prompt = f"""
            The primary product is out of stock. From this list of in-stock alternative products on Markaz, pick the ONE that is currently in highest demand for trendy youth in Pakistan:
            {candidate_titles}
            Return ONLY the integer index of your choice, nothing else.
            """
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            match_idx = int(re.search(r'\d+', response.text).group())
            if 0 <= match_idx < len(alternatives):
                selected = alternatives[match_idx]
                logger.info(f"Auto-switched to in-stock alternative: '{selected['title']}' | URL: {selected['url']}")
                return selected['url']
        except Exception as e:
            logger.error(f"AI alternative selection failed: {e}")

    return alternatives[0]['url'] if alternatives else current_url

def download_and_extract_media(raw_page_url, temp_dir):
    page_url = clean_url(raw_page_url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    logger.info(f"Fetching URL: {page_url}")
    res = requests.get(page_url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Check if out of stock and auto-switch to a winning in-stock alternative
    page_url = find_in_stock_alternative(soup, page_url)
    if page_url != clean_url(raw_page_url):
        res = requests.get(page_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Markaz Product"

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
