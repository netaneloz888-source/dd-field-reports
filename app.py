from datetime import datetime
import io
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

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

COPYRIGHT_TEXT = "כל הזכויות שייכות לנתנאל עוז הררי 0545520445"

st.set_page_config(
    page_title="ד.ד. מהנדסים בע''מ - תחקור אירוע בצומת",
    page_icon="🚦",
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
    div[data-baseweb="select"] > div {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE_DIR = Path(__file__).resolve().parent
ALEF_URL = "https://github.com/google/fonts/raw/main/ofl/alef/"


def heb(text):
    if not text:
        return ""
    lines = str(text).split("\n")
    return "<br/>".join(escape(get_display(line)) for line in lines)


def _find_or_download(filename):
    for folder in (BASE_DIR, Path.cwd()):
        p = folder / filename
        if p.exists():
            return str(p)
    try:
        target = BASE_DIR / filename
        urllib.request.urlretrieve(ALEF_URL + filename, target)
        return str(target)
    except Exception:
        return None


def register_fonts():
    reg = _find_or_download("Alef-Regular.ttf")
    bold = _find_or_download("Alef-Bold.ttf")
    if reg and bold:
        try:
            pdfmetrics.registerFont(TTFont("AlefRegular", reg))
            pdfmetrics.registerFont(TTFont("AlefBold", bold))
            return "AlefRegular", "AlefBold"
        except Exception as e:
            print("Error registering Alef:", e)

    dejavu = "/usr/share/fonts/truetype/dejavu/"
    if os.path.exists(dejavu + "DejaVuSans.ttf"):
        pdfmetrics.registerFont(TTFont("DejaVu", dejavu + "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuBold", dejavu + "DejaVuSans-Bold.ttf"))
        return "DejaVu", "DejaVuBold"

    st.error("לא נמצא פונט עברי. העלה את Alef-Regular.ttf ו-Alef-Bold.ttf לתיקיית הפרויקט.")
    return "Helvetica", "Helvetica-Bold"


def build_investigation_pdf(event_data, inspector_data, items):
    font_reg, font_bold = register_fonts()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=15 * mm,
        bottomMargin=16 * mm,
        title=f"ד
