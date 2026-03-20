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
from src.database.models import Skater, Video, Analysis, Attendance, Payment, Schedule
from src.analysis.scoring_engine import ScoringEngine
from src.models.movement_classifier import MovementClassifier, MovementFeatures
from src.models.training_engine import TrainingEngine, FeatureExtractor
from src.pages.attendance_page import show_attendance_page
from src.pages.payment_page import show_payments_page
from src.pages.schedule_page import show_schedule_page
from src.pages.member_profile_page import show_member_profile_page
import pandas as pd
import tempfile
import time
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import func
import plotly.graph_objects as go
import plotly.express as px
from src.utils.styles import get_custom_css, get_metric_card_html, get_alert_html

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
                "👤 ملف العضو الشامل",
                "📊 التحليلات السابقة",
                "📈 الإحصائيات",
                "📅 الحضور والغياب",
                "💰 المدفوعات",
                "📆 جدول التدريبات",
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

    elif page == "👤 ملف العضو الشامل":
        show_member_profile_page(db_manager)

    elif page == "📊 التحليلات السابقة":
        show_history_page(db_manager)

    elif page == "📈 الإحصائيات":
        show_statistics_page(db_manager)

    elif page == "📅 الحضور والغياب":
        show_attendance_page(db_manager)

    elif page == "💰 المدفوعات":
        show_payments_page(db_manager)

    elif page == "📆 جدول التدريبات":
        show_schedule_page(db_manager)

    elif page == "📖 معايير ISU":
        show_isu_standards_page()

    elif page == "⚙️ الإعدادات":
        show_settings_page(config)


