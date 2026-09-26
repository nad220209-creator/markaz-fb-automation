import datetime
from scraper import scrape_shoes_products
from ai_generator import generate_optimized_content
from history_manager import load_history, is_processed, mark_processed

WHATSAPP_LINK = "https://wa.me/923374633605"

def main():
    print("=" * 60)
    print("MARKAZ SHOES MANUAL-ASSIST PIPELINE")
    print(f"Run Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    history = load_history()
    products = scrape_shoes_products(max_products=3)
    
    if not products:
        print("No products found.")
        return

    for i, product in enumerate(products, start=1):
        url = product['url']
        if is_processed(url, history):
            print(f"\n[Skipping Already Processed]: {product['title']}")
            continue

        print(f"\n[PRODUCT #{i}]")
        print(f"Title: {product['title']}")
        print(f"Price: {product['price']}")
        print(f"Direct Markaz Link: {url}")
        print("Images Found:", len(product['images']))
        for img in product['images']:
            print(f"  - {img}")

        print("\n--- GENERATING AI SALES COPY ---")
        ai_output = generate_optimized_content(
            product_title=product['title'],
            raw_overview=product['overview'],
            price=product['price']
        )
        print(ai_output)
        
        print("\n--- ORDER INFO ---")
        print(f"WhatsApp Order Link: {WHATSAPP_LINK}")
        print("=" * 60)

        # Mark as processed so next run pulls new products
        mark_processed(url, history)

if __name__ == "__main__":
    main()
