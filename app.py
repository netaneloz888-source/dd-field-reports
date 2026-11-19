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
    text_box_w = page_width - img_box_w - 4

    for idx, item in enumerate(items, start=1):
        if pdf.get_y() + card_height > 264:
            pdf.add_page()

        start_y = pdf.get_y()

        pdf.set_draw_color(190, 200, 215)
        pdf.set_line_width(0.4)
        pdf.rect(left_margin, start_y, page_width, card_height)

        divider_x = left_margin + img_box_w + 2
        pdf.line(divider_x, start_y, divider_x, start_y + card_height)

        # תמונה בצד שמאל
        img = Image.open(item['file'])
        img = ImageOps.exif_transpose(img)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            img.save(tmp_file.name, format="JPEG", quality=88)
            tmp_path = tmp_file.name

        max_img_w = img_box_w - 4
        max_img_h = card_height - 4
        w, h = img.size
        aspect = w / h

        if w / h > max_img_w / max_img_h:
            disp_w = max_img_w
            disp_h = disp_w / aspect
        else:
            disp_h = max_img_h
            disp_w = disp_h * aspect

        img_x = left_margin + (img_box_w - disp_w) / 2 + 1
        img_y = start_y + (card_height - disp_h) / 2
        pdf.image(tmp_path, x=img_x, y=img_y, w=disp_w, h=disp_h)
        os.remove(tmp_path)

        # תיאור מרווח בצד ימין
        text_x = divider_x + 3
        text_w = text_box_w - 6

        pdf.set_xy(text_x, start_y + 3)
        pdf.set_fill_color(235, 242, 250)
        pdf.set_font('DejaVu', 'B', 11)
        pdf.set_text_color(18, 78, 145)
        pdf.cell(text_w, 8, heb(f"תמונה {idx} - תיאור"), ln=True, align='R', fill=True)

        pdf.set_xy(text_x, start_y + 13)
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(25, 25, 25)
        desc_text = item['desc'] if item['desc'] else "לא הוזן תיאור."
        pdf.multi_cell(text_w, 6, heb(desc_text), align='R')

        pdf.set_y(start_y + card_height + 5)

    # בלוק סיכום וחתימת מפקח בסוף הדוח
    if pdf.get_y() + 28 > 264:
        pdf.add_page()

    pdf.ln(3)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(180, 190, 205)
    sig_y = pdf.get_y()
    pdf.rect(12, sig_y, 186, 22, style='DF')

    pdf.set_xy(15, sig_y + 3)
    pdf.set_font('DejaVu', 'B', 10)
    pdf.set_text_color(15, 45, 85)
    pdf.cell(180, 6, heb("אישור מפקח:"), ln=True, align='R')

    pdf.set_xy(15, sig_y + 10)
    pdf.set_font('DejaVu', '', 9.5)
    pdf.set_text_color(30, 30, 30)
    sig_line = (
        f"שם המפקח: {inspector_data['name']}   |   "
        f"סוג רישיון: {inspector_data['license_type']}   |   "
        f"מס' רישיון: {inspector_data['license_num']}   |   "
        f"טלפון: {inspector_data['phone']}"
    )
    pdf.cell(180, 7, heb(sig_line), ln=True, align='R')

    return bytes(pdf.output())


# ================= ממשק המשתמש =================
col_logo, col_title = st.columns([1, 3])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
with col_title:
    st.title("ד.ד. מהנדסים בע''מ")
    st.caption("הפקת דוחות שטח ותמונות PDF")

st.divider()

# 1. ראש הדוח: שם צומת ומהות הדוח
st.subheader("1. פרטי ראש הדוח")
c1, c2 = st.columns(2)
with c1:
    junction_name = st.text_input("שם צומת", placeholder="לדוגמה: צומת בילו / הרב משה שפירא-שביט")
with c2:
    report_nature = st.text_input("מהות הדוח", value="דוח לפני מסירת צומת", placeholder="לדוגמה: דוח לפני מסירת צומת / ביקורת אחזקה")

st.divider()

# 2. תמונות ותיאור לכל תמונה
st.subheader("2. תמונות ותיאור")
uploaded_files = st.file_uploader(
    "בחר או צלם תמונות",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

items_data = []

if uploaded_files:
    for i, file in enumerate(uploaded_files):
        with st.container(border=True):
            col_img, col_desc = st.columns([1, 2])
            with col_img:
                st.image(file, use_container_width=True)
            with col_desc:
                desc = st.text_area(
                    f"תיאור תמונה {i + 1}",
                    key=f"desc_{i}",
                    height=165,
                    placeholder="רשום כאן את התיאור עבור התמונה..."
                )
                items_data.append({"file": file, "desc": desc})

st.divider()

# 3. פרטים בסוף הדוח: שם המפקח, סוג רישיון, מס' רישיון, טלפון
st.subheader("3. פרטי מפקח (יופיעו למטה בדוח)")
i1, i2, i3, i4 = st.columns(4)
with i1:
    inspector_name = st.text_input("שם המפקח", value="נתנאל עוז הררי")
with i2:
    license_type = st.text_input("סוג רישיון", value="הנדסאי חשמל / מפקח הסדרי תנועה")
with i3:
    license_num = st.text_input("מס' רישיון", placeholder="הזן מס' רישיון")
with i4:
    phone = st.text_input("טלפון", value="054-5520445")

st.divider()

if st.button("📄 הפק דוח PDF", type="primary", use_container_width=True):
    if not uploaded_files:
        st.warning("נא להעלות לפחות תמונה אחת לפני הפקת הדוח.")
    else:
        with st.spinner("מייצר קובץ PDF..."):
            inspector_info = {
                "name": inspector_name,
                "license_type": license_type,
                "license_num": license_num,
                "phone": phone
            }
            date_str = datetime.now().strftime("%d/%m/%Y")
            pdf_bytes = generate_pdf(
                junction_name=junction_name,
                report_nature=report_nature,
                report_date=date_str,
                inspector_data=inspector_info,
                items=items_data
            )
            clean_junction = junction_name.strip().replace(" ", "_") if junction_name.strip() else "צומת"
            file_name = f"דוח_{clean_junction}{datetime.now().strftime('%Y%m%d%H%M')}.pdf"
            st.success("הדוח מוכן!")
            st.download_button(
                label="⬇️ הורד דוח PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
