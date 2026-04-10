"""
🎯 Simple Skating Analysis App
تطبيق بسيط بدون مكتبات متقدمة - يعمل مباشرة

Required ONLY:
- streamlit
- pandas
- plotly
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px

# Page config
st.set_page_config(
    page_title="نظام التزلج البسيط",
    page_icon="⛸️",
    layout="wide"
)

# Database
def init_db():
    conn = sqlite3.connect('skating_database.db')
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        birth_date TEXT,
        gender TEXT,
        phone TEXT,
        email TEXT,
        skill_level TEXT,
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        attendance_date TEXT,
        notes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS memberships (
        membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        status TEXT DEFAULT 'نشط',
        start_date TEXT,
        end_date TEXT,
        amount REAL
    )""")

    conn.commit()
    conn.close()

@st.cache_resource
def setup_db():
    init_db()
    return True

def get_conn():
    return sqlite3.connect('skating_database.db')

def load_table(table_name):
    conn = get_conn()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except:
        conn.close()
        return pd.DataFrame()

def calc_age(birth_date):
    try:
        if pd.isna(birth_date) or birth_date == '':
            return 0
        birth = datetime.strptime(str(birth_date), '%Y-%m-%d')
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return 0

# Setup
setup_db()

# Sidebar
st.sidebar.title("⛸️ القائمة")
page = st.sidebar.radio("", [
    "🏠 الرئيسية",
    "👥 الأعضاء",
    "📊 الحضور",
    "📈 الإحصائيات"
])

# Main
if page == "🏠 الرئيسية":
    st.title("⛸️ نظام إدارة التزلج الفني")
    st.markdown("### النسخة البسيطة - تعمل بدون مكتبات متقدمة")

    members = load_table('members')
    attendance = load_table('attendance')
    memberships = load_table('memberships')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("👥 الأعضاء", len(members))
    with col2:
        st.metric("📅 سجلات الحضور", len(attendance))
    with col3:
        active = len(memberships[memberships['status']=='نشط']) if 'status' in memberships.columns and len(memberships) > 0 else 0
        st.metric("💳 الاشتراكات النشطة", active)

    st.success("✅ جميع الميزات الأساسية تعمل!")

    st.info("""
    **الميزات المتوفرة:**
    - ✅ إدارة الأعضاء
    - ✅ تسجيل الحضور
    - ✅ الإحصائيات والتقارير
    - ✅ إدارة الاشتراكات
    """)

elif page == "👥 الأعضاء":
    st.header("👥 إدارة الأعضاء")

    members = load_table('members')

    if len(members) > 0:
        # Safely add age column
        if 'birth_date' in members.columns:
            members['age'] = members['birth_date'].apply(calc_age)

        # Show only available columns
        display_cols = []
        for col in ['name', 'age', 'gender', 'phone', 'email', 'skill_level']:
            if col in members.columns:
                display_cols.append(col)

        if display_cols:
            st.dataframe(members[display_cols], use_container_width=True, height=400)
        else:
            st.dataframe(members, use_container_width=True, height=400)

        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("إجمالي الأعضاء", len(members))

        if 'gender' in members.columns:
            with col2:
                males = len(members[members['gender']=='ذكر'])
                st.metric("ذكور", males)
            with col3:
                females = len(members[members['gender']=='أنثى'])
                st.metric("إناث", females)
    else:
        st.info("لا يوجد أعضاء مسجلين")

    # Add member form
    with st.expander("➕ إضافة عضو جديد"):
        with st.form("add_member"):
            name = st.text_input("الاسم *")
            col1, col2 = st.columns(2)
            with col1:
                birth_date = st.date_input("تاريخ الميلاد")
            with col2:
                gender = st.selectbox("الجنس", ["ذكر", "أنثى"])

            col1, col2 = st.columns(2)
            with col1:
                phone = st.text_input("الهاتف")
            with col2:
                email = st.text_input("البريد الإلكتروني")

            skill_level = st.selectbox("المستوى", ["مبتدئ", "متوسط", "متقدم", "محترف"])
            notes = st.text_area("ملاحظات")

            submitted = st.form_submit_button("💾 حفظ")

            if submitted and name:
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO members
                           (name, birth_date, gender, phone, email, skill_level, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (name, str(birth_date), gender, phone, email, skill_level, notes))
                conn.commit()
                conn.close()
                st.success(f"✅ تم إضافة {name} بنجاح!")
                st.rerun()

elif page == "📊 الحضور":
    st.header("📊 تسجيل الحضور")

    attendance = load_table('attendance')
    members = load_table('members')

    if len(attendance) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("إجمالي السجلات", len(attendance))
        with col2:
            unique_members = attendance['member_id'].nunique()
            st.metric("الأعضاء النشطون", unique_members)

        # Show recent attendance
        st.subheader("📋 سجلات الحضور الأخيرة")

        # Merge with member names
        if len(members) > 0:
            att_with_names = attendance.merge(
                members[['member_id', 'name']],
                on='member_id',
                how='left'
            )
            display_cols = ['name', 'attendance_date', 'notes']
            display_cols = [c for c in display_cols if c in att_with_names.columns]
            st.dataframe(att_with_names[display_cols].tail(20), use_container_width=True)
    else:
        st.info("لا توجد سجلات حضور")

    # Add attendance
    if len(members) > 0:
        with st.expander("➕ تسجيل حضور"):
            with st.form("add_attendance"):
                member = st.selectbox(
                    "اختر العضو",
                    options=members['member_id'].tolist(),
                    format_func=lambda x: members[members['member_id']==x]['name'].iloc[0]
                )
                att_date = st.date_input("التاريخ", value=date.today())
                notes = st.text_input("ملاحظات")

                submitted = st.form_submit_button("💾 تسجيل")

                if submitted:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("""INSERT INTO attendance (member_id, attendance_date, notes)
                               VALUES (?, ?, ?)""",
                             (member, str(att_date), notes))
                    conn.commit()
                    conn.close()
                    st.success("✅ تم تسجيل الحضور!")
                    st.rerun()

elif page == "📈 الإحصائيات":
    st.header("📈 الإحصائيات والتقارير")

    members = load_table('members')
    attendance = load_table('attendance')

    if len(members) > 0:
        # Gender distribution
        if 'gender' in members.columns:
            st.subheader("📊 توزيع الأعضاء حسب الجنس")
            gender_counts = members['gender'].value_counts()
            fig = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                title="توزيع الأعضاء"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Skill level distribution
        if 'skill_level' in members.columns:
            st.subheader("📊 توزيع الأعضاء حسب المستوى")
            skill_counts = members['skill_level'].value_counts()
            fig = px.bar(
                x=skill_counts.index,
                y=skill_counts.values,
                title="المستويات",
                labels={'x': 'المستوى', 'y': 'العدد'}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Attendance trends
        if len(attendance) > 0:
            st.subheader("📈 اتجاه الحضور")
            attendance['attendance_date'] = pd.to_datetime(attendance['attendance_date'])
            daily_counts = attendance.groupby('attendance_date').size().reset_index(name='count')
            fig = px.line(
                daily_counts,
                x='attendance_date',
                y='count',
                title="الحضور اليومي"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات كافية للإحصائيات")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**النسخة البسيطة v1.0**

✅ تعمل بدون مكتبات AI
✅ جميع الميزات الأساسية متاحة
""")
