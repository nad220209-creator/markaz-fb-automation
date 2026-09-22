import os
import json
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Your 5 main target categories
TARGET_CATEGORIES = [
    "Baby Suit",
    "Women Handbag",
    "Girl Skincare Beauty Kit Serum",
    "Shoes",
    "Women Unstitched Lawn Suit"
]

def find_best_resembling_product(category_name):
    """
    Acts like an intelligent scanner:
    1. Scrapes live product listings from Markaz for the given category.
    2. Uses Gemini AI to analyze titles & descriptions to find the item 
       that best matches current high-end Punjab under-35 trends (resemblance match).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=str(api_key).strip("[]'\" "))

    search_query = category_name
    if category_name == "Shoes":
        search_query = "Women Khussa Heels Sandals"  # Specific elite trend focus for Punjab youth
    elif category_name == "Women Handbag":
        search_query = "Women Luxury Handbag Shoulder Bag"

    print(f"[{category_name}] Scouting trending items and scanning Markaz catalog for best resemblance...")
    search_url = f"https://www.markaz.app/shop/home-page/{requests.utils.quote(search_query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    scraped_products = []
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Find product cards / links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    full_url = "https://www.markaz.app" + href if href.startswith("/") else href
                    # Extract title text if nearby
                    title_text = a.get_text().strip()
                    if len(title_text) > 5:
                        scraped_products.append({"title": title_text, "url": full_url})
    except Exception as e:
        print(f"Notice scanning Markaz catalog for {category_name}: {e}")

    # If live catalog scan found options, let Gemini pick the closest resembling trending product
    if scraped_products and api_key:
        try:
            print(f"Found {len(scraped_products)} candidates on Markaz. Running AI resemblance scan...")
            candidate_titles = [f"{i}. {p['title']}" for i, p in enumerate(scraped_products[:20])]
            
            prompt = f"""
You are an expert e-commerce buyer for elite under-35 consumers in Punjab, Pakistan (Lahore/Islamabad lifestyle).
Target Category: {category_name}
Here is a list of available products found on Markaz:
{json.dumps(candidate_titles, indent=2)}

Select the ONE product from the list that best matches a highly trending, premium item for this demographic (e.g., most stylish, highest demand resemblance).
Return ONLY the exact index number (integer) of your choice. Return just the number, nothing else.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            match_idx = int(re.search(r'\d+', response.text).group())
            if 0 <= match_idx < len(scraped_products):
                selected = scraped_products[match_idx]
                print(f"AI Resemblance Match Found -> Selected: '{selected['title']}' | URL: {selected['url']}")
                return selected['url']
        except Exception as ai_err:
            print(f"Notice during AI resemblance selection: {ai_err}")

    # Fallback default verified URLs if live matching encounters any block
    fallback_map = {
        "Baby Suit": "https://www.markaz.app/shop/product/baby-suit-set-soft-blended-3-pcs-newborn/96520",
        "Women Handbag": "https://www.markaz.app/shop/product/womens-black-pu-leather-3pcs-handbag-set/715800",
        "Girl Skincare Beauty Kit Serum": "https://www.markaz.app/shop/product/vitamin-c-face-serum-for-glowing-skin-pakistan/715900",
        "Shoes": "https://www.markaz.app/shop/product/stylish-casual-sneakers-shoes-for-women/716000",
        "Women Unstitched Lawn Suit": "https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844"
    }
    fallback_url = fallback_map.get(category_name, "https://www.markaz.app/shop/product/multicolor-floral-lawn-kurta-pajama-set-for-women/715844")
    print(f"Using verified fallback URL for {category_name}: {fallback_url}")
    return fallback_url

def get_single_trending_product():
    """Rotational scheduled run: picks 1 category per run (5 times a day)."""
    current_hour = datetime.utcnow().hour
    hour_to_index = {3: 0, 7: 1, 11: 2, 15: 3, 19: 4}
    idx = hour_to_index.get(current_hour, datetime.utcnow().day % len(TARGET_CATEGORIES))
    category = TARGET_CATEGORIES[idx]
    url = find_best_resembling_product(category)
    return category, url

def get_all_trending_products():
    """Manual run: scans and processes all 5 categories instantly."""
    print("Manual Trigger Mode -> Scanning and matching all 5 categories...")
    category_urls = {}
    for category in TARGET_CATEGORIES:
        url = find_best_resembling_product(category)
        category_urls[category] = url
    return category_urls
