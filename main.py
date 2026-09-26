import os
import datetime
import traceback
import requests
from scraper import scrape_shoes_products
from ai_generator import generate_optimized_content
from drive_uploader import upload_product_to_drive
from history_manager import load_history, is_processed, mark_processed

WHATSAPP_LINK = "https://wa.me/923374633605"

def main():
    print("Starting Markaz Shoes Automation Pipeline...")
    try:
        history = load_history()
        print(f"Loaded history. Total processed items: {len(history)}")
        
        products = scrape_shoes_products(max_products=1)
        if not products:
            print("Error: No products returned from scraper.")
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
                    print(f"Downloading image {idx}: {img_url}")
                    img_data = requests.get(img_url, timeout=15).content
                    img_path = os.path.join("temp_images", f"image_{idx}.jpg")
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    local_images.append(img_path)
                except Exception as e:
                    print(f"Failed to download image {idx}: {e}")

            print("Generating AI content via Gemini...")
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

            print("Uploading to Google Drive...")
            upload_product_to_drive(product, local_images, details_content, date_str)
            mark_processed(url, history)

            # Cleanup temp files
            for img_path in local_images:
                if os.path.exists(img_path):
                    os.remove(img_path)
            if os.path.exists("temp_images"):
                try:
                    os.rmdir("temp_images")
                except Exception:
                    pass

            print(f"Successfully processed and uploaded: {product['title']}")

    except Exception as e:
        print("CRITICAL ERROR IN PIPELINE:")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    main()
