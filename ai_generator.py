import os
import json
import google.generativeai as genai

def configure_gemini():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY_2")
    if not api_key:
        raise ValueError("No Gemini API key found in environment variables.")
    genai.configure(api_key=api_key)

def generate_copy(title, selling_price, raw_details):
    configure_gemini()
    
    prompt = f"""
    You are an expert e-commerce copywriter in Pakistan. Write high-converting social media marketing copy for Facebook and Instagram for the following product.
    
    Product Title: {title}
    Selling Price: PKR {selling_price} (Cash on Delivery available)
    Product Details: {raw_details}
    
    Return ONLY a valid JSON object with a single key "description" containing the marketing copy. The copy must be engaging, mention Cash on Delivery across Pakistan, include relevant hashtags, and be written in a mix of clear English and appealing Roman Urdu where appropriate. 
    Do not include any markdown backticks or extra text outside the JSON.
    """

    # Dynamically fetch all active models supporting content generation from Google's API
    candidate_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                candidate_models.append(m.name)
    except Exception as e:
        print(f"Notice: Could not fetch model list dynamically: {e}")

    # Exhaustive backup list of standard production models
    fallback_list = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-pro",
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro"
    ]
    
    for m in fallback_list:
        if m not in candidate_models:
            candidate_models.append(m)

    last_error = None
    for model_name in candidate_models:
        try:
            print(f"Attempting content generation using model: {model_name}")
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
            print(f"Model {model_name} failed: {e}. Trying next...")
            last_error = e
            continue

    print(f"All models failed. Using default fallback copy. Error: {last_error}")
    return {
        "description": f"🔥 Best Quality {title} Now Available!\n\n✨ Price: PKR {selling_price:,}\n🚚 Cash on Delivery Available Across Pakistan!\n\nOrder now to get yours!"
    }
