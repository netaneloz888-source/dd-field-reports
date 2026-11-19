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


def ensure_font_file(candidates, urls, fallback_filename):
    existing = next(
        (p for p in candidates if os.path.exists(p) and os.path.getsize(p) > 10000),
        None,
    )
    if existing:
        return existing

    font_dir = "/tmp/dd_pdf_fonts"
    os.makedirs(font_dir, exist_ok=True)
    target_path = os.path.join(font_dir, fallback_filename)

    if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
        return target_path

    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(target_path, "wb") as out:
                out.write(resp.read())
            if os.path.exists(target_path) and os.path.getsize(target_path) > 10000:
                return target_path
        except Exception:
            continue

    return None


def register_fonts():
    reg_path = ensure_font_file(
        candidates=[
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
        urls=[
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/ttf/DejaVuSans.ttf",
        ],
        fallback_filename="DejaVuSans.ttf",
    )
    bold_path = ensure_font_file(
        candidates=[
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ],
        urls=[
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
            "https://cdn.jsdelivr.net/gh/dejavu-fonts/dejavu-fonts@master/ttf/DejaVuSans-Bold.ttf",
        ],
        fallback_filename="DejaVuSans-Bold.ttf",
    )

    if reg_path:
        try:
            pdfmetrics.registerFont(TTFont("AppHebrew", reg_path))
            bold_src = bold_path if bold_path else reg_path
            pdfmetrics.registerFont(TTFont("AppHebrewBold", bold_src))
            return "AppHebrew", "AppHebrewBold"
        except Exception:
            pass

    return "Helvetica", "Helvetica-Bold"


def build_pdf_bytes(junction_name, report_nature, report_date, inspector_data, items):
    font_reg, font_bold = register_fonts()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
