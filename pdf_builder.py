from fpdf import FPDF
from config import SELLER_NAME, WHATSAPP_NUMBER, WHATSAPP_LINK

def clean_text_for_pdf(text):
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def build_pdf(title, selling_price, copy_dict, image_files, output_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title & Pricing Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, clean_text_for_pdf(title), align="L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 128, 0)
    pdf.cell(0, 7, f"Selling Price: PKR {selling_price}", new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 7, f"Seller: {SELLER_NAME} | WhatsApp: {WHATSAPP_NUMBER} ({WHATSAPP_LINK})", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(4)

    # Organized Specification Table (Rows & Columns)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "  PRODUCT SPECIFICATIONS, SIZES & MEASUREMENTS", fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    spec_rows = [
        ("Product Name", title),
        ("Selling Price", f"PKR {selling_price}"),
        ("Fabric Material", "Wash And Wear / Premium Quality"),
        ("Design & Pattern", "Plain / Formal Wear"),
        ("Package Includes", "1 x Suit (Shirt & Trouser Cutting)"),
        ("Shirt Cutting", "2 Meter"),
        ("Trouser Cutting", "2 Meter"),
        ("Total Suit Cutting", "4 Meter"),
        ("Color", "Brown / Standard Variant"),
        ("Delivery Method", "Cash on Delivery (COD) across Pakistan"),
        ("Return Policy", "7-Day Easy Return Guarantee")
    ]

    pdf.set_font("Helvetica", "", 10)
    for row_idx, (key, val) in enumerate(spec_rows):
        if row_idx % 2 == 0:
            pdf.set_fill_color(240, 244, 248)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(65, 7, f"  {key}", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(125, 7, f"  {val}", border=1, fill=True, new_x='LMARGIN', new_y='NEXT')

    pdf.ln(6)

    # Social Media Copy Sections
    sections = [
        ("--- FACEBOOK MARKETPLACE COPY ---", copy_dict.get("fb_marketplace", "")),
        ("--- INSTAGRAM POST COPY & HASHTAGS ---", copy_dict.get("instagram", "")),
        ("--- TIKTOK VIDEO CAPTION ---", copy_dict.get("tiktok", "")),
        ("--- FACEBOOK GROUPS & PAGE COPY ---", copy_dict.get("fb_group", ""))
    ]

    for header, content in sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 7, header, new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, clean_text_for_pdf(content))
        pdf.ln(4)

    # All Uncompressed HD Product Gallery Images from ZIP
    if image_files:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"HD Product Gallery Photos ({len(image_files)} Uncompressed Images):", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(3)

        for img_path in image_files:
            try:
                pdf.image(img_path, w=130)
                pdf.ln(6)
            except Exception as img_err:
                print(f"Skipping PDF image render for {img_path}: {img_err}")

    pdf.output(output_path)
