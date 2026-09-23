import os
import tempfile
import re
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

CATEGORY_NAME = "Girl Skincare Beauty Kit Serum"
PRODUCT_URL = "https://www.markaz.app/product/vitamin-c-face-serum-for-glowing-skin-pakistan/715900"

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print(f"=== Processing Category: {CATEGORY_NAME} ===")
    temp_dir = tempfile.mkdtemp()
    
    title, selling_price, raw_details, image_paths = download_and_extract_media(PRODUCT_URL, temp_dir)
    print(f"Title: {title} | Price: PKR {selling_price} | Images: {len(image_paths)}")

    copy_dict = generate_copy(title, selling_price, raw_details)

    clean_file_title = sanitize_filename(f"{CATEGORY_NAME}_{title}")
    local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
    
    build_pdf(f"[{CATEGORY_NAME.upper()}] {title}", selling_price, copy_dict, image_paths, local_pdf_path)
    upload_pdf(local_pdf_path, clean_file_title)
    print(f"SUCCESS: {CATEGORY_NAME} PDF generated and uploaded!")

if __name__ == "__main__":
    main()
