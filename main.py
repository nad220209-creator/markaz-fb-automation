import datetime
from scraper import scrape_products
from ai_generator import generate_product_seo
from history_manager import is_already_processed, mark_as_processed
from drive_uploader import upload_product_folder

# Comprehensive search queries spanning Markaz categories
TARGET_KEYWORDS = [
    "womens unstitched winter collection dhanak lawn",
    "womens stitched cotton embroidered suit",
    "womens rexine textured handbag crossbody bag",
    "womens casual walking sneakers shoes"
]

def run_pipeline():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Starting Markaz Multi-Category Pipeline for Date: {today_str}")
    
    total_uploaded = 0
    
    for keyword in TARGET_KEYWORDS:
        print(f"\n🔍 Searching Markaz catalog for: {keyword}")
        try:
            products = scrape_products(keyword, max_items=2)
        except Exception as e:
            print(f"⚠️ Scraper error for '{keyword}': {e}")
            continue
        
        for product in products:
            try:
                p_id = product.get("id") or product.get("title")
                if not p_id or is_already_processed(p_id):
                    print(f"⏭️ Skipping already processed: {product.get('title')}")
                    continue
                    
                print(f"✨ Running AI Brain (Gemini) for: {product['title']}")
                seo_data = generate_product_seo(product)
                
                print(f"📁 Uploading organized package to Google Drive...")
                upload_product_folder(
                    date_str=today_str,
                    product_title=product['title'],
                    image_paths=product['image_paths'],
                    title=seo_data['title'],
                    price=seo_data['price'],
                    description=seo_data['description']
                )
                
                mark_as_processed(p_id)
                total_uploaded += 1
            except Exception as e:
                print(f"❌ Error processing product: {e}")
                
    print(f"\n🎉 Pipeline Finished! Successfully uploaded {total_uploaded} products to Google Drive.")

if __name__ == "__main__":
    run_pipeline()
