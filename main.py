import os
import datetime
import requests
from scraper import scrape_shoes_products
from ai_generator import generate_optimized_content
from history_manager import load_history, is_processed, mark_processed

WHATSAPP_LINK = "https://wa.me/923374633605"
BASE_DIR = os.path.join("products", "category", "shoes")

def main():
    print("Starting Markaz Shoes Local Folder & Details Generator...")
    history = load_history()
    
    products = scrape_shoes_products(max_products=3)
    if not products:
        print("No products found.")
        return

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    date_folder = os.path.join(BASE_DIR, date_str)
    os.makedirs(date_folder, exist_ok=True)

    new_items_added = False

    for product in products:
        url = product['url']
        if is_processed(url, history):
            print(f"Skipping already processed product: {product['title']}")
            continue

        print(f"Processing and generating files for: {product['title']}")
        ai_data = generate_optimized_content(
            product_title=product['title'],
            raw_overview=product['overview'],
            price=product['price']
        )

        # Create safe folder name for the product under the date folder
        safe_title = "".join(c for c in ai_data['title'] if c.isalnum() or c in (' ', '_', '-')).strip()[:40]
        product_folder = os.path.join(date_folder, safe_title)
        os.makedirs(product_folder, exist_ok=True)

        # Download images locally as .jpg files
        saved_images = []
        for idx, img_url in enumerate(product['images'], start=1):
            try:
                img_data = requests.get(img_url, timeout=10).content
                img_path = os.path.join(product_folder, f"image_{idx}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                saved_images.append(img_path)
            except Exception as e:
                print(f"Failed to download image {idx}: {e}")

        # Create details.txt file with price, keywords, description, and links
        details_content = f"""========================================
MARKAZ SHOES - FACEBOOK MARKETPLACE LISTING
========================================

SEO TITLE:
{ai_data['title']}

PRICE:
{product['price']}

SEO RANKED KEYWORDS (FOR MARKETPLACE TAGS):
{ai_data['keywords']}

ROMAN URDU SALES DESCRIPTION:
{ai_data['description']}

----------------------------------------
VERIFICATION & ORDER LINKS:
- Direct Markaz Product Link: {url}
- WhatsApp Order Link: {WHATSAPP_LINK}
========================================
"""
        details_path = os.path.join(product_folder, "details.txt")
        with open(details_path, "w", encoding="utf-8") as f:
            f.write(details_content)

        mark_processed(url, history)
        new_items_added = True
        print(f"Successfully created folder structure and files in: {product_folder}")

    if new_items_added:
        print("All folders, images, and details files created successfully!")
    else:
        print("No new products to process.")

if __name__ == "__main__":
    main()
