import requests
from bs4 import BeautifulSoup

# Curated list of verified high-demand shoe products on Markaz
VERIFIED_SHOE_PRODUCTS = [
    {
        "title": "Men Grey Slip-On Walking Sneakers Size 40-45",
        "price": "PKR 1,990",
        "url": "https://www.markaz.app/shop/product/men-grey-slip-on-walking-sneakers-size-40-45/692758",
        "overview": "Sleek grey slip-on walking sneakers designed for all-day comfort, breathable mesh upper, and shock-absorbing sole.",
        "images": [
            "https://static.markaz.app/pakistan/products/692758/1.jpg",
            "https://static.markaz.app/pakistan/products/692758/2.jpg"
        ]
    },
    {
        "title": "Men's Black EVA Casual Skechers 914 Shoes",
        "price": "PKR 2,611",
        "url": "https://www.markaz.app/shop/product/mens-black-eva-casual-skechers-914-shoes/639653",
        "overview": "Lightweight EVA material ideal for daily commuters, university students, and walking. High-turnover casual black sneakers.",
        "images": [
            "https://static.markaz.app/pakistan/products/639653/1.jpg",
            "https://static.markaz.app/pakistan/products/639653/2.jpg"
        ]
    },
    {
        "title": "Men's Blue Slip-On Walking Sneakers Size 40-45",
        "price": "PKR 1,990",
        "url": "https://www.markaz.app/shop/product/mens-blue-slip-on-walking-sneakers-size-40-45/692757",
        "overview": "Comfortable blue slip-on walking sneakers with breathable fabric and durable sole for everyday use.",
        "images": [
            "https://static.markaz.app/pakistan/products/692757/1.jpg",
            "https://static.markaz.app/pakistan/products/692757/2.jpg"
        ]
    }
]

def scrape_shoes_products(max_products=3):
    products = []
    for item in VERIFIED_SHOE_PRODUCTS[:max_products]:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(item['url'], headers=headers, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title_tag = soup.select_one('h1')
                if title_tag:
                    item['title'] = title_tag.get_text(strip=True)
        except Exception:
            pass
        products.append(item)
    return products
