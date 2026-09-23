import os
import tempfile
import re
import traceback
from search_helper import search_live_markaz_product
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

CATEGORY_NAME = "Women Handbag"
SEARCH_KEYWORD = "Womens Black PU Leather 3Pcs Handbag Set"

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print(f"=== Processing Category: {CATEGORY_NAME} ===")
    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Automatically search Markaz live just like you do in your browser
        product_url = search_live_markaz_product(SEARCH_KEYWORD)
        if not product_url:
            raise ValueError(f"No live product found on Markaz for search: {SEARCH_KEYWORD}")

        # 2. Scrape the live product page & download uncompressed HD photos from ZIP
        title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
        print(f"Title: {title} | Price: PKR {selling_price} | Images: {len(image_paths)}")

        # 3. Generate AI copy, build PDF, and upload to Google Drive
        copy_dict = generate_copy(title, selling_price, raw_details)
        clean_file_title = sanitize_filename(f"{CATEGORY_NAME}_{title}")
        local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
        
        build_pdf(f"[{CATEGORY_NAME.upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path)
        upload_pdf(local_pdf_path, clean_file_title)
        print(f"SUCCESS: {CATEGORY_NAME} PDF generated and uploaded!")
    except Exception as e:
        print(f"ERROR in {CATEGORY_NAME}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
