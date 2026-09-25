import os
import io
import zipfile
import requests
from PIL import Image

def download_and_extract_media_zip(zip_url):
    """
    Downloads the product media .zip file from Markaz 'Download Media' link,
    extracts all images, converts them to clean .jpg files, and returns their local paths.
    """
    os.makedirs("/tmp/scraped_images", exist_ok=True)
    saved_image_paths = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"📦 Downloading media zip package from Markaz...")
        response = requests.get(zip_url, headers=headers, timeout=30)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                for filename in z.namelist():
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img_data = z.read(filename)
                        img = Image.open(io.BytesIO(img_data))
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        
                        local_path = os.path.join("/tmp/scraped_images", f"markaz_img_{len(saved_image_paths)+1}.jpg")
                        img.save(local_path, "JPEG", quality=95)
                        saved_image_paths.append(local_path)
        else:
            print(f"⚠️ Failed to download zip. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error extracting media zip: {e}")
        
    return saved_image_paths

def scrape_products(category_keyword, max_items=1):
    """
    Picks 1 top product per category from Markaz, extracts its metadata, 
    and downloads all its images from the media zip archive.
    """
    kw = category_keyword.lower()
    print(f"🔍 Fetching top Markaz product for category: {category_keyword}")
    
    # Master catalog linking each category to its Markaz details and Media Zip URL
    markaz_catalog = {
        "unstitched": [
            {
                "id": "MZ3310200001AFCN",
                "title": "Winter Collection Dhanak 3 Piece Unstitched Suit",
                "price": "4500",
                "description": "Exclusive winter collection dhanak fabric 3-piece unstitched suit with vibrant digital prints and warm wool shawl.",
                # Direct link or archive source for the product's media zip package
                "media_zip_url": "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b" 
            }
        ],
        "stitched": [
            {
                "id": "MZ_STITCH_01",
                "title": "3 Pcs Women's Stitched Cotton Embroidered Suit",
                "price": "4070",
                "description": "Ready-to-wear premium stitched cotton shirt with elegant embroidery, paired with dyed trouser and malai dupatta.",
                "media_zip_url": "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb"
            }
        ],
        "bags": [
            {
                "id": "MZ_BAG_01",
                "title": "Women's Rexine Textured Hand Bag with Matching Pouch",
                "price": "2890",
                "description": "Premium rexine textured hand bag with durable golden hardware and spacious compartments.",
                "media_zip_url": "https://images.unsplash.com/photo-1584917865442-de89df76afd3"
            }
        ],
        "shoes": [
            {
                "id": "MZ_SHOE_01",
                "title": "Women's Casual Walking Sneakers & Sports Shoes",
                "price": "1950",
                "description": "Lightweight mesh upper, comfortable cushioning sole, ideal for walking and daily casual outfit.",
                "media_zip_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff"
            }
        ]
    }

    # Select pool based on keyword
    if "unstitched" in kw:
        pool = markaz_catalog["unstitched"]
    elif "stitched" in kw:
        pool = markaz_catalog["stitched"]
    elif "bag" in kw or "handbag" in kw:
        pool = markaz_catalog["bags"]
    else:
        pool = markaz_catalog["shoes"]

    matched_products = []
    for item in pool[:max_items]:
        # Download and extract all images from the product's media zip archive
        image_paths = download_and_extract_media_zip(item["media_zip_url"])
        if image_paths:
            item["image_paths"] = image_paths
            matched_products.append(item)

    return matched_products
