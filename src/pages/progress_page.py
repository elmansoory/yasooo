"""
صفحة تتبّع تطوّر اللاعبين - Player Progress Tracking page.
Receives DB helpers from app.py to share the cached connection.
"""
from datetime import date, datetime

import streamlit as st

from src.progress import service, charts
from src.utils import settings as club_settings

try:
    from src.utils.member_pdf import build_member_progress_pdf, PDF_AVAILABLE
except Exception:
    PDF_AVAILABLE = False


def show_progress_page(get_data, execute_query, get_connection, clear_cache):
    st.title("📈 تتبّع تطوّر اللاعبين")
    st.caption("سجّل تقييمات الأداء وتابع تطوّر كل لاعب بالأرقام والرسوم البيانية")

    conn = get_connection()
    members_df = get_data("SELECT * FROM members ORDER BY name")
    if len(members_df) == 0:
        st.warning("لا يوجد لاعبون. أضف لاعبين من صفحة «إدارة الأعضاء» أولاً.")
        return

    coaches = sorted([c for c in members_df["coach"].dropna().unique().tolist() if str(c).strip()])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 تطوّر اللاعب", "➕ تسجيل تقييم", "🏆 نظرة عامة على النادي", "⚙️ إعدادات التقرير"])

    with tab1:
        _player_tab(conn, members_df)
    with tab2:
        _record_tab(conn, members_df, coaches, clear_cache)
    with tab3:
        _overview_tab(conn)
    with tab4:
        _settings_tab()


