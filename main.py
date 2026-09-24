"""
main.py - Markaz -> Gemini copy -> PDF catalog -> Google Drive pipeline.

Modes (env var RUN_ALL):
  RUN_ALL=true   -> process all categories in sequence (manual run)
  otherwise      -> process ONE category chosen by the current UTC hour
                    (utc_hour % len(CATEGORIES)) for the scheduled cron run
"""

import datetime
import inspect
import json
import os
import re
import shutil
import sys
import tempfile
import time
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ai_generator import generate_copy
from drive_uploader import upload_pdf
from pdf_builder import build_pdf
from scraper import download_and_extract_media

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
BASE_URL = "https://www.markaz.app"
HISTORY_FILE = "processed_history.json"
HISTORY_MAX_ENTRIES = 500
SEARCH_CANDIDATE_ATTEMPTS = 3      # how many search results to try before falling back
REQUEST_RETRIES = 3
REQUEST_TIMEOUT = 20
PKT = datetime.timezone(datetime.timedelta(hours=5))   # Pakistan Standard Time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Titles the scraper returns when it failed to read the real product page
GENERIC_TITLES = {"", "markaz", "markaz app", "product", "shop"}

# Every fallback URL must be a direct /product/ link. Add more URLs to a
# category's "fallback_urls" list and the script will rotate through them.
CATEGORIES = [
    {
        "name": "Women Handbag",
        "query": "Womens Handbag Shoulder Bag",
        "fallback_urls": ["https://www.markaz.app/shop/product/womens-stylish-handbag-shoulder-bag/715000"],
        "required_keywords": ["bag", "handbag", "purse", "shoulder", "satchel", "tote"],
        "positive_keywords": ["women", "womens", "ladies", "girl", "female"],
        "forbidden_keywords": ["men", "mens", "boy", "gents", "male"],
    },
    {
        "name": "Baby Suit",
        "query": "Newborn Baby Suit Cotton Set",
        "fallback_urls": ["https://www.markaz.app/shop/product/baby-suit-set-soft-blended-3-pcs-newborn/96520"],
        "required_keywords": ["baby", "newborn", "infant", "kids", "romper", "toddler"],
        "positive_keywords": ["suit", "romper", "set", "dress", "kurta", "bodysuit", "frock", "cotton"],
        "forbidden_keywords": ["tablet", "lcd", "writing", "toy", "educational", "game", "men", "mens",
                               "women", "womens", "fabric", "boski", "gents", "lawn"],
    },
    {
        "name": "Girl Skincare Beauty Kit Serum",
        "query": "Vitamin C Face Serum Skincare Kit",
        "fallback_urls": ["https://www.markaz.app/shop/product/vitamin-c-face-serum-for-glowing-skin-pakistan/715900"],
        "required_keywords": ["serum", "face", "skin", "cream", "kit", "vitamin", "glow", "beauty",
                              "cleanser", "lotion"],
        "positive_keywords": [],
        "forbidden_keywords": ["shoe", "shoes", "bag", "handbag", "suit", "shirt", "pant", "watch", "toy"],
    },
    {
        "name": "Mens Shoes",
        "query": "Mens Casual Sneakers Shoes",
        "fallback_urls": ["https://www.markaz.app/shop/product/mens-blue-slip-on-walking-sneakers-size-40-45/692757"],
        "required_keywords": ["shoe", "shoes", "sneaker", "sneakers", "slip-on", "boot", "boots", "footwear"],
        "positive_keywords": ["men", "mens", "boy", "boys", "gents"],
        "forbidden_keywords": ["women", "womens", "ladies", "girl", "girls"],
    },
    {
        "name": "Womens Shoes",
        "query": "Womens Casual Sneakers Khussa",
        "fallback_urls": ["https://www.markaz.app/shop/product/womens-stylish-casual-sneakers-pakistan/715700"],
        "required_keywords": ["shoe", "shoes", "sneaker", "sneakers", "khussa", "sandal", "heel", "pumps",
                              "footwear"],
        "positive_keywords": ["women", "womens", "ladies", "girl", "girls", "female"],
        "forbidden_keywords": ["men", "mens", "boy", "boys", "gents"],
    },
    {
        "name": "Women Unstitched Lawn Suit",
        "query": "Women Unstitched Lawn Suit Printed",
        "fallback_urls": ["https://www.markaz.app/shop/product/womens-printed-unstitched-lawn-suit-pakistan/715500"],
        "required_keywords": ["lawn", "suit", "unstitched", "printed", "3-piece", "2-piece", "kurti", "cotton"],
        "positive_keywords": [],
        "forbidden_keywords": ["shoe", "shoes", "bag", "handbag", "serum", "watch", "toy", "men", "mens"],
    },
]


