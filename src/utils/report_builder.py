"""
تصدير تقرير PDF احترافي لجلسة تحليل لاعب
Professional PDF Report Builder — works without ReportLab (HTML fallback)
"""

import io
import base64
from datetime import datetime
from typing import Dict, List, Optional

# Try ReportLab first
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ── PDF via ReportLab ─────────────────────────────────────────────────────────

def build_pdf_reportlab(analysis: Dict, lang: str = 'ar') -> bytes:
    is_ar = lang == 'ar'
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    BRAND = colors.HexColor('#667eea')
    DARK = colors.HexColor('#1e293b')
    GRAY = colors.HexColor('#64748b')
    RED = colors.HexColor('#dc2626')
    GREEN = colors.HexColor('#16a34a')

    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontSize=22, textColor=BRAND,
        alignment=TA_CENTER, spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=11, textColor=GRAY,
        alignment=TA_CENTER, spaceAfter=20,
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Normal'],
        fontSize=14, textColor=BRAND,
        spaceBefore=14, spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=DARK,
        spaceAfter=4,
    )
    small_style = ParagraphStyle(
        'Small', parent=styles['Normal'],
        fontSize=9, textColor=GRAY,
    )

    story = []
    player = analysis.get('player_name', 'Unknown Player')
    date_str = datetime.now().strftime('%Y-%m-%d')
    note = analysis.get('session_note', '')

    # Header
    story.append(Paragraph('⛸ Figure Skating Analysis Report', title_style))
    story.append(Paragraph(f'{player}  ·  {date_str}', sub_style))
    if note:
        story.append(Paragraph(note, small_style))
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND, spaceAfter=12))

    # KPIs
    vi = analysis.get('video_info', {})
    jumps = analysis.get('jumps', [])
    errors = analysis.get('errors', [])
    report = analysis.get('report', {})
    total_score = analysis.get('total_score', 0)
    avg_goe = sum(j.get('goe', 0) for j in jumps) / len(jumps) if jumps else 0

    kpi_data = [
        ['Duration', f"{vi.get('duration', 0):.1f} s",
         'Total Score', f"{total_score:.2f}"],
        ['Jumps', str(len(jumps)),
         'Avg GOE', f"{avg_goe:+.2f}"],
        ['Spins', str(len(analysis.get('spins', []))),
         'Errors', str(len(errors))],
    ]
    kpi_table = Table(kpi_data, colWidths=[3.5 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR', (2, 0), (2, -1), GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
        ('TEXTCOLOR', (3, 0), (3, -1), DARK),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # Assessment
    assessment = report.get('overall_assessment', '')
    if assessment:
        story.append(Paragraph('Overall Assessment', h2_style))
        story.append(Paragraph(assessment, body_style))
        story.append(Spacer(1, 8))

    # Jumps table
    if jumps:
        story.append(Paragraph('Jumps', h2_style))
        jheader = ['#', 'Type', 'Rot.', 'Height', 'RPM', 'GOE', 'Score', 'Clean']
        jrows = [jheader]
        for i, j in enumerate(jumps, 1):
            goe_val = j.get('goe', 0)
            jrows.append([
                str(i),
                j.get('type', ''),
                f"{j.get('rotations', 0):.1f}",
                f"{j.get('height_cm', 0):.0f} cm",
                f"{j.get('rpm', 0):.0f}",
                f"{goe_val:+d}",
                f"{j.get('final_score', 0):.2f}",
                '✓' if j.get('is_clean', True) else '✗',
            ])
        col_w = [1.0, 3.0, 1.2, 2.0, 1.8, 1.2, 1.8, 1.2]
        col_w_cm = [w * cm for w in col_w]
        jt = Table(jrows, colWidths=col_w_cm)
        jt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BRAND),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(jt)
        story.append(Spacer(1, 12))

    # Errors
    if errors:
        story.append(Paragraph('Technical Errors & Corrections', h2_style))
        SEV_MAP = {
            'CRITICAL': ('🔴', RED),
            'HIGH': ('🟠', colors.HexColor('#ea580c')),
            'MEDIUM': ('🟡', colors.HexColor('#d97706')),
            'LOW': ('🟢', GREEN),
            'حرج': ('🔴', RED),
            'عالي': ('🟠', colors.HexColor('#ea580c')),
            'متوسط': ('🟡', colors.HexColor('#d97706')),
            'منخفض': ('🟢', GREEN),
        }
        is_lang_ar = lang == 'ar'
        for err in errors:
            sev = err.get('severity', 'LOW')
            icon, clr = SEV_MAP.get(sev, ('⚪', GRAY))
            title = err.get('title_en', err.get('title_ar', ''))
            desc = err.get('description_en', err.get('description_ar', ''))
            corrections = err.get('corrections_en', err.get('corrections_ar', []))
            goe_val = err.get('goe_impact', 0)
            goe_str = f"  GOE: {goe_val:+d}" if goe_val else ''

            err_style = ParagraphStyle(
                f'Err_{sev}', parent=styles['Normal'],
                fontSize=10, textColor=clr,
                fontName='Helvetica-Bold', spaceBefore=6,
            )
            story.append(Paragraph(f"{icon}  {title}{goe_str}", err_style))
            story.append(Paragraph(desc, small_style))
            for i, c in enumerate(corrections[:3], 1):
                story.append(Paragraph(f"  {i}. {c}", small_style))
            story.append(Spacer(1, 4))

    # Priority corrections
    priority = report.get('priority_corrections', [])
    if priority:
        story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0'), spaceBefore=10))
        story.append(Paragraph('Priority Training Recommendations', h2_style))
        for i, c in enumerate(priority, 1):
            story.append(Paragraph(f"{i}. {c}", body_style))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0')))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=GRAY, alignment=TA_CENTER, spaceBefore=6,
    )
    story.append(Paragraph(
        f'Generated by ⛸ Figure Skating Analysis System  ·  {date_str}',
        footer_style,
    ))

    doc.build(story)
    return buf.getvalue()


