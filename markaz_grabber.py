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

from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# 1. Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from environment variables!")

genai.configure(api_key=GEMINI_API_KEY)

# Seller Information
SELLER_NAME = "Muhammad Naveed Arshad"
WHATSAPP_NUMBER = "03374633605"
WHATSAPP_LINK = "https://wa.me/923374633605"

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
    models_to_try = ["gemini-3.6-flash", "gemini-1.5-flash-latest", "gemini-2.5-flash"]
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

# 2. Setup Google Drive Credentials via OAuth Refresh Token
MAIN_DRIVE_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN")
client_id = os.getenv("GDRIVE_CLIENT_ID")
client_secret = os.getenv("GDRIVE_CLIENT_SECRET")

if not all([refresh_token, client_id, client_secret]):
    raise ValueError("Missing GDRIVE secrets in environment variables!")

user_creds = UserCredentials(
    token=None,
    refresh_token=refresh_token.strip(),
    client_id=client_id.strip(),
    client_secret=client_secret.strip(),
    token_uri="[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
)

# Force immediate token validation/refresh
user_creds.refresh(Request())
drive_service = build('drive', 'v3', credentials=user_creds)
print("Google Drive OAuth connection authenticated successfully!")

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

    for elem in soup.find_all(["a", "button"]):
        text = elem.get_text().strip().lower()
        href = elem.get("href") or elem.get("data-href") or elem.get("data-url")
        if ("download media" in text or "download" in text) and href:
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
        print(f"Downloading Media ZIP from: {zip_url}")
        try:
            res = requests.get(
                zip_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=30
            )
            if res.status_code == 200 and len(res.content) > 100 and res.content.startswith(b'PK'):
                zip_path = os.path.join(temp_dir, "media.zip")
                with open(zip_path, "wb") as f:
                    f.write(res.content)

                extracted_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extracted_dir, exist_ok=True)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)

                img_idx = 1
                for root, _, files in os.walk(extracted_dir):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                            src_path = os.path.join(root, file)
                            jpg_out_path = os.path.join(temp_dir, f"unzipped_img_{img_idx}.jpg")
                            try:
                                with Image.open(src_path) as im:
                                    rgb_im = im.convert('RGB')
                                    rgb_im.save(jpg_out_path, 'JPEG')
                                    downloaded_img_paths.append(jpg_out_path)
                                    img_idx += 1
                            except Exception as c_err:
                                print(f"Notice converting image {file}: {c_err}")

                if downloaded_img_paths:
                    print(f"SUCCESS: Extracted {len(downloaded_img_paths)} product photos from Download Media ZIP!")
                    return downloaded_img_paths
        except Exception as z_err:
            print(f"ZIP media extraction notice ({z_err}). Falling back to HTML gallery scraping.")

    print("Scraping gallery photos directly from Markaz web page HTML...")
    image_urls = []
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        image_urls.append(og_img["content"])

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and "static.markaz.app" in src:
            clean_src = src.split("?")[0]
            if clean_src not in image_urls:
                image_urls.append(clean_src)

    if not image_urls:
        image_urls = [page_url]

    for idx, img_url in enumerate(image_urls, start=1):
        try:
            img_res = requests.get(img_url, timeout=10)
            if img_res.status_code == 200:
                raw_path = os.path.join(temp_dir, f"raw_{idx}")
                jpg_path = os.path.join(temp_dir, f"fallback_img_{idx}.jpg")
                with open(raw_path, "wb") as f:
                    f.write(img_res.content)
                with Image.open(raw_path) as im:
                    rgb_im = im.convert('RGB')
                    rgb_im.save(jpg_path, 'JPEG')
                downloaded_img_paths.append(jpg_path)
        except Exception as e:
            print(f"Notice downloading image {img_url}: {e}")

    return downloaded_img_paths

def create_structured_pdf(title, selling_price, copy_dict, image_files, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 7, f"Selling Price: PKR {selling_price}", ln=True)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 7, f"Seller: {SELLER_NAME} | WhatsApp: {WHATSAPP_NUMBER} ({WHATSAPP_LINK})", ln=True)
    pdf.ln(4)

    sections = [
        ("--- FACEBOOK MARKETPLACE COPY ---", copy_dict.get("fb_marketplace", "")),
        ("--- INSTAGRAM POST COPY & HASHTAGS ---", copy_dict.get("instagram", "")),
        ("--- TIKTOK VIDEO CAPTION ---", copy_dict.get("tiktok", "")),
        ("--- FACEBOOK GROUPS & PAGE COPY ---", copy_dict.get("fb_group", ""))
    ]

    for header, content in sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 7, header, ln=True)
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, clean_text_for_pdf(content))
        pdf.ln(5)

    if image_files:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Product Gallery Photos ({len(image_files)} extracted):", ln=True)
        pdf.ln(3)

        for img_path in image_files:
            try:
                pdf.image(img_path, w=150)
                pdf.ln(5)
            except Exception as img_err:
                print(f"Skipping PDF image render for {img_path}: {img_err}")

    pdf.output(output_path)

def upload_pdf_to_drive(pdf_path, pdf_filename):
    print(f"Uploading '{pdf_filename}.pdf' to Google Drive...")
    file_metadata = {
        'name': f"{pdf_filename}.pdf",
        'mimeType': 'application/pdf',
        'parents': [MAIN_DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(pdf_path, mimetype='application/pdf', resumable=True)
    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    folder_link = uploaded.get('webViewLink')
    print(f"SUCCESS: Uploaded PDF to Drive -> {folder_link}")
    return folder_link

# Target product links
PRODUCT_URLS = [
    "[https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844](https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844)"
]

def scrape_and_process(raw_url):
    url = clean_url(raw_url)
    print(f"\n--- Scraping product from Markaz Web: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Multicolor Floral Lawn Kurta Pajama Set for Women"

    price_text = ""
    for tag in soup.find_all(string=re.compile(r"PKR", re.IGNORECASE)):
        price_text += " " + str(tag).strip()

    digits = re.findall(r"\d[\d,]*", price_text)
    wholesale_price = 1930
    if digits:
        try:
            extracted = int(digits[0].replace(",", ""))
            if extracted > 100:
                wholesale_price = extracted
        except ValueError:
            pass

    selling_price = wholesale_price + 450

    overview_section = soup.find("div", {"id": "504"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
