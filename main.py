import os
import tempfile
import re
from trend_scout import find_trending_product_url
from scraper import download_and_extract_media
from ai_generator import generate_copy
from pdf_builder import build_pdf
from drive_uploader import upload_pdf

def sanitize_filename(name):
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    return clean if clean else "Markaz_Product"

def main():
    print("=== STARTING AI TREND-DRIVEN MARKAZ PIPELINE ===")
    
    # 1. Intelligently discover what is trending for elite Punjab youth
    trending_url = find_trending_product_url()
    print(f"\n--- Processing Discovered Product URL: {trending_url} ---")
    
    temp_dir = tempfile.mkdtemp()
    
    # 2. Scrape data and download exact uncompressed HD photos from ZIP
    title, selling_price, raw_details, image_paths = download_and_extract_media(trending_url, temp_dir)
    print(f"Extracted Title: {title} | Price: PKR {selling_price} | HD Images: {len(image_paths)}")

    # 3. Generate multi-platform AI copy with rotation/failover
    print("Generating high-converting social media copy via Gemini...")
    copy_dict = generate_copy(title, selling_price, raw_details)

    # 4. Build collective PDF with tabular rows/columns and uncompressed HD photos
    clean_file_title = sanitize_filename(title)
    local_pdf_path = os.path.join(temp_dir, f"{clean_file_title}.pdf")
    print("Compiling collective PDF document...")
    build_pdf(title, selling_price, copy_dict, image_paths, local_pdf_path)

    # 5. Upload final PDF to Google Drive
    upload_pdf(local_pdf_path, clean_file_title)
    print(f"SUCCESS: Intelligent trend pipeline completed for '{title}'!")

if __name__ == "__main__":
    main()