# ----------------------------------------------------------------------
# History cache  {product_url: "ISO timestamp of last successful run"}
# ----------------------------------------------------------------------
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[history] Could not read {HISTORY_FILE} ({e}); starting fresh.")
        return {}
    if isinstance(data, list):        # migrate old format (plain list of URLs)
        return {url: "1970-01-01T00:00:00" for url in data}
    return data if isinstance(data, dict) else {}


def save_history(history):
    # Keep only the most recent entries so the file never grows forever
    if len(history) > HISTORY_MAX_ENTRIES:
        newest = sorted(history.items(), key=lambda kv: kv[1], reverse=True)[:HISTORY_MAX_ENTRIES]
        history = dict(newest)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"[history] Error saving history: {e}")


def mark_processed(url):
    history = load_history()
    history[url] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_history(history)


# ----------------------------------------------------------------------
# URL + keyword helpers
# ----------------------------------------------------------------------
PRODUCT_PATH_RE = re.compile(r"/shop/product/[A-Za-z0-9\-_%]+/\d+")


def normalize_product_url(href):
    """Return a canonical https://www.markaz.app/shop/product/<slug>/<id> URL, or None."""
    if not href:
        return None
    parsed = urlparse(urljoin(BASE_URL, href.strip()))
    if parsed.netloc not in ("www.markaz.app", "markaz.app"):
        return None
    match = PRODUCT_PATH_RE.fullmatch(parsed.path.rstrip("/"))
    return f"{BASE_URL}{match.group(0)}" if match else None


def slug_title(url):
    slug = url.rstrip("/").split("/")[-2]
    return slug.replace("-", " ").replace("_", " ").title()


def _norm(text):
    return " " + re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() + " "


def has_word(text_norm, keyword):
    """Whole-word match (so 'men' does NOT match inside 'women'), plural tolerant."""
    kw = _norm(keyword).strip()
    return f" {kw} " in text_norm or f" {kw}s " in text_norm


def passes_filters(text, cat):
    t = _norm(text)
    if not any(has_word(t, kw) for kw in cat["required_keywords"]):
        return False
    if cat["positive_keywords"] and not any(has_word(t, kw) for kw in cat["positive_keywords"]):
        return False
    if any(has_word(t, kw) for kw in cat["forbidden_keywords"]):
        return False
    return True


# ----------------------------------------------------------------------
# Networking
# ----------------------------------------------------------------------
def fetch_html(url):
    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200 and res.text:
                return res.text
            print(f"[search] HTTP {res.status_code} on attempt {attempt}/{REQUEST_RETRIES}")
        except requests.RequestException as e:
            print(f"[search] Request error on attempt {attempt}/{REQUEST_RETRIES}: {e}")
        time.sleep(2 * attempt)
    return None


def find_candidates(cat):
    """Search Markaz and return [{'title', 'url'}] that pass the category filters."""
    search_url = f"{BASE_URL}/shop?search={quote(cat['query'])}"
    print(f"[search] {search_url}")
    html = fetch_html(search_url)
    if not html:
        print("[search] No HTML returned.")
        return []

    found = {}   # url -> title

    # 1) <a> tags - only real /product/<slug>/<id> links are accepted
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        url = normalize_product_url(a["href"])
        if not url:
            continue
        img = a.find("img")
        title = (a.get_text(" ", strip=True) or a.get("title") or (img.get("alt") if img else "") or "").strip()
        if len(title) > len(found.get(url, "")):
            found[url] = title

    # 2) Raw HTML/JSON - catches product links embedded in scripts (JS-rendered listings)
    for path in PRODUCT_PATH_RE.findall(html):
        found.setdefault(f"{BASE_URL}{path}", "")

    candidates = []
    for url, title in found.items():
        title = title if len(title) > 3 else slug_title(url)
        # Filter on title AND URL slug so blank/odd anchor text can't cause a false reject
        if passes_filters(f"{title} {slug_title(url)}", cat):
            candidates.append({"title": title, "url": url})

    print(f"[search] {len(found)} product links found, {len(candidates)} passed filters.")
    return candidates


# ----------------------------------------------------------------------
# Candidate ordering (fresh first -> oldest-used -> fallbacks)
# ----------------------------------------------------------------------
def build_attempt_queue(cat, candidates, history):
    def last_used(url):
        return history.get(url, "")          # "" sorts before any timestamp

    fresh = [c["url"] for c in candidates if c["url"] not in history]
    stale = sorted((c["url"] for c in candidates if c["url"] in history), key=last_used)
    fallbacks = sorted(cat["fallback_urls"], key=last_used)   # least-recently-used first

    if fresh:
        print(f"[select] {len(fresh)} fresh candidate(s).")
    elif stale:
        print("[select] All search results already processed - rotating to the oldest-used one.")
    else:
        print("[select] No valid search results - using verified fallback URL(s).")

    queue, seen = [], set()
    for url in (fresh + stale)[:SEARCH_CANDIDATE_ATTEMPTS] + fallbacks:
        if url not in seen:
            seen.add(url)
            queue.append(url)
    return queue


