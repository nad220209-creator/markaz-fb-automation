import json
import os

HISTORY_FILE = "processed_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history_list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, indent=4, ensure_ascii=False)

def is_processed(product_url, history):
    return product_url in history

def mark_processed(product_url, history):
    if product_url not in history:
        history.append(product_url)
        save_history(history)
