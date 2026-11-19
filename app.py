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


def ensure_font_file(candidates, url, fallback_filename):
    existing = next(
        (p for p in candidates if os.path.exists(p) and os.path.getsize(p) > 10000),
        None,
    )
    if existing:
        return existing

    font_dir = "/tmp/dd_pdf_fonts"
    os.makedirs(font_dir, exist_ok=True)
    target_path = os.path.join(font_dir, fallback_filename)

    if not (os.path.exists(target_path) and os.path.getsize(target_path) > 10000):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(target_path, "wb") as out:
                out.write(resp.read())
        except Exception:
            return None

    return (
        target_path
        if os.path.exists(target_path) and os.path.getsize(target_path) > 10000
        else None
    )


def register_fonts():
    reg_path = ensure_font_file(
        candidates=[
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ],
        url="https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
        fallback_filename="DejaVuSans.ttf",
    )
    bold_path = ensure_font_file(
        candidates=[
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        ],
        url="https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
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

    junction_txt = junction_name.strip() if junction_name and junction_name.strip() else "לא צוין"
    nature_txt = report_nature.strip() if report_nature and report_nature.strip() else "לא צוינה"

    header_title = heb("ד.ד. מהנדסים בע''מ - דוח שטח")
    header_sub = heb(f"צומת: {junction_txt}  |  מהות: {nature_txt}  |  תאריך: {report_date}")

    text_block = [
        Paragraph(header_title, title_style),
        Spacer(1, 2 * mm),
        Paragraph(header_sub, sub_style),
    ]

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
