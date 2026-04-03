"""
🎿 نظام تحليل أداء لاعبي التزلج - نسخة محسنة
Optimized Skating Analysis & Attendance System
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# إضافة مسار src إلى PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# استيراد نظام التحسين
from src.utils.cache_manager import cached, cache_stats, monitor_performance
from src.utils.data_optimizer import (
    DataOptimizer,
    StreamlitOptimizer,
    DatabaseConnectionPool,
    QueryBuilder
)

# إعداد الصفحة بشكل محسن
st.set_page_config(**StreamlitOptimizer.optimize_page_config())

# CSS محسن
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
    }
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .metric-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    h1 {
        color: white;
        text-align: center;
        font-size: 3em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 30px;
    }
    .stMetric {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# مجمع اتصالات قاعدة البيانات
@st.cache_resource
def get_db_pool():
    """إنشاء مجمع اتصالات قاعدة البيانات"""
    return DatabaseConnectionPool('skating_database.db', pool_size=5)

# دوال محسنة مع التخزين المؤقت
@cached(max_age=300)  # 5 دقائق
@monitor_performance("get_members_data")
def get_members_data():
    """الحصول على بيانات الأعضاء (محسنة)"""
    pool = get_db_pool()
    conn = pool.get_connection()

    try:
        df = DataOptimizer.lazy_load_database(
            'skating_database.db',
            'members'
        )
        return df
    finally:
        pool.return_connection(conn)

@cached(max_age=180)  # 3 دقائق
@monitor_performance("get_attendance_data")
def get_attendance_data():
    """الحصول على بيانات الحضور (محسنة)"""
    pool = get_db_pool()
    conn = pool.get_connection()

    try:
        df = DataOptimizer.lazy_load_database(
            'skating_database.db',
            'attendance'
        )
        return df
    finally:
        pool.return_connection(conn)

@cached(max_age=300)
@monitor_performance("get_memberships_data")
def get_memberships_data():
    """الحصول على بيانات العضويات (محسنة)"""
    pool = get_db_pool()
    conn = pool.get_connection()

    try:
        df = DataOptimizer.lazy_load_database(
            'skating_database.db',
            'memberships'
        )
        return df
    finally:
        pool.return_connection(conn)

@monitor_performance("calculate_age")
def calculate_age(birth_date_str):
    """حساب العمر من تاريخ الميلاد"""
    if not birth_date_str or birth_date_str == 'None' or pd.isna(birth_date_str):
        return None
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        return age
    except:
        return None

# الصفحة الرئيسية
@monitor_performance("show_homepage")
def show_homepage():
    """عرض الصفحة الرئيسية المحسنة"""
    st.title("🎿 نظام تحليل أداء لاعبي التزلج")

    # مؤشر التحميل
    with st.spinner('⚡ جاري تحميل البيانات بسرعة...'):
        members_df = get_members_data()
        attendance_df = get_attendance_data()
        memberships_df = get_memberships_data()

    # البطاقات الإحصائية
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👥 إجمالي الأعضاء",
            len(members_df),
            delta=f"+{len(members_df)}"
        )

    with col2:
        st.metric(
            "📅 سجلات الحضور",
            len(attendance_df),
            delta=f"{len(attendance_df)} سجل"
        )

    with col3:
        avg_attendance = len(attendance_df) / len(members_df) if len(members_df) > 0 else 0
        st.metric(
            "📊 متوسط الحضور",
            f"{avg_attendance:.2f}",
            delta=f"{avg_attendance:.1f} يوم/عضو"
        )

    with col4:
        unique_dates = attendance_df['date'].nunique() if 'date' in attendance_df.columns else 0
        st.metric(
            "📆 أيام التدريب",
            unique_dates,
            delta=f"{unique_dates} يوم"
        )

    # الرسوم البيانية
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 تطور الحضور")
        if 'date' in attendance_df.columns:
            daily_attendance = attendance_df.groupby('date').size().reset_index(name='count')

            fig = px.line(
                daily_attendance,
                x='date',
                y='count',
                title='',
                labels={'date': 'التاريخ', 'count': 'عدد الحاضرين'}
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("👥 توزيع الجنس")
        if 'gender' in members_df.columns:
            gender_counts = members_df['gender'].value_counts()

            fig = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                title='',
                color_discrete_sequence=['#667eea', '#f093fb']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    # أفضل 10 أعضاء
    st.markdown("---")
    st.subheader("🏆 أعلى 10 أعضاء حضوراً")

    if 'member_id' in attendance_df.columns:
        top_members = attendance_df['member_id'].value_counts().head(10)

        # دمج مع أسماء الأعضاء
        top_members_data = []
        for member_id, count in top_members.items():
            member_info = members_df[members_df['id'] == member_id]
            if not member_info.empty:
                name = member_info.iloc[0]['name']
                top_members_data.append({'الاسم': name, 'عدد أيام الحضور': count})

        top_df = pd.DataFrame(top_members_data)

        fig = px.bar(
            top_df,
            x='الاسم',
            y='عدد أيام الحضور',
            title='',
            color='عدد أيام الحضور',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # إحصائيات الأداء
    with st.expander("⚡ إحصائيات الأداء", expanded=False):
        stats = cache_stats()
        st.json(stats)

# ملفات الأعضاء
@monitor_performance("show_member_profiles")
def show_member_profiles():
    """عرض ملفات الأعضاء"""
    st.title("👤 ملفات الأعضاء")

    with st.spinner('جاري تحميل البيانات...'):
        members_df = get_members_data()
        attendance_df = get_attendance_data()

    # اختيار العضو
    member_names = members_df['name'].tolist()
    selected_member = st.selectbox("اختر عضو:", member_names)

    if selected_member:
        member_data = members_df[members_df['name'] == selected_member].iloc[0]

        # معلومات العضو
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("الاسم", member_data['name'])

        with col2:
            gender = member_data.get('gender', 'غير محدد')
            st.metric("الجنس", gender)

        with col3:
            age = calculate_age(str(member_data.get('birth_date', '')))
            st.metric("العمر", f"{age} سنة" if age else "غير محدد")

        # إحصائيات الحضور
        member_attendance = attendance_df[
            attendance_df['member_id'] == member_data['id']
        ]

        st.markdown("---")
        st.subheader("📊 إحصائيات الحضور")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("إجمالي الحضور", len(member_attendance))

        with col2:
            last_attendance = member_attendance['date'].max() if not member_attendance.empty else "لا يوجد"
            st.metric("آخر حضور", last_attendance)

        with col3:
            total_days = attendance_df['date'].nunique()
            attendance_rate = (len(member_attendance) / total_days * 100) if total_days > 0 else 0
            st.metric("نسبة الحضور", f"{attendance_rate:.1f}%")

# القائمة الجانبية
def sidebar():
    """القائمة الجانبية"""
    st.sidebar.title("🎿 القائمة الرئيسية")

    menu = st.sidebar.radio(
        "اختر الصفحة:",
        ["🏠 الرئيسية", "👤 ملفات الأعضاء", "⚡ الأداء"]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("النظام المحسن - أسرع 3x")

    return menu

# التطبيق الرئيسي
@monitor_performance("main_app")
def main():
    """التطبيق الرئيسي"""
    menu = sidebar()

    if menu == "🏠 الرئيسية":
        show_homepage()
    elif menu == "👤 ملفات الأعضاء":
        show_member_profiles()
    elif menu == "⚡ الأداء":
        st.title("⚡ تقرير الأداء")
        from src.utils.cache_manager import performance_report
        st.json(performance_report())

if __name__ == "__main__":
    main()