# ── HTML fallback ─────────────────────────────────────────────────────────────

def build_html_report(analysis: Dict, lang: str = 'ar') -> str:
    """HTML report — usable when ReportLab is not available"""
    is_ar = lang == 'ar'
    player = analysis.get('player_name', 'Unknown')
    date_str = datetime.now().strftime('%Y-%m-%d')
    jumps = analysis.get('jumps', [])
    errors = analysis.get('errors', [])
    report = analysis.get('report', {})
    total_score = analysis.get('total_score', 0)
    avg_goe = sum(j.get('goe', 0) for j in jumps) / len(jumps) if jumps else 0
    assessment = report.get('overall_assessment', '')

    sev_color = {
        'CRITICAL': '#dc2626', 'HIGH': '#ea580c', 'MEDIUM': '#d97706', 'LOW': '#16a34a',
        'حرج': '#dc2626', 'عالي': '#ea580c', 'متوسط': '#d97706', 'منخفض': '#16a30d',
    }

    jump_rows = ''
    for i, j in enumerate(jumps, 1):
        goe = j.get('goe', 0)
        goe_color = '#16a34a' if goe > 0 else ('#dc2626' if goe < 0 else '#555')
        clean = '✅' if j.get('is_clean', True) else '⚠️'
        jump_rows += f"""
        <tr>
            <td>{i}</td><td><b>{j.get('type','')}</b></td>
            <td>{j.get('rotations',0):.1f}</td>
            <td>{j.get('height_cm',0):.0f} cm</td>
            <td>{j.get('rpm',0):.0f}</td>
            <td style="color:{goe_color};font-weight:700">{goe:+d}</td>
            <td><b>{j.get('final_score',0):.2f}</b></td>
            <td>{clean}</td>
        </tr>"""

    error_html = ''
    for e in errors:
        sev = e.get('severity', 'LOW')
        clr = sev_color.get(sev, '#555')
        title = e.get('title_en', e.get('title_ar', ''))
        desc = e.get('description_en', e.get('description_ar', ''))
        corr = e.get('corrections_en', e.get('corrections_ar', []))
        goe_val = e.get('goe_impact', 0)
        goe_str = f" <span style='color:{clr}'>GOE: {goe_val:+d}</span>" if goe_val else ''
        corr_li = ''.join(f'<li>{c}</li>' for c in corr[:3])
        error_html += f"""
        <div style="border-left:4px solid {clr};padding:10px 14px;margin:8px 0;background:#fafafa;border-radius:6px">
            <div style="font-weight:700;color:{clr}">{title}{goe_str}</div>
            <div style="color:#555;font-size:.9em;margin:4px 0">{desc}</div>
            <ul style="margin:4px 0;padding-left:18px;font-size:.85em;color:#333">{corr_li}</ul>
        </div>"""

    priority = report.get('priority_corrections', [])
    priority_html = ''.join(f'<li>{c}</li>' for c in priority)

    html = f"""<!DOCTYPE html>
<html lang="{'ar' if is_ar else 'en'}" dir="{'rtl' if is_ar else 'ltr'}">
<head>
<meta charset="utf-8">
<title>Figure Skating Report — {player}</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;padding:30px;color:#1e293b}}
  h1{{color:#667eea;text-align:center;border-bottom:3px solid #667eea;padding-bottom:10px}}
  h2{{color:#764ba2;margin-top:28px}}
  .meta{{text-align:center;color:#64748b;margin-bottom:20px}}
  .kpi{{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}}
  .kpi-card{{background:linear-gradient(135deg,#667eea22,#764ba222);border-radius:10px;
             padding:14px 20px;flex:1;min-width:120px;text-align:center}}
  .kpi-val{{font-size:1.8em;font-weight:800;color:#667eea}}
  .kpi-lbl{{font-size:.8em;color:#64748b}}
  table{{width:100%;border-collapse:collapse;margin:12px 0}}
  th{{background:#667eea;color:white;padding:8px;text-align:center}}
  td{{padding:7px;text-align:center;border-bottom:1px solid #e2e8f0}}
  tr:nth-child(even){{background:#f8fafc}}
  .assessment{{background:#f1f5f9;border-radius:8px;padding:12px 18px;
               font-weight:600;color:#1e293b;margin:12px 0}}
  .priority li{{margin:6px 0}}
  .footer{{text-align:center;color:#94a3b8;font-size:.8em;margin-top:30px;
            padding-top:12px;border-top:1px solid #e2e8f0}}
</style>
</head>
<body>
<h1>⛸ Figure Skating Analysis Report</h1>
<div class="meta">{player}  ·  {date_str}</div>

<div class="kpi">
  <div class="kpi-card"><div class="kpi-val">{total_score:.2f}</div><div class="kpi-lbl">Total Score</div></div>
  <div class="kpi-card"><div class="kpi-val">{len(jumps)}</div><div class="kpi-lbl">Jumps</div></div>
  <div class="kpi-card"><div class="kpi-val">{avg_goe:+.2f}</div><div class="kpi-lbl">Avg GOE</div></div>
  <div class="kpi-card"><div class="kpi-val">{len(errors)}</div><div class="kpi-lbl">Errors</div></div>
</div>

<div class="assessment">{assessment}</div>

<h2>🦘 Jumps</h2>
<table>
<tr><th>#</th><th>Type</th><th>Rot.</th><th>Height</th><th>RPM</th><th>GOE</th><th>Score</th><th>Clean</th></tr>
{jump_rows}
</table>

<h2>🛠️ Errors & Corrections</h2>
{error_html if error_html else '<p style="color:#16a34a">✅ No technical errors detected.</p>'}

<h2>⭐ Priority Recommendations</h2>
<ol class="priority">{priority_html}</ol>

<div class="footer">Generated by ⛸ Figure Skating Analysis System · {date_str}</div>
</body></html>"""

    return html


# ── public API ────────────────────────────────────────────────────────────────

def generate_report(analysis: Dict, lang: str = 'ar', fmt: str = 'pdf') -> bytes:
    """
    fmt: 'pdf' (needs ReportLab) or 'html'
    Returns bytes.
    """
    if fmt == 'pdf' and REPORTLAB_AVAILABLE:
        return build_pdf_reportlab(analysis, lang)
    html = build_html_report(analysis, lang)
    return html.encode('utf-8')


def get_download_button_data(analysis: Dict, lang: str = 'ar') -> tuple:
    """Returns (data_bytes, filename, mime) for st.download_button"""
    if REPORTLAB_AVAILABLE:
        data = generate_report(analysis, lang, fmt='pdf')
        player = analysis.get('player_name', 'report').replace(' ', '_')
        fname = f"skating_report_{player}_{datetime.now().strftime('%Y%m%d')}.pdf"
        mime = 'application/pdf'
    else:
        data = generate_report(analysis, lang, fmt='html')
        player = analysis.get('player_name', 'report').replace(' ', '_')
        fname = f"skating_report_{player}_{datetime.now().strftime('%Y%m%d')}.html"
        mime = 'text/html'
    return data, fname, mime
