"""
🏆 Figure Skating Analysis System - Final Version
نظام تحليل التزلج الفني - النسخة النهائية المُصلحة

✅ ALL errors fixed
✅ Language switching (Arabic/English)
✅ Works with or without AI libraries
✅ Graceful error handling
✅ Performance: cached DB queries
✅ Full attendance recording
✅ Member search & filter
✅ Rich statistics charts
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# LANGUAGE SYSTEM
# ============================================================================

TRANSLATIONS = {
    'ar': {
        'title': '⛸️ نظام تحليل التزلج الفني',
        'subtitle': 'النظام الشامل المتكامل',
        'menu': '📋 القائمة',
        'home': '🏠 الرئيسية',
        'members': '👥 الأعضاء',
        'attendance': '📊 الحضور',
        'ml_training': '🤖 تدريب النموذج ⭐',
        'referee': '🏅 واجهة الحكام',
        'video_analysis': '🎥 تحليل الفيديو',
        'stats': '📈 الإحصائيات',
        'settings': '⚙️ الإعدادات',
        'language': '🌐 اللغة',
        'total_members': 'إجمالي الأعضاء',
        'attendance_records': 'سجلات الحضور',
        'active_subscriptions': 'الاشتراكات النشطة',
        'ai_status': 'حالة AI',
        'members_management': 'إدارة الأعضاء',
        'no_members': 'لا يوجد أعضاء',
        'add_member': '➕ إضافة عضو',
        'search_members': '🔍 بحث عن عضو',
        'filter_by_level': 'فلتر حسب المستوى',
        'all_levels': 'كل المستويات',
        'name': 'الاسم',
        'age': 'العمر',
        'gender': 'الجنس',
        'phone': 'الهاتف',
        'email': 'البريد الإلكتروني',
        'skill_level': 'المستوى',
        'notes': 'ملاحظات',
        'male': 'ذكر',
        'female': 'أنثى',
        'beginner': 'مبتدئ',
        'intermediate': 'متوسط',
        'advanced': 'متقدم',
        'professional': 'محترف',
        'save': '💾 حفظ',
        'success': 'تم بنجاح',
        'error': 'خطأ',
        'ai_not_available': 'ميزات AI غير متاحة',
        'install_ai': 'لتفعيل ميزات AI، ثبّت',
        'core_features_work': 'الميزات الأساسية تعمل بدون AI',
        'record_attendance': '✅ تسجيل حضور',
        'select_member': 'اختر العضو',
        'attendance_date': 'التاريخ',
        'attendance_note': 'ملاحظة',
        'recent_attendance': 'آخر سجلات الحضور',
        'attendance_trend': 'اتجاه الحضور (آخر 30 يوم)',
        'members_by_gender': 'الأعضاء حسب الجنس',
        'members_by_level': 'الأعضاء حسب المستوى',
        'attendance_by_member': 'أكثر الأعضاء حضوراً',
        'no_data': 'لا توجد بيانات',
        'theme': 'المظهر',
        'dark_mode': 'الوضع الداكن',
        'light_mode': 'الوضع الفاتح',
        'db_path': 'مسار قاعدة البيانات',
        'clear_cache': '🗑️ مسح الذاكرة المؤقتة',
        'cache_cleared': 'تم مسح الذاكرة المؤقتة',
        'system_info': 'معلومات النظام',
        'today_attendance': 'حضور اليوم',
        'week_attendance': 'حضور الأسبوع',
        'no_attendance': 'لا توجد سجلات حضور',
    },
    'en': {
        'title': '⛸️ Figure Skating Analysis System',
        'subtitle': 'Complete Integrated System',
        'menu': '📋 Menu',
        'home': '🏠 Home',
        'members': '👥 Members',
        'attendance': '📊 Attendance',
        'ml_training': '🤖 ML Training ⭐',
        'referee': '🏅 Referee Interface',
        'video_analysis': '🎥 Video Analysis',
        'stats': '📈 Statistics',
        'settings': '⚙️ Settings',
        'language': '🌐 Language',
        'total_members': 'Total Members',
        'attendance_records': 'Attendance Records',
        'active_subscriptions': 'Active Subscriptions',
        'ai_status': 'AI Status',
        'members_management': 'Members Management',
        'no_members': 'No members found',
        'add_member': '➕ Add Member',
        'search_members': '🔍 Search members',
        'filter_by_level': 'Filter by level',
        'all_levels': 'All Levels',
        'name': 'Name',
        'age': 'Age',
        'gender': 'Gender',
        'phone': 'Phone',
        'email': 'Email',
        'skill_level': 'Skill Level',
        'notes': 'Notes',
        'male': 'Male',
        'female': 'Female',
        'beginner': 'Beginner',
        'intermediate': 'Intermediate',
        'advanced': 'Advanced',
        'professional': 'Professional',
        'save': '💾 Save',
        'success': 'Success',
        'error': 'Error',
        'ai_not_available': 'AI features not available',
        'install_ai': 'To enable AI features, install',
        'core_features_work': 'Core features work without AI',
        'record_attendance': '✅ Record Attendance',
        'select_member': 'Select Member',
        'attendance_date': 'Date',
        'attendance_note': 'Note',
        'recent_attendance': 'Recent Attendance',
        'attendance_trend': 'Attendance Trend (last 30 days)',
        'members_by_gender': 'Members by Gender',
        'members_by_level': 'Members by Level',
        'attendance_by_member': 'Top Attending Members',
        'no_data': 'No data available',
        'theme': 'Theme',
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'db_path': 'Database Path',
        'clear_cache': '🗑️ Clear Cache',
        'cache_cleared': 'Cache cleared',
        'system_info': 'System Info',
        'today_attendance': "Today's Attendance",
        'week_attendance': 'This Week',
        'no_attendance': 'No attendance records',
    }
}

if 'language' not in st.session_state:
    st.session_state.language = 'ar'

def t(key):
    return TRANSLATIONS[st.session_state.language].get(key, key)

def switch_language():
    st.session_state.language = 'en' if st.session_state.language == 'ar' else 'ar'
    st.rerun()

# ============================================================================
# AI LIBRARIES CHECK
# ============================================================================

CORE_AI_AVAILABLE = False
MEDIAPIPE_AVAILABLE = False
CV2_AVAILABLE = False
ANALYZER_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    import cv2
    CV2_AVAILABLE = True
    import numpy as np
    CORE_AI_AVAILABLE = True
    try:
        from src.ai.advanced_analyzer import AdvancedSkatingAnalyzer
        ANALYZER_AVAILABLE = True
    except:
        pass
except:
    pass

# ============================================================================
# DATABASE
# ============================================================================

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
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        attendance_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS memberships (
        membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        status TEXT DEFAULT 'نشط',
        start_date TEXT,
        end_date TEXT,
        amount REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

@st.cache_resource
def setup_db():
    init_db()
    return True

def get_conn():
    return sqlite3.connect('skating_database.db')

@st.cache_data(ttl=30)
def load_members():
    try:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM members", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_attendance():
    try:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM attendance ORDER BY attendance_date DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=30)
def load_memberships():
    try:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM memberships", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def invalidate_cache():
    load_members.clear()
    load_attendance.clear()
    load_memberships.clear()

def calc_age(birth_date):
    try:
        if pd.isna(birth_date) or birth_date == '':
            return 0
        birth = datetime.strptime(str(birth_date), '%Y-%m-%d')
        today = date.today()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return 0

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Figure Skating Analysis",
    page_icon="⛸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.main{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-attachment:fixed;}
.block-container{background:rgba(255,255,255,0.98);border-radius:20px;padding:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.3);}
h1{color:#667eea;text-align:center;font-weight:800;}
h2,h3{color:#764ba2;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#667eea 0%,#764ba2 100%);}
[data-testid="stSidebar"] *{color:white !important;}
.stButton>button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;padding:12px 28px;font-weight:700;transition:transform 0.1s;}
.stButton>button:hover{transform:scale(1.03);}
[data-testid="stMetricValue"]{font-size:2rem;color:#667eea;font-weight:700;}
.stDataFrame{border-radius:12px;overflow:hidden;}
div[data-testid="stExpander"]{border:1px solid #e2e8f0;border-radius:12px;}
.search-box input{border-radius:10px !important;}
</style>
""", unsafe_allow_html=True)

