import os
import json
import re
import requests
from bs4 import BeautifulSoup
import gspread
import google.generativeai as genai

# 1. Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def generate_ai_description(title, wholesale_price, raw_details):
    prompt = f"""
    You are a top affiliate marketer in Pakistan.
    Rewrite the following product overview into an attractive Facebook Marketplace post in Roman Urdu and English.
    
    Product Title: {title}
    Wholesale Price: PKR {wholesale_price}
    Product Details: {raw_details}
    
    Instructions:
    - Write a short, clear, catchy title.
    - Include bullet points highlighting key features (Material, Available Sizes, Colors, Gender).
    - Clearly state: 'Cash on Delivery Available across Pakistan'.
    - End with a WhatsApp/Messenger call to action for buyers to send an inbox message.
    """
    
    # Try fetching available models dynamically from the API key
    try:
        available_models = [
            m.name.replace("models/", "") for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]
        print(f"Active models on this API key: {available_models}")
        for model_name in available_models:
            try:
                print(f"Trying dynamic model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"Model {model_name} notice: {e}")
    except Exception as list_err:
        print(f"Could not list models dynamically: {list_err}")

    # Fallback list with active models
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"Trying fallback model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Model {model_name} fallback notice: {e}")
            
    raise RuntimeError("All Gemini model endpoints failed. Please check your GEMINI_API_KEY in Google AI Studio.")

# 2. Setup Google Sheets Access
SPREADSHEET_ID = "1WPstH3ad5hVdKx_g-hTbBVqo4Qtl09nBLFspn0GqJV8"
gcp_key = json.loads(os.getenv("GCP_SA_KEY"))
gc = gspread.service_account_from_dict(gcp_key)

sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

# Markaz product URLs
PRODUCT_URLS = [
    "https://www.markaz.app/shop/product/monochrome-cross-slides-005-pink/740918"
]

def scrape_and_process(url):
    print(f"\n--- Fetching product details from: {url} ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    res = requests.get(url, headers=headers, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Extract Title
    title_tag = soup.find("h3") or soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Monochrome Cross Slides - 005 - Pink"
    
    # Extract Main Product Image URL
    image_tag = soup.find("meta", property="og:image")
    if image_tag and image_tag.get("content"):
        image_url = image_tag["content"]
    else:
        img_elem = soup.find("img")
        image_url = img_elem["src"] if img_elem and img_elem.get("src") else url

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
            
    selling_price = wholesale_price + 450
    
    # Extract Details
    overview_section = soup.find("div", {"id": "471"}) or soup.find("section", {"class": re.compile(r"overview|product", re.IGNORECASE)})
    raw_details = overview_section.text.strip() if overview_section else soup.get_text()[:2000]
    
    print("Generating AI Description...")
    formatted_desc = generate_ai_description(title, wholesale_price, raw_details)
    
    print(f"Writing to Google Sheet ID: {SPREADSHEET_ID}...")
    sheet.insert_row([title, selling_price, formatted_desc, image_url, "Pending"], index=2)
    print(f"SUCCESS: Added '{title}' (Rs. {selling_price}) to Google Sheet!")

if __name__ == "__main__":
    for product_url in PRODUCT_URLS:
        scrape_and_process(product_url)
