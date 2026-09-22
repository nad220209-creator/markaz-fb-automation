import os
import re
import zipfile
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
    print(f"Scraping URL: {page_url}")
    res = requests.get(page_url, headers=headers, timeout=15)
    res.raise_for_status()
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

    zip_url = None
    for elem in soup.find_all(["a", "button", "div", "span"]):
        text = elem.get_text().strip().lower()
        href = elem.get("href") or elem.get("data-href") or elem.get("data-url")
        if ("download media" in text or "media" in text or "download images" in text) and href:
            if "play.google.com" not in href:
                zip_url = urllib.parse.urljoin(page_url, href)
                break

    if not zip_url:
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if ".zip" in href.lower() and "play.google.com" not in href:
                zip_url = urllib.parse.urljoin(page_url, href)
                break

    downloaded_img_paths = []
    if zip_url:
        print(f"Downloading Product Media ZIP from: {zip_url}")
        try:
            zip_res = requests.get(zip_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
            if zip_res.status_code == 200 and len(zip_res.content) > 100:
                zip_path = os.path.join(temp_dir, "product_media.zip")
                with open(zip_path, "wb") as f:
                    f.write(zip_res.content)

                extracted_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extracted_dir, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)

                img_idx = 1
                for root, _, files in os.walk(extracted_dir):
                    for file in sorted(files):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                            src_path = os.path.join(root, file)
                            jpg_out_path = os.path.join(temp_dir, f"hd_img_{img_idx}.jpg")
                            try:
                                with Image.open(src_path) as im:
                                    rgb_im = im.convert('RGB')
                                    rgb_im.save(jpg_out_path, 'JPEG', quality=100, subsampling=0)
                                    downloaded_img_paths.append(jpg_out_path)
                                    img_idx += 1
                            except Exception as c_err:
                                print(f"Error converting image {file}: {c_err}")
        except Exception as z_err:
            print(f"ZIP extraction notice: {z_err}")

    # Fallback to scraping individual images if zip wasn't found
    if not downloaded_img_paths:
        print("Fallback: Scraping individual product images...")
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and "static.markaz.app" in src:
                clean_src = src.split("?")[0]
                if clean_src not in downloaded_img_paths:
                    try:
                        img_res = requests.get(clean_src, timeout=10)
                        if img_res.status_code == 200:
                            raw_path = os.path.join(temp_dir, f"fallback_{len(downloaded_img_paths)+1}.jpg")
                            with open(raw_path, "wb") as f:
                                f.write(img_res.content)
                            with Image.open(raw_path) as im:
                                rgb_im = im.convert('RGB')
                                rgb_im.save(raw_path, 'JPEG', quality=100, subsampling=0)
                                downloaded_img_paths.append(raw_path)
                    except Exception:
                        pass

    return title, selling_price, raw_details, downloaded_img_paths
