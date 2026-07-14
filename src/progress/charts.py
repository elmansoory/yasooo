"""
رسوم تطوّر اللاعب - Plotly للعرض داخل التطبيق + matplotlib PNG للتقارير
Charts for the progress page (Plotly) and PDF reports (matplotlib PNG buffers).
"""
import io
import pandas as pd
import plotly.graph_objects as go

# ── matplotlib setup (for PDF PNGs) ──────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

from src.utils.arabic_text import ar, FONT_REGULAR, fonts_available

_MPL_FONT = "DejaVu Sans"
if fonts_available():
    try:
        font_manager.fontManager.addfont(FONT_REGULAR)
        _MPL_FONT = font_manager.FontProperties(fname=FONT_REGULAR).get_name()
    except Exception:
        pass
plt.rcParams["font.family"] = _MPL_FONT
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#1f77b4"
PURPLE = "#764ba2"
GREEN = "#2ca02c"
GRAY = "#9aa5b1"


def _dates(df, col="evaluation_date"):
    return pd.to_datetime(df[col], errors="coerce")


# ══════════════════════════════════════════════════════════════════
# Plotly (Streamlit display)
# ══════════════════════════════════════════════════════════════════
def score_trend_plotly(evals_df):
    d = evals_df.copy()
    d["dt"] = _dates(d)
    d = d.sort_values("dt")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["dt"], y=d["total_score"], mode="lines+markers",
                             name="الدرجة الكلية", line=dict(color=BLUE, width=3)))
    fig.add_trace(go.Scatter(x=d["dt"], y=d["tes"], mode="lines+markers",
                             name="TES (التقني)", line=dict(color=GREEN, width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=d["dt"], y=d["pcs"], mode="lines+markers",
                             name="PCS (المكوّنات)", line=dict(color=PURPLE, width=2, dash="dot")))
    fig.update_layout(title="تطوّر الدرجات عبر الزمن", xaxis_title="التاريخ",
                      yaxis_title="الدرجة", hovermode="x unified",
                      legend=dict(orientation="h", y=1.12))
    return fig


def jump_success_plotly(evals_df):
    d = evals_df.copy()
    d["dt"] = _dates(d)
    d = d.dropna(subset=["jump_success_rate"]).sort_values("dt")
    if d.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["dt"], y=d["jump_success_rate"], mode="lines+markers",
                             fill="tozeroy", line=dict(color=GREEN, width=3)))
    fig.update_layout(title="نسبة نجاح القفزات (%)", xaxis_title="التاريخ",
                      yaxis_title="%", yaxis=dict(range=[0, 100]))
    return fig


def vs_club_plotly(evals_df, club_avg_df):
    d = evals_df.copy()
    d["month"] = _dates(d).dt.strftime("%Y-%m")
    monthly = d.groupby("month")["total_score"].mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly["month"], y=monthly["total_score"],
                         name="اللاعب", marker_color=BLUE))
    if club_avg_df is not None and not club_avg_df.empty:
        fig.add_trace(go.Scatter(x=club_avg_df["month"], y=club_avg_df["avg_score"],
                                 mode="lines+markers", name="متوسط النادي",
                                 line=dict(color=PURPLE, width=3)))
    fig.update_layout(title="اللاعب مقابل متوسط النادي", xaxis_title="الشهر",
                      yaxis_title="الدرجة", legend=dict(orientation="h", y=1.12))
    return fig


def attendance_trend_plotly(att_df):
    if att_df is None or att_df.empty:
        return None
    d = att_df.copy()
    d["month"] = pd.to_datetime(d["date"], errors="coerce").dt.strftime("%Y-%m")
    monthly = d.groupby("month").size().reset_index(name="count")
    fig = go.Figure(go.Bar(x=monthly["month"], y=monthly["count"], marker_color=BLUE))
    fig.update_layout(title="انتظام الحضور الشهري", xaxis_title="الشهر",
                      yaxis_title="عدد الحصص")
    return fig


# ══════════════════════════════════════════════════════════════════
# matplotlib PNG (PDF embedding)
# ══════════════════════════════════════════════════════════════════
def _fig_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def score_trend_png(evals_df):
    if evals_df is None or evals_df.empty:
        return None
    d = evals_df.copy()
    d["dt"] = _dates(d)
    d = d.sort_values("dt")
    fig, axis = plt.subplots(figsize=(7, 3.2))
    axis.plot(d["dt"], d["total_score"], "-o", color=BLUE, linewidth=2.5, label=ar("الدرجة الكلية"))
    axis.plot(d["dt"], d["tes"], "--o", color=GREEN, linewidth=1.5, label=ar("التقني TES"))
    axis.plot(d["dt"], d["pcs"], "--o", color=PURPLE, linewidth=1.5, label=ar("المكوّنات PCS"))
    axis.set_title(ar("تطوّر الدرجات عبر الزمن"), fontsize=13)
    axis.set_ylabel(ar("الدرجة"))
    axis.grid(True, alpha=0.3)
    axis.legend(loc="best", fontsize=8)
    fig.autofmt_xdate(rotation=30)
    return _fig_to_png(fig)


def attendance_png(att_df):
    if att_df is None or att_df.empty:
        return None
    d = att_df.copy()
    d["month"] = pd.to_datetime(d["date"], errors="coerce").dt.strftime("%Y-%m")
    monthly = d.groupby("month").size()
    if monthly.empty:
        return None
    fig, axis = plt.subplots(figsize=(7, 2.8))
    axis.bar(monthly.index, monthly.values, color=BLUE)
    axis.set_title(ar("انتظام الحضور الشهري"), fontsize=13)
    axis.set_ylabel(ar("عدد الحصص"))
    axis.grid(True, axis="y", alpha=0.3)
    plt.setp(axis.get_xticklabels(), rotation=30, ha="right")
    return _fig_to_png(fig)


def jump_success_png(evals_df):
    if evals_df is None or evals_df.empty:
        return None
    d = evals_df.copy()
    d["dt"] = _dates(d)
    d = d.dropna(subset=["jump_success_rate"]).sort_values("dt")
    if d.empty:
        return None
    fig, axis = plt.subplots(figsize=(7, 2.8))
    axis.fill_between(d["dt"], d["jump_success_rate"], color=GREEN, alpha=0.25)
    axis.plot(d["dt"], d["jump_success_rate"], "-o", color=GREEN, linewidth=2.5)
    axis.set_title(ar("نسبة نجاح القفزات (%)"), fontsize=13)
    axis.set_ylim(0, 100)
    axis.grid(True, alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    return _fig_to_png(fig)
