import datetime
from scraper import scrape_products
from ai_generator import generate_product_seo
from history_manager import is_already_processed, mark_as_processed
from drive_uploader import upload_product_folder

KEYWORDS = ["women shoes heels sneakers", "men shoes sneakers loafers"]

def run():
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"👟 Running Shoes Pipeline for {today_str}")
    
    for kw in KEYWORDS:
        print(f"\n🔍 Searching Markaz for: {kw}")
        for product in scrape_products(kw, max_items=5):
            p_id = product.get("id") or product.get("title")
            if is_already_processed(p_id):
                continue
            
            seo = generate_product_seo(product)
            upload_product_folder(today_str, product['title'], product['image_paths'], seo['title'], seo['price'], seo['description'])
            mark_as_processed(p_id)

if __name__ == "__main__":
    run()
