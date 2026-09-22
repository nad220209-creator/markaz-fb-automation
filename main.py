import os
import tempfile
import re
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

PRODUCT_URLS = [
    "[https://www.markaz.app/shop/product/men-s-unstitched-wash-and-wear-plain-suit/743822](https://www.markaz.app/shop/product/men-s-unstitched-wash-and-wear-plain-suit/743822)"
]

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    for product_url in PRODUCT_URLS:
        print(f"\n--- Processing Product URL: {product_url} ---")
        temp_dir = tempfile.mkdtemp()
        
        # 1. Scrape data and download all uncompressed ZIP media images
        title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
        print(f"Extracted title: {title}, Price: {selling_price}, Images count: {len(image_paths)}")

        # 2. Generate multi-platform AI copy
        print("Generating AI social media copy...")
        copy_dict = generate_copy(title, selling_price, raw_details)

        # 3. Build collective PDF with tabular rows/columns and uncompressed HD images
        clean_file_title = sanitize_filename(title)
        local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
        print("Compiling collective PDF document...")
        build_pdf(title, selling_price, copy_dict, image_paths, local_pdf_path)

        # 4. Upload final PDF to Google Drive
        upload_pdf(local_pdf_path, clean_file_title)
        print(f"SUCCESS: Pipeline completed for '{title}'!")

if __name__ == "__main__":
    main()
