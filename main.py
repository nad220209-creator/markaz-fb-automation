import os
import json
import datetime
from scraper import scrape_shoes_products
from ai_generator import generate_optimized_content
from history_manager import load_history, is_processed, mark_processed

WHATSAPP_LINK = "https://wa.me/923374633605"
JSON_FILE = "products.json"
MD_FILE = "PRODUCTS_CATALOG.md"

def load_json_catalog():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_json_catalog(catalog):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=4, ensure_ascii=False)

def update_markdown_catalog(catalog):
    md_content = f"# 👟 Markaz Shoes Facebook Marketplace Catalog\n\n"
    md_content += f"*Total Products: {len(catalog)}* | *Last Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    md_content += "---\n\n"

    for idx, item in enumerate(catalog, start=1):
        md_content += f"## [{idx}] {item['title']}\n\n"
        md_content += f"- **Price:** {item['price']}\n"
        md_content += f"- **SEO Keywords:** `{item['keywords']}`\n"
        md_content += f"- **Direct Product Link:** [View on Markaz]({item['url']})\n"
        md_content += f"- **WhatsApp Order Link:** [Order Now]({item['whatsapp_link']})\n\n"
        
        md_content += f"### 📝 Roman Urdu Description:\n```text\n{item['description']}\n```\n\n"
        
        md_content += f"### 📸 Product Images:\n"
        for img in item['images']:
            md_content += f"- ![{item['title']}]({img})\n"
        
        md_content += "\n---\n\n"

    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)

def main():
    print("Starting Markaz Dynamic Shoes Catalog Generator...")
    history = load_history()
    existing_catalog = load_json_catalog()
    existing_urls = {item['url'] for item in existing_catalog}
    
    # Scrape up to 5 fresh products per run
    products = scrape_shoes_products(max_products=5)
    if not products:
        print("No products found.")
        return

    new_items_added = False

    for product in products:
        url = product['url']
        if is_processed(url, history) or url in existing_urls:
            print(f"Skipping already processed product: {product['title']}")
            continue

        print(f"Processing new product & generating SEO copy: {product['title']}")
        ai_data = generate_optimized_content(
            product_title=product['title'],
            raw_overview=product['overview'],
            price=product['price']
        )

        catalog_entry = {
            "title": ai_data['title'],
            "price": product['price'],
            "keywords": ai_data['keywords'],
            "description": ai_data['description'],
            "url": url,
            "whatsapp_link": WHATSAPP_LINK,
            "images": product['images'],
            "date_added": datetime.datetime.now().strftime("%Y-%m-%d")
        }

        existing_catalog.insert(0, catalog_entry)
        mark_processed(url, history)
        new_items_added = True

    if new_items_added:
        save_json_catalog(existing_catalog)
        update_markdown_catalog(existing_catalog)
        print(f"Successfully added new items! Total catalog size: {len(existing_catalog)}")
    else:
        print("All scraped items were already in your catalog.")

if __name__ == "__main__":
    main()
