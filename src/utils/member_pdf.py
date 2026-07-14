"""
مولّد تقرير PDF احترافي لكل لاعب (عربي RTL + شعار النادي)
Branded per-skater progress PDF report (Arabic RTL).
"""
import io
import os
from datetime import datetime

import pandas as pd

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    _RL_OK = True
except Exception:
    _RL_OK = False

from src.utils.arabic_text import ar, FONT_REGULAR, FONT_BOLD, fonts_available
from src.progress import charts

PDF_AVAILABLE = _RL_OK

_FONT = "Helvetica"
_FONT_B = "Helvetica-Bold"
_FONTS_REGISTERED = False

PRIMARY = colors.HexColor("#1f77b4") if _RL_OK else None
ACCENT = colors.HexColor("#764ba2") if _RL_OK else None


def _register_fonts():
    global _FONT, _FONT_B, _FONTS_REGISTERED
    if _FONTS_REGISTERED or not _RL_OK:
        return
    if fonts_available():
        try:
            pdfmetrics.registerFont(TTFont("AppArabic", FONT_REGULAR))
            pdfmetrics.registerFont(TTFont("AppArabic-Bold", FONT_BOLD))
            _FONT, _FONT_B = "AppArabic", "AppArabic-Bold"
        except Exception:
            pass
    _FONTS_REGISTERED = True


def _styles():
    return {
        "title": ParagraphStyle("t", fontName=_FONT_B, fontSize=22,
                                textColor=PRIMARY, alignment=TA_CENTER,
                                spaceAfter=14, leading=30),
        "sub": ParagraphStyle("s", fontName=_FONT, fontSize=11,
                              textColor=colors.grey, alignment=TA_CENTER,
                              spaceAfter=5, leading=16),
        "h2": ParagraphStyle("h2", fontName=_FONT_B, fontSize=14,
                             textColor=ACCENT, alignment=TA_RIGHT, spaceBefore=12, spaceAfter=8),
        "body": ParagraphStyle("b", fontName=_FONT, fontSize=11,
                              alignment=TA_RIGHT, spaceAfter=4, leading=18),
        "note": ParagraphStyle("n", fontName=_FONT, fontSize=10,
                              alignment=TA_RIGHT, spaceAfter=2, leading=16,
                              textColor=colors.HexColor("#333333")),
    }


