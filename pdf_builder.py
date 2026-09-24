"""
pdf_builder.py
Generates clean, professional e-commerce product catalog PDFs
for Facebook / Instagram resellers (Pakistan).

Requires: pip install fpdf2 pillow requests
"""

import os
from io import BytesIO
from urllib.parse import quote

import requests
from fpdf import FPDF
from PIL import Image

# ----------------------------------------------------------------------
# CONFIG - edit these once
# ----------------------------------------------------------------------
WHATSAPP_NUMBER_INTL = "923374633605"        # digits only, no "+"
WHATSAPP_NUMBER_DISPLAY = "+92 337 4633605"
MAX_IMAGE_PX = 1600                          # longest side kept for print quality

# Colour palette (R, G, B)
DARK = (28, 37, 54)
ACCENT = (192, 57, 43)
LIGHT_BG = (245, 246, 248)
TEXT = (55, 55, 55)
WHITE = (255, 255, 255)
WA_GREEN = (37, 160, 82)
WA_GREEN_DARK = (27, 120, 62)
LINK_BLUE = (0, 84, 190)
LINK_BG = (232, 241, 252)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def sanitize_text(text):
    """Replace characters that break FPDF's built-in latin-1 fonts."""
    if not text:
        return ""
    replacements = {
        "\u2014": "-", "\u2013": "-",            # dashes
        "\u201c": '"', "\u201d": '"',            # double quotes
        "\u2018": "'", "\u2019": "'",            # single quotes
        "\u2026": "...",                         # ellipsis
        "\u2022": "*", "\u25cf": "*",            # bullets
        "\u20b9": "Rs.", "\u20a8": "PKR",        # rupee symbols
        "\u00a0": " ",                           # non-breaking space
        "\u200b": "", "\u200d": "", "\ufe0f": "",  # zero-width / emoji joiners
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    return str(text).encode("latin-1", "replace").decode("latin-1")


def load_image(source):
    """Load an image from a URL or local path -> RGB PIL image (or None)."""
    try:
        if source.startswith("http"):
            res = requests.get(source, timeout=15)
            res.raise_for_status()
            img = Image.open(BytesIO(res.content))
        else:
            img = Image.open(source)
        img.load()
        if img.mode != "RGB":
            # Flatten transparency onto white instead of black
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")
        if max(img.size) > MAX_IMAGE_PX:
            img.thumbnail((MAX_IMAGE_PX, MAX_IMAGE_PX), Image.LANCZOS)
        return img
    except Exception as e:
        print(f"Could not load image '{source}': {e}")
        return None


class CatalogPDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, f"Order on WhatsApp: {WHATSAPP_NUMBER_DISPLAY}   |   Page {self.page_no()}",
                  align="C")


