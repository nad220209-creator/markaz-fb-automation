import os
import google.generativeai as genai

# Configure Gemini API Key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def generate_product_seo(product_data):
    """
    AI Brain: Analyzes raw product details and generates SEO-optimized titles, 
    smart pricing, and engaging Roman Urdu descriptions tailored for shoes, bags, or seasonal clothes.
    """
    raw_title = product_data.get("title", "Product")
    raw_price = product_data.get("price", "1500")
    raw_desc = product_data.get("description", "")
    whatsapp_number = os.environ.get("WHATSAPP_NUMBER", "923001234567")

    prompt = f"""
    You are an expert E-commerce Copywriter and Facebook Marketplace SEO Specialist for the Pakistan market (Lahore, Faisalabad, Karachi, etc.).
    
    Analyze this product and generate a high-converting listing:
    - Raw Title: {raw_title}
    - Raw Price: {raw_price}
    - Raw Description: {raw_desc}

    Provide your response strictly in the following format:
    TITLE: [Create a catchy, SEO-optimized Facebook Marketplace title packed with searchable keywords. Max 80 chars.]
    PRICE: [Extract or optimize the selling price in digits only, e.g., 1850]
    DESCRIPTION: [Write an engaging, persuasive sales description in Roman Urdu mixed with English. 
    - Highlight quality, comfort (if shoes), space/pockets (if bags), or fabric/warmth (if seasonal clothes).
    - Mention: 📦 Cash on Delivery Available Across Pakistan!
    - Include call to action: 💬 Order Now via WhatsApp: https://wa.me/{whatsapp_number}
    - Add trending hashtags like #Markaz #OnlineShopping #PakistanShopping #CashOnDelivery]
    """

    try:
        # Use Gemini Flash for lightning-fast AI generation
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse AI response
        title = raw_title
        price = str(raw_price)
        description = raw_desc

        for line in text.split("\n"):
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("PRICE:"):
                price = line.replace("PRICE:", "").strip()
            elif line.startswith("DESCRIPTION:"):
                # Capture everything after DESCRIPTION:
                desc_idx = text.find("DESCRIPTION:")
                description = text[desc_idx + len("DESCRIPTION:"):].strip()
                break
                
        # Clean up price to ensure only numbers
        price = ''.join(filter(str.isdigit, price))
        if not price:
            price = "1500"

        return {
            "title": title,
            "price": price,
            "description": description
        }

    except Exception as e:
        print(f"⚠️ AI Brain generation error: {e}. Falling back to default formatting.")
        return {
            "title": raw_title[:100],
            "price": str(raw_price),
            "description": f"{raw_title}\n\n📦 Cash on Delivery Available Across Pakistan!\n💬 Order Now via WhatsApp: https://wa.me/{whatsapp_number}"
        }