def show_home_page():
    """لوحة التحكم الرئيسية - Dashboard"""

    # إضافة CSS المخصص
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # العنوان الرئيسي مع تصميم احترافي
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
        <h1 style="color: white; margin: 0; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">⛸️ لوحة التحكم</h1>
    </div>
    """, unsafe_allow_html=True)

    # عرض التاريخ والوقت بتصميم احترافي
    now = datetime.now()
    st.markdown(f"""
    <div style="text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 2rem;">
        📅 {now.strftime('%A, %d %B %Y')} | ⏰ {now.strftime('%I:%M %p')}
    </div>
    """, unsafe_allow_html=True)

    try:
        db_manager = st.session_state.db_manager
        with db_manager.get_session() as session:

            # ==================== القسم 1: إحصائيات عامة ====================
            st.subheader("📊 نظرة عامة")

            # حساب الإحصائيات
            total_skaters = session.query(Skater).count()
            total_coaches = session.query(Skater).filter(Skater.notes.like('%مدرب%')).count()
            total_players = total_skaters - total_coaches

            # تحديد آخر تاريخ للحضور في البيانات
            latest_date_query = session.query(func.max(Attendance.date)).scalar()
            if latest_date_query:
                today = latest_date_query.date()
            else:
                today = date.today()

            # الحضور في آخر يوم مسجل
            today_attendance = session.query(Attendance).filter(
                func.date(Attendance.date) == today,
                Attendance.status == 'present'
            ).count()

            # إيرادات الشهر (للشهر الذي به بيانات)
            first_day = today.replace(day=1)
            last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            monthly_revenue = session.query(func.sum(Payment.amount)).filter(
                Payment.payment_date >= first_day,
                Payment.payment_date <= last_day,
                Payment.status == 'completed'
            ).scalar() or 0

            # عدد التحليلات
            total_analyses = session.query(Analysis).count()

            # عرض البطاقات
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric(
                    label="👥 اللاعبون",
                    value=total_players,
                    delta=None
                )

            with col2:
                st.metric(
                    label="🎓 المدربون",
                    value=total_coaches,
                    delta=None
                )

            with col3:
                # عرض التاريخ المستخدم
                date_label = f"✅ حضور {today.strftime('%d/%m')}" if today != date.today() else "✅ حضور اليوم"
                st.metric(
                    label=date_label,
                    value=today_attendance,
                    delta=None,
                    help=f"آخر حضور مسجل في {today}"
                )

            with col4:
                st.metric(
                    label="💰 إيرادات الشهر",
                    value=f"{monthly_revenue:,.0f} EGP",
                    delta=None
                )

            with col5:
                st.metric(
                    label="📹 التحليلات",
                    value=total_analyses,
                    delta=None
                )

            st.markdown("---")

            # ==================== القسم 2: تنبيهات مهمة ====================
            st.subheader("⚠️ تنبيهات وإشعارات")

            col_alert1, col_alert2 = st.columns(2)

            with col_alert1:
                # الاشتراكات المنتهية خلال 7 أيام
                week_later = today + timedelta(days=7)
                expiring_soon = session.query(
                    Skater.name,
                    func.max(Payment.period_end).label('expiry')
                ).join(Payment).group_by(Skater.id).having(
                    func.max(Payment.period_end).between(today, week_later)
                ).all()

                st.warning(f"**🔔 اشتراكات تنتهي قريباً: {len(expiring_soon)}**")
                if expiring_soon:
                    with st.expander("عرض التفاصيل"):
                        for name, expiry in expiring_soon[:5]:
                            days_left = (expiry - datetime.now()).days
                            st.write(f"• {name} - متبقي {days_left} يوم")
                else:
                    st.success("✅ لا توجد اشتراكات تنتهي قريباً")

            with col_alert2:
                # الاشتراكات المنتهية
                expired = session.query(
                    func.count(Skater.id)
                ).join(Payment).group_by(Skater.id).having(
                    func.max(Payment.period_end) < datetime.now()
                ).count()

                if expired > 0:
                    st.error(f"**❌ اشتراكات منتهية: {expired}**")
                    if st.button("عرض المتأخرات"):
                        st.info("انتقل إلى صفحة المدفوعات > المتأخرات")
                else:
                    st.success("✅ لا توجد اشتراكات منتهية")

            st.markdown("---")

            # ==================== القسم 3: جدول اليوم ====================
            st.subheader("📆 جدول الحصص اليوم")

            # أيام الأسبوع (0 = Monday)
            day_of_week = today.weekday()

            today_schedule = session.query(Schedule).filter(
                Schedule.day_of_week == day_of_week,
                Schedule.is_active == True
            ).order_by(Schedule.start_time).all()

            if today_schedule:
                for schedule in today_schedule:
                    coach_name = "غير محدد"
                    if schedule.coach_id:
                        coach = session.query(Skater).filter(Skater.id == schedule.coach_id).first()
                        if coach:
                            coach_name = coach.name

                    col_time, col_type, col_level, col_coach = st.columns([2, 2, 2, 2])

                    with col_time:
                        st.write(f"⏰ **{schedule.start_time} - {schedule.end_time}**")
                    with col_type:
                        emoji = "🧊" if schedule.session_type == "on-ice" else "🏃"
                        st.write(f"{emoji} {schedule.session_type}")
                    with col_level:
                        st.write(f"🎯 {schedule.level or 'الكل'}")
                    with col_coach:
                        st.write(f"👨‍🏫 {coach_name}")
            else:
                st.info("📝 لا توجد حصص مجدولة اليوم")

            st.markdown("---")

            # ==================== القسم 4: آخر النشاطات ====================
            col_activity1, col_activity2 = st.columns(2)

            with col_activity1:
                st.subheader("📋 آخر التحليلات")
                recent_analyses = session.query(
                    Analysis, Skater.name
                ).join(Skater).order_by(
                    Analysis.analysis_date.desc()
                ).limit(5).all()

                if recent_analyses:
                    for analysis, name in recent_analyses:
                        st.write(f"• {name} - {analysis.analysis_date.strftime('%Y-%m-%d')}")
                else:
                    st.info("لا توجد تحليلات حتى الآن")

            with col_activity2:
                st.subheader("💳 آخر المدفوعات")
                recent_payments = session.query(
                    Payment, Skater.name
                ).join(Skater).order_by(
                    Payment.payment_date.desc()
                ).limit(5).all()

                if recent_payments:
                    for payment, name in recent_payments:
                        st.write(f"• {name} - {payment.amount:.0f} EGP ({payment.payment_date.strftime('%Y-%m-%d')})")
                else:
                    st.info("لا توجد مدفوعات حتى الآن")

            st.markdown("---")

            # ==================== القسم 5: إحصائيات الحضور ====================
            st.subheader("📊 إحصائيات الحضور (آخر 7 أيام)")

            week_ago = today - timedelta(days=7)
            weekly_attendance = session.query(
                func.date(Attendance.date).label('date'),
                func.count(Attendance.id).label('count')
            ).filter(
                Attendance.date >= week_ago,
                Attendance.status == 'present'
            ).group_by(func.date(Attendance.date)).all()

            if weekly_attendance:
                # إنشاء DataFrame للعرض
                df_attendance = pd.DataFrame(weekly_attendance, columns=['التاريخ', 'عدد الحاضرين'])

                # إنشاء رسم بياني تفاعلي احترافي باستخدام Plotly
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=df_attendance['التاريخ'],
                    y=df_attendance['عدد الحاضرين'],
                    text=df_attendance['عدد الحاضرين'],
                    textposition='outside',
                    marker=dict(
                        color=df_attendance['عدد الحاضرين'],
                        colorscale='Blues',
                        line=dict(color='rgba(0,0,0,0.2)', width=1)
                    ),
                    hovertemplate='<b>التاريخ</b>: %{x}<br><b>الحضور</b>: %{y}<extra></extra>'
                ))

                fig.update_layout(
                    title={
                        'text': 'إحصائيات الحضور الأسبوعية',
                        'y':0.95,
                        'x':0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {'size': 20, 'color': '#1e40af', 'family': 'Cairo'}
                    },
                    xaxis_title='التاريخ',
                    yaxis_title='عدد الحاضرين',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Cairo', size=14),
                    hovermode='x unified',
                    showlegend=False,
                    height=400,
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)',
                        showline=True,
                        linecolor='rgba(0,0,0,0.2)'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)',
                        showline=True,
                        linecolor='rgba(0,0,0,0.2)'
                    )
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات حضور لآخر 7 أيام")

            st.markdown("---")

            # ==================== القسم 6: رسوم بيانية إضافية ====================
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("📊 توزيع الأعضاء")
                # رسم دائري لتوزيع اللاعبين والمدربين
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['اللاعبون', 'المدربون'],
                    values=[total_players, total_coaches],
                    hole=.4,
                    marker=dict(colors=['#667eea', '#f5576c']),
                    textinfo='label+percent',
                    textfont=dict(size=14, family='Cairo'),
                    hovertemplate='<b>%{label}</b><br>العدد: %{value}<br>النسبة: %{percent}<extra></extra>'
                )])

                fig_pie.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0),
                    font=dict(family='Cairo', size=12),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig_pie, use_container_width=True)

            with col_chart2:
                st.subheader("💰 الإيرادات الشهرية (آخر 6 أشهر)")
                # حساب الإيرادات لآخر 6 أشهر
                months_data = []
                for i in range(5, -1, -1):
                    month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                    month_revenue = session.query(func.sum(Payment.amount)).filter(
                        Payment.payment_date >= month_start,
                        Payment.payment_date <= month_end,
                        Payment.status == 'completed'
                    ).scalar() or 0

                    months_data.append({
                        'شهر': month_start.strftime('%b %Y'),
                        'الإيرادات': month_revenue
                    })

                df_revenue = pd.DataFrame(months_data)

                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=df_revenue['شهر'],
                    y=df_revenue['الإيرادات'],
                    mode='lines+markers+text',
                    name='الإيرادات',
                    line=dict(color='#43e97b', width=3),
                    marker=dict(size=10, color='#38f9d7', line=dict(color='#43e97b', width=2)),
                    text=[f'{v:,.0f}' for v in df_revenue['الإيرادات']],
                    textposition='top center',
                    textfont=dict(size=10),
                    fill='tozeroy',
                    fillcolor='rgba(67, 233, 123, 0.1)',
                    hovertemplate='<b>%{x}</b><br>الإيرادات: %{y:,.0f} EGP<extra></extra>'
                ))

                fig_line.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(t=20, b=0, l=0, r=0),
                    font=dict(family='Cairo', size=12),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=False, showline=True, linecolor='rgba(0,0,0,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', showline=False)
                )

                st.plotly_chart(fig_line, use_container_width=True)

    except Exception as e:
        st.error(f"❌ خطأ في تحميل البيانات: {e}")
        st.info("تأكد من تشغيل النظام بشكل صحيح")


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

        ai_mode = st.checkbox("🤖 استخدام التحليل الذكي (AI)", value=False,
                             help="يستخدم نماذج الذكاء الاصطناعي للتعرف على الحركات")

        analysis_mode = st.selectbox(
            "نوع التحليل",
            ["تحليل كامل", "تحليل سريع", "الوضعيات فقط"]
        )

        program_type = st.selectbox(
            "نوع البرنامج",
            ["برنامج قصير", "برنامج حر", "تدريب"]
        )

        st.markdown("---")

        button_text = "🤖 بدء التحليل الذكي" if ai_mode else "🚀 بدء التحليل"
        if st.button(button_text, use_container_width=True, type="primary"):
            if uploaded_file:
                if ai_mode:
                    analyze_video_with_ai(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager)
                else:
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


def analyze_video_with_ai(uploaded_file, skater_id, analysis_mode, program_type, config, db_manager):
    """تحليل الفيديو باستخدام الذكاء الاصطناعي - وضع تجريبي"""

    st.warning("""
    ⚠️ **ملاحظة هامة: وضع العرض التجريبي**

    هذا الوضع يعرض قدرات نظام التعرف على الحركات بشكل تجريبي.
    - ✅ النظام يحتوي على 24 قفزة + 35 دوران + تسلسلات الخطوات
    - ⚠️ لاستخدام التحليل الحقيقي، يتطلب تثبيت MediaPipe و OpenCV
    - 📊 النتائج المعروضة هي نماذج تعليمية توضح طريقة عمل النظام
    """)

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # تهيئة النماذج
        status_text.text("🧠 تحميل نماذج الذكاء الاصطناعي...")
        progress_bar.progress(5)
        time.sleep(0.3)

        classifier = MovementClassifier()
        feature_extractor = FeatureExtractor()

        # 1. حفظ معلومات الفيديو
        status_text.text("📹 معالجة الفيديو...")
        progress_bar.progress(15)
        time.sleep(0.5)

        video_info = {
            'filename': uploaded_file.name,
            'size_mb': uploaded_file.size / (1024 * 1024),
            'type': uploaded_file.type
        }

        # 2. **وضع العرض** - توليد نتائج نموذجية (في النسخة الكاملة: MediaPipe)
        status_text.text("🎭 توليد نتائج نموذجية للعرض...")
        progress_bar.progress(30)
        time.sleep(0.5)

        # توليد عناصر نموذجية واقعية
        detected_elements = generate_realistic_demo_elements(program_type)

        # 3. **عرض تجريبي** - في النسخة الحقيقية: تحليل الحركات باستخدام AI
        status_text.text("🎯 تحليل الحركات المكتشفة...")
        progress_bar.progress(50)
        time.sleep(0.8)

        # إظهار الحركات المكتشفة
        progress_bar.progress(70)
        time.sleep(0.3)

        # 4. حساب مكونات البرنامج من التحليل
        status_text.text("📊 حساب مكونات البرنامج...")
        progress_bar.progress(80)

        # تقدير المكونات بناءً على جودة الحركات المكتشفة
        avg_confidence = np.mean([e['confidence'] for e in detected_elements]) if detected_elements else 0.5

        skating_skills = 7.0 + avg_confidence * 2.0
        transitions = 6.8 + avg_confidence * 2.2
        performance = 7.2 + avg_confidence * 1.8
        composition = 7.0 + avg_confidence * 2.0
        interpretation = 7.1 + avg_confidence * 1.9

        # 5. حساب الدرجات
        status_text.text("🎯 حساب الدرجة النهائية...")
        progress_bar.progress(90)
        time.sleep(0.5)

        scoring_engine = ScoringEngine()

        # تحويل العناصر المكتشفة إلى صيغة محرك التسجيل
        elements_for_scoring = [
            {'code': e['code'], 'goe': e['goe']}
            for e in detected_elements
            if e['type'] in ['jump', 'spin', 'step_sequence']
        ]

        program_score = scoring_engine.calculate_total_score(
            elements=elements_for_scoring,
            skating_skills=skating_skills,
            transitions=transitions,
            performance=performance,
            composition=composition,
            interpretation=interpretation,
            program_type='short' if "قصير" in program_type else 'free'
        )

        # 6. حفظ في قاعدة البيانات
        status_text.text("💾 حفظ النتائج...")
        progress_bar.progress(95)

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
                    analysis_type=analysis_mode + " (AI)",
                    overall_score=program_score.total_score,
                    confidence=avg_confidence,
                    status='completed',
                    analysis_metadata={
                        'ai_mode': True,
                        'detected_elements': len(detected_elements),
                        'avg_confidence': float(avg_confidence)
                    }
                )
                session.add(analysis)

                # تحديث إحصائيات اللاعب
                skater = session.query(Skater).filter_by(id=skater_id).first()
                if skater:
                    skater.total_videos = (skater.total_videos or 0) + 1
                    skater.total_analyses = (skater.total_analyses or 0) + 1

        except Exception as db_error:
            st.warning(f"⚠️ لم يتم حفظ النتائج في قاعدة البيانات: {db_error}")

        # 7. عرض النتائج
        progress_bar.progress(100)
        status_text.text("✅ اكتمل التحليل الذكي!")
        time.sleep(0.5)

        st.success("🎉 تم التحليل بنجاح باستخدام الذكاء الاصطناعي!")

        # معلومات التحليل
        with st.expander("🤖 معلومات التحليل الذكي", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("عناصر مكتشفة", len(detected_elements))
            with col2:
                st.metric("متوسط الثقة", f"{avg_confidence:.1%}")
            with col3:
                st.metric("وضع التحليل", "AI")

            # تفاصيل الحركات المكتشفة
            st.markdown("**🔍 الحركات المكتشفة:**")
            movements_data = []
            for idx, elem in enumerate(detected_elements, 1):
                movements_data.append({
                    '#': idx,
                    'النوع': elem['type'],
                    'الكود': elem['code'],
                    'الثقة': f"{elem['confidence']:.1%}",
                    'GOE المقدر': f"{elem['goe']:+d}"
                })

            df_movements = pd.DataFrame(movements_data)
            st.dataframe(df_movements, use_container_width=True, hide_index=True)

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
        st.subheader("🎯 تفاصيل العناصر المسجلة")

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

        # توصيات الذكاء الاصطناعي
        st.markdown("---")
        st.subheader("🤖 توصيات الذكاء الاصطناعي")

        recommendations = generate_ai_recommendations(detected_elements, program_score, avg_confidence)
        st.info(recommendations)

        # زر التصدير
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("📥 تصدير التقرير الكامل", use_container_width=True):
                st.info("🚧 ميزة التصدير قيد التطوير...")

    except Exception as e:
        st.error(f"❌ خطأ في التحليل الذكي: {e}")
        import traceback
        with st.expander("🔍 تفاصيل الخطأ"):
            st.code(traceback.format_exc())


def generate_realistic_demo_elements(program_type):
    """توليد عناصر نموذجية واقعية للعرض التجريبي"""

    # عناصر واقعية حسب نوع البرنامج
    if "قصير" in program_type:
        # برنامج قصير - 6 عناصر نموذجية
        elements = [
            {'code': '3A', 'type': 'jump', 'confidence': 0.88, 'goe': 2, 'name': 'Triple Axel'},
            {'code': '3Lz+3T', 'type': 'jump', 'confidence': 0.85, 'goe': 1, 'name': 'Triple Lutz + Triple Toe'},
            {'code': '3F', 'type': 'jump', 'confidence': 0.82, 'goe': 1, 'name': 'Triple Flip'},
            {'code': 'FCSp4', 'type': 'spin', 'confidence': 0.90, 'goe': 2, 'name': 'Flying Camel Spin Level 4'},
            {'code': 'StSq4', 'type': 'step_sequence', 'confidence': 0.87, 'goe': 2, 'name': 'Step Sequence Level 4'},
            {'code': 'CCoSp4', 'type': 'spin', 'confidence': 0.92, 'goe': 3, 'name': 'Change Combination Spin Level 4'}
        ]
    else:
        # برنامج حر - 11 عنصر نموذجي
        elements = [
            {'code': '4T', 'type': 'jump', 'confidence': 0.80, 'goe': 0, 'name': 'Quad Toe Loop'},
            {'code': '3A', 'type': 'jump', 'confidence': 0.89, 'goe': 2, 'name': 'Triple Axel'},
            {'code': '3Lz', 'type': 'jump', 'confidence': 0.84, 'goe': 1, 'name': 'Triple Lutz'},
            {'code': '3F+3T', 'type': 'jump', 'confidence': 0.86, 'goe': 2, 'name': 'Triple Flip + Triple Toe'},
            {'code': '3Lo', 'type': 'jump', 'confidence': 0.81, 'goe': 0, 'name': 'Triple Loop'},
            {'code': '2A', 'type': 'jump', 'confidence': 0.91, 'goe': 1, 'name': 'Double Axel'},
            {'code': 'FCSp4', 'type': 'spin', 'confidence': 0.90, 'goe': 2, 'name': 'Flying Camel Spin Level 4'},
            {'code': 'StSq4', 'type': 'step_sequence', 'confidence': 0.88, 'goe': 3, 'name': 'Step Sequence Level 4'},
            {'code': 'ChSq1', 'type': 'step_sequence', 'confidence': 0.85, 'goe': 2, 'name': 'Choreographic Sequence'},
            {'code': 'FCCoSp4', 'type': 'spin', 'confidence': 0.91, 'goe': 2, 'name': 'Flying Change Combination Spin Level 4'},
            {'code': 'CCoSp4', 'type': 'spin', 'confidence': 0.93, 'goe': 3, 'name': 'Change Combination Spin Level 4'}
        ]

    return elements


def generate_ai_recommendations(detected_elements, program_score, confidence):
    """توليد توصيات بناءً على التحليل الذكي"""

    recommendations = []

    # تحليل الثقة
    if confidence < 0.6:
        recommendations.append("⚠️ **جودة الفيديو:** الثقة منخفضة - يُنصح بتصوير فيديو بجودة أعلى للحصول على نتائج أدق")
    elif confidence > 0.85:
        recommendations.append("✅ **جودة ممتازة:** الفيديو واضح والتحليل دقيق")

    # تحليل الدرجة
    if program_score.total_score >= 150:
        recommendations.append("🌟 **أداء استثنائي:** مستوى عالمي - استمر في هذا المستوى!")
    elif program_score.total_score >= 120:
        recommendations.append("👍 **أداء قوي:** التركيز على تحسين GOE سيرفع الدرجة بشكل ملحوظ")
    else:
        recommendations.append("💪 **فرص للتطوير:** العمل على استقرار العناصر وجودة التنفيذ")

    # تحليل العناصر
    jump_elements = [e for e in detected_elements if e['type'] == 'jump']
    spin_elements = [e for e in detected_elements if e['type'] == 'spin']

    if jump_elements:
        avg_jump_goe = np.mean([e['goe'] for e in jump_elements])
        if avg_jump_goe < 0:
            recommendations.append("🦘 **القفزات:** يُنصح بالتدريب على استقرار الهبوط لتحسين GOE")
        elif avg_jump_goe > 1:
            recommendations.append("🦘 **القفزات ممتازة:** جودة تنفيذ عالية!")

    if spin_elements:
        avg_spin_goe = np.mean([e['goe'] for e in spin_elements])
        if avg_spin_goe < 0:
            recommendations.append("🌀 **الدورانات:** التركيز على السرعة وثبات المحور")
        elif avg_spin_goe > 1:
            recommendations.append("🌀 **دورانات ممتازة:** سرعة وثبات رائعين!")

    return "\n".join(recommendations) if recommendations else "✨ أداء جيد - استمر في التدريب!"


def display_player_info(player):
    """عرض معلومات اللاعب"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(f"**الدولة:** {player.country or 'مصر'}")
        st.write(f"**التخصص:** {player.discipline or 'Singles'}")
        if player.level:
            st.write(f"**المستوى:** {player.level}")

    with col2:
        st.write(f"**المدرب:** {player.coach_name or 'غير محدد'}")
        st.write(f"**النادي:** {player.club or 'غير محدد'}")
        if player.bundle:
            st.write(f"**الباقة:** {player.bundle}")

    with col3:
        st.write(f"**عدد الفيديوهات:** {player.total_videos or 0}")
        st.write(f"**عدد التحليلات:** {player.total_analyses or 0}")
        if player.membership_status:
            status_emoji = "✅" if player.membership_status == "active" else "⏸️"
            st.write(f"**الحالة:** {status_emoji} {player.membership_status}")


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

        # بحث وفلترة متقدمة
        st.markdown("### 🔍 البحث والفلترة")
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            search_query = st.text_input("🔍 البحث عن لاعب", placeholder="ادخل اسم اللاعب...", key="search_player")
        with col2:
            filter_level = st.selectbox("المستوى", ["الكل", "Alpha", "Beta", "Gamma", "Delta", "Epsilon"], key="filter_level")
        with col3:
            filter_bundle = st.selectbox("الباقة", ["الكل", "On-Ice Bronze", "On-Ice Silver", "On-Ice Gold", "Off-Ice Bronze", "Off-Ice Silver"], key="filter_bundle")
        with col4:
            sort_by = st.selectbox("الترتيب", ["الاسم", "الأحدث"], key="sort_player")

        try:
            with db_manager.get_session() as session:
                # استعلام اللاعبين (غير المدربين)
                query = session.query(Skater).filter(
                    ~Skater.notes.like('%مدرب%')
                )

                # تطبيق البحث
                if search_query:
                    query = query.filter(Skater.name.like(f'%{search_query}%'))

                # تطبيق فلتر المستوى
                if filter_level != "الكل":
                    query = query.filter(Skater.level == filter_level)

                # تطبيق فلتر الباقة
                if filter_bundle != "الكل":
                    query = query.filter(Skater.bundle.like(f'%{filter_bundle}%'))

                # الترتيب
                if sort_by == "الاسم":
                    players = query.order_by(Skater.name).all()
                else:
                    players = query.order_by(Skater.created_at.desc()).all()

                if players:
                    st.info(f"📊 عدد اللاعبين: {len(players)}")

                    # عرض اللاعبين في جدول
                    for idx, player in enumerate(players, 1):
                        with st.expander(f"{idx}. {player.name} - {player.country or 'مصر'}"):
                            # عرض الصورة إذا كانت موجودة
                            if player.photo_path:
                                import os
                                if os.path.exists(player.photo_path):
                                    col_photo, col_data = st.columns([1, 3])
                                    with col_photo:
                                        st.image(player.photo_path, width=150, caption=player.name)
                                    with col_data:
                                        display_player_info(player)
                                else:
                                    display_player_info(player)
                            else:
                                display_player_info(player)

                            if player.notes:
                                st.caption(f"📝 {player.notes}")

                            # أزرار التعديل والحذف
                            st.markdown("---")
                            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

                            with col_btn1:
                                if st.button("✏️ تعديل", key=f"edit_player_{player.id}", use_container_width=True):
                                    st.session_state[f'editing_player_{player.id}'] = True
                                    st.rerun()

                            with col_btn2:
                                if st.button("🗑️ حذف", key=f"delete_player_{player.id}", use_container_width=True, type="secondary"):
                                    st.session_state[f'confirm_delete_{player.id}'] = True
                                    st.rerun()

                            # نموذج التعديل
                            if st.session_state.get(f'editing_player_{player.id}', False):
                                st.markdown("### ✏️ تعديل البيانات")
                                with st.form(f"edit_form_{player.id}"):
                                    col_e1, col_e2 = st.columns(2)
                                    with col_e1:
                                        new_name = st.text_input("الاسم", value=player.name)
                                        new_country = st.text_input("الدولة", value=player.country or "مصر")
                                        new_level = st.selectbox("المستوى", ["", "Pre-Alpha", "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Freestyle 1", "Freestyle 2", "Freestyle 3", "Freestyle 4"], index=0 if not player.level else (["", "Pre-Alpha", "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Freestyle 1", "Freestyle 2", "Freestyle 3", "Freestyle 4"].index(player.level) if player.level in ["", "Pre-Alpha", "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Freestyle 1", "Freestyle 2", "Freestyle 3", "Freestyle 4"] else 0))

                                    with col_e2:
                                        new_coach = st.text_input("المدرب", value=player.coach_name or "")
                                        new_club = st.text_input("النادي", value=player.club or "")
                                        new_bundle = st.selectbox("الباقة", ["", "On-Ice Bronze", "On-Ice Silver", "On-Ice Gold", "Per Session"], index=0 if not player.bundle else (["", "On-Ice Bronze", "On-Ice Silver", "On-Ice Gold", "Per Session"].index(player.bundle) if player.bundle in ["", "On-Ice Bronze", "On-Ice Silver", "On-Ice Gold", "Per Session"] else 0))

                                    col_submit, col_cancel = st.columns(2)
                                    with col_submit:
                                        if st.form_submit_button("💾 حفظ التعديلات", use_container_width=True, type="primary"):
                                            try:
                                                with db_manager.get_session() as edit_session:
                                                    player_to_edit = edit_session.query(Skater).filter_by(id=player.id).first()
                                                    if player_to_edit:
                                                        player_to_edit.name = new_name
                                                        player_to_edit.country = new_country
                                                        player_to_edit.coach_name = new_coach if new_coach else None
                                                        player_to_edit.club = new_club if new_club else None
                                                        player_to_edit.level = new_level if new_level else None
                                                        player_to_edit.bundle = new_bundle if new_bundle else None

                                                st.success(f"✅ تم تحديث بيانات {new_name}")
                                                del st.session_state[f'editing_player_{player.id}']
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ خطأ: {e}")

                                    with col_cancel:
                                        if st.form_submit_button("❌ إلغاء", use_container_width=True):
                                            del st.session_state[f'editing_player_{player.id}']
                                            st.rerun()

                            # تأكيد الحذف
                            if st.session_state.get(f'confirm_delete_{player.id}', False):
                                st.warning(f"⚠️ هل أنت متأكد من حذف **{player.name}**؟")
                                col_yes, col_no = st.columns(2)

                                with col_yes:
                                    if st.button("✅ نعم، احذف", key=f"confirm_yes_{player.id}", use_container_width=True, type="primary"):
                                        try:
                                            with db_manager.get_session() as del_session:
                                                player_to_delete = del_session.query(Skater).filter_by(id=player.id).first()
                                                if player_to_delete:
                                                    del_session.delete(player_to_delete)

                                            st.success(f"✅ تم حذف {player.name}")
                                            del st.session_state[f'confirm_delete_{player.id}']
                                            time.sleep(0.5)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ خطأ: {e}")

                                with col_no:
                                    if st.button("❌ لا، إلغاء", key=f"confirm_no_{player.id}", use_container_width=True):
                                        del st.session_state[f'confirm_delete_{player.id}']
                                        st.rerun()
                else:
                    st.warning("⚠️ لا يوجد لاعبون حالياً")

        except Exception as e:
            st.error(f"❌ خطأ في تحميل اللاعبين: {e}")

    # تبويب المدربين
    with tab2:
        st.subheader("🎓 قائمة المدربين")

        # بحث المدربين
        st.markdown("### 🔍 البحث")
        col1, col2 = st.columns([4, 1])
        with col1:
            search_coach = st.text_input("🔍 البحث عن مدرب", placeholder="ادخل اسم المدرب...", key="search_coach")
        with col2:
            sort_coach = st.selectbox("الترتيب", ["الاسم", "الأحدث"], key="sort_coach")

        try:
            with db_manager.get_session() as session:
                # استعلام المدربين
                query = session.query(Skater).filter(
                    Skater.notes.like('%مدرب%')
                )

                # تطبيق البحث
                if search_coach:
                    query = query.filter(Skater.name.like(f'%{search_coach}%'))

                # الترتيب
                if sort_coach == "الاسم":
                    coaches = query.order_by(Skater.name).all()
                else:
                    coaches = query.order_by(Skater.created_at.desc()).all()

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

        # قسم رفع الصورة (خارج النموذج)
        st.markdown("### 📸 الصورة الشخصية")
        uploaded_photo = st.file_uploader(
            "اختر صورة العضو",
            type=['jpg', 'jpeg', 'png', 'webp'],
            help="الصيغ المدعومة: JPG, PNG, WEBP",
            key="member_photo_uploader"
        )

        if uploaded_photo:
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image(uploaded_photo, caption="معاينة الصورة", use_column_width=True)

        st.markdown("---")
        st.markdown("### 📋 البيانات الأساسية")

        with st.form("add_skater_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("الاسم الكامل*")
                country = st.text_input("الدولة", value="مصر")
                gender = st.selectbox("الجنس", ["أنثى", "ذكر"])
                category = st.selectbox("الفئة", ["Junior", "Senior"])
                level = st.selectbox("المستوى", ["", "Beta", "Gamma", "Delta", "Epsilon"])

            with col2:
                discipline = st.selectbox("التخصص", ["Singles", "Pairs", "Ice Dance", "Coach"])
                coach_name = st.text_input("اسم المدرب")
                club = st.text_input("النادي")
                bundle = st.selectbox("الباقة", [
                    "",
                    "On-Ice Bronze",
                    "On-Ice Silver",
                    "On-Ice Gold",
                    "Off-Ice Basic",
                    "Off-Ice Advanced"
                ])
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

                            # حفظ الصورة إذا تم رفعها
                            photo_path = None
                            if uploaded_photo is not None:
                                import os
                                from pathlib import Path

                                # إنشاء مجلد الصور
                                photos_dir = Path("uploads/photos")
                                photos_dir.mkdir(parents=True, exist_ok=True)

                                # حفظ الصورة
                                photo_filename = f"{name.replace(' ', '_')}_{int(time.time())}.{uploaded_photo.name.split('.')[-1]}"
                                photo_path = photos_dir / photo_filename

                                with open(photo_path, "wb") as f:
                                    f.write(uploaded_photo.getbuffer())

                                photo_path = str(photo_path)

                            skater = Skater(
                                name=name,
                                country=country,
                                gender=gender,
                                category=category,
                                discipline="Coach" if is_coach else discipline,
                                coach_name=coach_name,
                                club=club,
                                level=level if level else None,
                                bundle=bundle if bundle else None,
                                photo_path=photo_path,
                                notes=final_notes,
                                total_videos=0,
                                total_analyses=0
                            )
                            session.add(skater)

                        st.success(f"✅ تمت إضافة {'المدرب' if is_coach else 'اللاعب'}: {name}")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ خطأ في الإضافة: {e}")
                    import traceback
                    with st.expander("🔍 تفاصيل الخطأ"):
                        st.code(traceback.format_exc())

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