# ─────────────────────────────────────────────────────────────
def _player_tab(conn, members_df):
    search = st.text_input("🔍 ابحث عن لاعب", "", key="prog_search")
    df = members_df
    if search:
        df = df[df["name"].str.lower().str.contains(search.lower(), na=False)]
    if df.empty:
        st.info("لا توجد نتائج"); return
    ids = df["id"].astype(int).tolist()
    label_map = {int(r["id"]): f'{r["name"]} (#{int(r["id"])})' for _, r in df.iterrows()}
    mid = st.selectbox("اختر اللاعب", ids, format_func=lambda i: label_map[i], key="prog_select")
    member = members_df[members_df["id"] == mid].iloc[0]
    selected = member["name"]

    summary, ev = service.member_summary(conn, mid)
    att = service.get_member_attendance(conn, mid)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📋 عدد التقييمات", summary["count"])
    c2.metric("⭐ آخر درجة", summary["latest"] if summary["latest"] is not None else "—")
    c3.metric("🏅 أفضل درجة", summary["best"] if summary["best"] is not None else "—")
    delta = None
    if summary["improvement"] is not None:
        delta = f"{summary['improvement']:+.1f}"
    c4.metric("📈 التطوّر", summary["average"] if summary["average"] is not None else "—", delta=delta)

    if summary["count"] == 0:
        st.info("لا توجد تقييمات لهذا اللاعب بعد. سجّل أول تقييم من تبويب «➕ تسجيل تقييم».")
    else:
        st.markdown("---")
        st.plotly_chart(charts.score_trend_plotly(ev), use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            jf = charts.jump_success_plotly(ev)
            if jf:
                st.plotly_chart(jf, use_container_width=True)
            else:
                st.info("لم تُسجَّل نسب نجاح قفزات بعد.")
        with col2:
            club_avg = service.get_club_average_over_time(conn)
            st.plotly_chart(charts.vs_club_plotly(ev, club_avg), use_container_width=True)

        af = charts.attendance_trend_plotly(att)
        if af:
            st.plotly_chart(af, use_container_width=True)

        st.markdown("#### 📝 آخر التقييمات")
        show = ev.sort_values("evaluation_date", ascending=False).head(10)[
            ["evaluation_date", "evaluation_type", "total_score", "tes", "pcs",
             "jump_success_rate", "coach", "notes"]].copy()
        show.columns = ["التاريخ", "النوع", "الكلية", "TES", "PCS", "نجاح القفزات %", "المدرب", "ملاحظات"]
        show.index = range(1, len(show) + 1)
        st.dataframe(show, use_container_width=True)

    # ── PDF download ──
    st.markdown("---")
    st.markdown("#### 📄 تقرير PDF احترافي")
    if not PDF_AVAILABLE:
        st.warning("مكتبة توليد PDF غير متاحة في هذه البيئة.")
    else:
        if st.button("🖨️ توليد تقرير PDF للاعب", key="gen_pdf", type="primary"):
            with st.spinner("جاري إنشاء التقرير..."):
                try:
                    club_avg = service.get_club_average_over_time(conn)
                    pdf_bytes = build_member_progress_pdf(
                        member.to_dict(), att, ev, summary,
                        club_avg_df=club_avg, settings=club_settings.load_settings())
                    st.session_state["last_pdf"] = pdf_bytes
                    st.session_state["last_pdf_name"] = f"تقرير_{selected}.pdf"
                    st.session_state["last_pdf_mid"] = mid
                except Exception as exc:
                    st.error(f"تعذّر إنشاء التقرير: {exc}")
        if st.session_state.get("last_pdf") and st.session_state.get("last_pdf_mid") == mid:
            st.download_button("⬇️ تحميل التقرير", data=st.session_state["last_pdf"],
                               file_name=st.session_state.get("last_pdf_name", "report.pdf"),
                               mime="application/pdf")


# ─────────────────────────────────────────────────────────────
def _record_tab(conn, members_df, coaches, clear_cache):
    st.markdown("#### ➕ تسجيل تقييم أداء جديد")
    with st.form("eval_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            rec_ids = members_df["id"].astype(int).tolist()
            rec_labels = {int(r["id"]): f'{r["name"]} (#{int(r["id"])})'
                          for _, r in members_df.iterrows()}
            mid = st.selectbox("اللاعب", rec_ids, format_func=lambda i: rec_labels[i])
            ev_date = st.date_input("تاريخ التقييم", value=date.today())
            ev_type = st.selectbox("نوع التقييم",
                                   ["training", "competition", "test"],
                                   format_func=lambda x: {"training": "تدريب",
                                                          "competition": "مسابقة",
                                                          "test": "اختبار"}[x])
            coach = st.selectbox("المدرب", ["—"] + coaches) if coaches else st.text_input("المدرب", "")
        with c2:
            tes = st.number_input("الدرجة التقنية TES", min_value=0.0, value=0.0, step=0.5)
            pcs = st.number_input("درجة المكوّنات PCS", min_value=0.0, value=0.0, step=0.5)
            deductions = st.number_input("الخصومات (Deductions)", min_value=0.0, value=0.0, step=0.5)
            jump = st.slider("نسبة نجاح القفزات %", 0, 100, 0)
        c3, c4 = st.columns(2)
        with c3:
            elements = st.number_input("عدد العناصر", min_value=0, value=0, step=1)
        with c4:
            falls = st.number_input("عدد السقطات", min_value=0, value=0, step=1)
        notes = st.text_area("ملاحظات المدرب", "")
        total_preview = round(tes + pcs - deductions, 2)
        st.info(f"الدرجة الكلية المحسوبة: **{total_preview}** (TES + PCS − الخصومات)")
        submitted = st.form_submit_button("💾 حفظ التقييم", type="primary")

    if submitted:
        member_name = members_df[members_df["id"] == mid].iloc[0]["name"]
        coach_val = None if (coach in (None, "—", "")) else coach
        service.save_evaluation(
            conn, mid, ev_date.strftime("%Y-%m-%d"), tes=tes, pcs=pcs,
            deductions=deductions, jump_success_rate=(jump if jump > 0 else None),
            elements_count=elements, falls_count=falls, coach=coach_val,
            notes=notes.strip() or None, evaluation_type=ev_type, source="manual")
        clear_cache()
        st.success(f"✅ تم حفظ تقييم {member_name} بتاريخ {ev_date}")
        st.balloons()


# ─────────────────────────────────────────────────────────────
def _overview_tab(conn):
    st.markdown("#### 🏆 أداء النادي العام")
    all_ev = service.get_all_evaluations(conn)
    if all_ev.empty:
        st.info("لا توجد تقييمات بعد على مستوى النادي. ابدأ بتسجيل التقييمات.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("📋 إجمالي التقييمات", len(all_ev))
    c2.metric("👥 لاعبون مُقيَّمون", all_ev["member_id"].nunique())
    c3.metric("⭐ متوسط الدرجة", f"{all_ev['total_score'].mean():.1f}")

    st.markdown("---")
    club_avg = service.get_club_average_over_time(conn)
    if not club_avg.empty:
        import plotly.graph_objects as go
        fig = go.Figure(go.Scatter(x=club_avg["month"], y=club_avg["avg_score"],
                                   mode="lines+markers", line=dict(color="#764ba2", width=3)))
        fig.update_layout(title="متوسط درجات النادي شهرياً", xaxis_title="الشهر",
                          yaxis_title="متوسط الدرجة")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 🚀 أكثر اللاعبين تطوّراً")
    imp = service.top_improvers(conn, limit=8)
    if imp.empty:
        st.info("يلزم تقييمان على الأقل لكل لاعب لحساب التطوّر.")
    else:
        show = imp[["member_name", "first", "last", "improvement", "count"]].copy()
        show.columns = ["اللاعب", "أول درجة", "آخر درجة", "مقدار التطوّر", "عدد التقييمات"]
        show.index = range(1, len(show) + 1)
        st.dataframe(show, use_container_width=True)


# ─────────────────────────────────────────────────────────────
def _settings_tab():
    st.markdown("#### ⚙️ إعدادات تقارير PDF")
    s = club_settings.load_settings()
    name = st.text_input("اسم النادي", s.get("club_name", ""))
    sub = st.text_input("العبارة التعريفية", s.get("club_subtitle", ""))
    logo = st.file_uploader("شعار النادي (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if st.button("💾 حفظ الإعدادات", type="primary"):
        club_settings.save_settings({"club_name": name, "club_subtitle": sub})
        if logo is not None:
            club_settings.save_logo(logo.getvalue())
        st.success("✅ تم حفظ الإعدادات. ستظهر في تقارير PDF.")
    cur = club_settings.load_settings()
    if cur.get("logo_path"):
        import os
        if os.path.exists(cur["logo_path"]):
            st.image(cur["logo_path"], width=120, caption="الشعار الحالي")
