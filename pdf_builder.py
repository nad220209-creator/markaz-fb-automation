from fpdf import FPDF
from config import SELLER_NAME, WHATSAPP_NUMBER, WHATSAPP_LINK

def clean_text_for_pdf(text):
    if not text:
        return ""
    cleaned = str(text).replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return cleaned.encode('ascii', 'ignore').decode('ascii')

def build_pdf(title, selling_price, copy_dict, image_files, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. Product Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 51, 102)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(3)

    # Price Header
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 7, f"Price: PKR {selling_price}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    # 2. Necessary Product Description / Details
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 7, "Product Details & Description:", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    # Extract clean description text
    description_text = ""
    if isinstance(copy_dict, dict):
        description_text = copy_dict.get("fb_marketplace") or copy_dict.get("instagram") or ""
    else:
        description_text = str(copy_dict)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, clean_text_for_pdf(description_text))
    pdf.ln(6)

    # 3. Order Now Button & WhatsApp Section (with Pakistan Country Code)
    pdf.set_fill_color(240, 244, 248)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 8, "  ORDER NOW - CASH ON DELIVERY ACROSS PAKISTAN", fill=True, new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    
    pakistani_whatsapp_display = "+92 337 4633605"
    pakistani_whatsapp_link = "https://wa.me/923374633605"
    
    order_box_text = f"  Seller: {SELLER_NAME}\n  WhatsApp Number: {pakistani_whatsapp_display}\n  Direct Order Link: {pakistani_whatsapp_link}"
    pdf.multi_cell(0, 6, clean_text_for_pdf(order_box_text), border=1, fill=True)
    pdf.ln(8)

    # 4. Uncompressed HD Product Gallery Images
    if image_files:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"HD Product Gallery Photos ({len(image_files)} Uncompressed Images):", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(4)

        for img_path in image_files:
            try:
                pdf.image(img_path, w=130)
                pdf.ln(6)
            except Exception as img_err:
                print(f"Skipping PDF image render for {img_path}: {img_err}")

    pdf.output(output_path)
