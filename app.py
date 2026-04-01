"""
🎿 نظام تحليل أداء لاعبي التزلج
Skating Analysis & Attendance System
"""
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# إعداد الصفحة
st.set_page_config(
    page_title="نظام تحليل التزلج 🎿",
    page_icon="🎿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS مخصص
st.markdown("""
<style>
    .main {background-color: #f0f2f6;}
    .stMetric {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    h1 {color: #1f77b4; text-align: center; padding: 20px 0;}
    h2 {color: #2c3e50;}
    h3 {color: #34495e;}
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات
@st.cache_resource
def get_connection():
    """الاتصال بقاعدة البيانات"""
    return sqlite3.connect('skating_database.db', check_same_thread=False)

def get_data(query):
    """تنفيذ استعلام وإرجاع النتائج"""
    conn = get_connection()
    return pd.read_sql_query(query, conn)

def calculate_age(birth_date_str):
    """حساب العمر من تاريخ الميلاد"""
    if not birth_date_str or birth_date_str == 'None' or pd.isna(birth_date_str):
        return None
    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None

# الصفحة الرئيسية
def show_homepage():
    """عرض الصفحة الرئيسية"""
    st.title("🎿 نظام تحليل أداء لاعبي التزلج")
    st.markdown("### مرحباً بك في نظام إدارة وتحليل الأداء الشامل")

    # الإحصائيات العامة
    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")

    # البطاقات الإحصائية
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👥 إجمالي الأعضاء", len(members_df))

    with col2:
        st.metric("📅 سجلات الحضور", len(attendance_df))

    with col3:
        avg_attendance = len(attendance_df) / len(members_df) if len(members_df) > 0 else 0
        st.metric("📊 متوسط الحضور", f"{avg_attendance:.2f}")

    with col4:
        st.metric("💳 العضويات النشطة", len(memberships_df))

    st.markdown("---")

    # الرسوم البيانية
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 توزيع الحضور عبر الزمن")

        # تجميع الحضور حسب التاريخ
        if len(attendance_df) > 0:
            attendance_by_date = attendance_df.groupby('date').size().reset_index(name='count')
            attendance_by_date['date'] = pd.to_datetime(attendance_by_date['date'])
            attendance_by_date = attendance_by_date.sort_values('date')

            fig = px.line(
                attendance_by_date,
                x='date',
                y='count',
                title='عدد الحضور اليومي',
                labels={'date': 'التاريخ', 'count': 'عدد الحضور'}
            )
            fig.update_traces(line_color='#1f77b4', line_width=3)
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("لا توجد بيانات حضور")

    with col2:
        st.subheader("👥 توزيع المستويات")

        if len(members_df) > 0 and 'level' in members_df.columns:
            # حساب توزيع المستويات
            level_counts = members_df['level'].value_counts()
            level_counts = level_counts[level_counts.index != '']

            if len(level_counts) > 0:
                fig = px.pie(
                    values=level_counts.values,
                    names=level_counts.index,
                    title='توزيع الأعضاء حسب المستوى',
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("لا توجد بيانات مستويات")
        else:
            st.info("لا توجد بيانات مستويات")

    st.markdown("---")

    # أعلى الحاضرين
    st.subheader("🏆 أعلى 10 أعضاء حضوراً")

    if len(attendance_df) > 0:
        # تجميع الحضور حسب العضو
        member_attendance = attendance_df.groupby('member_id').size().reset_index(name='attendance_count')
        member_attendance = member_attendance.merge(
            members_df[['id', 'name']],
            left_on='member_id',
            right_on='id'
        )
        member_attendance = member_attendance.sort_values('attendance_count', ascending=False).head(10)

        # عرض الجدول
        display_df = member_attendance[['name', 'attendance_count']].copy()
        display_df.columns = ['الاسم', 'عدد الحضور']
        display_df.index = range(1, len(display_df) + 1)

        st.dataframe(display_df, width='stretch')

        # رسم بياني
        fig = px.bar(
            member_attendance,
            x='name',
            y='attendance_count',
            title='أعلى 10 أعضاء',
            labels={'name': 'الاسم', 'attendance_count': 'عدد الحضور'},
            color='attendance_count',
            color_continuous_scale='blues'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("لا توجد بيانات حضور")

# صفحة ملفات الأعضاء
def show_members_page():
    """عرض صفحة الأعضاء"""
    st.title("👥 ملفات الأعضاء")

    members_df = get_data("SELECT * FROM members")

    if len(members_df) == 0:
        st.warning("لا يوجد أعضاء في النظام")
        return

    # اختيار العضو
    member_names = members_df['name'].sort_values().tolist()
    selected_member = st.selectbox("اختر عضو", member_names)

    if selected_member:
        member = members_df[members_df['name'] == selected_member].iloc[0]
        member_id = member['id']

        # معلومات العضو
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"### 📝 المعلومات الأساسية")
            st.write(f"**الاسم:** {member['name']}")
            if member.get('level'):
                st.write(f"**المستوى:** {member['level']}")
            if member.get('coach'):
                st.write(f"**المدرب:** {member['coach']}")

        with col2:
            st.markdown(f"### 📊 إحصائيات الحضور")
            attendance = get_data(f"SELECT * FROM attendance WHERE member_id = {member_id}")
            st.metric("عدد الحضور", len(attendance))

            if len(attendance) > 0:
                last_attendance = attendance['date'].max()
                st.write(f"**آخر حضور:** {last_attendance}")

        with col3:
            st.markdown(f"### 💳 المعلومات المالية")
            memberships = get_data(f"SELECT * FROM memberships WHERE member_id = {member_id}")

            if len(memberships) > 0:
                total_paid = memberships['amount'].sum()
                st.metric("إجمالي المدفوعات", f"{total_paid:.2f} جنيه")

        st.markdown("---")

        # الحضور الشهري
        if len(attendance) > 0:
            st.subheader("📅 الحضور الشهري")

            attendance['date'] = pd.to_datetime(attendance['date'])
            attendance['month'] = attendance['date'].dt.to_period('M').astype(str)
            monthly_attendance = attendance.groupby('month').size().reset_index(name='count')

            fig = px.bar(
                monthly_attendance,
                x='month',
                y='count',
                title=f'الحضور الشهري - {selected_member}',
                labels={'month': 'الشهر', 'count': 'عدد الأيام'},
                color='count',
                color_continuous_scale='teal'
            )
            st.plotly_chart(fig, width='stretch')

            # سجل الحضور الكامل
            st.subheader("📜 سجل الحضور الكامل")
            attendance_display = attendance[['date', 'session_type', 'coach']].copy()
            attendance_display.columns = ['التاريخ', 'نوع الحصة', 'المدرب']
            attendance_display = attendance_display.sort_values('التاريخ', ascending=False)
            st.dataframe(attendance_display, width='stretch')

# صفحة التقارير
def show_reports_page():
    """عرض صفحة التقارير"""
    st.title("📊 التقارير والإحصائيات")

    members_df = get_data("SELECT * FROM members")
    attendance_df = get_data("SELECT * FROM attendance")
    memberships_df = get_data("SELECT * FROM memberships")

    # تقرير شامل
    tab1, tab2, tab3 = st.tabs(["📈 الحضور", "💰 المدفوعات", "👥 الأعضاء"])

    with tab1:
        st.subheader("تقرير الحضور")

        if len(attendance_df) > 0:
            # الحضور حسب الشهر
            attendance_df['date'] = pd.to_datetime(attendance_df['date'])
            attendance_df['month'] = attendance_df['date'].dt.to_period('M').astype(str)

            col1, col2 = st.columns(2)

            with col1:
                monthly_stats = attendance_df.groupby('month').size().reset_index(name='count')
                fig = px.bar(
                    monthly_stats,
                    x='month',
                    y='count',
                    title='الحضور الشهري',
                    labels={'month': 'الشهر', 'count': 'عدد الحضور'}
                )
                st.plotly_chart(fig, width='stretch')

            with col2:
                # الحضور حسب المدرب
                if 'coach' in attendance_df.columns:
                    coach_stats = attendance_df['coach'].value_counts()
                    coach_stats = coach_stats[coach_stats.index != '']

                    if len(coach_stats) > 0:
                        fig = px.pie(
                            values=coach_stats.values,
                            names=coach_stats.index,
                            title='توزيع الحضور حسب المدرب'
                        )
                        st.plotly_chart(fig, width='stretch')

    with tab2:
        st.subheader("تقرير المدفوعات")

        if len(memberships_df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                total_revenue = memberships_df['amount'].sum()
                total_discount = memberships_df['discount'].sum()
                net_revenue = total_revenue - total_discount

                st.metric("إجمالي الإيرادات", f"{total_revenue:.2f} جنيه")
                st.metric("إجمالي الخصومات", f"{total_discount:.2f} جنيه")
                st.metric("صافي الإيرادات", f"{net_revenue:.2f} جنيه")

            with col2:
                # التوزيع حسب المستوى
                if 'level' in memberships_df.columns:
                    level_revenue = memberships_df.groupby('level')['amount'].sum()
                    level_revenue = level_revenue[level_revenue.index != '']

                    if len(level_revenue) > 0:
                        fig = px.bar(
                            x=level_revenue.index,
                            y=level_revenue.values,
                            title='الإيرادات حسب المستوى',
                            labels={'x': 'المستوى', 'y': 'المبلغ'}
                        )
                        st.plotly_chart(fig, width='stretch')

    with tab3:
        st.subheader("تقرير الأعضاء")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("إجمالي الأعضاء", len(members_df))

            # الأعضاء حسب المدرب
            if 'coach' in members_df.columns:
                coach_distribution = members_df['coach'].value_counts()
                coach_distribution = coach_distribution[coach_distribution.index != '']

                if len(coach_distribution) > 0:
                    st.write("**توزيع الأعضاء حسب المدرب:**")
                    st.bar_chart(coach_distribution)

        with col2:
            # عرض جدول الأعضاء
            st.write("**قائمة الأعضاء:**")
            display_members = members_df[['name', 'level', 'coach']].copy()
            display_members.columns = ['الاسم', 'المستوى', 'المدرب']
            st.dataframe(display_members, height=400)

# القائمة الجانبية
def main():
    """الوظيفة الرئيسية"""

    with st.sidebar:
        st.title("🎿 القائمة الرئيسية")
        st.markdown("---")

        page = st.radio(
            "اختر الصفحة",
            [
                "🏠 الرئيسية",
                "👥 ملفات الأعضاء",
                "📊 التقارير والإحصائيات"
            ]
        )

        st.markdown("---")
        st.info("💡 نظام شامل لإدارة وتحليل أداء لاعبي التزلج")

        # معلومات النظام
        members_df = get_data("SELECT COUNT(*) as count FROM members")
        attendance_df = get_data("SELECT COUNT(*) as count FROM attendance")

        st.markdown("### 📊 إحصائيات سريعة")
        st.write(f"👥 الأعضاء: {members_df['count'].iloc[0]}")
        st.write(f"📅 الحضور: {attendance_df['count'].iloc[0]}")

    # عرض الصفحة المختارة
    if page == "🏠 الرئيسية":
        show_homepage()
    elif page == "👥 ملفات الأعضاء":
        show_members_page()
    elif page == "📊 التقارير والإحصائيات":
        show_reports_page()

if __name__ == "__main__":
    main()
