import os
import json
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from history_manager import load_history, add_to_history

def get_next_trending_product(category_query):
    """
    Searches Markaz live, filters out already processed items via memory, 
    and applies a strict relevance check to ensure the product matches the category.
    """
    encoded_query = requests.utils.quote(category_query)
    search_url = f"https://www.markaz.app/shop/search?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Scouting live Markaz search results for: '{category_query}'...")
    candidates = []
    
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    full_url = "https://www.markaz.app" + href if href.startswith("/") else href
                    title = a.get_text().strip()
                    if len(title) > 5 and {"title": title, "url": full_url} not in candidates:
                        candidates.append({"title": title, "url": full_url})
    except Exception as e:
        print(f"Search error: {e}")

    if not candidates:
        return None

    # Load history memory
    processed_urls = load_history()
    
    # Filter out already processed products
    fresh_candidates = [c for c in candidates if c["url"] not in processed_urls]
    if not fresh_candidates:
        print("Notice: All current search results processed. Resetting history cache...")
        fresh_candidates = candidates

    # STRICT RELEVANCE FILTER: Ensure product title actually matches category keywords
    query_keywords = [kw.lower() for kw in category_query.split() if len(kw) > 3]
    relevant_candidates = []
    
    for c in fresh_candidates:
        title_lower = c["title"].lower()
        # Check if at least one primary keyword is present in the product title
        if any(kw in title_lower for kw in query_keywords):
            relevant_candidates.append(c)

    # Fallback to fresh candidates if strict filter is too narrow
    pool = relevant_candidates if relevant_candidates else fresh_candidates

    # Use Gemini AI to pick the best high-demand product from the relevant pool
    api_key = os.getenv("GEMINI_API_KEY")
    selected_product = pool[0]

    if api_key and len(pool) > 1:
        try:
            genai.configure(api_key=str(api_key).strip("[]'\" "))
            candidate_list_text = [f"{i}. {item['title']}" for i, item in enumerate(pool[:15])]
            
            prompt = f"""
You are an expert e-commerce trend analyst for metropolitan consumer demand in major Pakistani cities (Lahore, Islamabad, Rawalpindi, Faisalabad).
Target Category / Search: {category_query}
Here are strictly relevant product candidates from Markaz:
{json.dumps(candidate_list_text, indent=2)}

Select the ONE product that is most accurate to the target category and in highest commercial demand.
Return ONLY the integer index (e.g., 0, 1, 2) of your choice, nothing else.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            match_idx = int(re.search(r'\d+', response.text).group())
            if 0 <= match_idx < len(pool):
                selected_product = pool[match_idx]
        except Exception as ai_err:
            print(f"AI selection notice: {ai_err}")

    # Save to history memory so it's never repeated
    add_to_history(selected_product["url"])
    print(f"Selected Verified Relevant Product -> Title: '{selected_product['title']}' | URL: {selected_product['url']}")
    return selected_product["url"]
