import os
import json
import google.generativeai as genai

def get_api_keys():
    keys = []
    key_names = ["GEMINI_API_KEY", "GEMINI_API_KEY_1", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5"]
    for key_name in key_names:
        key = os.environ.get(key_name)
        if key and key not in keys:
            keys.append(key)
            
    if not keys:
        raise ValueError("No Gemini API keys found in environment variables.")
    return keys

def generate_copy(title, selling_price, raw_details):
    api_keys = get_api_keys()
    
    prompt = f"""
    You are an expert e-commerce copywriter in Pakistan. Write high-converting social media marketing copy for Facebook and Instagram for the following product.
    
    Product Title: {title}
    Selling Price: PKR {selling_price} (Cash on Delivery available)
    Product Details: {raw_details}
    
    Return ONLY a valid JSON object with a single key "description" containing the marketing copy. The copy must be engaging, mention Cash on Delivery across Pakistan, include relevant hashtags, and be written in a mix of clear English and appealing Roman Urdu where appropriate. 
    Do not include any markdown backticks or extra text outside the JSON.
    """

    # Proven stable production models
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    last_error = None
    for key_idx, api_key in enumerate(api_keys, start=1):
        try:
            genai.configure(api_key=api_key)
            print(f"Trying Gemini API Key #{key_idx}")
            
            for model_name in models_to_try:
                try:
                    print(f"Attempting generation with model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    
                    text_resp = response.text.strip()
                    if text_resp.startswith("```json"):
                        text_resp = text_resp[7:]
                    if text_resp.endswith("```"):
                        text_resp = text_resp[:-3]
                    text_resp = text_resp.strip()
                    
                    parsed = json.loads(text_resp)
                    if "description" in parsed:
                        print(f"Successfully generated copy using {model_name}")
                        return parsed
                except Exception as model_err:
                    print(f"Model {model_name} failed: {model_err}")
                    last_error = model_err
                    if "429" in str(model_err) or "Quota" in str(model_err) or "RESOURCE_EXHAUSTED" in str(model_err):
                        print("Quota limit reached. Rotating to next API key...")
                        break
                    continue
        except Exception as key_err:
            print(f"API Key #{key_idx} error: {key_err}")
            continue

    print(f"All models/keys failed. Using default fallback copy. Last error: {last_error}")
    return {
        "description": f"🔥 Best Quality {title} Now Available!\n\n✨ Price: PKR {selling_price:,}\n🚚 Cash on Delivery Available Across Pakistan!\n\nOrder now to get yours!"
    }
