import datetime
from scraper import scrape_products
from ai_generator import generate_product_seo
from history_manager import is_already_processed, mark_as_processed
from drive_uploader import upload_product_folder

# Exactly 1 product per key category per run
TARGET_CATEGORIES = [
    "unstitched",
    "stitched",
    "bags",
    "shoes"
]

def run_pipeline():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Starting Markaz Automated Media Pipeline for Date: {today_str}")
    
    total_uploaded = 0
    
    for category in TARGET_CATEGORIES:
        print(f"\n🔍 Processing Category: {category.upper()}")
        try:
            products = scrape_products(category, max_items=1)
        except Exception as e:
            print(f"⚠️ Scraper error for category '{category}': {e}")
            continue
        
        for product in products:
            try:
                p_id = product.get("id")
                if not p_id or is_already_processed(p_id):
                    print(f"⏭️ Skipping already processed product: {product.get('title')}")
                    continue
                    
                print(f"✨ Running AI Brain for: {product['title']}")
                seo_data = generate_product_seo(product)
                
                print(f"📁 Uploading extracted media zip and details to Google Drive...")
                upload_product_folder(
                    date_str=today_str,
                    product_id=p_id,
                    product_title=product['title'],
                    image_paths=product['image_paths'],
                    title=seo_data['title'],
                    price=seo_data['price'],
                    description=seo_data['description']
                )
                
                mark_as_processed(p_id)
                total_uploaded += 1
            except Exception as e:
                print(f"❌ Error processing product in {category}: {e}")
                
    print(f"\n🎉 Pipeline Finished! Successfully uploaded {total_uploaded} unique product folders with extracted zip media.")

if __name__ == "__main__":
    run_pipeline()
