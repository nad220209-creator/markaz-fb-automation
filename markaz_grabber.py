import os
import json
import re
import zipfile
import tempfile
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image
from fpdf import FPDF
import google.generativeai as genai

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# 1. Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from environment variables!")

genai.configure(api_key=str(GEMINI_API_KEY).strip("[]'\" "))

# Seller Information
SELLER_NAME = "Muhammad Naveed Arshad"
WHATSAPP_NUMBER = "03374633605"
WHATSAPP_LINK = "https://wa.me/923374633605"

# HARDCODED OAUTH CREDENTIALS (VERIFIED & WORKING)
HARDCODED_CLIENT_ID = "295426809796-g7ij8hpd6c1bne47eitj0ilhbjqtfa5m.apps.googleusercontent.com"
HARDCODED_CLIENT_SECRET = "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"
HARDCODED_REFRESH_TOKEN = "1//04-lxAxN2RYljCgYIARAAGAQSNwF-L9Ir_SwrAvwFZoNn-FumsqBkX5JfeWoMXVbUlS6g0-JvybhUcfclRSpQp3v-HYIgFxb4fq8"
TOKEN_URL = "https://oauth2.googleapis.com/token"

def clean_str(val):
    if not val:
        return ""
    s = str(val).strip()
    while s.startswith(('[', "'", '"', '(', '<')) or s.endswith((']', "'", '"', ')', '>')):
        s = s[1:-1].strip()
    return s

CLIENT_ID = clean_str(HARDCODED_CLIENT_ID)
CLIENT_SECRET = clean_str(HARDCODED_CLIENT_SECRET)
REFRESH_TOKEN = clean_str(HARDCODED_REFRESH_TOKEN)
URL = clean_str(TOKEN_URL)

def clean_url(raw_url):
    match = re.search(r'https?://[^\s\]\)\"]+', raw_url)
    if match:
        return match.group(0)
    cleaned = raw_url.strip("[]()'\" ")
    if not cleaned.startswith("http"):
        cleaned = "https://" + cleaned.lstrip("/")
    return cleaned

def generate_multi_platform_copy(title, selling_price, raw_details):
    prompt = f"""
You are an expert e-commerce affiliate marketer in Pakistan.
Generate distinct, high-converting social media posts for this product:

Product Title: {title}
Price: PKR {selling_price}
Raw Details/Measurements: {raw_details}

SELLER CONTACT INFORMATION (MUST BE INCLUDED IN EVERY POST'S CALL TO ACTION):
- Contact Name: {SELLER_NAME}
- WhatsApp Number: {WHATSAPP_NUMBER}
- Direct WhatsApp Link: {WHATSAPP_LINK}

Return ONLY a valid JSON object with the following keys:
1. "fb_marketplace": Concise listing copy emphasizing exact measurements, size details, PKR price, Cash on Delivery across Pakistan, and a Call to Action with seller name ({SELLER_NAME}), WhatsApp ({WHATSAPP_NUMBER}), and link ({WHATSAPP_LINK}).
2. "instagram": Aesthetic Roman Urdu & English post with emojis, key feature bullet points, COD note, seller contact details ({SELLER_NAME}, {WHATSAPP_NUMBER}, {WHATSAPP_LINK}), and 10 trending Pakistani fashion hashtags.
3. "tiktok": Short, catchy caption (under 120 words) with attention-grabbing hook, seller WhatsApp ({WHATSAPP_NUMBER} / {WHATSAPP_LINK}), and video overlay hashtags.
4. "fb_group": Persuasive sales post for Facebook Buy & Sell groups with urgency, full size details, and direct order details via {SELLER_NAME} at {WHATSAPP_NUMBER} ({WHATSAPP_LINK}).

CRITICAL: DO NOT include any introductory text, markdown headers outside JSON, or self-check questions. Output pure JSON only.
"""
    models_to_try = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-1.5-flash"]
    for model_name in models_to_try:
        try:
            print(f"Generating AI copy with model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                clean_raw = response.text.strip()
                clean_raw = re.sub(r'^```json\s*', '', clean_raw, flags=re.IGNORECASE)
                clean_raw = re.sub(r'^```\s*', '', clean_raw)
                clean_raw = re.sub(r'\s*```$', '', clean_raw)
                
                try:
                    data = json.loads(clean_raw)
                    if isinstance(data, dict) and "fb_marketplace" in data:
                        return data
                except Exception:
                    pass

                return {
                    "fb_marketplace": clean_raw,
                    "instagram": clean_raw,
                    "tiktok": clean_raw[:300],
                    "fb_group": clean_raw
                }
        except Exception as e:
            print(f"Notice for model {model_name}: {e}")

    raise RuntimeError("All Gemini model endpoints failed.")

# 2. Direct OAuth Token Generation
MAIN_DRIVE_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

print(f"Requesting fresh OAuth access token from: {URL}")
token_res = requests.post(
    URL,
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token"
    },
    timeout=30
)

if token_res.status_code != 200:
    raise RuntimeError(f"Failed to refresh OAuth token: {token_res.text}")

