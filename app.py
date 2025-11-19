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
from src.analysis.scoring_engine import ScoringEngine
import pandas as pd
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
    st.title("🏠 مرحباً بك في نظام تحليل التزلج الفني")

    st.markdown("""
    ### ⛸️ نظام ذكاء اصطناعي متقدم لتحليل وتقييم التزلج الفني

    ---

    ## 🎯 الميزات الرئيسية:

    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
        ### 📹 تحليل الفيديو
        - رفع فيديوهات الأداء
        - كشف تلقائي للحركات
        - تحليل بالذكاء الاصطناعي
        """)

    with col2:
        st.success("""
        ### 📊 معايير ISU
        - 24 نوع قفزة
        - 35 نوع دوران
        - نظام GOE كامل
        """)

    with col3:
        st.warning("""
        ### 👥 إدارة اللاعبين
        - 91 لاعب مسجل
        - 20 مدرب
        - تتبع الأداء
        """)

    st.markdown("---")

    # إحصائيات سريعة
    st.subheader("📊 إحصائيات سريعة")

    try:
        db_manager = st.session_state.db_manager
        with db_manager.get_session() as session:
            total_skaters = session.query(Skater).count()
            total_coaches = session.query(Skater).filter(
                Skater.notes.like('%مدرب%')
            ).count()
            total_players = total_skaters - total_coaches

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("👥 اللاعبون", total_players)
        with col2:
            st.metric("🎓 المدربون", total_coaches)
        with col3:
            st.metric("📊 الإجمالي", total_skaters)
        with col4:
            st.metric("📹 الفيديوهات", "0")

    except:
        pass

    st.markdown("---")

    st.info("""
    ### 🚀 ابدأ الآن!
    استخدم القائمة الجانبية للانتقال بين الأقسام المختلفة
    """)


def show_analysis_page(config, db_manager):
    """صفحة تحليل فيديو جديد"""
    st.title("📹 تحليل فيديو جديد")

    # الحصول على قائمة اللاعبين
    try:
        with db_manager.get_session() as session:
            skaters = session.query(Skater).filter(
                ~Skater.notes.like('%مدرب%')
            ).order_by(Skater.name).all()

            if not skaters:
                st.warning("⚠️ لا يوجد لاعبون مسجلون. الرجاء إضافة لاعب أولاً من صفحة 'إدارة المتزلجين'")
                return

            skater_options = {f"{s.name} ({s.country or 'مصر'})": s.id for s in skaters}

    except Exception as e:
        st.error(f"❌ خطأ في تحميل اللاعبين: {e}")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📤 رفع الفيديو")

        uploaded_file = st.file_uploader(
            "اختر ملف الفيديو",
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="الصيغ المدعومة: MP4, AVI, MOV, MKV"
        )

        if uploaded_file:
            st.success(f"✅ تم اختيار: {uploaded_file.name}")
            st.write(f"📏 الحجم: {uploaded_file.size / (1024*1024):.2f} MB")

    with col2:
        st.subheader("⚙️ الإعدادات")

        skater_name = st.selectbox(
            "اللاعب",
            options=list(skater_options.keys())
        )

        skater_id = skater_options[skater_name]

        analysis_mode = st.selectbox(
            "نوع التحليل",
            ["تحليل كامل", "تحليل سريع", "الوضعيات فقط"]
        )

        program_type = st.selectbox(
            "نوع البرنامج",
            ["برنامج قصير", "برنامج حر", "تدريب"]
        )

        st.markdown("---")

        if st.button("🚀 بدء التحليل", use_container_width=True, type="primary"):
            if uploaded_file:
                analyze_video(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager)
            else:
                st.error("❌ الرجاء اختيار ملف فيديو أولاً")


