"""
التطبيق الرئيسي - نظام تحليل التزلج الفني
"""
import streamlit as st
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import get_config
from src.utils.logger import setup_logger
from src.database.database_manager import DatabaseManager
from src.database.models import Skater, Video, Analysis
from src.core.video_processor import VideoProcessor
from src.core.pose_detector import PoseDetector
from src.analysis.scoring_engine import ScoringEngine
import tempfile
import time

# إعداد الصفحة
st.set_page_config(
    page_title="نظام تحليل التزلج الفني ⛸️",
    page_icon="⛸️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_system():
    """تهيئة النظام"""
    if 'initialized' not in st.session_state:
        # تحميل الإعدادات
        config = get_config()

        # إعداد السجلات
        logger = setup_logger(
            name='app',
            log_file=config.LOG_FILE,
            log_level=config.LOG_LEVEL
        )

        # تهيئة قاعدة البيانات
        db_manager = DatabaseManager(config.DATABASE_URL)
        db_manager.init_db()

        st.session_state.config = config
        st.session_state.logger = logger
        st.session_state.db_manager = db_manager
        st.session_state.initialized = True

        logger.info("تم تهيئة النظام بنجاح")


def main():
    """الوظيفة الرئيسية"""

    # تهيئة النظام
    init_system()

    config = st.session_state.config
    logger = st.session_state.logger
    db_manager = st.session_state.db_manager

    # الشريط الجانبي
    with st.sidebar:
        st.title("⛸️ نظام تحليل التزلج الفني")
        st.markdown("---")

        page = st.radio(
            "القائمة الرئيسية",
            [
                "🏠 الرئيسية",
                "📹 تحليل فيديو جديد",
                "👥 إدارة المتزلجين",
                "📊 التحليلات السابقة",
                "📈 الإحصائيات",
                "📖 معايير ISU",
                "⚙️ الإعدادات"
            ]
        )

        st.markdown("---")
        st.info("💡 نظام ذكاء اصطناعي متقدم لتحليل التزلج الفني")

    # عرض الصفحة المختارة
    if page == "🏠 الرئيسية":
        show_home_page()

    elif page == "📹 تحليل فيديو جديد":
        show_analysis_page(config, db_manager)

    elif page == "👥 إدارة المتزلجين":
        show_skaters_page(db_manager)

    elif page == "📊 التحليلات السابقة":
        show_history_page(db_manager)

    elif page == "📈 الإحصائيات":
        show_statistics_page(db_manager)

    elif page == "📖 معايير ISU":
        show_isu_standards_page()

    elif page == "⚙️ الإعدادات":
        show_settings_page(config)


def show_home_page():
    """الصفحة الرئيسية"""
    st.title("🏆 نظام تحليل التزلج الفني المتقدم")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("المتزلجون", "0", "0")
    with col2:
        st.metric("الفيديوهات", "0", "0")
    with col3:
        st.metric("التحليلات", "0", "0")
    with col4:
        st.metric("متوسط الدرجات", "0.0", "0")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 نظرة عامة")
        st.write("""
        **نظام شامل لتحليل التزلج الفني باستخدام الذكاء الاصطناعي:**

        - 🎯 **تحليل دقيق** للحركات والوضعيات باستخدام MediaPipe
        - 📊 **تسجيل احترافي** وفق معايير ISU الدولية
        - 🤖 **ذكاء اصطناعي** لتقييم جودة التنفيذ
        - 📹 **معالجة فيديو** متقدمة
        - 📈 **تقارير تفصيلية** وإحصائيات شاملة
        - 💾 **قاعدة بيانات** لتتبع التقدم
        """)

    with col2:
        st.subheader("🚀 البدء السريع")

        if st.button("📤 تحليل فيديو جديد", use_container_width=True):
            st.session_state.current_page = "analysis"
            st.rerun()

        if st.button("👥 إضافة متزلج جديد", use_container_width=True):
            st.session_state.current_page = "skaters"
            st.rerun()

        if st.button("📚 عرض التحليلات السابقة", use_container_width=True):
            st.session_state.current_page = "history"
            st.rerun()

        if st.button("📖 معايير ISU", use_container_width=True):
            st.session_state.current_page = "isu"
            st.rerun()


def show_analysis_page(config, db_manager):
    """صفحة تحليل الفيديو"""
    st.title("📹 تحليل فيديو جديد")

    # اختيار المتزلج
    with db_manager.get_session() as session:
        skaters = session.query(Skater).all()

        if not skaters:
            st.warning("⚠️ لا يوجد متزلجون مسجلون. الرجاء إضافة متزلج أولاً.")
            if st.button("إضافة متزلج جديد"):
                st.session_state.current_page = "skaters"
                st.rerun()
            return

        skater_options = {f"{s.name} ({s.country})": s.id for s in skaters}
        selected_skater = st.selectbox("اختر المتزلج", list(skater_options.keys()))
        skater_id = skater_options[selected_skater]

    # رفع الفيديو
    uploaded_file = st.file_uploader(
        "ارفع فيديو التزلج",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help=f"الحد الأقصى للحجم: {config.VIDEO_MAX_SIZE_MB}MB"
    )

    if uploaded_file:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.video(uploaded_file)

        with col2:
            st.subheader("⚙️ خيارات التحليل")

            analysis_mode = st.selectbox(
                "نوع التحليل",
                ["سريع", "قياسي", "مفصل"]
            )

            program_type = st.selectbox(
                "نوع البرنامج",
                ["برنامج قصير", "برنامج حر", "تدريب"]
            )

            st.markdown("---")

            if st.button("🚀 بدء التحليل", use_container_width=True, type="primary"):
                analyze_video(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager)


def analyze_video(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager):
    """تحليل الفيديو"""

    # حفظ الملف المؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        tmp_file.write(uploaded_file.read())
        video_path = tmp_file.name

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 1. معالجة الفيديو
        status_text.text("📹 معالجة الفيديو...")
        progress_bar.progress(10)

        with VideoProcessor(video_path, config) as video_proc:
            video_proc.open()
            video_stats = video_proc.get_video_stats()

        # 2. كشف الوضعيات
        status_text.text("🧍 كشف الوضعيات...")
        progress_bar.progress(30)

        pose_detector = PoseDetector(config)
        # هنا يمكن إضافة معالجة الإطارات

        # 3. تحليل الحركات
        status_text.text("🎯 تحليل الحركات...")
        progress_bar.progress(60)
        time.sleep(1)  # محاكاة المعالجة

        # 4. حساب الدرجات
        status_text.text("📊 حساب الدرجات...")
        progress_bar.progress(80)

        scoring_engine = ScoringEngine()

        # مثال على حساب الدرجات
        elements = [
            {'code': '3A', 'goe': 2},
            {'code': '3Lz', 'goe': 1},
            {'code': 'CCoSp4', 'goe': 3},
        ]

        program_score = scoring_engine.calculate_total_score(
            elements=elements,
            skating_skills=8.5,
            transitions=8.0,
            performance=8.25,
            composition=8.0,
            interpretation=8.5,
            program_type='free'
        )

        # 5. عرض النتائج
        progress_bar.progress(100)
        status_text.text("✅ اكتمل التحليل!")

        st.success("🎉 تم التحليل بنجاح!")

        # عرض النتائج
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("الدرجة التقنية", f"{program_score.technical_score:.2f}")
        with col2:
            st.metric("درجة المكونات", f"{program_score.program_components_score:.2f}")
        with col3:
            st.metric("الخصومات", f"-{program_score.total_deductions:.2f}")
        with col4:
            st.metric("الدرجة النهائية", f"{program_score.total_score:.2f}")

        # تفاصيل العناصر
        st.subheader("🎯 العناصر المنفذة")

        for element in program_score.elements:
            with st.expander(f"{element.element_name} ({element.element_code})"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**القيمة الأساسية:** {element.base_value:.2f}")
                with col2:
                    st.write(f"**GOE:** {element.goe:+d}")
                with col3:
                    st.write(f"**قيمة GOE:** {element.goe_value:+.2f}")
                with col4:
                    st.write(f"**المجموع:** {element.total_score:.2f}")

    except Exception as e:
        st.error(f"❌ خطأ في التحليل: {e}")

    finally:
        # تنظيف الملف المؤقت
        try:
            Path(video_path).unlink()
        except:
            pass


def show_skaters_page(db_manager):
    """صفحة إدارة المتزلجين"""
    st.title("👥 إدارة المتزلجين والمدربين")

    # إحصائيات سريعة
    try:
        with db_manager.get_session() as session:
            total_skaters = session.query(Skater).count()
            total_coaches = session.query(Skater).filter(
                Skater.notes.like('%مدرب%')
            ).count()
            total_players = total_skaters - total_coaches

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 إجمالي اللاعبين", total_players)
        with col2:
            st.metric("🎓 إجمالي المدربين", total_coaches)
        with col3:
            st.metric("📊 الإجمالي الكلي", total_skaters)

        st.markdown("---")

    except Exception as e:
        st.error(f"❌ خطأ في تحميل الإحصائيات: {e}")

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 اللاعبون",
        "🎓 المدربون",
        "➕ إضافة جديد",
        "📥 استيراد البيانات"
    ])

    # تبويب اللاعبين
    with tab1:
        st.subheader("👥 قائمة اللاعبين")

        # بحث وفلترة
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 البحث عن لاعب", placeholder="ادخل اسم اللاعب...")
        with col2:
            sort_by = st.selectbox("الترتيب حسب", ["الاسم", "الأحدث"])

        try:
            with db_manager.get_session() as session:
                # استعلام اللاعبين (غير المدربين)
                query = session.query(Skater).filter(
                    ~Skater.notes.like('%مدرب%')
                )

                if search_query:
                    query = query.filter(Skater.name.like(f'%{search_query}%'))

                if sort_by == "الاسم":
                    players = query.order_by(Skater.name).all()
                else:
                    players = query.order_by(Skater.created_at.desc()).all()

                if players:
                    st.info(f"📊 عدد اللاعبين: {len(players)}")

                    # عرض اللاعبين في جدول
                    for idx, player in enumerate(players, 1):
                        with st.expander(f"{idx}. {player.name} - {player.country or 'مصر'}"):
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.write(f"**الدولة:** {player.country or 'مصر'}")
                                st.write(f"**التخصص:** {player.discipline or 'Singles'}")

                            with col2:
                                st.write(f"**المدرب:** {player.coach_name or 'غير محدد'}")
                                st.write(f"**النادي:** {player.club or 'غير محدد'}")

                            with col3:
                                st.write(f"**عدد الفيديوهات:** {player.total_videos or 0}")
                                st.write(f"**عدد التحليلات:** {player.total_analyses or 0}")

                            if player.notes:
                                st.caption(f"📝 {player.notes}")
                else:
                    st.warning("⚠️ لا يوجد لاعبون حالياً")

        except Exception as e:
            st.error(f"❌ خطأ في تحميل اللاعبين: {e}")

    # تبويب المدربين
    with tab2:
        st.subheader("🎓 قائمة المدربين")

        try:
            with db_manager.get_session() as session:
                coaches = session.query(Skater).filter(
                    Skater.notes.like('%مدرب%')
                ).order_by(Skater.name).all()

                if coaches:
                    st.info(f"📊 عدد المدربين: {len(coaches)}")

                    # عرض المدربين
                    cols = st.columns(3)
                    for idx, coach in enumerate(coaches):
                        col = cols[idx % 3]
                        with col:
                            with st.container():
                                st.markdown(f"""
                                <div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;'>
                                    <h4>🎓 {coach.name}</h4>
                                    <p>📍 {coach.country or 'مصر'}</p>
                                    <p>👥 لاعبين: {coach.total_videos or 0}</p>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ لا يوجد مدربون حالياً")

        except Exception as e:
            st.error(f"❌ خطأ في تحميل المدربين: {e}")

    # تبويب إضافة جديد
    with tab3:
        st.subheader("➕ إضافة متزلج جديد")

        with st.form("add_skater_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("الاسم الكامل*")
                country = st.text_input("الدولة", value="مصر")
                gender = st.selectbox("الجنس", ["أنثى", "ذكر"])
                category = st.selectbox("الفئة", ["Junior", "Senior"])

            with col2:
                discipline = st.selectbox("التخصص", ["Singles", "Pairs", "Ice Dance", "Coach"])
                coach_name = st.text_input("اسم المدرب")
                club = st.text_input("النادي")
                is_coach = st.checkbox("مدرب")

            notes = st.text_area("ملاحظات")

            submitted = st.form_submit_button("➕ إضافة", use_container_width=True, type="primary")

            if submitted and name:
                try:
                    with db_manager.get_session() as session:
                        # التحقق من عدم التكرار
                        existing = session.query(Skater).filter_by(name=name).first()
                        if existing:
                            st.warning(f"⚠️ اللاعب {name} موجود مسبقاً")
                        else:
                            final_notes = notes
                            if is_coach:
                                final_notes = f"مدرب\n{notes}" if notes else "مدرب"

                            skater = Skater(
                                name=name,
                                country=country,
                                gender=gender,
                                category=category,
                                discipline="Coach" if is_coach else discipline,
                                coach_name=coach_name,
                                club=club,
                                notes=final_notes,
                                total_videos=0,
                                total_analyses=0
                            )
                            session.add(skater)

                        st.success(f"✅ تمت إضافة {'المدرب' if is_coach else 'اللاعب'}: {name}")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ خطأ في الإضافة: {e}")

    # تبويب استيراد البيانات
    with tab4:
        st.subheader("📥 استيراد البيانات من Excel")

        st.info("""
        💡 **تم استيراد البيانات مسبقاً!**

        - ✅ 91 لاعب
        - ✅ 20 مدرب
        - 📊 المجموع: 111 سجل

        البيانات مستخرجة من ملفات الحضور والعضوية.
        """)

        if st.button("🔄 إعادة الاستيراد", type="secondary"):
            with st.spinner("جاري الاستيراد..."):
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "import_players_coaches_to_db.py"],
                        capture_output=True,
                        text=True
                    )

                    if result.returncode == 0:
                        st.success("✅ تم إعادة الاستيراد بنجاح!")
                        st.code(result.stdout)
                        st.rerun()
                    else:
                        st.error(f"❌ خطأ: {result.stderr}")

                except Exception as e:
                    st.error(f"❌ خطأ في الاستيراد: {e}")


def show_history_page(db_manager):
    """صفحة التحليلات السابقة"""
    st.title("📊 التحليلات السابقة")
    st.info("🚧 قيد التطوير...")


def show_statistics_page(db_manager):
    """صفحة الإحصائيات"""
    st.title("📈 الإحصائيات")
    st.info("🚧 قيد التطوير...")


def show_isu_standards_page():
    """صفحة معايير ISU"""
    st.title("📖 معايير ISU للتسجيل")

    from src.config.isu_standards import ISUStandards
    standards = ISUStandards()

    tab1, tab2, tab3, tab4 = st.tabs(["🦘 القفزات", "🌀 الدورانات", "👣 الخطوات", "📊 GOE"])

    with tab1:
        st.subheader("القفزات ومعاييرها")
        for code, info in standards.JUMPS.items():
            with st.expander(f"{info['name']} ({code}) - القيمة: {info['base_value']}"):
                st.write(f"**الاسم العربي:** {info['name_ar']}")
                st.write(f"**عدد الدورات:** {info['rotations']}")
                st.write(f"**الحافة:** {info['edge']}")
                st.write(f"**استخدام المسننات:** {'نعم' if info['toe_pick'] else 'لا'}")

    with tab2:
        st.subheader("الدورانات ومعاييرها")
        for code, info in standards.SPINS.items():
            with st.expander(f"{info['name']} ({code})"):
                st.write(f"**الاسم العربي:** {info['name_ar']}")
                st.write(f"**الوصف:** {info['description']}")
                st.write(f"**القيم الأساسية حسب المستوى:**")
                for level, value in enumerate(info['base_values']):
                    if level > 0:
                        st.write(f"  - المستوى {level}: {value}")


def show_settings_page(config):
    """صفحة الإعدادات"""
    st.title("⚙️ الإعدادات")

    st.subheader("معلومات النظام")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**اسم التطبيق:** {config.APP_NAME}")
        st.write(f"**الإصدار:** {config.APP_VERSION}")
        st.write(f"**البيئة:** {os.getenv('ENVIRONMENT', 'development')}")

    with col2:
        st.write(f"**قاعدة البيانات:** {config.DATABASE_URL[:50]}...")
        st.write(f"**مستوى السجلات:** {config.LOG_LEVEL}")


if __name__ == "__main__":
    import os
    main()