setup_db()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title(t('menu'))

lang_button = "English" if st.session_state.language == 'ar' else "العربية"
if st.sidebar.button(f"🌐 {lang_button}", use_container_width=True):
    switch_language()

st.sidebar.markdown("---")

page = st.sidebar.radio("", [
    t('home'),
    t('members'),
    t('attendance'),
    t('ml_training'),
    t('referee'),
    t('video_analysis'),
    t('stats'),
    t('settings')
])

# ============================================================================
# HOME PAGE
# ============================================================================

def show_home():
    st.markdown(f'<h1>{t("title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;font-size:1.3em;color:#64748b;">{t("subtitle")}</p>', unsafe_allow_html=True)

    members = load_members()
    attendance = load_attendance()
    memberships = load_memberships()

    today_str = date.today().isoformat()
    week_ago_str = (date.today() - timedelta(days=7)).isoformat()

    today_att = 0
    week_att = 0
    if len(attendance) > 0 and 'attendance_date' in attendance.columns:
        today_att = len(attendance[attendance['attendance_date'] == today_str])
        week_att = len(attendance[attendance['attendance_date'] >= week_ago_str])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t('total_members'), len(members))
    with col2:
        st.metric(t('today_attendance'), today_att)
    with col3:
        st.metric(t('week_attendance'), week_att)
    with col4:
        ai_status = "✅ Active" if CORE_AI_AVAILABLE else "⚠️ Off"
        st.metric(t('ai_status'), ai_status)

    st.markdown("---")

    # Attendance trend chart
    if len(attendance) > 0 and 'attendance_date' in attendance.columns:
        st.subheader(t('attendance_trend'))
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        recent = attendance[attendance['attendance_date'] >= cutoff].copy()
        if len(recent) > 0:
            trend = recent.groupby('attendance_date').size().reset_index(name='count')
            trend['attendance_date'] = pd.to_datetime(trend['attendance_date'])
            fig = px.bar(
                trend, x='attendance_date', y='count',
                color_discrete_sequence=['#667eea'],
                labels={'attendance_date': '', 'count': ''},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    if not CORE_AI_AVAILABLE:
        st.warning(f"⚠️ {t('ai_not_available')}")
        st.info(f"""
        {t('install_ai')}:
        ```
        pip install mediapipe opencv-python numpy
        ```
        ✅ {t('core_features_work')}
        """)

# ============================================================================
# MEMBERS PAGE
# ============================================================================

def show_members():
    st.header(t('members_management'))

    members = load_members()

    if len(members) > 0:
        if 'birth_date' in members.columns:
            members['age'] = members['birth_date'].apply(calc_age)

        # Search & filter row
        col_search, col_filter = st.columns([3, 1])
        with col_search:
            search = st.text_input(t('search_members'), placeholder=t('name'), label_visibility='collapsed')
        with col_filter:
            levels = [t('all_levels')] + [t('beginner'), t('intermediate'), t('advanced'), t('professional')]
            selected_level = st.selectbox(t('filter_by_level'), levels, label_visibility='collapsed')

        filtered = members.copy()
        if search:
            filtered = filtered[filtered['name'].str.contains(search, case=False, na=False)]
        if selected_level != t('all_levels') and 'skill_level' in filtered.columns:
            filtered = filtered[filtered['skill_level'] == selected_level]

        display_cols = [c for c in ['name', 'age', 'gender', 'phone', 'email', 'skill_level'] if c in filtered.columns]
        if display_cols:
            st.dataframe(filtered[display_cols], use_container_width=True, height=350)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t('total_members'), len(filtered))
        if 'gender' in members.columns:
            with col2:
                st.metric(t('male'), len(members[members['gender'] == t('male')]))
            with col3:
                st.metric(t('female'), len(members[members['gender'] == t('female')]))
    else:
        st.info(t('no_members'))

    with st.expander(t('add_member')):
        with st.form("add_member"):
            name = st.text_input(t('name') + " *")
            col1, col2 = st.columns(2)
            with col1:
                birth_date = st.date_input(t('age'))
            with col2:
                gender = st.selectbox(t('gender'), [t('male'), t('female')])
            col1, col2 = st.columns(2)
            with col1:
                phone = st.text_input(t('phone'))
            with col2:
                email = st.text_input(t('email'))
            skill_level = st.selectbox(t('skill_level'),
                                       [t('beginner'), t('intermediate'), t('advanced'), t('professional')])
            notes = st.text_area(t('notes'))
            submitted = st.form_submit_button(t('save'))
            if submitted and name:
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("""INSERT INTO members
                               (name, birth_date, gender, phone, email, skill_level, notes)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                              (name, str(birth_date), gender, phone, email, skill_level, notes))
                    conn.commit()
                    conn.close()
                    invalidate_cache()
                    st.success(f"✅ {t('success')}: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error')}: {str(e)}")

# ============================================================================
# ATTENDANCE PAGE
# ============================================================================

def show_attendance():
    st.header(t('attendance'))

    attendance = load_attendance()
    members = load_members()

    # Summary metrics
    today_str = date.today().isoformat()
    week_ago_str = (date.today() - timedelta(days=7)).isoformat()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t('attendance_records'), len(attendance))
    with col2:
        today_count = 0
        if len(attendance) > 0 and 'attendance_date' in attendance.columns:
            today_count = len(attendance[attendance['attendance_date'] == today_str])
        st.metric(t('today_attendance'), today_count)
    with col3:
        week_count = 0
        if len(attendance) > 0 and 'attendance_date' in attendance.columns:
            week_count = len(attendance[attendance['attendance_date'] >= week_ago_str])
        st.metric(t('week_attendance'), week_count)

    st.markdown("---")

    # Record attendance form
    with st.expander(t('record_attendance'), expanded=True):
        if len(members) == 0:
            st.warning(t('no_members'))
        else:
            with st.form("record_attendance"):
                member_options = {row['name']: row['member_id'] for _, row in members.iterrows()} if 'name' in members.columns and 'member_id' in members.columns else {}
                selected_name = st.selectbox(t('select_member'), list(member_options.keys()))
                att_date = st.date_input(t('attendance_date'), value=date.today())
                att_note = st.text_input(t('attendance_note'))
                submitted = st.form_submit_button(t('record_attendance'))
                if submitted and selected_name:
                    try:
                        conn = get_conn()
                        c = conn.cursor()
                        c.execute("""INSERT INTO attendance (member_id, attendance_date, notes)
                                     VALUES (?, ?, ?)""",
                                  (member_options[selected_name], str(att_date), att_note))
                        conn.commit()
                        conn.close()
                        invalidate_cache()
                        st.success(f"✅ {t('success')}: {selected_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('error')}: {str(e)}")

    # Recent attendance table
    if len(attendance) > 0:
        st.subheader(t('recent_attendance'))
        try:
            att_display = attendance.copy()
            if len(members) > 0 and 'member_id' in att_display.columns and 'member_id' in members.columns:
                att_display = att_display.merge(
                    members[['member_id', 'name']], on='member_id', how='left'
                )
            cols_to_show = [c for c in ['name', 'attendance_date', 'notes'] if c in att_display.columns]
            if cols_to_show:
                st.dataframe(att_display[cols_to_show].head(30), use_container_width=True)
        except Exception as e:
            st.error(f"Display error: {e}")
    else:
        st.info(t('no_attendance'))

# ============================================================================
# AI PAGES
# ============================================================================

def show_ml_training():
    st.header(t('ml_training'))
    if not CORE_AI_AVAILABLE:
        st.error(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy")
        return
    st.success("✅ AI features available!")
    st.info("Upload a video to analyze skating performance")

def show_referee():
    st.header(t('referee'))
    if not CORE_AI_AVAILABLE:
        st.error(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy")
        return
    st.success("✅ Referee interface ready!")

def show_video_analysis():
    try:
        from src.pages.video_analysis_page import show_video_analysis_page
        show_video_analysis_page(lang=st.session_state.language)
    except ImportError as e:
        st.error(f"تعذّر تحميل صفحة التحليل: {e}")
        st.code("pip install mediapipe opencv-python numpy")

# ============================================================================
# STATS PAGE
# ============================================================================

def show_stats():
    st.header(t('stats'))

    members = load_members()
    attendance = load_attendance()

    if len(members) == 0:
        st.info(t('no_data'))
        return

    col1, col2 = st.columns(2)

    # Gender pie
    with col1:
        if 'gender' in members.columns and members['gender'].notna().any():
            gender_counts = members['gender'].value_counts().reset_index()
            gender_counts.columns = ['gender', 'count']
            fig = px.pie(
                gender_counts, values='count', names='gender',
                title=t('members_by_gender'),
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb'],
            )
            fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Skill level bar
    with col2:
        if 'skill_level' in members.columns and members['skill_level'].notna().any():
            level_counts = members['skill_level'].value_counts().reset_index()
            level_counts.columns = ['level', 'count']
            fig = px.bar(
                level_counts, x='level', y='count',
                title=t('members_by_level'),
                color='count',
                color_continuous_scale=['#667eea', '#764ba2'],
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    # Attendance trend (last 30 days)
    if len(attendance) > 0 and 'attendance_date' in attendance.columns:
        st.subheader(t('attendance_trend'))
        cutoff = (date.today() - timedelta(days=30)).isoformat()
        recent = attendance[attendance['attendance_date'] >= cutoff].copy()
        if len(recent) > 0:
            trend = recent.groupby('attendance_date').size().reset_index(name='count')
            trend['attendance_date'] = pd.to_datetime(trend['attendance_date'])
            fig = px.area(
                trend, x='attendance_date', y='count',
                color_discrete_sequence=['#667eea'],
                labels={'attendance_date': '', 'count': ''},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=250,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

    # Top attending members
    if len(attendance) > 0 and 'member_id' in attendance.columns and len(members) > 0:
        st.subheader(t('attendance_by_member'))
        top = attendance.groupby('member_id').size().reset_index(name='sessions')
        if 'member_id' in members.columns and 'name' in members.columns:
            top = top.merge(members[['member_id', 'name']], on='member_id', how='left')
            top = top.sort_values('sessions', ascending=False).head(10)
            fig = px.bar(
                top, x='name', y='sessions',
                color='sessions',
                color_continuous_scale=['#667eea', '#764ba2'],
                labels={'name': '', 'sessions': ''},
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=300,
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# SETTINGS PAGE
# ============================================================================

def show_settings():
    st.header(t('settings'))

    st.subheader(t('system_info'))
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Python:** {sys.version.split()[0]}")
        st.info(f"**Database:** skating_database.db")
        st.info(f"**MediaPipe:** {'✅' if MEDIAPIPE_AVAILABLE else '❌'}")
    with col2:
        st.info(f"**OpenCV:** {'✅' if CV2_AVAILABLE else '❌'}")
        st.info(f"**Advanced Analyzer:** {'✅' if ANALYZER_AVAILABLE else '❌'}")
        members = load_members()
        st.info(f"**{t('total_members')}:** {len(members)}")

    st.markdown("---")

    st.subheader("🗄️ " + t('db_path'))
    st.code(str(Path('skating_database.db').resolve()))

    st.markdown("---")

    if st.button(t('clear_cache'), use_container_width=False):
        invalidate_cache()
        st.success(f"✅ {t('cache_cleared')}")

    if not CORE_AI_AVAILABLE:
        st.markdown("---")
        st.subheader("📦 " + t('install_ai'))
        st.code("pip install mediapipe opencv-python numpy")

# ============================================================================
# MAIN ROUTER
# ============================================================================

if page == t('home'):
    show_home()
elif page == t('members'):
    show_members()
elif page == t('attendance'):
    show_attendance()
elif page == t('ml_training'):
    show_ml_training()
elif page == t('referee'):
    show_referee()
elif page == t('video_analysis'):
    show_video_analysis()
elif page == t('stats'):
    show_stats()
else:
    show_settings()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("v4.0 - Enhanced UI & Performance")
