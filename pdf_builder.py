from fpdf import FPDF
from config import SELLER_NAME, WHATSAPP_NUMBER, WHATSAPP_LINK

def clean_text_for_pdf(text):
    if not text:
        return ""
    cleaned = str(text).replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    return cleaned.encode('ascii', 'ignore').decode('ascii')

def build_pdf(title, selling_price, raw_details, image_files, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 1. Product Title
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 7, clean_text_for_pdf(title), align="L")
    pdf.ln(3)

    # 2. Price & Contact Header
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 6, f"Price: PKR {selling_price}", new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 6, f"Order via WhatsApp: {WHATSAPP_NUMBER} ({WHATSAPP_LINK}) | Seller: {SELLER_NAME}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # 3. Product Description / Details
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 6, "Product Description:", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, clean_text_for_pdf(raw_details))
    pdf.ln(8)

    # 4. All Uncompressed HD Product Gallery Images
    if image_files:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Product Gallery Photos ({len(image_files)} Images):", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(3)

        for img_path in image_files:
            try:
                pdf.image(img_path, w=130)
                pdf.ln(6)
            except Exception as img_err:
                print(f"Skipping PDF image render for {img_path}: {img_err}")

    pdf.output(output_path)
