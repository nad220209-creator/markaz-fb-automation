import os
from google import genai

def generate_optimized_content(product_title, raw_overview, price):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "title": product_title,
            "keywords": "shoes for men, casual sneakers, walking shoes Pakistan, black joggers",
            "description": "Behtareen comfort aur stylish look ke sath! Daily use aur walk ke liye zabardast. Cash on delivery available across Pakistan."
        }

    try:
        client = genai.Client(api_key=api_key)
        candidate_models = [
            "gemini-3.8-flash",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]

        prompt = f"""
        You are an expert e-commerce copywriter for Facebook Marketplace in Pakistan.
        Optimize the following shoe product details:
        
        Original Title: {product_title}
        Original Overview: {raw_overview}
        Price: {price}
        
        Provide your response strictly in this exact format:
        SEO TITLE: [An attractive, high-converting English title]
        SEO KEYWORDS: [Comma-separated SEO-ranked keywords for Facebook Marketplace search algorithm, e.g., mens casual shoes, running sneakers pakistan, comfortable walking shoes]
        ROMAN URDU DESCRIPTION: [Persuasive sales description highlighting comfort, daily college/office use, durability, and cash on delivery]
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
                    break
            except Exception:
                continue

        if not response_text:
            return {
                "title": product_title,
                "keywords": "shoes for men, casual sneakers, walking shoes Pakistan",
                "description": "Behtareen comfort aur stylish look ke sath! Daily use aur walk ke liye zabardast. Cash on delivery available."
            }

        # Parse sections
        title_res = product_title
        keywords_res = "shoes for men, casual sneakers, walking shoes"
        desc_res = "Behtareen comfort aur stylish look ke sath!"

        lines = response_text.split('\n')
        curr_section = None
        desc_lines = []

        for line in lines:
            if "SEO TITLE:" in line:
                title_res = line.replace("SEO TITLE:", "").strip()
                curr_section = None
            elif "SEO KEYWORDS:" in line:
                keywords_res = line.replace("SEO KEYWORDS:", "").strip()
                curr_section = None
            elif "ROMAN URDU DESCRIPTION:" in line:
                curr_section = "desc"
            elif curr_section == "desc":
                desc_lines.append(line)

        if desc_lines:
            desc_res = "\n".join(desc_lines).strip()

        return {
            "title": title_res,
            "keywords": keywords_res,
            "description": desc_res
        }
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return {
            "title": product_title,
            "keywords": "shoes for men, casual sneakers",
            "description": "Behtareen comfort aur stylish look ke sath! Cash on delivery available."
        }
