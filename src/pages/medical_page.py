"""
صفحة السجلات الطبية - Medical Records Page
تتبع الحالة الصحية للرياضيين في نظام التزلج الفني
"""
import streamlit as st
import sqlite3
import pandas as pd
import io
import sys
from pathlib import Path
from datetime import date, datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

DB_PATH = "skating_database.db"


def _get_conn():
    return sqlite3.connect(DB_PATH)


def _init_db():
    """إنشاء جدول السجلات الطبية إن لم يكن موجوداً"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skater_name TEXT NOT NULL,
                record_type TEXT,
                record_date TEXT,
                description TEXT,
                severity TEXT,
                status TEXT,
                doctor_name TEXT,
                return_date TEXT,
                attachments TEXT,
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    finally:
        conn.close()


def _get_skaters():
    """جلب أسماء المتزلجين"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM skaters ORDER BY name")
        rows = cur.fetchall()
        return [r[0] for r in rows] if rows else []
    except Exception:
        return []
    finally:
        conn.close()


def _get_active_injuries():
    """جلب عدد الإصابات النشطة حالياً"""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM medical_records WHERE record_type='injury' AND status='active'"
        )
        return cur.fetchone()[0]
    except Exception:
        return 0
    finally:
        conn.close()


def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            df.to_excel(w, index=False)
        return buf.getvalue()
    except Exception:
        return df.to_csv(index=False).encode('utf-8-sig')


# ---------------------------------------------------------------------------
# Tab 1 — السجلات الطبية
# ---------------------------------------------------------------------------

def _tab_records():
    st.subheader("📋 السجلات الطبية")

    col_f1, col_f2, col_f3 = st.columns(3)

    skaters = _get_skaters()
    skater_filter_options = ["الكل"] + skaters

    with col_f1:
        filter_skater = st.selectbox("تصفية حسب المتزلج", skater_filter_options, key="med_filter_skater")
    with col_f2:
        filter_type = st.selectbox(
            "تصفية حسب النوع",
            ["الكل", "injury", "checkup", "clearance", "note"],
            key="med_filter_type"
        )
    with col_f3:
        filter_status = st.selectbox(
            "تصفية حسب الحالة",
            ["الكل", "active", "recovered", "monitoring"],
            key="med_filter_status"
        )

    conn = _get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM medical_records ORDER BY record_date DESC, created_at DESC",
            conn
        )
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        conn.close()
        return
    finally:
        conn.close()

    # تطبيق الفلاتر
    if filter_skater != "الكل" and not df.empty:
        df = df[df['skater_name'] == filter_skater]
    if filter_type != "الكل" and not df.empty:
        df = df[df['record_type'] == filter_type]
    if filter_status != "الكل" and not df.empty:
        df = df[df['status'] == filter_status]

    if df.empty:
        st.info("لا توجد سجلات تطابق معايير البحث.")
        return

    # تلوين الصفوف حسب النوع
    type_icons = {
        "injury": "🔴 إصابة",
        "checkup": "🟢 فحص دوري",
        "clearance": "🔵 تصريح طبي",
        "note": "📝 ملاحظة"
    }
    status_labels = {
        "active": "نشط",
        "recovered": "تعافى",
        "monitoring": "تحت المتابعة"
    }
    severity_labels = {
        "minor": "بسيطة",
        "moderate": "متوسطة",
        "severe": "شديدة"
    }

    df_display = df.copy()
    df_display['record_type'] = df_display['record_type'].map(type_icons).fillna(df_display['record_type'])
    df_display['status'] = df_display['status'].map(status_labels).fillna(df_display['status'])
    df_display['severity'] = df_display['severity'].map(severity_labels).fillna(df_display['severity'])

    col_names = {
        "id": "الرقم",
        "skater_name": "المتزلج",
        "record_type": "النوع",
        "record_date": "التاريخ",
        "description": "الوصف",
        "severity": "الشدة",
        "status": "الحالة",
        "doctor_name": "الطبيب",
        "return_date": "تاريخ العودة",
        "created_by": "أنشأ بواسطة",
        "created_at": "تاريخ الإنشاء",
        "attachments": "المرفقات"
    }
    df_display = df_display.rename(columns=col_names)
    # إزالة الأعمدة غير الضرورية من العرض
    display_cols = ["الرقم", "المتزلج", "النوع", "التاريخ", "الوصف", "الشدة", "الحالة", "الطبيب", "تاريخ العودة"]
    display_cols = [c for c in display_cols if c in df_display.columns]
    st.dataframe(df_display[display_cols], use_container_width=True)

    excel_data = _to_excel(df)
    st.download_button(
        label="📥 تصدير إلى Excel",
        data=excel_data,
        file_name="medical_records.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_medical"
    )


# ---------------------------------------------------------------------------
# Tab 2 — إضافة سجل
# ---------------------------------------------------------------------------

def _tab_add_record():
    st.subheader("➕ إضافة سجل طبي جديد")

    skaters = _get_skaters()

    with st.form("add_medical_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if skaters:
                skater_name = st.selectbox("اسم المتزلج *", skaters, key="med_skater")
            else:
                skater_name = st.text_input("اسم المتزلج *", key="med_skater_txt")

            record_type = st.selectbox(
                "نوع السجل *",
                ["injury", "checkup", "clearance", "note"],
                format_func=lambda x: {
                    "injury": "🔴 إصابة",
                    "checkup": "🟢 فحص دوري",
                    "clearance": "🔵 تصريح طبي",
                    "note": "📝 ملاحظة"
                }.get(x, x)
            )
            record_date = st.date_input("تاريخ السجل *", value=date.today())
            description = st.text_area("الوصف *", height=100)

        with col2:
            severity = st.selectbox(
                "شدة الإصابة (للإصابات فقط)",
                ["minor", "moderate", "severe"],
                format_func=lambda x: {"minor": "بسيطة", "moderate": "متوسطة", "severe": "شديدة"}.get(x, x)
            )
            status = st.selectbox(
                "الحالة",
                ["active", "recovered", "monitoring"],
                format_func=lambda x: {"active": "نشط", "recovered": "تعافى", "monitoring": "تحت المتابعة"}.get(x, x)
            )
            doctor_name = st.text_input("اسم الطبيب")
            return_date = st.date_input(
                "تاريخ العودة المتوقعة للتدريب",
                value=None,
                help="اتركه فارغاً إذا لم يُحدد بعد"
            )
            created_by = st.text_input("أنشئ بواسطة")

        submitted = st.form_submit_button("💾 حفظ السجل")
        if submitted:
            sname = skater_name if isinstance(skater_name, str) else str(skater_name)
            if not sname.strip():
                st.error("يرجى إدخال اسم المتزلج.")
            elif not description.strip():
                st.error("يرجى إدخال وصف السجل.")
            else:
                try:
                    return_date_str = str(return_date) if return_date else None
                    conn = _get_conn()
                    cur = conn.cursor()
                    cur.execute(
                        """INSERT INTO medical_records
                           (skater_name, record_type, record_date, description, severity,
                            status, doctor_name, return_date, created_by)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (
                            sname.strip(), record_type, str(record_date),
                            description.strip(), severity, status,
                            doctor_name.strip(), return_date_str, created_by.strip()
                        )
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ تم حفظ السجل الطبي لـ '{sname}' بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في الحفظ: {e}")


# ---------------------------------------------------------------------------
# Tab 3 — إحصائيات
# ---------------------------------------------------------------------------

def _tab_statistics():
    import plotly.express as px

    st.subheader("📊 إحصائيات طبية")

    conn = _get_conn()
    try:
        df = pd.read_sql_query("SELECT * FROM medical_records", conn)
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        conn.close()
        return
    finally:
        conn.close()

    if df.empty:
        st.info("لا توجد سجلات طبية بعد.")
        return

    # مؤشرات الأداء
    total = len(df)
    injuries = df[df['record_type'] == 'injury']
    active_injuries = injuries[injuries['status'] == 'active']
    recovered = injuries[injuries['status'] == 'recovered']

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("إجمالي السجلات", total)
    with col2:
        st.metric("إجمالي الإصابات", len(injuries))
    with col3:
        st.metric("إصابات نشطة", len(active_injuries))
    with col4:
        st.metric("حالات التعافي", len(recovered))

    st.markdown("---")

    # قائمة الرياضيين المصابين حالياً
    if not active_injuries.empty:
        st.subheader("⚠️ الرياضيون المصابون حالياً")
        today = date.today()
        active_display = active_injuries[['skater_name', 'description', 'severity', 'return_date', 'doctor_name']].copy()

        # حساب أيام العودة المتوقعة
        def days_until_return(ret_date_str):
            if not ret_date_str or pd.isna(ret_date_str):
                return "غير محدد"
            try:
                ret_date = datetime.strptime(str(ret_date_str), "%Y-%m-%d").date()
                delta = (ret_date - today).days
                if delta < 0:
                    return f"متأخر {abs(delta)} يوم"
                elif delta == 0:
                    return "اليوم"
                else:
                    return f"{delta} يوم"
            except Exception:
                return "غير محدد"

        active_display['أيام حتى العودة'] = active_display['return_date'].apply(days_until_return)
        active_display = active_display.rename(columns={
            'skater_name': 'المتزلج',
            'description': 'الوصف',
            'severity': 'الشدة',
            'return_date': 'تاريخ العودة',
            'doctor_name': 'الطبيب'
        })
        active_display['الشدة'] = active_display['الشدة'].map(
            {"minor": "بسيطة", "moderate": "متوسطة", "severe": "شديدة"}
        ).fillna(active_display['الشدة'])
        st.dataframe(active_display, use_container_width=True)

    st.markdown("---")

    # مخطط الإصابات حسب الشدة
    if not injuries.empty:
        severity_map = {"minor": "بسيطة", "moderate": "متوسطة", "severe": "شديدة"}
        inj_sev = injuries.copy()
        inj_sev['severity_ar'] = inj_sev['severity'].map(severity_map).fillna(inj_sev['severity'])
        sev_counts = inj_sev['severity_ar'].value_counts().reset_index()
        sev_counts.columns = ['الشدة', 'العدد']
        fig_sev = px.bar(
            sev_counts,
            x='الشدة',
            y='العدد',
            title='📊 توزيع الإصابات حسب الشدة',
            color='الشدة',
            color_discrete_map={"بسيطة": "#4CAF50", "متوسطة": "#FF9800", "شديدة": "#F44336"}
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    # مخطط أنواع السجلات الطبية
    type_map = {"injury": "إصابة", "checkup": "فحص دوري", "clearance": "تصريح طبي", "note": "ملاحظة"}
    df_types = df.copy()
    df_types['record_type_ar'] = df_types['record_type'].map(type_map).fillna(df_types['record_type'])
    type_counts = df_types['record_type_ar'].value_counts().reset_index()
    type_counts.columns = ['نوع السجل', 'العدد']
    fig_types = px.pie(
        type_counts,
        values='العدد',
        names='نوع السجل',
        title='🔍 توزيع أنواع السجلات الطبية',
        color_discrete_map={
            "إصابة": "#F44336",
            "فحص دوري": "#4CAF50",
            "تصريح طبي": "#2196F3",
            "ملاحظة": "#9E9E9E"
        }
    )
    st.plotly_chart(fig_types, use_container_width=True)

    # الرياضيون الأكثر إصابةً
    if not injuries.empty:
        st.subheader("📉 الرياضيون الأكثر إصابةً")
        inj_by_skater = injuries['skater_name'].value_counts().reset_index()
        inj_by_skater.columns = ['المتزلج', 'عدد الإصابات']
        fig_inj = px.bar(
            inj_by_skater.head(10),
            x='المتزلج',
            y='عدد الإصابات',
            title='🏥 أكثر 10 رياضيين إصابةً',
            color='عدد الإصابات',
            color_continuous_scale='reds'
        )
        fig_inj.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_inj, use_container_width=True)

    # تصدير
    excel_data = _to_excel(df)
    st.download_button(
        label="📥 تصدير الإحصائيات إلى Excel",
        data=excel_data,
        file_name="medical_statistics.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="dl_med_stats"
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def show_medical_page(lang='ar'):
    """الدالة الرئيسية لصفحة السجلات الطبية"""
    ar = lang == 'ar'

    # تهيئة قاعدة البيانات
    try:
        _init_db()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return

    st.title("🏥 السجلات الطبية")
    st.markdown("تتبع الحالة الصحية والإصابات للرياضيين" if ar else "Athlete Health & Medical Records")

    # تنبيه الإصابات النشطة
    try:
        active_count = _get_active_injuries()
        if active_count > 0:
            st.warning(f"⚠️ {active_count} لاعب{'ون' if active_count > 1 else ''} مصاب{'ون' if active_count > 1 else ''} حالياً")
    except Exception:
        pass

    tabs = st.tabs([
        "📋 السجلات الطبية",
        "➕ إضافة سجل",
        "📊 إحصائيات"
    ])

    with tabs[0]:
        try:
            _tab_records()
        except Exception as e:
            st.error(f"خطأ في تبويب السجلات: {e}")

    with tabs[1]:
        try:
            _tab_add_record()
        except Exception as e:
            st.error(f"خطأ في تبويب الإضافة: {e}")

    with tabs[2]:
        try:
            _tab_statistics()
        except Exception as e:
            st.error(f"خطأ في تبويب الإحصائيات: {e}")


# ---------------------------------------------------------------------------
# Standalone run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    show_medical_page()
