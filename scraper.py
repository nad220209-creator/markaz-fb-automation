import requests
from bs4 import BeautifulSoup

def scrape_shoes_products(max_products=3):
    category_url = "https://www.markaz.app/shop/shoes"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        print(f"Fetching category URL: {category_url}")
        response = requests.get(category_url, headers=headers, timeout=15)
        print(f"Category page status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: Blocked or failed to fetch category page. Status: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        product_links = []
        for a_tag in soup.select('a[href*="/shop/product/"]'):
            href = a_tag.get('href')
            if href:
                full_url = href if href.startswith('http') else f"https://www.markaz.app{href}"
                if full_url not in product_links:
                    product_links.append(full_url)
        
        print(f"Found {len(product_links)} product links.")
        products = []
        for url in product_links[:max_products]:
            p_data = scrape_single_product(url, headers)
            if p_data:
                products.append(p_data)
                
        return products
    except Exception as e:
        print(f"Exception in scrape_shoes_products: {e}")
        return []

def scrape_single_product(product_url, headers=None):
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
        
    try:
        response = requests.get(product_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch product URL {product_url}, status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.select_one('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Sleek Casual Shoes"
        
        price = "PKR 1,990"
        price_tag = soup.find(string=lambda t: t and "PKR" in t)
        if price_tag:
            price = price_tag.strip()

        overview = "Comfortable, stylish footwear designed for daily use."
        desc_tag = soup.select_one('.product-overview')
        if desc_tag:
            overview = desc_tag.get_text(strip=True)

        img_tags = soup.select('img[src*="markaz"], .swiper-slide img, img')
        image_urls = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http') and src not in image_urls and 'logo' not in src.lower() and 'avatar' not in src.lower():
                image_urls.append(src)

        return {
            "title": title,
            "price": price,
            "overview": overview,
            "url": product_url,
            "images": image_urls[:5]
        }
    except Exception as e:
        print(f"Exception scraping product {product_url}: {e}")
        return None
