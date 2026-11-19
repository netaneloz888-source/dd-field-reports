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
    if text is None:
        return ""
    s = str(text)
    if not s:
        return ""
    lines = s.split("\n")
    return "<br/>".join(get_display(line) for line in lines)


def _find_hebrew_font_paths():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates_reg = [
        os.path.join(base_dir, "Alef-Regular.ttf"),
        "Alef-Regular.ttf",
        os.path.join(base_dir, "fonts", "Alef-Regular.ttf"),
        "/usr/share/fonts/truetype/alef/Alef-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\david.ttf",
    ]
    candidates_bold = [
        os.path.join(base_dir, "Alef-Bold.ttf"),
        "Alef-Bold.ttf",
        os.path.join(base_dir, "fonts", "Alef-Bold.ttf"),
        "/usr/share/fonts/truetype/alef/Alef-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\davidbd.ttf",
    ]

    reg_path = next((p for p in candidates_reg if p and os.path.exists(p)), None)
    bold_path = next((p for p in candidates_bold if p and os.path.exists(p)), None)
    return reg_path, bold_path


def _ensure_fallback_fonts():
    cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "dd_pdf_fonts")
    os.makedirs(cache_dir, exist_ok=True)
    reg_cache = os.path.join(cache_dir, "Alef-Regular.ttf")
    bold_cache = os.path.join(cache_dir, "Alef-Bold.ttf")

    urls = {
        reg_cache: "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Regular.ttf",
        bold_cache: "https://github.com/google/fonts/raw/main/ofl/alef/Alef-Bold.ttf",
    }

    for target_path, url in urls.items():
        if not os.path.exists(target_path):
            try:
                urllib.request.urlretrieve(url, target_path)
            except Exception:
                pass

    return (
        reg_cache if os.path.exists(reg_cache) else None,
        bold_cache if os.path.exists(bold_cache) else None,
    )


def register_fonts():
    reg_path, bold_path = _find_hebrew_font_paths()
    if not reg_path or not bold_path:
        dl_reg, dl_bold = _ensure_fallback_fonts()
        reg_path = reg_path or dl_reg
        bold_path = bold_path or dl_bold

    if not reg_path:
        raise RuntimeError(
            "לא נמצא קובץ פונט תומך עברית (.ttf). מומלץ להניח את Alef-Regular.ttf ו-Alef-Bold.ttf בתיקיית הקוד."
        )

    if not bold_path:
        bold_path = reg_path

    pdfmetrics.registerFont(TTFont("HebReg", reg_path))
    pdfmetrics.registerFont(TTFont("HebBold", bold_path))
    return "HebReg", "HebBold"


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
        fontSize=10
