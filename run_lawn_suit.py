import os
import tempfile
import re
import traceback
from search_helper import get_next_trending_product
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

CATEGORY_NAME = "Women Unstitched Lawn Suit"
SEARCH_QUERY = "Women Unstitched Lawn Suit Printed"

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print(f"=== Processing Category: {CATEGORY_NAME} ===")
    temp_dir = tempfile.mkdtemp()
    try:
        product_url = get_next_trending_product(SEARCH_QUERY)
        if not product_url:
            raise ValueError(f"No products found for query: {SEARCH_QUERY}")

        title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
        print(f"Title: {title} | Selling Price: PKR {selling_price} | Images: {len(image_paths)}")

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
