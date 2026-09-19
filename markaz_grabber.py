import os
import json
import re
import io
import zipfile
import tempfile
import urllib.parse
import requests
from bs4 import BeautifulSoup
from PIL import Image
from fpdf import FPDF
import gspread
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

def generate_ai_description(title, selling_price, raw_details):
    prompt = f"""
You are a top affiliate marketer in Pakistan.
Write an attractive, high-converting Facebook Marketplace post in Roman Urdu and English for this product.

Product Title: {title}
Price: PKR {selling_price}
Details: {raw_details}

CRITICAL INSTRUCTIONS:
- Return ONLY the final Facebook Marketplace post copy.
- DO NOT include greetings, instructions, metadata, or repeated prompts.
- Use clear bullet points for features/sizes, mention 'Cash on Delivery Available across Pakistan', and end with a WhatsApp inbox Call to Action.
"""
    try:
        available_models = [
            m.name.replace("models/", "") for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        for model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"Notice for model {model_name}: {e}")
    except Exception as list_err:
        print(f"Dynamic model lookup notice: {list_err}")

    fallback_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
    for model_name in fallback_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Fallback model error ({model_name}): {e}")
            
    raise RuntimeError("All Gemini model endpoints failed.")

# 2. Setup Google Credentials
SPREADSHEET_ID = "1WPstH3ad5hVdKx_g-hTbBVqo4Qtl09nBLFspn0GqJV8"
MAIN_DRIVE_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN")
client_id = os.getenv("GDRIVE_CLIENT_ID")
client_secret = os.getenv("GDRIVE_CLIENT_SECRET")
gcp_sa_key_str = os.getenv("GCP_SA_KEY")

if not all([refresh_token, client_id, client_secret, gcp_sa_key_str]):
    raise ValueError("Missing GDRIVE or GCP_SA_KEY secrets in GitHub Actions environment variables!")

# Authenticate Google Drive via User OAuth (Personal 15GB+ Storage Quota)
user_creds = UserCredentials(
    token=None,
    refresh_token=refresh_token,
    client_id=client_id,
    client_secret=client_secret,
    token_uri="https://oauth2.googleapis.com/token"
)

user_creds.refresh(Request())
drive_service = build('drive', 'v3', credentials=user_creds)

# Authenticate Google Sheets via Service Account
gc = gspread.service_account_from_dict(json.loads(gcp_sa_key_str))
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

def clean_text_for_pdf(text):
    """Safely converts unicode text to ASCII to prevent FPDF font encoding crashes."""
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def sanitize_filename(name):
    """Cleans product titles for safe file system naming."""
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def fetch_media_and_unzip(soup, page_url, temp_dir):
    """
    Finds the 'Download Media' ZIP button/link on the page, downloads the ZIP,
    and unzips all product images. Falls back to page image tags if ZIP is unavailable.
    """
    downloaded_img_paths = []
    zip_url = None

    # Search for 'Download Media' button or direct ZIP download link
    for a_tag in soup.find_all(["a", "button"]):
        text = a_tag.get_text().strip().lower()
        href = a_tag.get("href") or a_tag.get("data-href") or a_tag.get("data-url")
        if "download media" in text or "download" in text:
            if href:
                zip_url = urllib.parse.urljoin(page_url, href)
                break

    if not zip_url:
        for a_tag in soup.find_all("a", href=True):
            if ".zip" in a_tag["href"].lower() or "media" in a_tag["href"].lower():
                zip_url = urllib.parse.urljoin(page_url, a_tag["href"])
                break

    if zip_url:
        print(f"Found 'Download Media' link: {zip_url}")
        try:
            zip_res = requests.get(
                zip_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=30
            )
            if zip_res.status_code == 200 and len(zip_res.content) > 100:
                zip_file_path = os.path.join(temp_dir, "media.zip")
                with open(zip_file_path, "wb") as f:
                    f.write(zip_res.content)

                extracted_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extracted_dir, exist_ok=True)

                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
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
                            except Exception as convert_err:
                                print(f"Notice converting unzipped image {file}: {convert_err}")

                if downloaded_img_paths:
                    print(f"SUCCESS: Downloaded and unzipped {len(downloaded_img_paths)} product images from media ZIP!")
                    return downloaded_img_paths
        except Exception as zip_err:
            print(f"ZIP media download notice ({zip_err}). Falling back to HTML photo scraping.")

    # Fallback to page photo elements if media zip is missing
    print("Fetching images directly from product gallery HTML...")
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
            print(f"Notice fetching fallback image {img_url}: {e}")

    return downloaded_img_paths

def create_product_pdf(title, selling_price, description, image_files, output_path):
    """Generates a PDF containing title, price, listing copy, and photos."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Product Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(3)

    # Price
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 8, f"Selling Price: PKR {selling_price}", ln=True)
    pdf.ln(4)

    # Description
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, clean_text_for_pdf(description))
    pdf.ln(6)

    # Unzipped Images Gallery
    if image_files:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Product Gallery Images ({len(image_files)} photos unzipped):", ln=True)
        pdf.ln(3)

        for img_path in image_files:
            try:
                pdf.image(img_path, w=150)
                pdf.ln(5)
            except Exception as img_err:
                print(f"Skipping PDF image render for {img_path}: {img_err}")

    pdf.output(output_path)

def upload_pdf_to_drive(pdf_path, pdf_filename):
    """Uploads PDF file directly to Google Drive."""
    print(f"Uploading '{pdf_filename}.pdf' to Google Drive...")
    file_metadata = {
        'name': f"{pdf_filename}.pdf",
        'mimeType': 'application/pdf',
        'parents': [MAIN_DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(pdf_path, mimetype='application/pdf')
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
    "https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844"
]

def scrape_and_process(url):
    print(f"\n--- Scraping product from: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Extract Product Title
    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Multicolor Floral Lawn Kurta Pajama Set for Women"

    # Extract Wholesale Price
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

    selling_price = wholesale_price + 450  # Profit margin PKR 450

    # Extract Product Overview details
    overview_section = soup.find("div", {"id": "471"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
    if not overview_section:
        for elem in soup.find_all(["div", "section", "article"]):
            if "product overview" in elem.get_text().lower():
                overview_section = elem
                break

    raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]

    # Download Media ZIP & Unzip all images into temporary directory
    temp_dir = tempfile.mkdtemp()
    unzipped_img_paths = fetch_media_and_unzip(soup, url, temp_dir)

    print("Generating AI marketplace post copy...")
    formatted_desc = generate_ai_description(title, selling_price, raw_details)

    # Build local PDF file named on Product Title
    clean_file_title = sanitize_filename(title)
    local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
    create_product_pdf(title, selling_price, formatted_desc, unzipped_img_paths, local_pdf_path)

    # Upload PDF to Google Drive
    drive_pdf_link = upload_pdf_to_drive(local_pdf_path, clean_file_title)

    # Log record entry into Google Sheet
    sheet.insert_row([title, selling_price, formatted_desc, drive_pdf_link, "Pending"], index=2)
    print(f"SUCCESS: Created PDF '{clean_file_title}.pdf' with unzipped photos and saved to Google Drive!")

if __name__ == "__main__":
    for product_url in PRODUCT_URLS:
        scrape_and_process(product_url)
