import os
import json

HISTORY_FILE = "processed_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading history file: {e}")
        return []

def save_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=4)
    except Exception as e:
        print(f"⚠️ Error saving history file: {e}")

def is_already_processed(product_id):
    """
    Checks if a product ID has already been processed and uploaded.
    """
    history = load_history()
    return str(product_id) in [str(item) for item in history]

def mark_as_processed(product_id):
    """
    Adds a product ID to the processed history list and saves it.
    """
    history = load_history()
    p_id_str = str(product_id)
    if p_id_str not in history:
        history.append(p_id_str)
        save_history(history)
