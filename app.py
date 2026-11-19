from datetime import datetime
import io
import os
import urllib.request

from bidi.algorithm import get_display
from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import streamlit as st

st.set_page_config(
    page_title="ד.ד. מהנדסים בע''מ - דוח שטח",
    page_icon="⚡",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    input, textarea, select {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stFileUploader"] {
        direction: rtl;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def heb(text):
    if not text:
        return ""
    lines = str(text).split("\n")
    return "<br/>".join(get_display(line) for line in lines)


def register_fonts():
    try:
        reg_name = "AlefRegular"
        bold_name = "AlefBold"
        registered = set(pdfmetrics.getRegisteredFontNames())
        if reg_name in registered and bold_name in registered:
            return reg_name, bold_name

        reg_path = "Alef-Regular.ttf"
        bold_path = "Alef-Bold.ttf"

        if not os.path.exists(reg_path):
            reg_path = "/tmp/Alef-Regular.ttf"
            if not os.path.exists(reg_path):
                urllib.request.urlretrieve(
                    "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Regular.ttf",
                    reg_path,
                )

        if not os.path.exists(bold_path):
            bold_path = "/tmp/Alef-Bold.ttf"
            if not os.path.exists(bold_path):
                urllib.request.urlretrieve(
                    "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Bold.ttf",
                    bold_path,
                )

        if reg_name not in registered:
            pdfmetrics.registerFont(TTFont(reg_name, reg_path))
        if bold_name not in registered:
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
        return reg_name, bold_name
    except Exception as e:
        print("Error registering fonts:", e)
        return "Helvetica", "Helvetica-Bold"


def build_pdf_bytes(junction_name, report_nature, report_date, inspector_data, items):
    font_reg, font_bold = register_fonts()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="דוח פיקוח ושטח",
    )

    story = []

    title_style = ParagraphStyle(
        "TitleStyle",
        fontName=font_bold,
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#124E91"),
        alignment=2,
    )
    sub_style = ParagraphStyle(
        "SubStyle",
        fontName=font_reg,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#333333"),
        alignment=2,
    )
    card_header_style = ParagraphStyle(
        "CardHeader",
        fontName=font_bold,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#124E91"),
        alignment=2,
    )
    desc_style = ParagraphStyle(
        "DescStyle",
        fontName=font_reg,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1A1A1A"),
        alignment=2,
    )

    # כותרת עליונה ולוגו
    header_title = heb("ד.ד. מהנדסים בע''מ - דוח שטח")
    header_sub = heb(
        f"צומת: {junction_name or 'לא צוין'}  |  מהות: {report_nature or 'לא צוינה'}  |  תאריך: {report_date}"
    )

    text_block = [Paragraph(header_title, title_style), Spacer(1, 2 * mm), Paragraph(header_sub, sub_style)]

    if os.path.exists("logo.png"):
        try:
            logo_img = RLImage("logo.png", width=36 * mm, height=16 * mm, kind="proportional")
            top_table = Table([[logo_img, text_block]], colWidths=[42 * mm, 140 * mm])
            top_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ]
                )
            )
            story.append(top_table)
        except Exception:
            story.extend(text_block)
    else:
        story.extend(text_block)

    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#124E91")))
    story.append(Spacer(1, 5 * mm))

    # כרטיסי תמונות ותיאור
    for idx, item in enumerate(items, start=1):
        img = Image.open(item["file"])
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img_io = io.BytesIO()
        img.save(img_io, format="JPEG", quality=85)
        img_io.seek(0)

        img_reader
