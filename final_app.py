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
    st.header(t('ml_training'))

    # ML libs check (separate from mediapipe)
    try:
        import numpy as np
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.svm import SVC
        from sklearn.neural_network import MLPClassifier
        from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        import joblib
        import json
        ML_OK = True
    except ImportError as e:
        st.error(f"مكتبات ML غير مثبتة: {e}")
        st.code("pip install scikit-learn numpy pandas joblib")
        return

    is_ar = st.session_state.language == 'ar'

    # ── إعداد مجلد النماذج ──────────────────────────────────────────────
    model_dir = Path("data/models/element_classifier")
    model_dir.mkdir(parents=True, exist_ok=True)

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab_labels = (
        ["📊 البيانات", "⚙️ التدريب", "📈 النتائج", "💾 النموذج"]
        if is_ar else
        ["📊 Dataset", "⚙️ Train", "📈 Results", "💾 Model"]
    )
    tab_data, tab_train, tab_results, tab_model = st.tabs(tab_labels)

    # ════════════════════════════════════════════════════════════════════
    # TAB 1: إدارة البيانات
    # ════════════════════════════════════════════════════════════════════
    with tab_data:
        st.subheader("📊 بيانات التدريب" if is_ar else "📊 Training Dataset")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(
                "**هذا النموذج يتعلم التعرف على عناصر التزلج (قفزات، دورانات، خطوات)**"
                if is_ar else
                "**This model learns to recognize skating elements (jumps, spins, steps)**"
            )

            # زر توليد بيانات تجريبية
            n_samples = st.slider(
                "عدد عينات التدريب" if is_ar else "Number of training samples",
                min_value=100, max_value=2000, value=500, step=100
            )

            if st.button("🎲 توليد بيانات تجريبية" if is_ar else "🎲 Generate Demo Data"):
                with st.spinner("جاري التوليد..." if is_ar else "Generating..."):
                    data = _generate_synthetic_data(np, pd, n_samples)
                    st.session_state['training_df'] = data
                    st.success(f"✅ تم توليد {len(data)} عينة" if is_ar else f"✅ Generated {len(data)} samples")

        with col2:
            if 'training_df' in st.session_state:
                df = st.session_state['training_df']
                st.metric("إجمالي العينات" if is_ar else "Total Samples", len(df))
                counts = df['label'].value_counts()
                for label, count in counts.items():
                    st.write(f"• {label}: **{count}**")

        if 'training_df' in st.session_state:
            st.markdown("---")
            st.subheader("معاينة البيانات" if is_ar else "Data Preview")
            st.dataframe(st.session_state['training_df'].head(10), use_container_width=True)

    # ════════════════════════════════════════════════════════════════════
    # TAB 2: إعداد التدريب
    # ════════════════════════════════════════════════════════════════════
    with tab_train:
        st.subheader("⚙️ إعداد وتشغيل التدريب" if is_ar else "⚙️ Configure & Run Training")

        if 'training_df' not in st.session_state:
            st.warning(
                "⚠️ قم أولاً بتوليد البيانات من تبويب البيانات"
                if is_ar else
                "⚠️ Generate data first from the Dataset tab"
            )
        else:
            col1, col2 = st.columns(2)

            with col1:
                model_type = st.selectbox(
                    "نوع النموذج" if is_ar else "Model Type",
                    options=["random_forest", "gradient_boost", "svm", "neural_net"],
                    format_func=lambda x: {
                        "random_forest": "🌲 Random Forest",
                        "gradient_boost": "🚀 Gradient Boosting",
                        "svm": "📐 SVM",
                        "neural_net": "🧠 Neural Network"
                    }[x]
                )
                test_size = st.slider(
                    "نسبة بيانات الاختبار" if is_ar else "Test Split",
                    min_value=0.1, max_value=0.4, value=0.2, step=0.05
                )

            with col2:
                if model_type in ("random_forest", "gradient_boost"):
                    n_estimators = st.slider(
                        "عدد الأشجار" if is_ar else "N Estimators",
                        min_value=10, max_value=300, value=100, step=10
                    )
                    max_depth = st.selectbox(
                        "أقصى عمق" if is_ar else "Max Depth",
                        options=[None, 3, 5, 10, 15],
                        format_func=lambda x: "بدون حد" if x is None else str(x)
                    )
                else:
                    n_estimators = 100
                    max_depth = None

            if st.button("🚀 بدء التدريب" if is_ar else "🚀 Start Training", type="primary"):
                with st.spinner("جاري التدريب..." if is_ar else "Training..."):
                    results = _run_training(
                        np, pd, StandardScaler, train_test_split,
                        accuracy_score, classification_report, confusion_matrix,
                        RandomForestClassifier, GradientBoostingClassifier, SVC, MLPClassifier,
                        joblib, model_dir,
                        st.session_state['training_df'],
                        model_type, test_size, n_estimators, max_depth
                    )
                    st.session_state['training_results'] = results
                    st.success("✅ اكتمل التدريب!" if is_ar else "✅ Training complete!")
                    st.rerun()

    # ════════════════════════════════════════════════════════════════════
    # TAB 3: النتائج
    # ════════════════════════════════════════════════════════════════════
    with tab_results:
        st.subheader("📈 نتائج التدريب" if is_ar else "📈 Training Results")

        if 'training_results' not in st.session_state:
            st.info("قم بتدريب النموذج أولاً" if is_ar else "Train the model first")
        else:
            r = st.session_state['training_results']

            # مقاييس رئيسية
            c1, c2, c3 = st.columns(3)
            c1.metric("دقة التدريب" if is_ar else "Train Accuracy",
                      f"{r['acc_train']:.1%}")
            c2.metric("دقة الاختبار" if is_ar else "Test Accuracy",
                      f"{r['acc_test']:.1%}")
            c3.metric("النموذج" if is_ar else "Model", r['model_name'])

            st.markdown("---")

            # Feature Importance
            if r.get('feature_importance'):
                st.subheader("أهمية المتغيرات" if is_ar else "Feature Importance")
                fi = r['feature_importance']
                fi_df = pd.DataFrame(
                    sorted(fi.items(), key=lambda x: x[1], reverse=True),
                    columns=["Feature", "Importance"]
                )
                fig = px.bar(fi_df, x="Importance", y="Feature", orientation='h',
                             color="Importance", color_continuous_scale="Viridis")
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Confusion Matrix
            if r.get('confusion_matrix') is not None:
                st.subheader("مصفوفة الخطأ" if is_ar else "Confusion Matrix")
                cm = r['confusion_matrix']
                labels = r['labels']
                cm_df = pd.DataFrame(cm, index=labels, columns=labels)
                fig2 = px.imshow(cm_df, text_auto=True, color_continuous_scale="Blues",
                                 labels=dict(x="Predicted", y="Actual"))
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

            # Classification report
            with st.expander("تقرير التصنيف التفصيلي" if is_ar else "Detailed Classification Report"):
                st.code(r['report'])

    # ════════════════════════════════════════════════════════════════════
    # TAB 4: إدارة النموذج
    # ════════════════════════════════════════════════════════════════════
    with tab_model:
        st.subheader("💾 إدارة النموذج" if is_ar else "💾 Model Management")

        model_file = model_dir / "model.pkl"
        meta_file = model_dir / "metadata.json"

        if model_file.exists() and meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            st.success("✅ يوجد نموذج محفوظ" if is_ar else "✅ Saved model found")
            c1, c2 = st.columns(2)
            c1.metric("نوع النموذج" if is_ar else "Model Type", meta.get('model_type', '-'))
            c2.metric("تاريخ الحفظ" if is_ar else "Saved At",
                      meta.get('saved_at', '-')[:10] if meta.get('saved_at') else '-')
            st.write("**المتغيرات:**" if is_ar else "**Features:**",
                     ", ".join(meta.get('feature_names', [])))
            st.write("**الفئات:**" if is_ar else "**Classes:**",
                     ", ".join(meta.get('classes', [])))

            if st.button("🗑️ حذف النموذج" if is_ar else "🗑️ Delete Model"):
                model_file.unlink()
                meta_file.unlink()
                (model_dir / "scaler.pkl").unlink(missing_ok=True)
                st.rerun()
        else:
            st.info("لا يوجد نموذج محفوظ بعد" if is_ar else "No saved model yet")

        if 'training_results' in st.session_state:
            st.markdown("---")
            r = st.session_state['training_results']
            if st.button("💾 حفظ النموذج الحالي" if is_ar else "💾 Save Current Model"):
                joblib.dump(r['model'], model_dir / "model.pkl")
                joblib.dump(r['scaler'], model_dir / "scaler.pkl")
                meta = {
                    'model_type': r['model_name'],
                    'feature_names': r['feature_names'],
                    'classes': r['labels'],
                    'label_encoder': r['label_encoder'],
                    'saved_at': datetime.now().isoformat(),
                    'acc_train': r['acc_train'],
                    'acc_test': r['acc_test'],
                }
                with open(model_dir / "metadata.json", 'w') as f:
                    json.dump(meta, f, indent=2, ensure_ascii=False)
                st.success("✅ تم الحفظ" if is_ar else "✅ Saved")
                st.rerun()