# ----------------------------------------------------------------------
# Scrape / copy / PDF / upload
# ----------------------------------------------------------------------
def parse_price(value):
    cleaned = re.sub(r"[^\d.]", "", str(value))
    price = int(float(cleaned)) if cleaned else 0
    if price <= 0:
        raise ValueError(f"invalid selling price: {value!r}")
    return price


def scrape_product(url, temp_dir):
    """Scrape and validate. Raises ValueError if the result is unusable."""
    print(f"[scrape] {url}")
    title, price, raw_details, image_paths = download_and_extract_media(url, temp_dir)

    title = (title or "").strip()
    if title.lower() in GENERIC_TITLES:
        raise ValueError(f"scraper returned a generic title ({title!r})")
    image_paths = [p for p in (image_paths or []) if p]
    if not image_paths:
        raise ValueError("scraper returned no images")
    price = parse_price(price)

    print(f"[scrape] OK: '{title}' | PKR {price:,} | {len(image_paths)} image(s)")
    return title, price, raw_details, image_paths


def make_copy(title, price, raw_details):
    print("[copy] Generating marketing copy with Gemini...")
    try:
        copy_dict = generate_copy(title, price, raw_details)
        if isinstance(copy_dict, dict) and copy_dict.get("description"):
            return copy_dict
        print("[copy] Empty response from Gemini - using raw details.")
    except Exception as e:
        print(f"[copy] Gemini failed ({e}) - using raw details.")
    fallback = str(raw_details or "Best Quality Product Available!").strip()
    return {"description": fallback[:1200]}


def sanitize_filename(name):
    clean = re.sub(r"[^\w\s-]", "", name).strip()
    clean = re.sub(r"\s+", "_", clean)[:120]
    return clean or "Markaz_Product"


def upload(local_pdf_path, file_title):
    """Upload into today's YYYY-MM-DD (Pakistan time) Drive folder."""
    folder_name = datetime.datetime.now(PKT).strftime("%Y-%m-%d")
    print(f"[upload] Uploading to Drive folder '{folder_name}'...")
    params = inspect.signature(upload_pdf).parameters
    # Pass the folder name only if drive_uploader.upload_pdf accepts it;
    # otherwise it is assumed to create the dated folder itself.
    if len(params) >= 3 or "folder_name" in params:
        return upload_pdf(local_pdf_path, file_title, folder_name)
    return upload_pdf(local_pdf_path, file_title)


def process_category(cat):
    print(f"\n{'=' * 60}\nPROCESSING CATEGORY: {cat['name']}\n{'=' * 60}")

    history = load_history()
    candidates = find_candidates(cat)
    queue = build_attempt_queue(cat, candidates, history)

    for url in queue:
        temp_dir = tempfile.mkdtemp(prefix="markaz_")
        try:
            title, price, raw_details, image_paths = scrape_product(url, temp_dir)
            copy_dict = make_copy(title, price, raw_details)

            file_title = sanitize_filename(f"{cat['name']}_{title}")
            pdf_path = os.path.join(temp_dir, f"{file_title}.pdf")

            print(f"[pdf] Building PDF with {len(image_paths)} image(s)...")
            build_pdf(f"[{cat['name'].upper()}] {title}", price, copy_dict, image_paths,
                      pdf_path, product_url=url)

            upload(pdf_path, file_title)
            mark_processed(url)          # only recorded after a full success
            print(f"[done] SUCCESS: {cat['name']} PDF generated and uploaded.")
            return True
        except Exception as e:
            print(f"[skip] {url} failed: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"[fail] Every candidate failed for {cat['name']}.")
    return False


# ----------------------------------------------------------------------
def main():
    run_all = os.environ.get("RUN_ALL", "false").strip().lower() == "true"

    if run_all:
        print("--- MANUAL RUN: processing ALL categories ---")
        targets = CATEGORIES
    else:
        hour = datetime.datetime.now(datetime.timezone.utc).hour
        idx = hour % len(CATEGORIES)
        print(f"--- AUTOMATED RUN: UTC hour {hour} -> category #{idx} ---")
        targets = [CATEGORIES[idx]]

    failed = []
    for cat in targets:
        try:
            if not process_category(cat):
                failed.append(cat["name"])
        except Exception as e:                       # never let one category kill the batch
            print(f"[fail] Unexpected error in {cat['name']}: {e}")
            failed.append(cat["name"])

    print(f"\nSummary: {len(targets) - len(failed)}/{len(targets)} category run(s) succeeded.")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)      # non-zero exit so GitHub Actions / cron flags the failure


if __name__ == "__main__":
    main()
