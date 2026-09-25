import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_product_seo(product_data):
    """Formats SEO text, locks WhatsApp to +923374633605, and keeps price clean."""
    raw_title = product_data.get("title", "Product")
    raw_price = str(product_data.get("price", "1500"))
    raw_desc = product_data.get("description", "")
    
    whatsapp_number = "923374633605"

    prompt = f"""
    You are an expert E-commerce Copywriter for Facebook Marketplace in Pakistan.
    Analyze this product:
    - Title: {raw_title}
    - Price: {raw_price}
    - Description: {raw_desc}

    Return strictly in this format:
    TITLE: [Catchy SEO-optimized marketplace title with keywords, max 80 chars]
    PRICE: [Digits only, exactly the wholesale price provided e.g. {raw_price}]
    DESCRIPTION: [Persuasive Roman Urdu & English description highlighting quality/comfort, 
    mentioning '📦 Cash on Delivery Available Across Pakistan!', 
    and call to action '💬 Order Now via WhatsApp: https://wa.me/{whatsapp_number}',
    plus hashtags #Markaz #OnlineShopping #PakistanShopping #CashOnDelivery]
    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        title, price, description = raw_title, raw_price, raw_desc
        for line in text.split("\n"):
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("PRICE:"):
                digits = ''.join(filter(str.isdigit, line))
                if digits and len(digits) <= 5:
                    price = digits
            elif line.startswith("DESCRIPTION:"):
                desc_idx = text.find("DESCRIPTION:")
                description = text[desc_idx + len("DESCRIPTION:"):].strip()
                break

        return {"title": title, "price": price, "description": description}
    except Exception as e:
        print(f"⚠️ AI Brain error: {e}")
        return {
            "title": raw_title[:100],
            "price": raw_price,
            "description": f"{raw_title}\n\n📦 Cash on Delivery Available Across Pakistan!\n💬 Order Now via WhatsApp: https://wa.me/{whatsapp_number}"
        }
