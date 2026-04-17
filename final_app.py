"""
🏆 Figure Skating Analysis System - Final Version
نظام تحليل التزلج الفني - النسخة النهائية المُصلحة

✅ ALL errors fixed
✅ Language switching (Arabic/English)
✅ Works with or without AI libraries
✅ Graceful error handling
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import plotly.express as px
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# IMPORT PROFESSIONAL PAGES
# ============================================================================

PROFESSIONAL_VIDEO_AVAILABLE = False
REFEREE_AVAILABLE = False
MUSIC_EDITOR_AVAILABLE = False
ADVANCED_DASHBOARD_AVAILABLE = False

try:
    from src.pages.professional_video_analysis import show_professional_video_analysis
    PROFESSIONAL_VIDEO_AVAILABLE = True
except Exception:
    pass

try:
    from src.pages.referee_testing_interface import show_referee_testing_interface
    REFEREE_AVAILABLE = True
except Exception:
    pass

try:
    from src.pages.music_editor_page import show_music_editor_page
    MUSIC_EDITOR_AVAILABLE = True
except Exception:
    pass

try:
    from src.pages.advanced_dashboard import show_advanced_dashboard
    ADVANCED_DASHBOARD_AVAILABLE = True
except Exception:
    pass

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
        'music_editor': '🎵 محرر الموسيقى',
        'advanced_analytics': '📊 التحليلات المتقدمة',
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
        'music_editor': '🎵 Music Editor',
        'advanced_analytics': '📊 Advanced Analytics',
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
    }
}

# Initialize session state for language
if 'language' not in st.session_state:
    st.session_state.language = 'ar'

def t(key):
    """Get translation for current language"""
    return TRANSLATIONS[st.session_state.language].get(key, key)

def switch_language():
    """Toggle language"""
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

    # Try advanced analyzer
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
    """Initialize database with all required tables"""
    conn = sqlite3.connect('skating_database.db')
    c = conn.cursor()

    # Members table with ALL columns
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

    # Attendance table
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER,
        attendance_date TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    # Memberships table
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

def load_table(table_name):
    """Safely load table data"""
    try:
        conn = get_conn()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading {table_name}: {e}")
        return pd.DataFrame()

def calc_age(birth_date):
    """Calculate age from birth date"""
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

# Modern CSS
st.markdown("""
<style>
.main{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-attachment:fixed;}
.block-container{background:rgba(255,255,255,0.98);border-radius:20px;padding:2rem;box-shadow:0 15px 40px rgba(0,0,0,0.3);}
h1{color:#667eea;text-align:center;font-weight:800;}
h2,h3{color:#764ba2;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#667eea 0%,#764ba2 100%);}
[data-testid="stSidebar"] *{color:white !important;}
.stButton>button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;padding:12px 28px;font-weight:700;}
[data-testid="stMetricValue"]{font-size:2rem;color:#667eea;font-weight:700;}
</style>
""", unsafe_allow_html=True)

# Setup database
setup_db()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title(t('menu'))

# Language switcher at top
lang_button = "English" if st.session_state.language == 'ar' else "العربية"
if st.sidebar.button(f"🌐 {lang_button}", use_container_width=True):
    switch_language()

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio("", [
    t('home'),
    t('members'),
    t('attendance'),
    t('ml_training'),
    t('referee'),
    t('video_analysis'),
    t('music_editor'),
    t('advanced_analytics'),
    t('stats'),
    t('settings')
])

# ============================================================================
# HOME PAGE
# ============================================================================

def show_home():
    st.markdown(f'<h1>{t("title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;font-size:1.3em;color:#64748b;">{t("subtitle")}</p>', unsafe_allow_html=True)

    members = load_table('members')
    attendance = load_table('attendance')
    memberships = load_table('memberships')

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(t('total_members'), len(members))
    with col2:
        st.metric(t('attendance_records'), len(attendance))
    with col3:
        active = 0
        if len(memberships) > 0 and 'status' in memberships.columns:
            active = len(memberships[memberships['status']=='نشط'])
        st.metric(t('active_subscriptions'), active)
    with col4:
        ai_status = "✅" if CORE_AI_AVAILABLE else "⚠️"
        st.metric(t('ai_status'), ai_status)

    st.markdown("---")

    if not CORE_AI_AVAILABLE:
        st.warning(f"⚠️ {t('ai_not_available')}")
        st.info(f"""
        {t('install_ai')}:
        ```
        pip install mediapipe opencv-python numpy
        ```

        ✅ {t('core_features_work')}
        """)

    st.success("✅ System Ready!")

# ============================================================================
# MEMBERS PAGE
# ============================================================================

def show_members():
    st.header(t('members_management'))

    members = load_table('members')

    if len(members) > 0:
        # Safely add age column
        if 'birth_date' in members.columns:
            members['age'] = members['birth_date'].apply(calc_age)

        # Build display columns list (only existing columns)
        display_cols = []
        for col in ['name', 'age', 'gender', 'phone', 'email', 'skill_level']:
            if col in members.columns:
                display_cols.append(col)

        if display_cols:
            st.dataframe(members[display_cols], use_container_width=True, height=400)

        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t('total_members'), len(members))

        if 'gender' in members.columns:
            with col2:
                males = len(members[members['gender']==t('male')])
                st.metric(t('male'), males)
            with col3:
                females = len(members[members['gender']==t('female')])
                st.metric(t('female'), females)
    else:
        st.info(t('no_members'))

    # Add member form
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
                    st.success(f"✅ {t('success')}: {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('error')}: {str(e)}")

# ============================================================================
# ATTENDANCE PAGE
# ============================================================================

def show_attendance():
    st.header(t('attendance'))

    attendance = load_table('attendance')
    members = load_table('members')

    if len(attendance) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t('attendance_records'), len(attendance))
        with col2:
            unique = attendance['member_id'].nunique() if 'member_id' in attendance.columns else 0
            st.metric("Active Members", unique)

        # Show recent attendance
        if len(members) > 0 and 'member_id' in members.columns:
            try:
                att_display = attendance.copy()
                if 'member_id' in att_display.columns:
                    # Merge with member names
                    att_display = att_display.merge(
                        members[['member_id', 'name']],
                        on='member_id',
                        how='left'
                    )
                    cols_to_show = []
                    for col in ['name', 'attendance_date', 'notes']:
                        if col in att_display.columns:
                            cols_to_show.append(col)
                    if cols_to_show:
                        st.dataframe(att_display[cols_to_show].tail(20), use_container_width=True)
            except Exception as e:
                st.error(f"Display error: {e}")
                st.dataframe(attendance.tail(20), use_container_width=True)
    else:
        st.info("No attendance records")

# ============================================================================
# AI PAGES
# ============================================================================

def show_ml_training():
    if PROFESSIONAL_VIDEO_AVAILABLE:
        show_professional_video_analysis()
    else:
        st.header(t('ml_training'))
        st.warning(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy tensorflow torch")

def show_referee():
    if REFEREE_AVAILABLE:
        show_referee_testing_interface()
    else:
        st.header(t('referee'))
        st.warning(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy tensorflow torch")

def show_video_analysis():
    if PROFESSIONAL_VIDEO_AVAILABLE:
        show_professional_video_analysis()
    else:
        st.header(t('video_analysis'))
        st.warning(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy")

def show_music_editor():
    if MUSIC_EDITOR_AVAILABLE:
        show_music_editor_page()
    else:
        st.header(t('music_editor'))
        st.warning("Music editor not available")
        st.code("pip install pydub librosa soundfile")

def show_advanced_analytics():
    if ADVANCED_DASHBOARD_AVAILABLE:
        show_advanced_dashboard()
    else:
        st.header(t('advanced_analytics'))
        st.warning(t('ai_not_available'))
        st.code("pip install scikit-learn numpy")

def show_stats():
    st.header(t('stats'))

    members = load_table('members')

    if len(members) > 0 and 'gender' in members.columns:
        gender_counts = members['gender'].value_counts()
        fig = px.pie(values=gender_counts.values, names=gender_counts.index,
                    title="Members by Gender")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for statistics")

def show_settings():
    st.header(t('settings'))
    st.info("Settings page - coming soon")

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
elif page == t('music_editor'):
    show_music_editor()
elif page == t('advanced_analytics'):
    show_advanced_analytics()
elif page == t('stats'):
    show_stats()
else:
    show_settings()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("v4.0 - Professional Connected")
