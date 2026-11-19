from datetime import datetime
import io
import os

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
    regular_candidates = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    bold_candidates = [
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]

    reg_path = next((p for p in regular_candidates if os.path.exists(p)), None)
    bold_path = next((p for p in bold_candidates if os.path.exists(p)), None)

    if reg_path:
        try:
            pdfmetrics.registerFont(TTFont("AppHebrew", reg_path))
            if bold_path:
                pdfmetrics.registerFont(TTFont("AppHebrewBold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont("AppHebrewBold", reg_path))
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

        img_reader = ImageReader(img_io)
        iw, ih = img_reader.getSize()
        max_w = 68 * mm
        max_h = 48 * mm
        scale = min(max_w / max(iw, 1), max_h / max(ih, 1))
        rl_img = RLImage(img_io, width=iw * scale, height=ih * scale)

        desc_raw = item["desc"].strip() if item["desc"] and item["desc"].strip() else "לא הוזן תיאור."
        right_cell = [
            Paragraph(heb(f"תמונה {idx} - תיאור"), card_header_style),
            Spacer(1, 2 * mm),
            Paragraph(heb(desc_raw), desc_style),
        ]

        row_table = Table([[right_cell, rl_img]], colWidths=[108 * mm, 74 * mm])
        row_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B8C6D8")),
                    ("LINEBEFORE", (1, 0), (1, -1), 0.7, colors.HexColor("#B8C6D8")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FCFDFE")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(row_table)
        story.append(Spacer(1, 4 * mm))

    # פרטי מפקח בסוף הדוח
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#124E91")))
    story.append(Spacer(1, 3 * mm))

    inspector_line = heb(
        f"מפקח: {inspector_data['name']}  |  "
        f"רישיון: {inspector_data['license_type']}  |  "
        f"מס' רישיון: {inspector_data['license_num'] or '-'}  |  "
        f"טלפון: {inspector_data['phone']}"
    )
    sig_table = Table([[Paragraph(inspector_line, sub_style)]], colWidths=[182 * mm])
    sig_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3F9")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#9BB2CE")),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ================= ממשק המשתמש =================
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
with col_title:
    st.title("ד.ד. מהנדסים בע''מ")
    st.caption("הפקת דוחות שטח ותמונות PDF")

st.divider()

st.subheader("1. פרטי ראש הדוח")
c1, c2 = st.columns(2)
with c1:
    junction_name = st.text_input("שם צומת", placeholder="לדוגמה: ניסים טולדנו")
with c2:
    report_nature = st.text_input("מהות הדוח", value="דוח לפני מסירת צומת")

st.divider()

st.subheader("2. תמונות ותיאור")
uploaded_files = st.file_uploader(
    "בחר או צלם תמונות",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
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
                    height=150,
                    placeholder="רשום תיאור לתמונה...",
                )
                items_data.append({"file": file, "desc": desc})

st.divider()

st.subheader("3. פרטי מפקח")
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

if "pdf_ready_bytes" not in st.session_state:
    st.session_state.pdf_ready_bytes = None
    st.session_state.pdf_ready_name = None

if st.button("📄 הפק דוח PDF", type="primary", use_container_width=True):
    if not uploaded_files:
        st.warning("נא להעלות לפחות תמונה אחת לפני הפקת הדוח.")
    else:
        with st.spinner("מייצר קובץ PDF..."):
            inspector_info = {
                "name": inspector_name,
                "license_type": license_type,
                "license_num": license_num,
                "phone": phone,
            }
            date_str = datetime.now().strftime("%d/%m/%Y")
            pdf_bytes = build_pdf_bytes(
                junction_name=junction_name,
                report_nature=report_nature,
                report_date=date_str,
                inspector_data=inspector_info,
                items=items_data,
            )
            clean_junction = junction_name.strip().replace(" ", "_") if junction_name.strip() else "דוח"
            st.session_state.pdf_ready_bytes = pdf_bytes
            st.session_state.pdf_ready_name = f"{clean_junction}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

if st.session_state.pdf_ready_bytes:
    st.success("הדוח מוכן! לחץ על הכפתור למטה להורדה.")
    st.download_button(
        label="⬇️ הורד דוח PDF",
        data=st.session_state.pdf_ready_bytes,
        file_name=st.session_state.pdf_ready_name,
        mime="application/pdf",
        use_container_width=True,
    )
