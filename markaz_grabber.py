import os
import json
import gspread
import google.generativeai as genai

# 1. Setup Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# 2. Setup Google Sheets
gcp_key = json.loads(os.getenv("GCP_SA_KEY"))
gc = gspread.service_account_from_dict(gcp_key)
sheet = gc.open("Markaz Products").sheet1

def process_markaz_product(title, wholesale_price, raw_details, image_url):
    """Formats raw Markaz details with AI and saves to Google Sheets."""
    selling_price = wholesale_price + 450  # Adds Rs. 450 profit margin
    
    prompt = f"""
    You are a top affiliate marketer in Pakistan.
    Rewrite this Markaz product detail into an attractive Facebook Marketplace post in Roman Urdu & English.
    Include bullet points for key features, mention 'Cash on Delivery Available across Pakistan', 
    and end with a Call to Action to message on WhatsApp.
    
    Product Title: {title}
    Original Details: {raw_details}
    """
    
    response = model.generate_content(prompt)
    formatted_desc = response.text.strip()
    
    # Save directly to Google Sheets
    sheet.append_row([title, selling_price, formatted_desc, image_url, "Pending"])
    print(f"Successfully added {title} (Rs. {selling_price}) to Google Sheets!")

if __name__ == "__main__":
    # Put actual Markaz product details here when running
    product_title = input("Enter Product Title: ")
    wholesale_price = int(input("Enter Wholesale Price: "))
    raw_details = input("Paste Product Details: ")
    image_url = input("Enter Image URL: ")
    
    process_markaz_product(product_title, wholesale_price, raw_details, image_url)
