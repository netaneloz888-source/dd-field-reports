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


def _download_font(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
        if data and len(data) > 5000:
            with open(dest_path, "wb") as f:
                f.write(data)
            return dest_path
    except Exception as e:
        print("Font download error:", e)
    return None


def register_fonts():
    reg_name = "AlefRegular"
    bold_name = "AlefBold"
    registered = set(pdfmetrics.getRegisteredFontNames())
    if reg_name in registered and bold_name in registered:
        return reg_name, bold_name

    reg_candidates = [
        "Alef-Regular.ttf",
        "fonts/Alef-Regular.ttf",
        "/tmp/Alef-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    bold_candidates = [
        "Alef-Bold.ttf",
        "fonts/Alef-Bold.ttf",
        "/tmp/Alef-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    reg_path = next((p for p in reg_candidates if os.path.exists(p)), None)
    bold_path = next((p for p in bold_candidates if p and os.path.exists(p)), None)

    if not reg_path:
        reg_path = _download_font(
            "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Regular.ttf",
            "/tmp/Alef-Regular.ttf",
        )
    if not bold_path:
        bold_path = _download_font(
            "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Bold.ttf",
            "/tmp/Alef-Bold.ttf",
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
        textColor