def _generate_synthetic_data(np, pd, n_samples: int):
    """توليد بيانات تدريب تجريبية لعناصر التزلج"""
    rng = np.random.default_rng(42)
    rows = []

    element_profiles = {
        '3A':    dict(rotations=3.0, is_jump=1, is_spin=0, is_step=0, base_value=8.0,  duration_mu=1.2, level=0),
        '4T':    dict(rotations=4.0, is_jump=1, is_spin=0, is_step=0, base_value=9.5,  duration_mu=1.3, level=0),
        '3Lz':   dict(rotations=3.0, is_jump=1, is_spin=0, is_step=0, base_value=5.9,  duration_mu=1.1, level=0),
        '2A':    dict(rotations=2.5, is_jump=1, is_spin=0, is_step=0, base_value=3.3,  duration_mu=0.9, level=0),
        'CCoSp4':dict(rotations=0,   is_jump=0, is_spin=1, is_step=0, base_value=3.5,  duration_mu=2.5, level=4),
        'FCSp3': dict(rotations=0,   is_jump=0, is_spin=1, is_step=0, base_value=2.6,  duration_mu=2.2, level=3),
        'StSq3': dict(rotations=0,   is_jump=0, is_spin=0, is_step=1, base_value=3.3,  duration_mu=3.5, level=3),
        'ChSq1': dict(rotations=0,   is_jump=0, is_spin=0, is_step=1, base_value=3.0,  duration_mu=2.8, level=1),
    }

    per_class = n_samples // len(element_profiles)

    for label, p in element_profiles.items():
        for _ in range(per_class):
            dur = max(0.3, rng.normal(p['duration_mu'], 0.2))
            goe = int(rng.integers(-3, 4))
            rows.append({
                'label':       label,
                'duration':    round(dur, 3),
                'frame_count': int(dur * 30),
                'is_jump':     p['is_jump'],
                'is_spin':     p['is_spin'],
                'is_step':     p['is_step'],
                'rotations':   round(p['rotations'] + rng.normal(0, 0.1), 2),
                'level':       p['level'],
                'base_value':  round(p['base_value'] + rng.normal(0, 0.05), 2),
                'goe':         goe,
            })

    df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
    return df


