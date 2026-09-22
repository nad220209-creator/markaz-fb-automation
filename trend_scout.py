import os
import json
import re
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

def find_trending_product_url():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing!")
    
    genai.configure(api_key=str(api_key).strip("[]'\" "))
    
    prompt = """
    You are an expert e-commerce trend analyst for elite under-35 consumers in Punjab, Pakistan (Lahore, Islamabad, DHA/Gulberg lifestyle, active on Instagram and TikTok).
    Identify a top-selling, high-demand fashion product category currently trending for this group that is widely available on Markaz app (e.g., luxury unstitched lawn, premium men executive wash & wear, chic festive pret).
    Give me a precise search keyword phrase to find this product on Markaz.
    Return ONLY a valid JSON object with key "search_query". Example: {"search_query": "luxury lawn unstitched 3 piece"}
    """
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    
    query = "unstitched wash and wear plain suit"  # Default fallback
    try:
        clean_res = response.text.strip()
        clean_res = re.sub(r'^```json\s*', '', clean_res, flags=re.IGNORECASE)
        clean_res = re.sub(r'^```\s*', '', clean_res).strip()
        data = json.loads(clean_res)
        if "search_query" in data:
            query = data["search_query"]
    except Exception:
        pass
        
    print(f"AI Trend Scout selected trending query for Punjab elite demographic: '{query}'")
    
    # Search Markaz catalog for this query to get a live product URL
    search_url = f"https://www.markaz.app/shop?search={requests.utils.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    full_url = "https://www.markaz.app" + href if href.startswith("/") else href
                    print(f"Discovered trending product URL: {full_url}")
                    return full_url
    except Exception as e:
        print(f"Notice during catalog search: {e}")
        
    # Fallback to a verified top elite product if search fails
    return "https://www.markaz.app/shop/product/men-s-unstitched-wash-and-wear-plain-suit/743822"
