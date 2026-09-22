import os
import tempfile
import re
from trend_scout import get_products_for_all_categories
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print("=== STARTING MULTI-CATEGORY BATCH PIPELINE (5 SEPARATE PDFs) ===")
    
    # 1. Get product URLs for all 5 categories
    category_products = get_products_for_all_categories()
    
    if not category_products:
        print("Error: No product URLs were retrieved for any category.")
        return

    # 2. Process each category independently
    for category_name, product_url in category_products.items():
        print(f"\n==================================================")
        print(f"Processing Category: [{category_name}]")
        print(f"Product URL: {product_url}")
        print(f"==================================================")
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Scrape data and download exact uncompressed HD photos from ZIP
            title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
            print(f"Extracted Title: {title} | Price: PKR {selling_price} | HD Images: {len(image_paths)}")

            # Generate multi-platform AI copy with rotation/failover
            print("Generating high-converting social media copy via Gemini...")
            copy_dict = generate_copy(title, selling_price, raw_details)

            # Build collective PDF for THIS category only
            clean_file_title = sanitize_filename(f"{category_name}_{title}")
            local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
            print(f"Compiling PDF for {category_name}...")
            build_pdf(f"[{category_name.upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path)

            # Upload the separate PDF to Google Drive
            upload_pdf(local_pdf_path, clean_file_title)
            print(f"SUCCESS: Completed and uploaded independent PDF for '{category_name}'!")
            
        except Exception as e:
            print(f"ERROR processing category '{category_name}': {e}")
            continue

    print("\n=== ALL CATEGORY BATCH PIPELINES COMPLETED ===")

if __name__ == "__main__":
    main()