token_data = token_res.json()
access_token = token_data.get("access_token")

creds = Credentials(token=access_token)
drive_service = build('drive', 'v3', credentials=creds)
print("Google Drive direct OAuth authentication successful!")

def clean_text_for_pdf(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def fetch_media_and_unzip(soup, page_url, temp_dir):
    downloaded_img_paths = []
    zip_url = None

    # Search specifically for download media links/buttons on Markaz
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

    if zip_url:
        print(f"Downloading Product Media ZIP from: {zip_url}")
        try:
            res = requests.get(
                zip_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=45
            )
            if res.status_code == 200 and len(res.content) > 100:
                zip_path = os.path.join(temp_dir, "product_media.zip")
                with open(zip_path, "wb") as f:
                    f.write(res.content)

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
                                    # Save at 100% full original quality without downscaling or compression
                                    rgb_im.save(jpg_out_path, 'JPEG', quality=100, subsampling=0)
                                    downloaded_img_paths.append(jpg_out_path)
                                    img_idx += 1
                            except Exception as c_err:
                                print(f"Notice converting HD image {file}: {c_err}")

                if downloaded_img_paths:
                    print(f"SUCCESS: Extracted {len(downloaded_img_paths)} uncompressed HD product photos from ZIP!")
                    return downloaded_img_paths
        except Exception as z_err:
            print(f"ZIP media extraction notice ({z_err}). Falling back to strict product gallery scraping.")

    # STRICT FALLBACK: Only grab main product gallery images (no recommendations/footers)
    print("Scraping core product gallery photos strictly...")
    image_urls = []
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image_urls.append(og_img["content"])

    gallery_containers = soup.find_all("div", class_=re.compile(r"gallery|slider|carousel|product-image|image-container", re.IGNORECASE))
    if gallery_containers:
        for container in gallery_containers:
            for img in container.find_all("img"):
                src = img.get("src") or img.get("data-src")
                if src and "static.markaz.app" in src:
                    clean_src = src.split("?")[0]
                    if clean_src not in image_urls:
                        image_urls.append(clean_src)

    if not image_urls:
        image_urls = [page_url]

    for idx, img_url in enumerate(image_urls[:15], start=1):
        try:
            img_res = requests.get(img_url, timeout=15)
            if img_res.status_code == 200:
                raw_path = os.path.join(temp_dir, f"raw_{idx}")
                jpg_path = os.path.join(temp_dir, f"fallback_img_{idx}.jpg")
                with open(raw_path, "wb") as f:
                    f.write(img_res.content)
                with Image.open(raw_path) as im:
                    rgb_im = im.convert('RGB')
                    rgb_im.save(jpg_path, 'JPEG', quality=100, subsampling=0)
                downloaded_img_paths.append(jpg_path)
        except Exception as e:
            print(f"Notice downloading image {img_url}: {e}")

    return downloaded_img_paths

def create_structured_pdf(title, selling_price, copy_dict, image_files, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & Pricing Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 7, f"Selling Price: PKR {selling_price}", new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 7, f"Seller: {SELLER_NAME} | WhatsApp: {WHATSAPP_NUMBER} ({WHATSAPP_LINK})", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    # Organized Specification Table (Rows & Columns)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  PRODUCT SPECIFICATIONS, SIZES & MEASUREMENTS", fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    spec_rows = [
        ("Product Name", title),
        ("Selling Price", f"PKR {selling_price}"),
        ("Fabric Material", "Premium Lawn (Soft & Breathable)"),
        ("Design & Pattern", "Multicolor Digital Floral Print"),
        ("Package Includes", "1 Stitched Shirt + 1 Stitched Trouser (2 Pcs Set)"),
        ("Shirt Length", "37 Inches"),
        ("Shirt Chest", "22 Inches"),
        ("Shirt Shoulder", "16.5 Inches"),
        ("Arm Length", "19 Inches"),
        ("Trouser Length", "37 Inches"),
        ("Trouser Waist", "42 Inches"),
        ("Trouser Hip", "44 Inches"),
        ("Delivery Method", "Cash on Delivery (COD) across Pakistan"),
        ("Return Policy", "7-Day Easy Return Guarantee")
    ]

    pdf.set_font("Helvetica", "", 10)
    for row_idx, (key, val) in enumerate(spec_rows):
        if row_idx % 2 == 0:
            pdf.set_fill_color(240, 244, 248)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(65, 7, f"  {key}", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(125, 7, f"  {val}", border=1, fill=True, new_x='LMARGIN', new_y='NEXT')

    pdf.ln(6)

    # Social Media Copy Sections
    sections = [
        ("--- FACEBOOK MARKETPLACE COPY ---", copy_dict.get("fb_marketplace", "")),
        ("--- INSTAGRAM POST COPY & HASHTAGS ---", copy_dict.get("instagram", "")),
        ("--- TIKTOK VIDEO CAPTION ---", copy_dict.get("tiktok", "")),
        ("--- FACEBOOK GROUPS & PAGE COPY ---", copy_dict.get("fb_group", ""))
    ]

    for header, content in sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 7, header, new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        pdf.set_font("
