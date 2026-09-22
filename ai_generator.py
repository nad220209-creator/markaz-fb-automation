import os
import json
import re
import time
import google.generativeai as genai
from config import SELLER_NAME, WHATSAPP_NUMBER, WHATSAPP_LINK

def generate_copy(title, selling_price, raw_details):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables!")
    
    genai.configure(api_key=str(api_key).strip("[]'\" "))

    prompt = f"""
You are an expert e-commerce affiliate marketer in Pakistan.
Generate distinct, high-converting social media posts for this product:

Product Title: {title}
Price: PKR {selling_price}
Raw Details/Measurements: {raw_details}

SELLER CONTACT INFORMATION (MUST BE INCLUDED IN EVERY POST'S CALL TO ACTION):
- Contact Name: {SELLER_NAME}
- WhatsApp Number: {WHATSAPP_NUMBER}
- Direct WhatsApp Link: {WHATSAPP_LINK}

Return ONLY a valid JSON object with the following keys:
1. "fb_marketplace": Concise listing copy emphasizing exact measurements, size details, PKR price, Cash on Delivery across Pakistan, and a Call to Action with seller name ({SELLER_NAME}), WhatsApp ({WHATSAPP_NUMBER}), and link ({WHATSAPP_LINK}).
2. "instagram": Aesthetic Roman Urdu & English post with emojis, key feature bullet points, COD note, seller contact details ({SELLER_NAME}, {WHATSAPP_NUMBER}, {WHATSAPP_LINK}), and 10 trending Pakistani fashion hashtags.
3. "tiktok": Short, catchy caption (under 120 words) with attention-grabbing hook, seller WhatsApp ({WHATSAPP_NUMBER} / {WHATSAPP_LINK}), and video overlay hashtags.
4. "fb_group": Persuasive sales post for Facebook Buy & Sell groups with urgency, full size details, and direct order details via {SELLER_NAME} at {WHATSAPP_NUMBER} ({WHATSAPP_LINK}).

CRITICAL: DO NOT include any introductory text, markdown headers outside JSON, or self-check questions. Output pure JSON only.
"""
    # Prioritize latest models with robust fallbacks for 404 and 429 rate limits
    models_to_try = [
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    for model_name in models_to_try:
        try:
            print(f"Trying Gemini model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                clean_raw = response.text.strip()
                clean_raw = re.sub(r'^```json\s*', '', clean_raw, flags=re.IGNORECASE)
                clean_raw = re.sub(r'^```\s*', '', clean_raw)
                clean_raw = re.sub(r'\s*```$', '', clean_raw)
                try:
                    data = json.loads(clean_raw)
                    if isinstance(data, dict) and "fb_marketplace" in data:
                        print(f"Successfully generated copy using {model_name}!")
                        return data
                except Exception:
                    pass
                return {
                    "fb_marketplace": clean_raw,
                    "instagram": clean_raw,
                    "tiktok": clean_raw[:300],
                    "fb_group": clean_raw
                }
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            if "429" in str(e) or "Quota" in str(e):
                print("Rate limit hit, waiting 5 seconds before trying next model...")
                time.sleep(5)
            continue

    # Graceful fallback if all models hit rate limits or unavailability
    print("Warning: All Gemini models failed or hit rate limits. Using standard marketing copy fallback.")
    fallback_text = f"🔥 {title} 🔥\nPrice: PKR {selling_price}\nCash on Delivery across Pakistan!\nOrder now via WhatsApp: {WHATSAPP_NUMBER} ({WHATSAPP_LINK})\nSeller: {SELLER_NAME}"
    return {
        "fb_marketplace": fallback_text,
        "instagram": fallback_text,
        "tiktok": fallback_text[:120],
        "fb_group": fallback_text
    }
