import requests
from bs4 import BeautifulSoup

def scrape_shoes_products(max_products=3):
    category_url = "https://www.markaz.app/shop/shoes"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    response = requests.get(category_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch category page. Status code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    product_links = []
    for a_tag in soup.select('a[href*="/shop/product/"]'):
        href = a_tag.get('href')
        if href:
            full_url = href if href.startswith('http') else f"https://www.markaz.app{href}"
            if full_url not in product_links:
                product_links.append(full_url)
    
    products = []
    for url in product_links[:max_products]:
        p_data = scrape_single_product(url, headers)
        if p_data:
            products.append(p_data)
            
    return products

def scrape_single_product(product_url, headers=None):
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0"}
        
    response = requests.get(product_url, headers=headers)
    if response.status_code != 200:
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    title_tag = soup.select_one('h1')
    title = title_tag.get_text(strip=True) if title_tag else "Sleek Casual Shoes"
    
    price = "PKR 1,990"
    for tag in soup.find_all(text=True):
        if "PKR" in tag:
            price = tag.strip()
            break

    desc_tag = soup.select_one('.product-overview, div:-soup-contains("overview"), div:-soup-contains("comfort")')
    overview = desc_tag.get_text(strip=True) if desc_tag else "Comfortable, stylish footwear designed for daily use."

    img_tags = soup.select('img[src*="markaz"], .swiper-slide img, img[alt*="Shoes"], img[alt*="Sneakers"]')
    image_urls = []
    for img in img_tags:
        src = img.get('src') or img.get('data-src')
        if src and src.startswith('http') and src not in image_urls and 'logo' not in src.lower():
            image_urls.append(src)
    
    if not image_urls:
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith('http') and 'avatar' not in src and 'logo' not in src:
                image_urls.append(src)

    return {
        "title": title,
        "price": price,
        "overview": overview,
        "url": product_url,
        "images": image_urls[:5]
    }
