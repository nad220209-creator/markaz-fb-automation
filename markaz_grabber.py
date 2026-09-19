import os
import json
import re
import io
import requests
from bs4 import BeautifulSoup
import gspread
import google.generativeai as genai

from google.oauth2.credentials import Credentials as UserCredentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. Setup Gemini API with Dynamic Model Discovery
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
    
    # Query active models supported by API Key
    try:
        available_models = [
            m.name.replace("models/", "") for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"Active models on this API key: {available_models}")
        for model_name in available_models:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"Model {model_name} notice: {e}")
    except Exception as list_err:
        print(f"Dynamic model lookup failed: {list_err}")

    # Fallback models list
    fallback_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash"
    ]
    
    for model_name in fallback_models:
        try:
            print(f"Trying fallback model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"Fallback model {model_name} error: {e}")
            
    raise RuntimeError("All Gemini model endpoints failed. Please check your GEMINI_API_KEY.")

# 2. Setup Google Service Clients
SPREADSHEET_ID = "1WPstH3ad5hVdKx_g-hTbBVqo4Qtl09nBLFspn0GqJV8"
MAIN_DRIVE_FOLDER_ID = "1NPYh-JHxjxF_kyu1ibkTO-AWhRCIJVmP"

# Google Sheets client via Service Account
gcp_key = json.loads(os.getenv("GCP_SA_KEY"))
gc = gspread.service_account_from_dict(gcp_key)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Google Drive client via Personal User OAuth Credentials
refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN")
client_id = os.getenv("GDRIVE_CLIENT_ID")
client_secret = os.getenv("GDRIVE_CLIENT_SECRET")

if not all([refresh_token, client_id, client_secret]):
    raise ValueError("Missing GDRIVE_REFRESH_TOKEN, GDRIVE_CLIENT_ID, or GDRIVE_CLIENT_SECRET in GitHub Secrets!")

user_creds = UserCredentials(
    token=None,
    refresh_token=refresh_token,
    client_id=client_id,
    client_secret=client_secret,
    token_uri="https://oauth2.googleapis.com/token"
)

try:
    user_creds.refresh(Request())
    print("Successfully authenticated Google Drive User OAuth Credentials!")
except Exception as auth_err:
    print(f"OAuth token refresh notice: {auth_err}")

drive_service = build('drive', 'v3', credentials=user_creds)

def ensure_clean_headers():
    expected_headers = ["Title", "Price (PKR)", "Description", "Drive Image Folder Link", "Status"]
    first_row = sheet.row_values(1)
    if first_row != expected_headers:
        print("Formatting Row 1 with standard clean headers...")
        sheet.insert_row(expected_headers, index=1)

def create_drive_folder_and_upload_images(product_title, image_urls):
    """Creates a subfolder in your personal Google Drive and uploads JPEG image files."""
    print(f"Creating Google Drive subfolder for: {product_title}...")
    folder_metadata = {
        'name': product_title,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [MAIN_DRIVE_FOLDER_ID]
    }
    
    folder = drive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
    subfolder_id = folder.get('id')
    folder_link = folder.get('webViewLink')

    # Download each product photo and upload directly into the subfolder
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            print(f"Uploading image {idx}/{len(image_urls)} to Drive...")
            res = requests.get(img_url, timeout=15)
            if res.status_code == 200:
                media = MediaIoBaseUpload(io.BytesIO(res.content), mimetype='image/jpeg')
                file_metadata = {
                    'name': f"{product_title}_image_{idx}.jpg",
                    'parents': [subfolder_id]
                }
                drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except Exception as err:
            print(f"Failed image upload ({img_url}): {err}")

    return folder_link

# List of Markaz product URLs to process automatically
PRODUCT_URLS = [
    "https://www.markaz.app/shop/product/monochrome-cross-slides-005-pink-00224bfb-8ddc-4c6e-9331-5f21fca6913f"
]

def scrape_and_process(url):
    print(f"\n--- Scraping product from: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Extract Title
        title_tag = soup.find("h3") or soup.find("h1")
        title = title_tag.text.strip() if title_tag else "Monochrome Cross Slides - 005 - Pink"
        
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
                
        selling_price = wholesale_price + 450  # Profit margin PKR 450
        
        # Extract Details / Overview
        overview_section = soup.find("div", {"id": "471"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
        raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]
        
        # Scrape Product Images
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
            
        # Upload real images to personal Google Drive
        drive_folder_link = create_drive_folder_and_upload_images(title, image_urls)
        
        print("Generating AI description...")
        formatted_desc = generate_ai_description(title, selling_price, raw_details)
        
        ensure_clean_headers()
        
        # Write row to Google Sheet
        sheet.insert_row([title, selling_price, formatted_desc, drive_folder_link, "Pending"], index=2)
        print(f"SUCCESS: Uploaded images to Drive & saved '{title}' to Google Sheet!")
    except Exception as e:
        print(f"Error processing URL {url}: {e}")

if __name__ == "__main__":
    for product_url in PRODUCT_URLS:
        scrape_and_process(product_url)
