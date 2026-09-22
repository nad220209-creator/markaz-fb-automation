import os
import tempfile
import re
from trend_scout import get_single_trending_product, get_all_trending_products
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def process_single_product(category_name, product_url):
    print(f"\n==================================================")
    print(f"Processing Category: [{category_name}]")
    print(f"Product URL: {product_url}")
    print(f"==================================================")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 1. Scrape data and download uncompressed HD photos from ZIP
        title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
        print(f"Extracted Title: {title} | Price: PKR {selling_price} | HD Images: {len(image_paths)}")

        # 2. Generate multi-platform AI copy with key rotation/failover
        print("Generating high-converting social media copy via Gemini...")
        copy_dict = generate_copy(title, selling_price, raw_details)

        # 3. Build independent PDF for THIS category only
        clean_file_title = sanitize_filename(f"{category_name}_{title}")
        local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
        print(f"Compiling PDF for {category_name}...")
        build_pdf(f"[{category_name.upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path)

        # 4. Upload the separate PDF to Google Drive
        upload_pdf(local_pdf_path, clean_file_title)
        print(f"SUCCESS: Completed and uploaded independent PDF for '{category_name}'!")
        
    except Exception as e:
        print(f"ERROR processing category '{category_name}': {e}")

def main():
    # Detect if triggered automatically by schedule or manually by user click
    event_name = os.getenv("GITHUB_EVENT_NAME", "schedule")
    print(f"Workflow Trigger Event: {event_name}")

    if event_name == "workflow_dispatch":
        print("\n=== MANUAL TRIGGER DETECTED: Processing ALL 5 Categories Instantly ===")
        all_products = get_all_trending_products()
        for category_name, product_url in all_products.items():
            process_single_product(category_name, product_url)
    else:
        print("\n=== SCHEDULED TRIGGER DETECTED: Processing Single Rotational Category ===")
        category_name, product_url = get_single_trending_product()
        process_single_product(category_name, product_url)

    print("\n=== PIPELINE RUN COMPLETED ===")

if __name__ == "__main__":
    main()
