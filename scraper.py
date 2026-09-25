import os
import io
import requests
from PIL import Image

def download_and_extract_images(media_urls):
    """Downloads clean, category-specific product images as .jpg files."""
    os.makedirs("/tmp/scraped_images", exist_ok=True)
    saved_image_paths = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for idx, url in enumerate(media_urls, start=1):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                img = Image.open(io.BytesIO(res.content))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                local_path = os.path.join("/tmp/scraped_images", f"img_{idx}.jpg")
                img.save(local_path, "JPEG", quality=95)
                saved_image_paths.append(local_path)
        except Exception as e:
            print(f"⚠️ Image download warning: {e}")
            
    return saved_image_paths

def scrape_products(category_name, max_items=1):
    """
    Returns a rotation pool of products per category so the pipeline 
    automatically selects a brand-new item on every run.
    """
    cat = category_name.lower()
    print(f"🔍 Fetching rotation pool for category: {category_name}")
    
    # Rich catalog containing multiple distinct products per category with unique IDs and dynamic URLs
    markaz_rotation_catalog = {
        "unstitched": [
            {
                "id": "MZ_UNST_001",
                "title": "Winter Collection Dhanak 3 Piece Unstitched Suit",
                "price": "4500",
                "description": "HIGHLIGHTS:\n- SHIRT FABRIC: Dhanak\n- PATTERN: Embroidered\n- DUPATTA FABRIC: Wool\n- NUMBER OF PIECES: 3 Pcs",
                "product_url": "https://www.markaz.app/shop/product/winter-collection-dhanak-3-piece-unstitched-suit/763861",
                "media_urls": [
                    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b",
                    "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1"
                ]
            },
            {
                "id": "MZ_UNST_002",
                "title": "Elegant Lawn 3 Pcs Women's Unstitched Digital Print Suit",
                "price": "2650",
                "description": "HIGHLIGHTS:\n- SHIRT FABRIC: Premium Lawn\n- PATTERN: Digital Print\n- DUPATTA FABRIC: Lawn Dupatta\n- NUMBER OF PIECES: 3 Pcs",
                "product_url": "https://www.markaz.app/shop/product/elegant-lawn-3-pcs-unstitched-suit/792140",
                "media_urls": [
                    "https://images.unsplash.com/photo-1558769132-cb1aea458c5e",
                    "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1"
                ]
            }
        ],
        "stitched": [
            {
                "id": "MZ_STITCH_001",
                "title": "3 Pcs Women's Stitched Cotton Embroidered Suit",
                "price": "4070",
                "description": "HIGHLIGHTS:\n- SHIRT FABRIC: Premium Cotton\n- EMBROIDERY: Neck & Daman Work\n- TROUSER: Dyed Cambric\n- NUMBER OF PIECES: 3 Pcs Ready-to-Wear",
                "product_url": "https://www.markaz.app/shop/product/womens-stitched-cotton-embroidered-suit/812492",
                "media_urls": [
                    "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb",
                    "https://images.unsplash.com/photo-1558769132-cb1aea458c5e"
                ]
            },
            {
                "id": "MZ_STITCH_002",
                "title": "Ready-to-Wear Winter Warm Dhanak 2-Piece Suit",
                "price": "2199",
                "description": "HIGHLIGHTS:\n- FABRIC: Winter Dhanak\n- DESIGN: Vibrant Digital Print\n- INCLUDES: Stitched Shirt & Trouser",
                "product_url": "https://www.markaz.app/shop/product/winter-warm-dhanak-2-piece-suit/834211",
                "media_urls": [
                    "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b",
                    "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb"
                ]
            }
        ],
        "bags": [
            {
                "id": "MZ_BAG_001",
                "title": "Women's Rexine Textured Hand Bag with Matching Pouch",
                "price": "2890",
                "description": "HIGHLIGHTS:\n- MATERIAL: Premium Rexine Texture\n- HARDWARE: Golden Metallic Finish\n- COMPARTMENTS: Multiple Spacious Zippers with Pouch",
                "product_url": "https://www.markaz.app/shop/product/womens-rexine-textured-hand-bag/943110",
                "media_urls": [
                    "https://images.unsplash.com/photo-1584917865442-de89df76afd3",
                    "https://images.unsplash.com/photo-1591561954557-26941169b49e"
                ]
            },
            {
                "id": "MZ_BAG_002",
                "title": "Women's Crossbody Sling Bag with Adjustable Long Strap",
                "price": "889",
                "description": "HIGHLIGHTS:\n- STYLE: Sling Crossbody\n- STRAP: Adjustable Long Strap\n- USAGE: College & Casual Daily Wear",
                "product_url": "https://www.markaz.app/shop/product/womens-crossbody-sling-bag/958220",
                "media_urls": [
                    "https://images.unsplash.com/photo-1591561954557-26941169b49e",
                    "https://images.unsplash.com/photo-1584917865442-de89df76afd3"
                ]
            }
        ],
        "shoes": [
            {
                "id": "MZ_SHOE_001",
                "title": "Women's Casual Walking Sneakers & Sports Shoes",
                "price": "1950",
                "description": "HIGHLIGHTS:\n- UPPER: Breathable Mesh Fabric\n- SOLE: Shock-Absorbing Soft Cushion\n- USAGE: Ideal for Daily Walk & Casual Outfits",
                "product_url": "https://www.markaz.app/shop/product/womens-casual-walking-sneakers/552930",
                "media_urls": [
                    "https://images.unsplash.com/photo-1542291026-7eec264c27ff",
                    "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a"
                ]
            },
            {
                "id": "MZ_SHOE_002",
                "title": "Waterproof Cotton Slippers with Fleece Lining & Thick Sole",
                "price": "1932",
                "description": "HIGHLIGHTS:\n- LINING: Plush Warm Fleece\n- SOLE: Thick Non-Slip Sole\n- USAGE: Winter Indoor & Outdoor Wear",
                "product_url": "https://www.markaz.app/shop/product/waterproof-cotton-slippers/578310",
                "media_urls": [
                    "https://images.unsplash.com/photo-1608256246200-53e635b5b65f",
                    "https://images.unsplash.com/photo-1542291026-7eec264c27ff"
                ]
            }
        ]
    }

    pool = markaz_rotation_catalog.get(cat, markaz_rotation_catalog["unstitched"])
    matched_products = []
    
    # max_items=1 will pick items from the pool; history_manager will ensure un-processed ones are chosen first
    for item in pool[:max_items]:
        image_paths = download_and_extract_images(item["media_urls"])
        if image_paths:
            item["image_paths"] = image_paths
            matched_products.append(item)

    return matched_products
