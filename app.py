import streamlit as st
from fpdf import FPDF
from PIL import Image, ImageOps
from bidi.algorithm import get_display
import tempfile
import os
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
            self.set_font('DejaVu', 'B', 16)
            self.set_text_color(18, 78, 145)
            self.cell(0, 10, heb('ד.ד. מהנדסים בע"מ'), ln=True, align='C')
            self.ln(2)

        # קו הפרדה ראשי
        self.set_draw_color(18, 78, 145)
        self.set_line_width(0.8)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(5)

    def footer(self):
        # בלוק פרטי מפקח בתחתית הדף
        self.set_y(-26)
        self.set_draw_color(18, 78, 145)
        self.set_line_width(0.5)
        self.line(12, self.get_y(), 198, self.get_y())
        self.ln(2)

        self.set_font('DejaVu', 'B', 9)
        self.set_text_color(25, 25, 25)
        parts = []
        if self.inspector_name:
            parts.append(f"שם המפקח: {self.inspector_name}")
        if self.license_type:
            parts.append(f"סוג רישיון: {self.license_type}")
        if self.license_num:
            parts.append(f"מס' רישיון: {self.license_num}")
        if self.phone:
            parts.append(f"טלפון: {self.phone}")

        self.cell(0, 6, heb("   |   ".join(parts)), ln=True, align='C')

        self.set_font('DejaVu', '', 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, heb(f'ד.ד. מהנדסים בע"מ  |  עמוד {self.page_no()} מתוך {{nb}}'), align='C')


def generate_pdf(junction_name, report_nature, report_date, inspector_data, items):
    pdf = EngineeringReportPDF(
        junction_name=junction_name,
        report_nature=report_nature,
        report_date=report_date,
        inspector_name=inspector_data["name"],
        license_type=inspector_data["license_type"],
        license_num=inspector_data["license_num"],
        phone=inspector_data["phone"]
    )
    pdf.alias_nb_pages()

    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
    pdf.add_page()

    # באנר מסודר בראש הדוח: שם צומת ומהות הדוח
    pdf.set_fill_color(240, 245, 252)
    pdf.set_draw_color(190, 205, 225)
    pdf.rect(12, pdf.get_y(), 186, 18, style='DF')

    banner_y = pdf.get_y() + 2
    pdf.set_xy(15, banner_y)
    pdf.set_font('DejaVu', 'B', 11)
    pdf.set_text_color(15, 45, 85)
    junction_line = f"שם צומת: {junction_name if junction_name else 'לא צוין'}"
    pdf.cell(180, 7, heb(junction_line), ln=True, align='R')

    pdf.set_xy(15, banner_y + 8)
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_text_color(45, 45, 45)
    nature_line = f"מהות הדוח: {report_nature if report_nature else 'לא צוינה'}"
    pdf.cell(180, 7, heb(nature_line), ln=True, align='R')

    pdf.set_y(banner_y + 21)

    # כרטיסי תמונה + תיאור לכל פריט
    card_height = 78
    page_width = 186
    left_margin = 12
    img_box_w = 78
    text_box
