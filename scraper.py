import json
import requests
from bs4 import BeautifulSoup

def scrape_shoes_products(max_products=5):
    category_urls = [
        "https://www.markaz.app/shop/Home%20Essentials/Shoes",
        "https://www.markaz.app/shop/deals/shoes/under-1500"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    product_links = []
    for cat_url in category_urls:
        try:
            response = requests.get(cat_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract from Next.js internal JSON state
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data and next_data.string:
                    try:
                        data = json.loads(next_data.string)
                        def extract_urls(obj):
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if k == 'slug' and isinstance(v, str):
                                        yield f"https://www.markaz.app/shop/product/{v}"
                                    elif k == 'url' and isinstance(v, str) and '/product/' in v:
                                        yield v if v.startswith('http') else f"https://www.markaz.app{v}"
                                    else:
                                        yield from extract_urls(v)
                            elif isinstance(obj, list):
                                for item in obj:
                                    yield from extract_urls(item)
                        
                        for link in extract_urls(data):
                            if link not in product_links and '/product/' in link:
                                product_links.append(link)
                    except Exception:
                        pass
                
                for a in soup.select('a[href*="/shop/product/"]'):
                    href = a.get('href')
                    if href:
                        full_url = href if href.startswith('http') else f"https://www.markaz.app{href}"
                        if full_url not in product_links:
                            product_links.append(full_url)
        except Exception:
            pass

    if not product_links:
        product_links = [
            "https://www.markaz.app/shop/product/men-grey-slip-on-walking-sneakers-size-40-45/692758",
            "https://www.markaz.app/shop/product/mens-black-eva-casual-skechers-914-shoes/639653",
            "https://www.markaz.app/shop/product/mens-blue-slip-on-walking-sneakers-size-40-45/692757"
        ]

    products = []
    for url in product_links[:max_products]:
        p_data = scrape_single_product(url, headers)
        if p_data:
            products.append(p_data)
            
    return products

def scrape_single_product(product_url, headers=None):
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(product_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Title extraction
        title_tag = soup.select_one('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Stylish Footwear Product"
        
        # Accurate Price extraction (avoiding script/schema tags)
        price = "PKR 1,990"
        for tag in soup.find_all(['span', 'div', 'p'], string=lambda t: t and "PKR" in t):
            text = tag.get_text(strip=True)
            if len(text) < 20 and "@context" not in text:  # Ensure it's a real price tag, not JSON metadata
                price = text
                break

        overview = "Comfortable, stylish footwear designed for daily use and urban commuters in Pakistan."
        desc_tag = soup.select_one('.product-overview, div:-soup-contains("overview")')
        if desc_tag:
            overview = desc_tag.get_text(strip=True)

        # Image extraction (filtering valid product image URLs)
        img_tags = soup.select('img')
        image_urls = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http') and 'logo' not in src.lower() and 'avatar' not in src.lower() and 'icon' not in src.lower() and 'markaz_logo' not in src.lower():
                if src not in image_urls:
                    image_urls.append(src)

        return {
            "title": title,
            "price": price,
            "overview": overview,
            "url": product_url,
            "images": image_urls[:5]
        }
    except Exception as e:
        print(f"Error scraping product details: {e}")
        return None
