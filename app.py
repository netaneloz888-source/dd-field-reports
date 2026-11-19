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
    .stApp { direction: rtl; text-align: right; }
    input, textarea, select { direction: rtl; text-align: right; }
    div[data-testid="stFileUploader"] { direction: rtl; }
    </style>
    """,
    unsafe_allow_html=True,
)


def heb(text):
    if not text:
        return ""
    lines = str(text).split("\n")
    return "<br/>".join(get_display(line) for line in lines)


def ensure_font(candidates, urls, filename):
    existing = next(
        (p for p in candidates if os.path.exists(p) and os.path.getsize(p) > 10000),
        None,
    )
    if existing:
        return existing

    font_dir = "/tmp/dd_pdf_fonts"
    os.makedirs(font_dir, exist_ok=True)
    target = os.path.join(font_dir, filename)

    if os.path.exists(target) and os.path.getsize(target) > 10000:
        return target

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(target, "wb") as out:
                out.write(resp.read())
            if os.path.exists(target) and os.path.getsize(target) > 10000:
                return target
        except Exception:
            continue

    return None


def register_fonts():
    reg = ensure_font(
        [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
        [
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/ttf/DejaVuSans.ttf",
        ],
        "DejaVuSans.ttf",
    )
    bold = ensure_font(
        [
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ],
        [
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/ttf/DejaVuSans-Bold.ttf",
        ],
        "DejaVuSans-Bold.ttf",
    )

    if reg:
        try:
            pdfmetrics.registerFont(TTFont("AppHeb", reg))
            pdfmetrics.registerFont(TTFont("AppHebBold", bold if bold else reg))
            return "AppHeb", "AppHebBold"
        except Exception:
            pass

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
    card_title_style = ParagraphStyle(
        "CardTitleStyle",
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

    junction_txt = junction_name.strip() if junction_name and junction_name.strip() else "לא צוין"
    nature_txt = report_nature.strip() if report_nature and report_nature.strip() else "לא צוינה"

    header_title = heb("ד.ד. מהנדסים בע''מ - דוח שטח")
    header_sub = heb(f"צומת: {junction_txt}  |  מהות: {nature_txt}  |  תאריך: {report_date}")
    text_block = [
        Paragraph(header_title, title_style),
        Spacer(1, 2 * mm),
        Paragraph(header_sub, sub_style),
    ]

    story = []
    if os.path.exists("logo.png"):
        try:
