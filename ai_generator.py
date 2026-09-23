import os
import json
import google.generativeai as genai

# Prioritized model list: Newest Gemini 3 frontier models first, falling back gracefully
PREFERRED_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.1-pro",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
]

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

    last_error = None
    for model_name in PREFERRED_MODELS:
        try:
            print(f"Attempting content generation using model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            text_resp = response.text.strip()
            # Clean markdown code blocks if the model wrapped the JSON
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]
            text_resp = text_resp.strip()
            
            parsed = json.loads(text_resp)
            if "description" in parsed:
                return parsed
        except Exception as e:
            print(f"Model {model_name} failed with error: {e}. Trying next model...")
            last_error = e
            continue

    # Fallback default dictionary if all models fail
    print(f"All prioritized models failed. Using default fallback copy. Error: {last_error}")
    return {
        "description": f"🔥 Best Quality {title} Now Available!\n\n✨ Price: PKR {selling_price:,}\n🚚 Cash on Delivery Available Across Pakistan!\n\nOrder now to get yours!"
    }
