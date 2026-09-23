import os
import json
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from history_manager import load_history, add_to_history

def get_next_trending_product(category_query):
    """
    Scouts live Markaz search results, filters out already processed URLs using memory,
    and uses Gemini AI to select the highest-demand product for Lahore, Islamabad, Rawalpindi, and Faisalabad.
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

    # Filter out already processed products using history memory
    processed_urls = load_history()
    fresh_candidates = [c for c in candidates if c["url"] not in processed_urls]
    
    if not fresh_candidates:
        print("Notice: All current search results have been processed already! Resetting history cache...")
        fresh_candidates = candidates

    # Use Gemini AI with metropolitan Pakistan context (Lahore, Islamabad, Rawalpindi, Faisalabad)
    api_key = os.getenv("GEMINI_API_KEY")
    selected_product = fresh_candidates[0]

    if api_key and len(fresh_candidates) > 1:
        try:
            genai.configure(api_key=str(api_key).strip("[]'\" "))
            candidate_list_text = [f"{i}. {item['title']}" for i, item in enumerate(fresh_candidates[:15])]
            
            prompt = f"""
You are an expert e-commerce trend analyst for metropolitan consumer demand in major Pakistani cities (Lahore, Islamabad, Rawalpindi, Faisalabad).
Category: {category_query}
Here are available fresh product candidates from Markaz search results:
{json.dumps(candidate_list_text, indent=2)}

Analyze what young, fashionable buyers in Lahore, Islamabad, Rawalpindi, and Faisalabad are currently demanding most on social media. Select the ONE product that has the highest commercial demand and trending appeal.
Return ONLY the integer index (e.g., 0, 1, 2) of your choice, nothing else.
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            match_idx = int(re.search(r'\d+', response.text).group())
            if 0 <= match_idx < len(fresh_candidates):
                selected_product = fresh_candidates[match_idx]
        except Exception as ai_err:
            print(f"AI trend selection notice: {ai_err}")

    # Save to memory history
    add_to_history(selected_product["url"])
    print(f"Selected High-Demand Trend Product -> Title: '{selected_product['title']}' | URL: {selected_product['url']}")
    return selected_product["url"]