def _calc_age(birth_date):
    try:
        bd = pd.to_datetime(birth_date, errors="coerce")
        if pd.isna(bd):
            return None
        return int((datetime.now() - bd).days // 365)
    except Exception:
        return None


def _kv_table(rows, styles):
    """جدول مفتاح/قيمة بمحاذاة عربية (القيمة يمين، التسمية أقصى اليمين)."""
    data = [[Paragraph(ar(str(v)), styles["body"]), Paragraph(ar(str(k)), styles["body"])]
            for k, v in rows]
    t = Table(data, colWidths=[10.5 * cm, 5.5 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#eef2fb")),
        ("ROWBACKGROUNDS", (0, 0), (0, -1), [colors.white, colors.HexColor("#f7f9fc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7dce5")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _metric_band(metrics, styles):
    """شريط بطاقات أرقام (الأحدث/الأفضل/المتوسط/التطور)."""
    cells = []
    for label, value in metrics:
        cells.append(Table(
            [[Paragraph(ar(str(value)), ParagraphStyle("mv", fontName=_FONT_B, fontSize=16,
                                                       textColor=PRIMARY, alignment=TA_CENTER))],
             [Paragraph(ar(label), ParagraphStyle("ml", fontName=_FONT, fontSize=9,
                                                  textColor=colors.grey, alignment=TA_CENTER))]],
            colWidths=[3.8 * cm]))
    band = Table([cells], colWidths=[4 * cm] * len(cells))
    band.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7dce5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e3e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return band


def _data_table(headers, rows, styles, col_widths):
    head = [Paragraph(ar(h), ParagraphStyle("th", fontName=_FONT_B, fontSize=10,
                                            textColor=colors.white, alignment=TA_CENTER))
            for h in headers]
    body = [[Paragraph(ar(str(c)), ParagraphStyle("td", fontName=_FONT, fontSize=9,
                                                  alignment=TA_CENTER)) for c in r]
            for r in rows]
    t = Table([head] + body, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d7dce5")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_member_progress_pdf(member, attendance_df, evals_df, summary,
                              club_avg_df=None, settings=None):
    """يبني تقرير PDF ويعيد البايتات. member: dict-like بالأعمدة الأساسية."""
    if not _RL_OK:
        raise RuntimeError("reportlab غير متاح")
    _register_fonts()
    settings = settings or {}
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=1.6 * cm, leftMargin=1.6 * cm,
                            topMargin=1.4 * cm, bottomMargin=1.4 * cm)
    story = []

    # ── header: logo + club name ──
    club_name = settings.get("club_name", "نادي التزلج")
    club_sub = settings.get("club_subtitle", "")
    logo_path = settings.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        try:
            story.append(Image(logo_path, width=2.6 * cm, height=2.6 * cm))
        except Exception:
            pass
    story.append(Paragraph(ar(club_name), styles["title"]))
    if club_sub:
        story.append(Paragraph(ar(club_sub), styles["sub"]))
    story.append(Paragraph(ar("تقرير تطوّر اللاعب"), styles["sub"]))
    story.append(Paragraph("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M"),
                           styles["sub"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── member info ──
    age = _calc_age(member.get("birth_date"))
    story.append(Paragraph(ar("بيانات اللاعب"), styles["h2"]))
    info = [
        ("الاسم", member.get("name", "—")),
        ("المستوى", member.get("level") or "—"),
        ("المدرب", member.get("coach") or "—"),
        ("الباقة", member.get("bundle") or "—"),
        ("الجنس", member.get("gender") or "—"),
        ("العمر", f"{age} سنة" if age else "—"),
    ]
    story.append(_kv_table(info, styles))
    story.append(Spacer(1, 0.3 * cm))

    # ── progress metrics band ──
    story.append(Paragraph(ar("ملخّص الأداء"), styles["h2"]))
    if summary.get("count", 0) > 0:
        imp = summary.get("improvement")
        imp_txt = ("+" + str(imp)) if (imp is not None and imp >= 0) else str(imp) if imp is not None else "—"
        band = [
            ("آخر درجة", summary.get("latest", "—")),
            ("أفضل درجة", summary.get("best", "—")),
            ("المتوسط", summary.get("average", "—")),
            ("التطوّر", imp_txt),
        ]
        story.append(_metric_band(band, styles))
        if summary.get("avg_jump") is not None:
            story.append(Spacer(1, 0.15 * cm))
            story.append(Paragraph(ar(f"متوسط نسبة نجاح القفزات: {summary['avg_jump']}%"), styles["body"]))
    else:
        story.append(Paragraph(ar("لا توجد تقييمات مسجّلة لهذا اللاعب بعد."), styles["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── charts ──
    if evals_df is not None and not evals_df.empty:
        png = charts.score_trend_png(evals_df)
        if png:
            story.append(Image(png, width=16 * cm, height=7.3 * cm))
            story.append(Spacer(1, 0.2 * cm))
        jp = charts.jump_success_png(evals_df)
        if jp:
            story.append(Image(jp, width=16 * cm, height=6.4 * cm))
            story.append(Spacer(1, 0.2 * cm))

    # ── attendance ──
    story.append(Paragraph(ar("الحضور"), styles["h2"]))
    if attendance_df is not None and not attendance_df.empty:
        oi = int((attendance_df["session_type"] == "on-ice").sum()) if "session_type" in attendance_df else 0
        ofi = int((attendance_df["session_type"] == "off-ice").sum()) if "session_type" in attendance_df else 0
        last = attendance_df["date"].max()
        story.append(_kv_table([
            ("إجمالي الحضور", len(attendance_df)),
            ("على الجليد On-Ice", oi),
            ("خارج الجليد Off-Ice", ofi),
            ("آخر حضور", last),
        ], styles))
        ap = charts.attendance_png(attendance_df)
        if ap:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Image(ap, width=16 * cm, height=6.4 * cm))
    else:
        story.append(Paragraph(ar("لا توجد سجلات حضور."), styles["body"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── evaluations table ──
    if evals_df is not None and not evals_df.empty:
        story.append(Paragraph(ar("سجل التقييمات"), styles["h2"]))
        recent = evals_df.sort_values("evaluation_date", ascending=False).head(12)
        rows = []
        for _, e in recent.iterrows():
            rows.append([
                e["evaluation_date"],
                round(float(e["total_score"]), 1),
                round(float(e["tes"]), 1),
                round(float(e["pcs"]), 1),
                "—" if pd.isna(e["jump_success_rate"]) else f"{e['jump_success_rate']:.0f}%",
                e.get("evaluation_type", "—"),
            ])
        story.append(_data_table(
            ["التاريخ", "الكلية", "TES", "PCS", "القفزات", "النوع"], rows, styles,
            [3.2 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.8 * cm, 2.8 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        # ── coach notes timeline ──
        notes = recent[recent["notes"].notna() & (recent["notes"].astype(str).str.strip() != "")]
        if not notes.empty:
            story.append(Paragraph(ar("ملاحظات المدرب"), styles["h2"]))
            for _, e in notes.iterrows():
                story.append(Paragraph(ar(f"• [{e['evaluation_date']}] {e['notes']}"), styles["note"]))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
