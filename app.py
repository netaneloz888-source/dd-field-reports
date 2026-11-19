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


def _get_font_file(filename, url):
    if os.path.exists(filename):
        return filename
    cache_path = os.path.join("/tmp", filename)
    if os.path.exists(cache_path):
        return cache_path
    try:
        urllib.request.urlretrieve(url, cache_path)
        if os.path.exists(cache_path):
            return cache_path
    except Exception as e:
        print(f"Could not download {filename}:", e)
    return None


def register_fonts():
    reg_name = "AlefRegular"
    bold_name = "AlefBold"
    registered = set(pdfmetrics.getRegisteredFontNames())

    if reg_name in registered and bold_name in registered:
        return reg_name, bold_name

    reg_path = _get_font_file(
        "Alef-Regular.ttf",
        "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Regular.ttf",
    )
    bold_path = _get_font_file(
        "Alef-Bold.ttf",
        "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Bold.ttf",
    )

    if reg_path and bold_path:
        try:
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
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors
