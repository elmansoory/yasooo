"""
صفحة المالية - الإيرادات وتنبيهات تجديد الاشتراكات.
Finance dashboard + renewal alerts. Receives DB helpers from app.py.
"""
from datetime import date

import pandas as pd
import streamlit as st
import plotly.express as px

from src.finance import service

_STATUS_AR = {"active": "🟢 نشط", "expiring": "🟠 يقترب الانتهاء",
              "expired": "🔴 منتهٍ", "none": "⚪ لا يوجد اشتراك", "unknown": "❔ غير معروف"}


def show_finance_page(get_data, execute_query, get_connection, clear_cache):
    st.title("💰 لوحة المالية وتنبيهات التجديد")
    conn = get_connection()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 نظرة عامة", "🔔 تنبيهات التجديد", "🧾 سجل المدفوعات", "➕ تسجيل دفعة"])

    with tab1:
        _overview(conn)
    with tab2:
        _alerts(conn)
    with tab3:
        _payments(conn, execute_query, clear_cache)
    with tab4:
        _new_payment(conn, get_data, execute_query, clear_cache)


def _overview(conn):
    t = service.revenue_totals(conn)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 إجمالي الإيرادات", f"{t['gross']:,.0f} ج")
    c2.metric("🎁 إجمالي الخصومات", f"{t['discount']:,.0f} ج")
    c3.metric("✅ الصافي", f"{t['net']:,.0f} ج")
    c4.metric("🧾 عدد المدفوعات", t["count"])

    if t["count"] == 0:
        st.info("لا توجد مدفوعات مسجّلة بعد. أضف دفعة من تبويب «➕ تسجيل دفعة».")
        return

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        mr = service.monthly_revenue(conn)
        if not mr.empty:
            fig = px.bar(mr, x="month", y="revenue", title="الإيرادات الشهرية",
                         labels={"month": "الشهر", "revenue": "الإيراد"})
            fig.update_traces(marker_color="#27ae60")
            fig.update_layout(height=320)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        rb = service.revenue_by_bundle(conn)
        if not rb.empty:
            fig2 = px.pie(rb, names="bundle_type", values="revenue",
                          title="الإيرادات حسب الباقة", hole=0.4)
            fig2.update_layout(height=320)
            st.plotly_chart(fig2, use_container_width=True)


def _alerts(conn):
    st.markdown("#### 🔔 اللاعبون الذين يحتاجون متابعة تجديد")
    within = st.slider("نطاق التنبيه قبل الانتهاء (أيام)", 3, 60, 14, key="fin_within")
    df = service.renewal_alerts(conn, within_days=within)
    status_all = service.membership_status(conn, within_days=within)

    if not status_all.empty:
        n_exp = int((status_all["status"] == "expired").sum())
        n_soon = int((status_all["status"] == "expiring").sum())
        n_none = int((status_all["status"] == "none").sum())
        n_active = int((status_all["status"] == "active").sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 منتهٍ", n_exp)
        c2.metric("🟠 يقترب", n_soon)
        c3.metric("⚪ بلا اشتراك", n_none)
        c4.metric("🟢 نشط", n_active)

    if df.empty:
        st.success("🎉 لا توجد تنبيهات — جميع الاشتراكات نشطة.")
        return

    show = df.copy()
    show["الحالة"] = show["status"].map(_STATUS_AR)
    show["الأيام المتبقية"] = show["days_left"].apply(
        lambda x: "—" if pd.isna(x) else (f"{int(x)} يوم" if x >= 0 else f"متأخر {abs(int(x))} يوم"))
    out = show[["name", "bundle_type", "payment_date", "expiry_date",
                "الأيام المتبقية", "الحالة"]].copy()
    out.columns = ["اللاعب", "الباقة", "تاريخ آخر دفعة", "تاريخ الانتهاء",
                   "الأيام المتبقية", "الحالة"]
    out.index = range(1, len(out) + 1)
    st.dataframe(out, use_container_width=True)


def _payments(conn, execute_query, clear_cache):
    st.markdown("#### 🧾 سجل المدفوعات")
    df = service.all_payments(conn)
    if df.empty:
        st.info("لا توجد مدفوعات.")
        return
    show = df.copy()
    show.columns = ["م", "اللاعب", "الباقة", "المبلغ", "الخصم", "تاريخ الدفع", "المدة (شهور)"]
    show_display = show.drop(columns=["م"])
    show_display.index = range(1, len(show_display) + 1)
    st.dataframe(show_display, use_container_width=True)

    with st.expander("🗑 حذف دفعة"):
        ids = df["id"].astype(int).tolist()
        labels = {int(r["id"]): f'{r["name"]} — {r["amount"]:,.0f}ج — {r["payment_date"]}'
                  for _, r in df.iterrows()}
        pid = st.selectbox("اختر الدفعة", ids, format_func=lambda i: labels[i], key="fin_del")
        if st.button("🗑 حذف الدفعة المحددة", type="secondary"):
            execute_query("DELETE FROM memberships WHERE id=?", (int(pid),))
            clear_cache()
            st.success("تم حذف الدفعة.")
            st.rerun()


def _new_payment(conn, get_data, execute_query, clear_cache):
    st.markdown("#### ➕ تسجيل دفعة جديدة")
    members = get_data("SELECT id, name, bundle FROM members ORDER BY name")
    if members.empty:
        st.warning("أضف لاعبين أولاً من «إدارة الأعضاء».")
        return
    bundles = get_data(
        "SELECT DISTINCT bundle AS b FROM members WHERE bundle IS NOT NULL AND bundle!=''"
    )["b"].tolist()

    with st.form("new_payment", clear_on_submit=True):
        ids = members["id"].astype(int).tolist()
        labels = {int(r["id"]): f'{r["name"]} (#{int(r["id"])})' for _, r in members.iterrows()}
        mid = st.selectbox("اللاعب", ids, format_func=lambda i: labels[i])
        c1, c2 = st.columns(2)
        with c1:
            if bundles:
                bundle = st.selectbox("الباقة", bundles + ["✏️ أخرى"])
                if bundle == "✏️ أخرى":
                    bundle = st.text_input("اكتب اسم الباقة", "")
            else:
                bundle = st.text_input("الباقة", "")
            amount = st.number_input("المبلغ (ج)", min_value=0.0, value=0.0, step=50.0)
        with c2:
            discount = st.number_input("الخصم (ج)", min_value=0.0, value=0.0, step=10.0)
            pay_date = st.date_input("تاريخ الدفع", value=date.today())
            duration = st.number_input("مدة الاشتراك (شهور)", min_value=1, value=1, step=1)
        submitted = st.form_submit_button("💾 حفظ الدفعة", type="primary")

    if submitted:
        execute_query(
            """INSERT INTO memberships
               (member_id, bundle_type, amount, payment_date, discount, duration_months)
               VALUES (?,?,?,?,?,?)""",
            (int(mid), bundle or None, float(amount), pay_date.strftime("%Y-%m-%d"),
             float(discount), int(duration)),
        )
        clear_cache()
        st.success("✅ تم تسجيل الدفعة.")
        st.balloons()
