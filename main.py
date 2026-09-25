import datetime
from scraper import scrape_products
from ai_generator import generate_product_seo
from history_manager import is_already_processed, mark_as_processed
from drive_uploader import upload_product_folder

# High-demand categories: Shoes, Bags, and Seasonal Clothes
TARGET_KEYWORDS = [
    "women shoes heels sneakers",
    "men shoes sneakers loafers",
    "women shoulder bag crossbody handbag",
    "women luxury handbags",
    "seasonal winter autumn clothes stitched"
]

def run_pipeline():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🚀 Starting Cloud Pipeline for Date: {today_str}")
    
    total_uploaded = 0
    
    for keyword in TARGET_KEYWORDS:
        print(f"\n🔍 Searching Markaz for: {keyword}")
        try:
            products = scrape_products(keyword, max_items=3)
        except Exception as e:
            print(f"⚠️ Scraper error for keyword '{keyword}': {e}")
            continue
        
        if not products:
            print(f"⚠️ No products found for: {keyword}")
            continue
            
        for product in products:
            try:
                p_id = product.get("id") or product.get("title")
                if not p_id:
                    continue
                    
                if is_already_processed(p_id):
                    print(f"⏭️ Skipping already processed: {product.get('title', 'Unknown')}")
                    continue
                    
                print(f"✨ Generating AI SEO & Roman Urdu description for: {product.get('title')}")
                seo_data = generate_product_seo(product)
                
                print(f"📁 Uploading folder to Google Drive...")
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
                print(f"❌ Error processing individual product: {e}")
                continue
                
    print(f"\n🎉 Pipeline Finished! Successfully uploaded {total_uploaded} new products to Google Drive.")

if __name__ == "__main__":
    run_pipeline()
