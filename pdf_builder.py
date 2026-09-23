import os
from fpdf import FPDF
from PIL import Image
import requests
from io import BytesIO

def sanitize_text(text):
    if not text:
        return ""
    # Replace special unicode characters that crash FPDF latin-1 encoding
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "•": "*",
        "₹": "Rs.",
        "₨": "PKR"
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1')

def build_pdf(title, selling_price, copy_dict, image_paths, output_pdf_path, product_url=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Sanitize title
    safe_title = sanitize_text(title)
    
    # Title Header
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 8, safe_title)
    pdf.ln(5)
    
    # Pricing Box
    pdf.set_font("helvetica", "B", 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(192, 57, 43)
    pdf.cell(0, 10, f"Selling Price: PKR {selling_price:,} (COD Available)", ln=True, align="C", fill=True)
    pdf.ln(5)
    
    # Clickable Markaz Source Link
    if product_url:
        pdf.set_font("helvetica", "U", 10)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 8, ">> Click Here to View Original Product on Markaz", ln=True, link=product_url, align="C")
        pdf.ln(5)

    # Marketing Copy Description
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    description = copy_dict.get("description", "Best Quality Product Available!")
    safe_description = sanitize_text(description)
    pdf.multi_cell(0, 6, safe_description)
    pdf.ln(10)
    
    # Product Images Section
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Product Images:", ln=True)
    pdf.ln(3)
    
    temp_imgs = []
    for img_path in image_paths[:4]: # Max 4 images
        try:
            if img_path.startswith("http"):
                res = requests.get(img_path, timeout=10)
                img = Image.open(BytesIO(res.content))
            else:
                img = Image.open(img_path)
                
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            temp_img_path = temp_imgs_temp = os.path.join(tempfile_dir := os.path.dirname(output_pdf_path), f"temp_{os.path.basename(img_path)}.jpg")
            img.save(temp_img_path, "JPEG")
            temp_imgs.append(temp_img_path)
            
            # Place image in PDF
            pdf.image(temp_img_path, w=90)
            pdf.ln(5)
        except Exception as e:
            print(f"Error adding image to PDF: {e}")
            
    pdf.output(output_pdf_path)
    print(f"PDF successfully built at: {output_pdf_path}")
