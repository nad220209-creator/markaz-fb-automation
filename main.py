import os
import datetime
import requests
from scraper import scrape_shoes_products
from ai_generator import generate_optimized_content
from drive_uploader import upload_product_to_drive
from history_manager import load_history, is_processed, mark_processed

WHATSAPP_LINK = "https://wa.me/923374633605"

def main():
    print("Starting Markaz Shoes Automation Pipeline...")
    history = load_history()
    
    products = scrape_shoes_products(max_products=3)
    if not products:
        print("No products found during scraping.")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    for product in products:
        url = product['url']
        if is_processed(url, history):
            print(f"Skipping already processed product: {product['title']}")
            continue

        print(f"Processing product: {product['title']}")

        os.makedirs("temp_images", exist_ok=True)
        local_images = []
        for idx, img_url in enumerate(product['images'], start=1):
            try:
                img_data = requests.get(img_url, timeout=10).content
                img_path = os.path.join("temp_images", f"image_{idx}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                local_images.append(img_path)
            except Exception as e:
                print(f"Failed to download image {idx}: {e}")

        ai_output = generate_optimized_content(
            product_title=product['title'],
            raw_overview=product['overview'],
            price=product['price']
        )

        details_content = f"""========================================
MARKAZ SHOES AUTOMATION PIPELINE
========================================

{ai_output}

----------------------------------------
PRICING & ORDERING:
Price: {product['price']}
WhatsApp Order Link: {WHATSAPP_LINK}
Direct Verification Link: {url}
========================================
"""

        upload_product_to_drive(product, local_images, details_content, date_str)
        mark_processed(url, history)

        for img_path in local_images:
            if os.path.exists(img_path):
                os.remove(img_path)
        if os.path.exists("temp_images"):
            os.rmdir("temp_images")

        print(f"Successfully processed and uploaded: {product['title']}")

if __name__ == "__main__":
    main()
