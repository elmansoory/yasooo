"""
صفحة جدول الحصص الأسبوعي.
Weekly schedule / calendar. Receives DB helpers from app.py.
"""
from datetime import time
from html import escape

import streamlit as st

from src.schedule import service
from src.schedule.service import DAYS_AR


def show_schedule_page(get_data, execute_query, get_connection, clear_cache):
    st.title("📅 جدول الحصص الأسبوعي")
    conn = get_connection()

    tab1, tab2 = st.tabs(["🗓 الجدول الأسبوعي", "⚙️ إضافة وإدارة الحصص"])
    with tab1:
        _weekly(conn)
    with tab2:
        _manage(conn, get_data, clear_cache)


def _weekly(conn):
    df = service.list_sessions(conn)
    if df.empty:
        st.info("لا توجد حصص مجدولة بعد. أضف حصصاً من تبويب «⚙️ إضافة وإدارة الحصص».")
        return
    cols = st.columns(7)
    for d in range(7):
        with cols[d]:
            st.markdown(f"**{DAYS_AR[d]}**")
            day_df = df[df["day_of_week"] == d]
            if day_df.empty:
                st.caption("—")
                continue
            for _, s in day_df.iterrows():
                extra = []
                if s["coach"]:
                    extra.append(f"👤 {escape(str(s['coach']))}")
                if s["level"]:
                    extra.append(f"🎯 {escape(str(s['level']))}")
                if s["location"]:
                    extra.append(f"📍 {escape(str(s['location']))}")
                if s["capacity"]:
                    extra.append(f"👥 {int(s['capacity'])}")
                extra_html = "<br>".join(extra)
                st.markdown(
                    f"""<div style="background:#eef2ff;border-radius:8px;padding:8px 10px;
                              margin:4px 0;border-right:4px solid #667eea;font-size:0.85em;">
                        <b>{escape(str(s['title']))}</b><br>
                        ⏰ {escape(str(s['start_time']))} - {escape(str(s['end_time']))}
                        {'<br>' + extra_html if extra_html else ''}
                    </div>""",
                    unsafe_allow_html=True,
                )


def _manage(conn, get_data, clear_cache):
    coaches = get_data(
        "SELECT DISTINCT coach AS c FROM members WHERE coach IS NOT NULL AND coach!=''"
    )["c"].tolist()

    st.markdown("#### ➕ إضافة حصة")
    with st.form("add_session", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("عنوان الحصة", placeholder="مثال: تدريب على الجليد")
            day = st.selectbox("اليوم", list(range(7)), format_func=lambda d: DAYS_AR[d])
            start_t = st.time_input("وقت البداية", value=time(16, 0))
            end_t = st.time_input("وقت النهاية", value=time(17, 0))
        with c2:
            coach = (st.selectbox("المدرب", ["—"] + coaches) if coaches
                     else st.text_input("المدرب", ""))
            level = st.text_input("المستوى / الفئة", "")
            location = st.text_input("المكان", "")
            capacity = st.number_input("السعة (عدد اللاعبين)", min_value=0, value=0, step=1)
        notes = st.text_input("ملاحظات", "")
        if st.form_submit_button("💾 إضافة الحصة", type="primary"):
            if not title.strip():
                st.error("اكتب عنوان الحصة.")
            else:
                try:
                    service.add_session(
                        conn, title, day, start_t.strftime("%H:%M"), end_t.strftime("%H:%M"),
                        coach=(None if coach in (None, "—", "") else coach),
                        level=level or None, location=location or None,
                        capacity=(capacity if capacity > 0 else None), notes=notes or None)
                    clear_cache()
                    st.success("✅ تمت إضافة الحصة.")
                    st.rerun()
                except ValueError as e:
                    st.error(f"⚠️ {e}")

    st.markdown("#### 🗂 الحصص الحالية")
    df = service.list_sessions(conn)
    if df.empty:
        st.info("لا توجد حصص.")
        return
    show = df.copy()
    show["اليوم"] = show["day_of_week"].map(lambda d: DAYS_AR[int(d)])
    out = show[["اليوم", "title", "start_time", "end_time", "coach", "level", "location"]].copy()
    out.columns = ["اليوم", "العنوان", "البداية", "النهاية", "المدرب", "المستوى", "المكان"]
    out.index = range(1, len(out) + 1)
    st.dataframe(out, use_container_width=True)

    with st.expander("🗑 حذف حصة"):
        ids = df["id"].astype(int).tolist()
        labels = {int(r["id"]): f'{DAYS_AR[int(r["day_of_week"])]} — {r["title"]} ({r["start_time"]})'
                  for _, r in df.iterrows()}
        sid = st.selectbox("اختر الحصة", ids, format_func=lambda i: labels[i], key="sch_del")
        if st.button("🗑 حذف الحصة المحددة", type="secondary"):
            service.delete_session(conn, sid)
            clear_cache()
            st.success("تم الحذف.")
            st.rerun()
