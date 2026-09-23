import requests
from bs4 import BeautifulSoup

def search_live_markaz_product(search_query):
    """
    Automates the Markaz search bar method: 
    Takes a search term, queries Markaz live, and extracts the first top-matching product URL.
    """
    encoded_query = requests.utils.quote(search_query)
    search_url = f"https://www.markaz.app/shop/search?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Searching Markaz live for: '{search_query}' -> URL: {search_url}")
    try:
        res = requests.get(search_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/product/" in href:
                    product_url = "https://www.markaz.app" + href if href.startswith("/") else href
                    print(f"Found live product match: {product_url}")
                    return product_url
    except Exception as e:
        print(f"Search error for '{search_query}': {e}")
        
    return None