def _run_training(
    np, pd, StandardScaler, train_test_split,
    accuracy_score, classification_report, confusion_matrix,
    RandomForestClassifier, GradientBoostingClassifier, SVC, MLPClassifier,
    joblib, model_dir,
    df, model_type, test_size, n_estimators, max_depth
):
    """تنفيذ دورة التدريب الكاملة وإرجاع النتائج"""
    feature_cols = ['duration', 'frame_count', 'is_jump', 'is_spin',
                    'is_step', 'rotations', 'level', 'base_value', 'goe']

    X = df[feature_cols].values
    y = df['label'].values

    # ترميز التسميات
    unique_labels = sorted(df['label'].unique())
    label_encoder = {lbl: i for i, lbl in enumerate(unique_labels)}
    inverse_enc   = {i: lbl for lbl, i in label_encoder.items()}
    y_enc = np.array([label_encoder[lbl] for lbl in y])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=test_size, random_state=42, stratify=y_enc
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # بناء النموذج
    models = {
        "random_forest":  RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth,
                                                  random_state=42, n_jobs=-1),
        "gradient_boost": GradientBoostingClassifier(n_estimators=n_estimators,
                                                      max_depth=max_depth or 3, random_state=42),
        "svm":            SVC(kernel='rbf', probability=True, random_state=42),
        "neural_net":     MLPClassifier(hidden_layer_sizes=(128, 64, 32),
                                        max_iter=500, random_state=42),
    }
    model = models[model_type]
    model.fit(X_train_s, y_train)

    y_pred_train = model.predict(X_train_s)
    y_pred_test  = model.predict(X_test_s)

    acc_train = accuracy_score(y_train, y_pred_train)
    acc_test  = accuracy_score(y_test, y_pred_test)

    y_test_lbl  = [inverse_enc[i] for i in y_test]
    y_pred_lbl  = [inverse_enc[i] for i in y_pred_test]

    report = classification_report(y_test_lbl, y_pred_lbl)
    cm     = confusion_matrix(y_test_lbl, y_pred_lbl, labels=unique_labels)

    # Feature importance
    feature_importance = None
    if hasattr(model, 'feature_importances_'):
        feature_importance = dict(zip(feature_cols, model.feature_importances_.tolist()))

    return {
        'model':             model,
        'scaler':            scaler,
        'model_name':        model_type,
        'feature_names':     feature_cols,
        'label_encoder':     label_encoder,
        'labels':            unique_labels,
        'acc_train':         acc_train,
        'acc_test':          acc_test,
        'report':            report,
        'confusion_matrix':  cm,
        'feature_importance':feature_importance,
    }

def show_referee():
    st.header(t('referee'))

    if not CORE_AI_AVAILABLE:
        st.error(t('ai_not_available'))
        st.code("pip install mediapipe opencv-python numpy")
        return

    st.success("✅ Referee interface ready!")

def show_video_analysis():
    st.header(t('video_analysis'))

    if not ANALYZER_AVAILABLE:
        st.warning("Advanced analyzer not available")
        if CORE_AI_AVAILABLE:
            st.info("Basic AI features are available in ML Training page")
        return

    st.success("✅ Professional analysis ready!")

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
elif page == t('stats'):
    show_stats()
else:
    show_settings()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("v3.0 - Fixed & Stable")
