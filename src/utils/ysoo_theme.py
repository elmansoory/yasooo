"""
YASOOO Design System — نظام التصميم الموحّد
مستوحى من واجهة "Ice Skating Analyzer" المرجعية (Cairo/Tajawal، بطاقات مرتفعة عند
المرور، شارات حالة ملوّنة بالحدة، KPI tiles بأيقونات). يُستخدم عبر st.markdown
لحقن CSS مرة واحدة، مع دوال بناء HTML جاهزة لبطاقات الأخطاء وبطاقات KPI.
"""
from __future__ import annotations
from typing import Optional

# ── Severity design tokens (bg / border / text / icon) ─────────────────────────
SEVERITY_STYLE = {
    'critical': {'bg': '#fef2f2', 'border': '#fecaca', 'text': '#991b1b', 'icon': '⛔', 'label_ar': 'حرج'},
    'major':    {'bg': '#fefce8', 'border': '#fde68a', 'text': '#854d0e', 'icon': '⚠️', 'label_ar': 'كبير'},
    'minor':    {'bg': '#f0fdf4', 'border': '#bbf7d0', 'text': '#166534', 'icon': '✅', 'label_ar': 'بسيط'},
}

# Map our existing Arabic/English severity vocabulary onto the 3-tier system
_SEV_MAP = {
    'حرج': 'critical', 'CRITICAL': 'critical',
    'عالي': 'critical', 'HIGH': 'critical',
    'متوسط': 'major', 'MEDIUM': 'major',
    'منخفض': 'minor', 'LOW': 'minor',
}

PHASE_COLORS = {
    'entry': '#2563eb', 'execution': '#7c3aed', 'exit': '#16a34a',
    'دخول': '#2563eb', 'تنفيذ': '#7c3aed', 'خروج': '#16a34a',
}


def normalize_severity(sev: str) -> str:
    return _SEV_MAP.get((sev or '').strip(), 'major')


def inject_theme_css() -> str:
    """Return the <style> block. Call once via st.markdown(..., unsafe_allow_html=True)."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&family=Tajawal:wght@400;500;700;800&display=swap');

    .ysoo-scope, .ysoo-scope * { font-family: 'Cairo','Tajawal',sans-serif !important; }

    .ysoo-kpi-row { display:flex; gap:14px; flex-wrap:wrap; margin:6px 0 18px; }
    .ysoo-kpi {
        flex:1; min-width:150px; background:#ffffff; border:1px solid #e5e7eb;
        border-radius:16px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.06);
        transition:box-shadow .25s ease, transform .25s ease;
    }
    .ysoo-kpi:hover { box-shadow:0 10px 24px rgba(0,0,0,.08); transform:translateY(-2px); }
    .ysoo-kpi .icon { font-size:1.6em; margin-bottom:6px; display:block; }
    .ysoo-kpi .label { font-size:.82em; color:#6b7280; font-weight:500; }
    .ysoo-kpi .value { font-size:1.7em; font-weight:800; color:#111827; margin-top:2px; }

    .ysoo-pill {
        display:inline-flex; align-items:center; gap:6px; padding:4px 12px;
        border-radius:999px; font-size:.82em; font-weight:700;
    }

    .ysoo-error-card {
        border-radius:14px; padding:16px 20px; margin-bottom:16px;
        box-shadow:0 1px 3px rgba(0,0,0,.05); transition:box-shadow .2s ease;
        border-width:1px; border-style:solid;
    }
    .ysoo-error-card:hover { box-shadow:0 8px 20px rgba(0,0,0,.08); }
    .ysoo-error-head { display:flex; align-items:flex-start; justify-content:space-between; gap:12px; margin-bottom:10px; }
    .ysoo-error-title { font-weight:800; font-size:1.05em; display:flex; align-items:center; gap:8px; }
    .ysoo-error-badges { display:flex; align-items:center; gap:8px; margin-top:6px; flex-wrap:wrap; }
    .ysoo-phase-badge {
        border:1px solid currentColor; border-radius:999px; padding:2px 10px;
        font-size:.76em; font-weight:700;
    }
    .ysoo-confidence { text-align:center; min-width:70px; }
    .ysoo-confidence .num { font-size:1.35em; font-weight:800; color:#2563eb; }
    .ysoo-confidence .cap { font-size:.72em; color:#6b7280; }

    .ysoo-box { border-radius:10px; padding:10px 14px; margin-top:8px; font-size:.88em; }
    .ysoo-box-tech { background:rgba(255,255,255,.6); }
    .ysoo-box-fix  { background:#ecfdf5; color:#065f46; }
    .ysoo-box-title { font-weight:700; font-size:.85em; margin-bottom:4px; display:flex; align-items:center; gap:5px; }
    </style>
    """


def kpi_html(icon: str, label: str, value: str) -> str:
    return (
        f"<div class='ysoo-kpi'><span class='icon'>{icon}</span>"
        f"<div class='label'>{label}</div><div class='value'>{value}</div></div>"
    )


def kpi_row_html(items) -> str:
    """items: list of (icon, label, value) tuples."""
    cards = "".join(kpi_html(i, l, v) for i, l, v in items)
    return f"<div class='ysoo-scope ysoo-kpi-row'>{cards}</div>"


def error_card_html(
    title: str,
    severity: str,
    phase_label: Optional[str] = None,
    phase_key: Optional[str] = None,
    confidence: Optional[int] = None,
    tech_details: Optional[str] = None,
    correction: Optional[str] = None,
    extra_stats: Optional[str] = None,
) -> str:
    """Render one error as a severity-colored card, mirroring the reference
    ImprovedErrorDetection.tsx layout: icon+title, phase pill, confidence %,
    a 'technical details' box, and a green 'correction' box."""
    tier = normalize_severity(severity)
    s = SEVERITY_STYLE[tier]
    phase_color = PHASE_COLORS.get(phase_key or '', '#6b7280')

    phase_html = ''
    if phase_label:
        phase_html = (
            f"<span class='ysoo-phase-badge' style='color:{phase_color}'>{phase_label}</span>"
        )

    conf_html = ''
    if confidence is not None:
        conf_html = (
            f"<div class='ysoo-confidence'><div class='num'>{confidence}%</div>"
            f"<div class='cap'>دقة الكشف</div></div>"
        )

    tech_html = ''
    if tech_details:
        stats = f"<div style='margin-top:6px;font-size:.82em;opacity:.85'>{extra_stats}</div>" if extra_stats else ''
        tech_html = (
            f"<div class='ysoo-box ysoo-box-tech'>"
            f"<div class='ysoo-box-title'>🔬 التفاصيل التقنية</div>{tech_details}{stats}</div>"
        )

    fix_html = ''
    if correction:
        fix_html = (
            f"<div class='ysoo-box ysoo-box-fix'>"
            f"<div class='ysoo-box-title'>📈 طريقة التصحيح</div>{correction}</div>"
        )

    return f"""
    <div class="ysoo-scope ysoo-error-card" style="background:{s['bg']};border-color:{s['border']};color:{s['text']}">
      <div class="ysoo-error-head">
        <div>
          <div class="ysoo-error-title">{s['icon']} {title}</div>
          <div class="ysoo-error-badges">{phase_html}</div>
        </div>
        {conf_html}
      </div>
      {tech_html}
      {fix_html}
    </div>
    """
