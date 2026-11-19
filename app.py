import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageOps
from bidi.algorithm import get_display
import tempfile
import os
import urllib.request
from datetime import datetime

# הגדרות עמוד וכיוון מימין לשמאל
st.set_page_config(page_title="ד.ד. מהנדסים בע''מ - דוח שטח", page_icon="⚡", layout="wide")

st.markdown("""
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
""", unsafe_allow_html=True)


# פונקציית עזר לסידור עברית ומספרים (BiDi) עבור FPDF
def heb(text):
    if not text:
        return ""
    lines = str(text).split('\n')
    return '\n'.join(get_display(line) for line in lines)


def resolve_font_paths():
    """מאתר קובצי DejaVu TTF מקומיים, בשרת, או מוריד אותם לתיקיית זמנית כגיבוי."""
    candidates = {
        "regular": [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
        "bold": [
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ],
    }

    resolved = {}
    fallback_dir = os.path.join(tempfile.gettempdir(), "dd_report_fonts")
    os.makedirs(fallback_dir, exist_ok=True)

    urls = {
        "regular": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
        "bold": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
    }

    for style in ("regular", "bold"):
        found = next((p for p in candidates[style] if os.path.exists(p)), None)
        if not found:
            target = os.path.join(fallback_dir, os.path.basename(candidates[style][0]))
            if not os.path.exists(target):
                urllib.request.urlretrieve(urls[style], target)
            found = target
        resolved[style] = found

    return resolved["regular"], resolved["bold"]


class EngineeringReportPDF(FPDF):
    def __init__(self, junction_name, report_nature, report_date, inspector_name, license_type, license_num, phone):
        super().__init__()
        self.junction_name = junction_name
        self.report_nature = report_nature
        self.report_date = report_date
        self.inspector_name = inspector_name
        self.license_type = license_type
        self.license_num = license_num
        self.phone = phone

    def header(self):
        # הלוגו בראש הדף
        if os.path.exists("logo.png"):
            self.image("logo.png", x=130, y=8, w=68)
            self.set_xy(12, 11)
            self.set_font('DejaVu', 'B', 13)
            self.set_text_color(18, 78, 145)
            self.cell(110, 7, heb(self.junction_name if self.junction_name else "דוח פיקוח ושטח"), ln=True, align='L')

            self.set_font('DejaVu', 'B', 10)
            self.set_text_color(40, 40, 40)
            self.cell(110, 6, heb(self.report_nature if self.report_nature else ""), ln=True, align='L')

            self.set_font('DejaVu', '', 9)
            self.set_text_color(100, 100, 100)
            self.cell(110, 6, heb(f"תאריך: {self.report_date}"), ln=True, align='L')
            self.set_y(37)
        else:
