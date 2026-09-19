import os
import json
import re
import io
import requests
from bs4 import BeautifulSoup
import gspread
import google.generativeai as genai

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
- Use emojis, clear bullet points for features/sizes, mention 'Cash on Delivery Available across Pakistan', and end with a WhatsApp inbox Call to Action.
"""
    
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro"
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Notice for model {model_name}: {e}")
            
    raise RuntimeError("All Gemini model endpoints failed. Please verify your GEMINI_API_KEY.")

# 2. Setup Google Credentials & Services
SPREADSHEET_ID = "1WPstH3ad5hVdKx_g-hTbBVqo4Qtl09nBLFspn0GqJV8"

# PASTE YOUR GOOGLE DRIVE FOLDER ID HERE
MAIN_DRIVE_FOLDER_ID = "YOUR_GOOGLE_DRIVE_FOLDER_ID_HERE"

gcp_key = json.loads(os.getenv("GCP_SA_KEY"))
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_info(gcp_key, scopes=scopes)

# Service Clients
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
drive_service = build('drive', 'v3', credentials=creds)

def ensure_clean_headers():
    expected_headers = ["Title", "Price (PKR)", "Description", "Drive Image Folder Link", "Status"]
    first_row = sheet.row_values(1)
    if first_row != expected_headers:
        print("Formatting Row 1 with standard headers...")
        sheet.insert_row(expected_headers, index=1)

def create_drive_folder_and_upload_images(product_title, image_urls):
    """Creates a subfolder in Google Drive and uploads all images."""
    print(f"Creating Google Drive subfolder for: {product_title}...")
    folder_metadata = {
        'name': product_title,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [MAIN_DRIVE_FOLDER_ID]
    }
    
    folder = drive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
    subfolder_id = folder.get('id')
    folder_link = folder.get('webViewLink')
    
    # Make subfolder accessible
    user_perm = {'type': 'anyone', 'role': 'reader'}
    try:
        drive_service.permissions().create(fileId=subfolder_id, body=user_perm).execute()
    except Exception as e:
        print(f"Notice setting folder permission: {e}")

    # Download each image and upload directly to Google Drive
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            print(f"Downloading & uploading image {idx}/{len(image_urls)} to Drive...")
            res = requests.get(img_url, timeout=15)
            if res.status_code == 200:
                media = MediaIoBaseUpload(io.BytesIO(res.content), mimetype='image/jpeg')
                file_metadata = {
                    'name': f"{product_title}_image_{idx}.jpg",
                    'parents': [subfolder_id]
                }
                drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except Exception as err:
            print(f"Failed to upload image {img_url}: {err}")

    return folder_link

# List of Markaz product URLs
PRODUCT_URLS = [
    "https://www.markaz.app/shop/product/monochrome-cross-slides-005-pink/740918"
]

def scrape_and_process(url):
    print(f"\n--- Scraping product from: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Extract Title
    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Markaz Product"
    
    # Extract Wholesale Price
    price_text = ""
    for tag in soup.find_all(string=re.compile(r"PKR", re.IGNORECASE)):
        price_text += " " + str(tag).strip()
        
    digits = re.findall(r"\d[\d,]*", price_text)
    wholesale_price = 1439
    if digits:
        try:
            extracted = int(digits[0].replace(",", ""))
            if extracted > 100:
                wholesale_price = extracted
        except ValueError:
            pass
            
    selling_price = wholesale_price + 450  # Profit Margin
    
    # Extract Details / Overview
    overview_section = soup.find("div", {"id": "471"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
    raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]
    
    # Scrape ALL Product Images
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
        image_urls = [url]
        
    # Upload images to Google Drive
    drive_folder_link = create_drive_folder_and_upload_images(title, image_urls)
    
    print("Generating clean AI marketplace post...")
    formatted_desc = generate_ai_description(title, selling_price, raw_details)
    
    ensure_clean_headers()
    
    # Insert formatted data at Row 2
    print("Writing row to Google Sheet...")
    sheet.insert_row([title, selling_price, formatted_desc, drive_folder_link, "Pending"], index=2)
    print(f"SUCCESS: Created Drive folder & added '{title}' (Rs. {selling_price}) to Google Sheet!")

if __name__ == "__main__":
    for product_url in PRODUCT_URLS:
        scrape_and_process(product_url)
