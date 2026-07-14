"""
🎿 نظام تحليل أداء لاعبي التزلج - النسخة الحديثة
Modern Skating Analysis System with Enhanced UI
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.modern_theme import ModernTheme
from src.utils.cache_manager import cached, cache_stats, monitor_performance
from src.utils.data_optimizer import DataOptimizer, DatabaseConnectionPool

# إعداد الصفحة
st.set_page_config(
    page_title="نظام التزلج الحديث 🎿",
    page_icon="🎿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق الثيم الحديث
st.markdown(ModernTheme.get_css(), unsafe_allow_html=True)

# مجمع قاعدة البيانات
@st.cache_resource
def get_db_pool():
    return DatabaseConnectionPool('skating_database.db', pool_size=5)

# دوال محسنة
@cached(max_age=300)
def get_members_data():
    return DataOptimizer.lazy_load_database('skating_database.db', 'members')

@cached(max_age=180)
def get_attendance_data():
    return DataOptimizer.lazy_load_database('skating_database.db', 'attendance')

@cached(max_age=300)
def get_memberships_data():
    return DataOptimizer.lazy_load_database('skating_database.db', 'memberships')

def calculate_age(birth_date_str):
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

# الصفحات
def show_homepage():
    """الصفحة الرئيسية الحديثة"""
    st.markdown('<h1>🎿 نظام تحليل أداء لاعبي التزلج</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.3em; color: #64748b; margin-bottom: 40px;">مرحباً بك في النظام الأكثر تطوراً لإدارة وتحليل أداء لاعبي التزلج</p>', unsafe_allow_html=True)

    with st.spinner('⚡ جاري تحميل البيانات...'):
        members_df = get_members_data()
        attendance_df = get_attendance_data()
        memberships_df = get_memberships_data()

    # البطاقات الإحصائية
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            ModernTheme.create_metric_card(
                "إجمالي الأعضاء",
                str(len(members_df)),
                f"+{len(members_df)} عضو",
                "👥"
            ),
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            ModernTheme.create_metric_card(
                "سجلات الحضور",
                str(len(attendance_df)),
                f"{len(attendance_df)} سجل",
                "📅"
            ),
            unsafe_allow_html=True
        )

    with col3:
        avg = len(attendance_df) / len(members_df) if len(members_df) > 0 else 0
        st.markdown(
            ModernTheme.create_metric_card(
                "متوسط الحضور",
                f"{avg:.2f}",
                f"{avg:.1f} يوم/عضو",
                "📊"
            ),
            unsafe_allow_html=True
        )

    with col4:
        unique_dates = attendance_df['date'].nunique() if 'date' in attendance_df.columns else 0
        st.markdown(
            ModernTheme.create_metric_card(
                "أيام التدريب",
                str(unique_dates),
                f"{unique_dates} يوم نشط",
                "📆"
            ),
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # التبويبات
    tab1, tab2, tab3, tab4 = st.tabs(["📈 التحليلات", "🏆 الأفضل أداءً", "👥 التوزيعات", "⚙️ النظام"])

    with tab1:
        st.subheader("📈 تطور الحضور عبر الزمن")

        if 'date' in attendance_df.columns:
            daily_attendance = attendance_df.groupby('date').size().reset_index(name='count')

            fig = px.area(
                daily_attendance,
                x='date',
                y='count',
                title='',
                labels={'date': 'التاريخ', 'count': 'عدد الحاضرين'}
            )
            fig.update_traces(
                fillcolor='rgba(102, 126, 234, 0.3)',
                line_color='#667eea',
                line_width=3
            )
            fig.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=450,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🏆 أعلى 10 أعضاء حضوراً")

        if 'member_id' in attendance_df.columns:
            top_members = attendance_df['member_id'].value_counts().head(10)

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
                height=450
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👥 توزيع الجنس")
            if 'gender' in members_df.columns:
                gender_counts = members_df['gender'].value_counts()

                fig = px.pie(
                    values=gender_counts.values,
                    names=gender_counts.index,
                    title='',
                    hole=0.4,
                    color_discrete_sequence=['#667eea', '#f093fb']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📊 توزيع الأعمار")
            if 'birth_date' in members_df.columns:
                ages = members_df['birth_date'].apply(lambda x: calculate_age(str(x)) if pd.notna(x) else None)
                ages = ages.dropna()

                fig = px.histogram(
                    ages,
                    nbins=20,
                    title='',
                    labels={'value': 'العمر', 'count': 'العدد'},
                    color_discrete_sequence=['#764ba2']
                )
                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("⚙️ إحصائيات النظام")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚀 الأداء")
            stats = cache_stats()
            st.json(stats)

        with col2:
            st.markdown("### 💾 قاعدة البيانات")
            db_stats = {
                'members': len(members_df),
                'attendance': len(attendance_df),
                'memberships': len(memberships_df)
            }
            st.json(db_stats)

def show_member_profiles():
    """ملفات الأعضاء"""
    st.markdown('<h1>👤 ملفات الأعضاء</h1>', unsafe_allow_html=True)

    with st.spinner('جاري تحميل البيانات...'):
        members_df = get_members_data()
        attendance_df = get_attendance_data()

    # بحث وفلترة
    col1, col2 = st.columns([3, 1])

    with col1:
        search = st.text_input("🔍 ابحث عن عضو", placeholder="اكتب اسم العضو...")

    with col2:
        gender_filter = st.selectbox("الجنس", ["الكل", "ذكر", "أنثى"])

    # تطبيق الفلاتر
    filtered_df = members_df.copy()

    if search:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False, na=False)]

    if gender_filter != "الكل":
        filtered_df = filtered_df[filtered_df['gender'] == gender_filter]

    # عرض الأعضاء
    st.markdown(f"### عدد النتائج: {len(filtered_df)}")

    for idx, member in filtered_df.head(10).iterrows():
        with st.expander(f"👤 {member['name']}"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("الاسم", member['name'])

            with col2:
                gender = member.get('gender', 'غير محدد')
                st.metric("الجنس", gender)

            with col3:
                age = calculate_age(str(member.get('birth_date', '')))
                st.metric("العمر", f"{age} سنة" if age else "غير محدد")

            with col4:
                member_attendance = attendance_df[attendance_df['member_id'] == member['id']]
                st.metric("إجمالي الحضور", len(member_attendance))

            # رسم بياني للحضور
            if not member_attendance.empty and 'date' in member_attendance.columns:
                dates = pd.to_datetime(member_attendance['date'])
                monthly = dates.dt.to_period('M').value_counts().sort_index()

                fig = px.line(
                    x=monthly.index.astype(str),
                    y=monthly.values,
                    title='الحضور الشهري',
                    labels={'x': 'الشهر', 'y': 'عدد الأيام'}
                )
                fig.update_traces(line_color='#667eea', line_width=3)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

def sidebar():
    """القائمة الجانبية"""
    with st.sidebar:
        st.markdown('<h1 style="color: white;">🎿 القائمة</h1>', unsafe_allow_html=True)

        menu = st.radio(
            "",
            ["🏠 الرئيسية", "👤 ملفات الأعضاء", "📊 التقارير", "⚙️ الإعدادات"]
        )

        st.markdown("---")

        st.markdown(
            ModernTheme.create_alert_box(
                "النظام محسن بالكامل ⚡",
                "success"
            ),
            unsafe_allow_html=True
        )

        st.markdown("---")
        st.markdown("**النسخة:** 2.0.0")
        st.markdown("**آخر تحديث:** 2026-04-03")

    return menu

# التطبيق الرئيسي
def main():
    menu = sidebar()

    if menu == "🏠 الرئيسية":
        show_homepage()
    elif menu == "👤 ملفات الأعضاء":
        show_member_profiles()
    elif menu == "📊 التقارير":
        st.title("📊 التقارير")
        st.info("قريباً...")
    elif menu == "⚙️ الإعدادات":
        st.title("⚙️ الإعدادات")
        st.info("قريباً...")

if __name__ == "__main__":
    main()
