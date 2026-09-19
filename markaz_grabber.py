import os
import json
import requests
from bs4 import BeautifulSoup
import gspread
import google.generativeai as genai

# 1. Setup Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# 2. Setup Google Sheets
gcp_key = json.loads(os.getenv("GCP_SA_KEY"))
gc = gspread.service_account_from_dict(gcp_key)
sheet = gc.open("Markaz Products").sheet1

# List of Markaz product URLs to process automatically
PRODUCT_URLS = [
    "https://www.markaz.app/shop/product/monochrome-cross-slides-005-pink/740918"
]

def scrape_and_process(url):
    print(f"Fetching product details from: {url}")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Extract Title and Overview details
    title_element = soup.find("h3")
    title = title_element.text.strip() if title_element else "Monochrome Cross Slides - 005 - Pink"
    
    # Product Overview Details (Rexine, Plain, Women's, Sizes 36-41)
    raw_details = """
    Material: Rexine
    Pattern: Plain
    Gender: Women's
    Feature: Fancy, Formal, Casual, Semi-Formal
    Sizes: 36, 37, 38, 39, 40, 41
    Package Includes: 1 x Flats
    Color: Pink
    """
    
    wholesale_price = 1439  # Default wholesale price in PKR
    selling_price = wholesale_price + 450  # Profit margin added
    
    prompt = f"""
    You are a top affiliate marketer in Pakistan.
    Rewrite this product overview into an attractive Facebook Marketplace post in Roman Urdu and English:
    
    Title: {title}
    Details: {raw_details}
    
    Instructions:
    - Use clear bullet points for features and available sizes.
    - Mention 'Cash on Delivery Available across Pakistan'.
    - End with a WhatsApp inbox call to action.
    """
    
    response = model.generate_content(prompt)
    formatted_desc = response.text.strip()
    
    # Append formatted data to Google Sheet
    sheet.append_row([title, selling_price, formatted_desc, url, "Pending"])
    print(f"Successfully added {title} (Rs. {selling_price}) to Google Sheet!")

if __name__ == "__main__":
    for url in PRODUCT_URLS:
        scrape_and_process(url)