# ----------------------------------------------------------------------
# Main builder
# ----------------------------------------------------------------------
def build_pdf(title, selling_price, copy_dict, image_paths, output_pdf_path, product_url=None):
    pdf = CatalogPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    page_w = pdf.w - pdf.l_margin - pdf.r_margin   # usable width (180mm)
    safe_title = sanitize_text(title)

    # ------------------------------------------------------------------
    # 1. HEADER & TITLE (dark banner + accent underline)
    # ------------------------------------------------------------------
    pad = 6
    line_h = 9
    pdf.set_font("helvetica", "B", 18)
    lines = pdf.multi_cell(page_w - 2 * pad, line_h, safe_title, dry_run=True, output="LINES")
    banner_h = len(lines) * line_h + 2 * pad
    top = pdf.get_y()

    pdf.set_fill_color(*DARK)
    pdf.rect(pdf.l_margin, top, page_w, banner_h, style="F")
    pdf.set_fill_color(*ACCENT)
    pdf.rect(pdf.l_margin, top + banner_h, page_w, 1.6, style="F")   # underline

    pdf.set_xy(pdf.l_margin + pad, top + pad)
    pdf.set_text_color(*WHITE)
    pdf.multi_cell(page_w - 2 * pad, line_h, safe_title, align="L",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(top + banner_h + 1.6 + 4)

    # Clickable Markaz verification link (prominent, blue + underlined)
    if product_url and str(product_url).startswith("http"):
        link_h = 11
        link_y = pdf.get_y()
        pdf.set_fill_color(*LINK_BG)
        pdf.set_draw_color(*LINK_BLUE)
        pdf.set_line_width(0.4)
        pdf.rect(pdf.l_margin, link_y, page_w, link_h, style="DF",
                 round_corners=True, corner_radius=2)

        # Whole box is clickable: one cell with the link, drawn over the box
        pdf.set_xy(pdf.l_margin, link_y)
        pdf.set_font("helvetica", "BU", 12)
        pdf.set_text_color(*LINK_BLUE)
        pdf.cell(page_w, link_h, ">> View Original Product on Markaz Store",
                 align="C", link=product_url, new_x="LMARGIN", new_y="NEXT")

        # Small line so the exact URL is visible (also clickable) for verification
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(120, 120, 120)
        short_url = sanitize_text(product_url if len(product_url) <= 95 else product_url[:92] + "...")
        pdf.cell(page_w, 5, short_url, align="C", link=product_url,
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ------------------------------------------------------------------
    # 2. PRICING & DESCRIPTION
    # ------------------------------------------------------------------
    box_y = pdf.get_y()
    box_h = 24
    pdf.set_fill_color(*LIGHT_BG)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.6)
    pdf.rect(pdf.l_margin, box_y, page_w, box_h, style="DF", round_corners=True, corner_radius=3)

    pdf.set_xy(pdf.l_margin, box_y + 3)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(page_w, 5, "SELLING PRICE", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(*ACCENT)
    pdf.cell(page_w, 9, f"PKR {int(selling_price):,}", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(*WA_GREEN_DARK)
    pdf.cell(page_w, 5, "Cash on Delivery Available Across Pakistan", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(box_y + box_h + 7)

    # Description
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*DARK)
    pdf.cell(page_w, 7, "Product Details", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 25, pdf.get_y())
    pdf.ln(3)

    description = (copy_dict or {}).get("description", "Best Quality Product Available!")
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(*TEXT)
    pdf.multi_cell(page_w, 6.2, sanitize_text(description), align="L",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # ------------------------------------------------------------------
    # 3. CALL-TO-ACTION: ORDER NOW + WHATSAPP
    # ------------------------------------------------------------------
    wa_text = quote(f"Hi! I want to order: {title}")
    wa_link = f"https://wa.me/{WHATSAPP_NUMBER_INTL}?text={wa_text}"
    wa_display_link = f"https://wa.me/{WHATSAPP_NUMBER_INTL}"

    cta_h = 42
    if pdf.get_y() + cta_h > pdf.h - pdf.b_margin:   # keep the box in one piece
        pdf.add_page()
    cta_y = pdf.get_y()

    pdf.set_fill_color(*WA_GREEN)
    pdf.set_draw_color(*WA_GREEN_DARK)
    pdf.set_line_width(0.8)
    pdf.rect(pdf.l_margin, cta_y, page_w, cta_h, style="DF", round_corners=True, corner_radius=4)

    pdf.set_xy(pdf.l_margin, cta_y + 4)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(*WHITE)
    pdf.cell(page_w, 10, "ORDER NOW", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "", 10)
    pdf.cell(page_w, 6, "Message us on WhatsApp to place your order instantly",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(page_w, 9, f"WhatsApp: {WHATSAPP_NUMBER_DISPLAY}", align="C",
             link=wa_link, new_x="LMARGIN", new_y="NEXT")

    # White pill "button" with the clickable link
    btn_w, btn_h = 96, 8
    btn_x = pdf.l_margin + (page_w - btn_w) / 2
    btn_y = pdf.get_y() + 1
    pdf.set_fill_color(*WHITE)
    pdf.rect(btn_x, btn_y, btn_w, btn_h, style="F", round_corners=True, corner_radius=4)
    pdf.set_xy(btn_x, btn_y)
    pdf.set_font("helvetica", "BU", 10)
    pdf.set_text_color(*WA_GREEN_DARK)
    pdf.cell(btn_w, btn_h, f"Tap to chat: {wa_display_link}", align="C", link=wa_link)

    pdf.set_y(cta_y + cta_h + 10)

    # ------------------------------------------------------------------
    # 4. PRODUCT IMAGES (centered, high-res, aspect ratio preserved)
    # ------------------------------------------------------------------
    img_w_max = 130          # mm
    img_h_max = 150          # mm

    # Load + size EVERY image first so the heading never gets orphaned.
    # Store compact JPEG bytes (not PIL objects) to keep memory low for big galleries.
    image_paths = image_paths or []
    prepared = []
    for img_path in image_paths:
        img = load_image(img_path)
        if img is None:
            continue
        w = img_w_max
        h = w * img.height / img.width
        if h > img_h_max:
            h = img_h_max
            w = h * img.width / img.height
        buf = BytesIO()
        img.save(buf, "JPEG", quality=92, optimize=True)
        prepared.append((buf.getvalue(), w, h))

    heading_h = 16
    first_h = prepared[0][2] if prepared else 10
    if pdf.get_y() + heading_h + first_h > pdf.h - pdf.b_margin:
        pdf.add_page()

    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*DARK)
    pdf.cell(page_w, 7, "Product Images", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.5)
    mid = pdf.l_margin + page_w / 2
    pdf.line(mid - 12, pdf.get_y(), mid + 12, pdf.get_y())
    pdf.ln(5)

    for jpeg_bytes, w, h in prepared:
        if pdf.get_y() + h > pdf.h - pdf.b_margin:
            pdf.add_page()

        buf = BytesIO(jpeg_bytes)

        x = pdf.l_margin + (page_w - w) / 2
        y = pdf.get_y()
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.3)
        pdf.rect(x - 1, y - 1, w + 2, h + 2)                 # thin frame
        pdf.image(buf, x=x, y=y, w=w, h=h)
        pdf.set_y(y + h + 8)

    if not prepared:
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(page_w, 8, "(Images not available)", align="C")

    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    pdf.output(output_pdf_path)
    print(f"PDF successfully built at: {output_pdf_path}")
    return output_pdf_path
