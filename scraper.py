import os
import io
import zipfile
import requests
from bs4 import BeautifulSoup
from PIL import Image

def download_and_extract_markaz_media(media_url):
    """
    Downloads real product media from Markaz (ZIP archive or direct images) 
    and extracts every photo into clean .jpg files.
    """
    os.makedirs("/tmp/scraped_images", exist_ok=True)
    saved_image_paths = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.markaz.app/"
    }
    
    try:
        print(f"📥 Downloading live media from Markaz...")
        response = requests.get(media_url, headers=headers, timeout=30)
        if response.status_code == 200:
            content = response.content
            # Check if it's a ZIP file (Download Media package)
            if b"PK\x03\x04" in content[:4] or zipfile.is_zipfile(io.BytesIO(content)):
                print("📦 Unzipping Markaz media package...")
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    for filename in z.namelist():
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            try:
                                img_data = z.read(filename)
                                img = Image.open(io.BytesIO(img_data))
                                if img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                local_path = os.path.join("/tmp/scraped_images", f"live_img_{len(saved_image_paths)+1}.jpg")
                                img.save(local_path, "JPEG", quality=95)
                                saved_image_paths.append(local_path)
                            except Exception as e:
                                print(f"⚠️ Skipped image {filename}: {e}")
            else:
                # Direct image file
                img = Image.open(io.BytesIO(content))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                local_path = os.path.join("/tmp/scraped_images", "live_img_1.jpg")
                img.save(local_path, "JPEG", quality=95)
                saved_image_paths.append(local_path)
    except Exception as e:
        print(f"❌ Error downloading media: {e}")
        
    return saved_image_paths

def scrape_product_from_url(product_url):
    """
    Scrapes a live Markaz product page URL, extracts real title, price, 
    overview highlights, and downloads real media.
    """
    print(f"🔍 Scraping live Markaz URL: {product_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.markaz.app/"
    }
    
    try:
        res = requests.get(product_url, headers=headers, timeout=25)
        if res.status_code != 200:
            print(f"❌ Failed to reach URL. Status: {res.status_code}")
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Extract live title
        title_elem = soup.find('h1') or soup.find('h3')
        title = title_elem.text.strip() if title_elem else "Markaz Product"
        
        # 2. Extract live price
        price = "2000"
        price_elem = soup.find(string=lambda t: t and 'PKR' in t)
        if price_elem:
            digits = ''.join(filter(str.isdigit, price_elem))
            if digits and len(digits) <= 6:
                price = digits
                
        # 3. Extract product overview highlights
        highlights = []
        for p in soup.find_all(['li', 'p', 'div']):
            text = p.text.strip()
            if text and ("FABRIC:" in text or "PATTERN:" in text or "PIECES:" in text or "INCLUDES:" in text or "SKU:" in text):
                if text not in highlights:
                    highlights.append(text)
                    
        description = "\n".join(highlights) if highlights else f"{title}\nHigh quality product from Markaz. Cash on Delivery available."
        
        # 4. Extract Product ID from URL
        product_id = product_url.rstrip('/').split('/')[-1]
        
        # 5. Locate download media link or product image links on page
        media_link = product_url
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'zip' in href or 'media' in href or 'download' in href.lower():
                media_link = "https://www.markaz.app" + href if href.startswith('/') else href
                break
                
        # Scrape image URLs directly from page if zip link isn't standalone
        page_image_urls = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and ('product' in src or 'upload' in src or 'images' in src):
                if src.startswith('/'):
                    src = "https://www.markaz.app" + src
                if src not in page_image_urls:
                    page_image_urls.append(src)
                    
        # Download images
        image_paths = []
        if media_link and media_link != product_url:
            image_paths = download_and_extract_markaz_media(media_link)
            
        if not image_paths and page_image_urls:
            for idx, img_url in enumerate(page_image_urls[:6], start=1):
                try:
                    img_res = requests.get(img_url, headers=headers, timeout=10)
                    if img_res.status_code == 200:
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        path = os.path.join("/tmp/scraped_images", f"live_img_{idx}.jpg")
                        img.save(path, "JPEG", quality=95)
                        image_paths.append(path)
                except:
                    pass

        if not image_paths:
            print("⚠️ No images found for this product.")
            return None

        return {
            "id": product_id,
            "title": title,
            "price": price,
            "description": description,
            "product_url": product_url,
            "image_paths": image_paths
        }
        
    except Exception as e:
        print(f"❌ Error scraping live product URL: {e}")
        return None

def scrape_products(category_name, max_items=1):
    """
    Directly scrapes live Markaz product URLs for the given category.
    """
    print(f"🔍 Live scraping Markaz catalog for category: {category_name}")
    
    # Configure your live Markaz product URLs here per category
    category_live_urls = {
        "unstitched": [
            "https://www.markaz.app/shop/product/winter-collection-dhanak-3-piece-unstitched-suit/763861"
        ],
        "stitched": [
            # Add live Markaz stitched product URL here when ready
        ],
        "bags": [
            # Add live Markaz bag product URL here when ready
        ],
        "shoes": [
            # Add live Markaz shoe product URL here when ready
        ]
    }

    urls_to_scrape = category_live_urls.get(category_name.lower(), [])
    matched_products = []
    
    for url in urls_to_scrape[:max_items]:
        product_data = scrape_product_from_url(url)
        if product_data:
            matched_products.append(product_data)
            
    return matched_products
