import os
from google import genai

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

def generate_optimized_content(product_title, raw_overview, price):
    client = get_gemini_client()
    
    # Candidate models list prioritizing Gemini 3.6 and falling back across active models
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.6-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    # Dynamically inject any available active models from the API client if supported
    try:
        available_models = [m.name.replace("models/", "") for m in client.models.list()]
        for am in available_models:
            if "gemini" in am and am not in candidate_models:
                candidate_models.insert(0, am)
    except Exception:
        pass

    prompt = f"""
    You are an expert e-commerce copywriter for Facebook Marketplace in Pakistan.
    Optimize the following product details for a shoe listing:
    
    Original Title: {product_title}
    Original Overview: {raw_overview}
    Price: {price}
    
    Requirements:
    1. Provide an attractive, SEO-optimized Facebook Marketplace Title in English.
    2. Write a persuasive, high-converting sales description in Roman Urdu that highlights comfort, durability for local city streets (Lahore, Karachi, Islamabad), available sizing, and easy ordering.
    
    Format your response clearly:
    SEO TITLE: [Title]
    
    ROMAN URDU DESCRIPTION:
    [Description]
    """

    response_text = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                response_text = response.text
                print(f"Successfully generated content using Gemini model: {model_name}")
                break
        except Exception as e:
            print(f"Model {model_name} unavailable, trying next fallback: {e}")
            continue

    if not response_text:
        response_text = f"SEO TITLE: {product_title}\n\nROMAN URDU DESCRIPTION:\nBehtareen comfort aur stylish look ke sath! Daily use aur walk ke liye zabardast. Lahore, Karachi, Islamabad aur poore Pakistan mein cash on delivery available hai."

    return response_text
