import tempfile
from scraper import download_and_extract_media
from ai_generator import generate_copy

PRODUCT_URLS = [
    "https://www.markaz.app/shop/product/men-s-unstitched-wash-and-wear-plain-suit/743822"
]

def test_pipeline():
    print("=== STARTING DIAGNOSTIC TEST RUN (No PDF / No Drive Upload) ===")
    for product_url in PRODUCT_URLS:
        try:
            print(f"\n[TEST] Testing scraping for: {product_url}")
            temp_dir = tempfile.mkdtemp()
            
            title, selling_price, raw_details, image_paths = download_and_extract_media(product_url, temp_dir)
            print(f"[SUCCESS] Scraped Title: {title}")
            print(f"[SUCCESS] Calculated Selling Price: PKR {selling_price}")
            print(f"[SUCCESS] Images Downloaded: {len(image_paths)} images found.")
            
            print("\n[TEST] Testing Gemini AI copy generation...")
            copy_dict = generate_copy(title, selling_price, raw_details)
            print("[SUCCESS] AI Copy Generated Successfully!")
            print("--- Sample Copy (FB Marketplace): ---")
            print(copy_dict.get("fb_marketplace", "N/A")[:300] + "...")
            
        except Exception as e:
            print(f"\n[ERROR DETECTED] Failed during test run: {e}")
            raise e
    print("\n=== DIAGNOSTIC TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_pipeline()
