import os
import json
import google.generativeai as genai

def get_api_keys():
    keys = []
    key_names = ["GEMINI_API_KEY"] + [f"GEMINI_API_KEY_{i}" for i in range(1, 10)]
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

    fallback_models = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-pro"
    ]

    last_error = None
    for key_idx, api_key in enumerate(api_keys, start=1):
        try:
            genai.configure(api_key=api_key)
            print(f"Using Gemini API Key #{key_idx}")
            
            candidate_models = []
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        candidate_models.append(m.name)
            except Exception:
                pass
                
            for m in fallback_models:
                if m not in candidate_models:
                    candidate_models.append(m)

            for model_name in candidate_models:
                try:
                    print(f"Attempting model: {model_name}")
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
                        return parsed
                except Exception as e:
                    print(f"Model {model_name} failed: {e}")
                    last_error = e
                    if "429" in str(e) or "Quota" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print("Quota limit reached. Rotating to next API key...")
                        break
                    continue
        except Exception as key_err:
            print(f"API Key #{key_idx} configuration error: {key_err}")
            continue

    print(f"All API keys and models exhausted. Using default fallback copy. Error: {last_error}")
    return {
        "description": f"🔥 Best Quality {title} Now Available!\n\n✨ Price: PKR {selling_price:,}\n🚚 Cash on Delivery Available Across Pakistan!\n\nOrder now to get yours!"
    }
