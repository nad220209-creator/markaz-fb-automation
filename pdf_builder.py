import os
from fpdf import FPDF

class PDFReport(FPDF):
    def __init__(self, product_title=""):
        super().__init__()
        self.product_title = product_title

    def header(self):
        self.set_fill_color(240, 240, 240)
        self.rect(0, 0, 210, 15, 'F')
        self.set_font('helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "MARKAZ RESELLER AUTOMATED CATALOGUE", 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def build_pdf(title, selling_price, copy_dict, image_paths, output_pdf_path, product_url=""):
    pdf = PDFReport(product_title=title)
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PAGE 1: Text Summary, Pricing, CTA & Markaz Link ---
    pdf.add_page()
    
    pdf.set_font('helvetica', 'B', 16)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(0, 8, title)
    pdf.ln(4)
    
    # Pricing Box
    pdf.set_fill_color(230, 245, 230)
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, f"  Selling Price: PKR {selling_price:,} (Cash on Delivery)", 0, 1, 'L', fill=True)
    pdf.ln(6)
    
    # Social Media Copy
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 6, "Product Description & Social Media Copy:", 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    
    desc_text = copy_dict.get('description', 'High quality trending product.')
    safe_desc = desc_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_desc)
    pdf.ln(8)
    
    # Order Box & Source Verification Link
    pdf.set_fill_color(245, 245, 250)
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, "  ORDER NOW - CASH ON DELIVERY ACROSS PAKISTAN", 0, 1, 'L', fill=True)
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, "  Seller: Muhammad Naveed Arshad", 0, 1)
    pdf.cell(0, 6, "  WhatsApp Number: +92 337 4633605", 0, 1)
    pdf.cell(0, 6, "  Direct WhatsApp Order Link: https://wa.me/923374633605", 0, 1)
    
    if product_url:
        pdf.set_font('helvetica', 'U', 9)
        pdf.set_text_color(0, 0, 238)
        pdf.cell(0, 6, f"  Original Markaz Product Link: {product_url}", 0, 1, link=product_url)
    
    pdf.ln(10)
    
    # --- SUBSEQUENT PAGES: HD Gallery Photos ---
    for img_path in image_paths:
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 6, "HD Product Gallery Photo:", 0, 1, 'C')
            pdf.ln(4)
            try:
                pdf.image(img_path, x=15, y=30, w=180)
            except Exception as img_err:
                print(f"Notice embedding image {img_path}: {img_err}")

    pdf.output(output_pdf_path)