def analyze_video(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager):
    """تحليل الفيديو - النسخة المحسنة"""

    st.info("🎥 **وضع التشغيل التجريبي** - يتم عرض نتائج نموذجية للتوضيح")

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 1. حفظ معلومات الفيديو
        status_text.text("📹 معالجة الفيديو...")
        progress_bar.progress(20)
        time.sleep(0.5)

        video_info = {
            'filename': uploaded_file.name,
            'size_mb': uploaded_file.size / (1024 * 1024),
            'type': uploaded_file.type
        }

        # 2. تحليل تجريبي
        status_text.text("🧍 كشف الحركات...")
        progress_bar.progress(40)
        time.sleep(0.5)

        # 3. تحليل العناصر (تجريبي)
        status_text.text("🎯 تحليل العناصر...")
        progress_bar.progress(60)
        time.sleep(0.5)

        # عناصر تجريبية حسب نوع البرنامج
        if "قصير" in program_type:
            elements = [
                {'code': '3A', 'goe': 2},
                {'code': '3F', 'goe': 1},
                {'code': '3Lz+3T', 'goe': 2},
                {'code': 'FCSp4', 'goe': 2},
                {'code': 'StSq3', 'goe': 1},
                {'code': 'CCoSp4', 'goe': 3},
            ]
            skating_skills = 7.5
            transitions = 7.25
            performance = 7.75
            composition = 7.50
            interpretation = 7.75
        else:  # برنامج حر
            elements = [
                {'code': '4T', 'goe': 1},
                {'code': '3A', 'goe': 2},
                {'code': '3Lz', 'goe': 1},
                {'code': '3F+3T', 'goe': 2},
                {'code': '3Lo', 'goe': 0},
                {'code': '2A', 'goe': 1},
                {'code': 'FCSp4', 'goe': 2},
                {'code': 'StSq4', 'goe': 3},
                {'code': 'ChSq1', 'goe': 2},
                {'code': 'FCCoSp4', 'goe': 2},
                {'code': 'CCoSp4', 'goe': 3},
            ]
            skating_skills = 8.25
            transitions = 8.0
            performance = 8.50
            composition = 8.25
            interpretation = 8.50

        # 4. حساب الدرجات
        status_text.text("📊 حساب الدرجات...")
        progress_bar.progress(80)
        time.sleep(0.5)

        scoring_engine = ScoringEngine()

        program_score = scoring_engine.calculate_total_score(
            elements=elements,
            skating_skills=skating_skills,
            transitions=transitions,
            performance=performance,
            composition=composition,
            interpretation=interpretation,
            program_type='short' if "قصير" in program_type else 'free'
        )

        # 5. حفظ في قاعدة البيانات
        status_text.text("💾 حفظ النتائج...")
        progress_bar.progress(90)

        try:
            with db_manager.get_session() as session:
                # حفظ الفيديو
                video = Video(
                    skater_id=skater_id,
                    filename=video_info['filename'],
                    file_path=f"uploads/{video_info['filename']}",
                    file_size_mb=video_info['size_mb'],
                    program_type=program_type,
                    status='completed'
                )
                session.add(video)
                session.flush()

                # حفظ التحليل
                analysis = Analysis(
                    video_id=video.id,
                    analysis_type=analysis_mode,
                    overall_score=program_score.total_score,
                    confidence=0.85,
                    status='completed',
                    analysis_metadata={'demo_mode': True}
                )
                session.add(analysis)

                # تحديث إحصائيات اللاعب
                skater = session.query(Skater).filter_by(id=skater_id).first()
                if skater:
                    skater.total_videos = (skater.total_videos or 0) + 1
                    skater.total_analyses = (skater.total_analyses or 0) + 1

        except Exception as db_error:
            st.warning(f"⚠️ لم يتم حفظ النتائج في قاعدة البيانات: {db_error}")

        # 6. عرض النتائج
        progress_bar.progress(100)
        status_text.text("✅ اكتمل التحليل!")
        time.sleep(0.5)

        st.success("🎉 تم التحليل بنجاح!")

        # معلومات الفيديو
        with st.expander("📹 معلومات الفيديو", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**الاسم:** {video_info['filename']}")
            with col2:
                st.write(f"**الحجم:** {video_info['size_mb']:.2f} MB")
            with col3:
                st.write(f"**النوع:** {video_info['type']}")

        st.markdown("---")

        # عرض الدرجات
        st.subheader("🏆 النتيجة النهائية")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("الدرجة التقنية", f"{program_score.technical_score:.2f}")
        with col2:
            st.metric("درجة المكونات", f"{program_score.program_components_score:.2f}")
        with col3:
            st.metric("الخصومات", f"-{program_score.total_deductions:.2f}")
        with col4:
            st.metric("⭐ الدرجة النهائية", f"{program_score.total_score:.2f}")

        # تفاصيل العناصر
        st.markdown("---")
        st.subheader("🎯 تفاصيل العناصر المنفذة")

        # جدول العناصر
        elements_data = []
        for idx, element in enumerate(program_score.elements, 1):
            elements_data.append({
                '#': idx,
                'العنصر': element.element_name,
                'الكود': element.element_code,
                'القيمة الأساسية': f"{element.base_value:.2f}",
                'GOE': f"{element.goe:+d}",
                'قيمة GOE': f"{element.goe_value:+.2f}",
                'المجموع': f"{element.total_score:.2f}"
            })

        df_elements = pd.DataFrame(elements_data)
        st.dataframe(df_elements, use_container_width=True, hide_index=True)

        # مكونات البرنامج
        st.markdown("---")
        st.subheader("🎨 مكونات البرنامج")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**💫 المهارات الفنية:**")
            st.progress(skating_skills / 10, text=f"Skating Skills: {skating_skills:.2f}")
            st.progress(transitions / 10, text=f"Transitions: {transitions:.2f}")
            st.progress(performance / 10, text=f"Performance: {performance:.2f}")

        with col2:
            st.write("**🎭 المهارات التعبيرية:**")
            st.progress(composition / 10, text=f"Composition: {composition:.2f}")
            st.progress(interpretation / 10, text=f"Interpretation: {interpretation:.2f}")

            avg_components = (skating_skills + transitions + performance + composition + interpretation) / 5
            st.metric("المتوسط", f"{avg_components:.2f}")

        # ملاحظات وتوصيات
        st.markdown("---")
        st.subheader("📝 ملاحظات وتوصيات")

        if program_score.total_score >= 150:
            st.success("""
            ✨ **أداء ممتاز!**
            - درجة عالية تؤهل للمنافسة الدولية
            - جودة تنفيذ ممتازة للعناصر
            - مكونات البرنامج على مستوى احترافي
            """)
        elif program_score.total_score >= 120:
            st.info("""
            👍 **أداء جيد جداً**
            - مستوى تنافسي قوي
            - يُنصح بالتركيز على تحسين GOE
            - تطوير مكونات البرنامج سيرفع الدرجة
            """)
        else:
            st.warning("""
            💪 **مجال للتطوير**
            - التدريب على استقرار القفزات
            - تحسين سرعة الدوران
            - العمل على التعبير الفني
            """)

        # زر التصدير
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("📥 تصدير التقرير الكامل", use_container_width=True):
                st.info("🚧 ميزة التصدير قيد التطوير...")

    except Exception as e:
        st.error(f"❌ خطأ في التحليل: {e}")
        import traceback
        with st.expander("🔍 تفاصيل الخطأ"):
            st.code(traceback.format_exc())


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
            with st.expander(f"{info['name']} ({code}) - القيمة: {info['base_value']}"):
                st.write(f"**الاسم العربي:** {info['name_ar']}")
                st.write(f"**النوع:** {info['type']}")
                if 'features' in info:
                    st.write(f"**المميزات:** {', '.join(info['features'])}")

    with tab3:
        st.subheader("تسلسلات الخطوات")
        st.info("تسلسلات الخطوات يتم تقييمها من المستوى 1 إلى المستوى 4")

    with tab4:
        st.subheader("نظام GOE (Grade of Execution)")
        st.write("نطاق التقييم: من -5 إلى +5")

        goe_data = []
        for goe, multiplier in standards.GOE_VALUES.items():
            goe_data.append({
                'GOE': f"{goe:+d}",
                'المضاعف': f"{multiplier:+.2f}",
                'التأثير': 'سلبي' if goe < 0 else ('إيجابي' if goe > 0 else 'محايد')
            })

        df_goe = pd.DataFrame(goe_data)
        st.dataframe(df_goe, use_container_width=True, hide_index=True)


def show_settings_page(config):
    """صفحة الإعدادات"""
    st.title("⚙️ الإعدادات")
    st.info("🚧 قيد التطوير...")


if __name__ == "__main__":
    main()
