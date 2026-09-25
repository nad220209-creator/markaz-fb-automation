import os
from google import genai

def generate_optimized_content(product_title, raw_overview, price):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is missing.")
        return f"SEO TITLE: {product_title}\n\nROMAN URDU DESCRIPTION:\nZabardast quality footwear. Cash on delivery available across Pakistan."

    try:
        client = genai.Client(api_key=api_key)
        candidate_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]

        prompt = f"""
        You are an expert e-commerce copywriter for Facebook Marketplace in Pakistan.
        Optimize the following product details for a shoe listing:
        
        Original Title: {product_title}
        Original Overview: {raw_overview}
        Price: {price}
        
        Requirements:
        1. Provide an attractive, SEO-optimized Facebook Marketplace Title in English.
        2. Write a persuasive, high-converting sales description in Roman Urdu highlighting comfort, durability for local city streets (Lahore, Karachi, Islamabad), available sizing, and easy ordering.
        
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
            except Exception as model_err:
                print(f"Model {model_name} failed: {model_err}")
                continue

        if not response_text:
            response_text = f"SEO TITLE: {product_title}\n\nROMAN URDU DESCRIPTION:\nBehtareen comfort aur stylish look ke sath! Daily use aur walk ke liye zabardast. Lahore, Karachi, Islamabad aur poore Pakistan mein cash on delivery available hai."

        return response_text
    except Exception as e:
        print(f"Gemini Client initialization or generation error: {e}")
        return f"SEO TITLE: {product_title}\n\nROMAN URDU DESCRIPTION:\nZabardast quality footwear. Cash on delivery available across Pakistan."
