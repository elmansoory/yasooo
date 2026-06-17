"""
🎥 Professional Video Analysis Interface
واجهة التحليل الاحترافي للفيديو

يوفر تحليل متقدم للفيديوهات باستخدام الذكاء الاصطناعي:
- كشف القفزات وتصنيفها
- تحليل الدورانات
- تقييم GOE تلقائي
- تقارير مفصلة
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os
from typing import Optional

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import new analyzer (replaces old AdvancedSkatingAnalyzer)
try:
    from src.pages.video_analysis_page import SkatingVideoAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False


def show_professional_video_analysis():
    """
    واجهة التحليل الاحترافي
    """
    st.markdown('<h1>🎥 التحليل الاحترافي بالذكاء الاصطناعي</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2em; color: #64748b; text-align: center;">تحليل متقدم لفيديوهات التزلج باستخدام تقنيات الذكاء الاصطناعي</p>', unsafe_allow_html=True)

    st.markdown("---")

    # Check if analyzer is available
    if not ANALYZER_AVAILABLE:
        st.error("⚠️ محرك التحليل غير متاح")
        st.info("تأكد من تثبيت المكتبات المطلوبة: mediapipe, tensorflow, torch, opencv-python")
        return

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📹 تحليل جديد",
        "📊 النتائج",
        "📈 الإحصائيات",
        "⚙️ الإعدادات"
    ])

    with tab1:
        show_analysis_tab()

    with tab2:
        show_results_tab()

    with tab3:
        show_statistics_tab()

    with tab4:
        show_settings_tab()


def show_analysis_tab():
    """تبويب التحليل الجديد"""
    st.subheader("📹 تحليل فيديو جديد")

    st.info("""
    **📋 كيفية الاستخدام:**
    1. ارفع فيديو برنامج التزلج (MP4, AVI, MOV)
    2. اختر خيارات التحليل
    3. اضغط 'بدء التحليل'
    4. راجع النتائج المفصلة

    **⏱️ ملاحظة:** التحليل قد يستغرق عدة دقائق حسب طول الفيديو
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "📁 ارفع فيديو البرنامج",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="ارفع فيديو برنامج تزلج كامل للتحليل الاحترافي"
    )

    if uploaded_file is not None:
        st.success(f"✅ تم رفع الفيديو: **{uploaded_file.name}**")

        # Analysis options
        st.markdown("### ⚙️ خيارات التحليل")

        col1, col2, col3 = st.columns(3)

        with col1:
            enable_pose = st.checkbox("✅ كشف الوضعيات (Pose Detection)", value=True,
                                    help="تتبع 33 نقطة رئيسية في الجسم")

        with col2:
            enable_jumps = st.checkbox("✅ كشف وتصنيف القفزات", value=True,
                                      help="تحديد نوع القفزة والدورانات والارتفاع")

        with col3:
            enable_spins = st.checkbox("✅ تحليل الدورانات", value=True,
                                      help="تحليل أنواع الدورانات والسرعة")

        col1, col2 = st.columns(2)

        with col1:
            enable_goe = st.checkbox("✅ تقييم GOE تلقائي", value=True,
                                    help="تقييم جودة التنفيذ حسب معايير ISU")

        with col2:
            enable_report = st.checkbox("✅ إنشاء تقرير مفصل", value=True,
                                       help="تقرير شامل بجميع التفاصيل")

        col1, col2 = st.columns(2)
        with col1:
            program_type = st.selectbox(
                "🎯 نوع البرنامج", ['short', 'free'],
                format_func=lambda x: '🎯 برنامج قصير (Short)' if x == 'short' else '🎭 برنامج حر (Free Skate)'
            )
        with col2:
            skater_level = st.selectbox(
                "📊 مستوى اللاعب", ['novice', 'junior', 'senior'], index=2,
                format_func=lambda x: {'novice': 'مبتدئ (Novice)', 'junior': 'جونيور (Junior)',
                                        'senior': 'سينيور (Senior)'}[x]
            )

        st.markdown("---")

        # Advanced settings
        with st.expander("⚙️ إعدادات متقدمة"):
            col1, col2 = st.columns(2)

            with col1:
                confidence_threshold = st.slider(
                    "عتبة الثقة",
                    0.0, 1.0, 0.7,
                    help="الحد الأدنى للثقة في الكشف"
                )

            with col2:
                frame_skip = st.number_input(
                    "تخطي الإطارات",
                    1, 10, 1,
                    help="تخطي N إطار لتسريع المعالجة"
                )

        # Start analysis button
        if st.button("🚀 بدء التحليل الاحترافي", type="primary", use_container_width=True):
            analyze_video(
                uploaded_file,
                enable_pose,
                enable_jumps,
                enable_spins,
                enable_goe,
                enable_report,
                confidence_threshold,
                frame_skip,
                program_type,
                skater_level
            )
    else:
        st.info("👆 **ارفع فيديو للبدء في التحليل الاحترافي**")

        # Show example
        with st.expander("💡 مثال على النتائج المتوقعة"):
            show_example_results()


def analyze_video(uploaded_file, enable_pose, enable_jumps, enable_spins,
                 enable_goe, enable_report, confidence, frame_skip,
                 program_type='free', skater_level='senior'):
    """تحليل الفيديو — uses new SkatingVideoAnalyzer (dict API)"""

    # Save uploaded file
    video_path = f"temp/{uploaded_file.name}"
    Path("temp").mkdir(exist_ok=True)

    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())

    st.info(f"📁 تم حفظ الفيديو في: {video_path}")

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("🔍 جاري تحليل الفيديو...")
        progress_bar.progress(20)

        analyzer = SkatingVideoAnalyzer()
        results = analyzer.analyze(video_path, program_type=program_type, skater_level=skater_level)

        progress_bar.progress(100)
        status_text.text("✅ اكتمل التحليل!")

        if 'error' in results:
            st.error(results['error'])
            return

        jumps = results.get('jumps', [])
        spins = results.get('spins', [])
        video_info = results.get('video_info', {})
        total_score = results.get('total_score', 0)
        tes = results.get('tes', 0)
        pcs = results.get('pcs', 0)

        st.success(f"✅ معلومات الفيديو: {video_info.get('duration', 0):.1f}s, {video_info.get('fps', 0):.1f} FPS")
        st.success(f"✅ تم كشف {len(jumps)} قفزة و {len(spins)} دوران")

        st.balloons()

        # Display results
        st.markdown("---")
        st.markdown("## 📊 نتائج التحليل")

        display_analysis_results(jumps, spins, {
            'total_score': total_score, 'tes': tes, 'pcs': pcs
        })

        # Save to session state
        st.session_state['last_analysis'] = {
            'video_name': uploaded_file.name,
            'jumps': jumps,
            'spins': spins,
            'summary': {'total_score': total_score, 'tes': tes, 'pcs': pcs},
            'video_info': video_info
        }

    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء التحليل: {e}")
        st.exception(e)


def display_analysis_results(jumps, spins, summary):
    """عرض نتائج التحليل — dict-based API"""

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    total_score = summary.get('total_score', 0) or sum(j.get('final_score', 0) for j in jumps)
    avg_goe = sum(j.get('goe', 0) for j in jumps) / len(jumps) if jumps else 0

    with col1:
        st.metric("🦘 القفزات", len(jumps))
    with col2:
        st.metric("🌀 الدورانات", len(spins))
    with col3:
        st.metric("🏆 النقاط الكلية", f"{total_score:.2f}")
    with col4:
        st.metric("📊 متوسط GOE", f"{avg_goe:+.1f}")

    st.markdown("---")

    # Jump details
    if jumps:
        st.subheader("🦘 تفاصيل القفزات")

        jumps_data = []
        for i, jump in enumerate(jumps, 1):
            jumps_data.append({
                '#': i,
                'النوع': jump.get('type', ''),
                'الدورانات': f"{jump.get('rotations', 0):.1f}",
                'الارتفاع (cm)': f"{jump.get('height_cm', 0):.1f}",
                'Base Value': f"{jump.get('base_value', 0):.2f}",
                'GOE': f"{jump.get('goe', 0):+d}",
                'النقاط': f"{jump.get('final_score', 0):.2f}",
                'نظيف': '✅' if jump.get('is_clean', True) else '⚠️'
            })

        df = pd.DataFrame(jumps_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Jump breakdown chart
        st.markdown("### 📊 توزيع القفزات")

        col1, col2 = st.columns(2)

        with col1:
            type_counts = {}
            for jump in jumps:
                key = jump.get('type', 'Unknown')
                type_counts[key] = type_counts.get(key, 0) + 1

            fig = px.pie(
                values=list(type_counts.values()),
                names=list(type_counts.keys()),
                title='توزيع أنواع القفزات'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            scores = [j.get('final_score', 0) for j in jumps]
            fig = px.bar(
                x=[f"Jump {i+1}" for i in range(len(jumps))],
                y=scores,
                title='النقاط لكل قفزة',
                labels={'x': 'القفزة', 'y': 'النقاط'},
                color=scores,
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig, use_container_width=True)

    # Summary
    if summary:
        st.markdown("---")
        st.subheader("📈 الملخص والتوصيات")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ نقاط القوة")
            if summary.get('strengths'):
                for strength in summary['strengths']:
                    st.success(f"• {strength}")
            else:
                st.info("استمر في التدريب لتحديد نقاط القوة")

        with col2:
            st.markdown("### 🎯 مجالات التحسين")
            if summary.get('areas_for_improvement'):
                for area in summary['areas_for_improvement']:
                    st.warning(f"• {area}")
            else:
                st.success("أداء ممتاز! لا توجد مجالات رئيسية للتحسين")


def show_example_results():
    """عرض مثال على النتائج"""
    st.markdown("""
    **📊 مثال على نتائج التحليل:**

    بعد التحليل، ستحصل على:

    ### 1️⃣ تفاصيل القفزات
    - نوع كل قفزة (Axel, Lutz, Flip, etc.)
    - عدد الدورانات
    - ارتفاع القفزة
    - سرعة الدوران (RPM)
    - تقييم GOE
    - النقاط الكلية

    ### 2️⃣ تحليل الدورانات
    - نوع الدوران (Sit, Camel, Upright, etc.)
    - عدد الدورانات
    - السرعة
    - المستوى (Level)
    - النقاط

    ### 3️⃣ الملخص
    - نقاط القوة
    - مجالات التحسين
    - التوصيات
    - مقارنة مع المعايير

    ### 4️⃣ الإحصائيات
    - رسوم بيانية تفاعلية
    - مقارنات
    - اتجاهات الأداء
    """)


def show_results_tab():
    """تبويب النتائج السابقة"""
    st.subheader("📊 النتائج السابقة")

    if 'last_analysis' in st.session_state:
        analysis = st.session_state['last_analysis']

        st.info(f"📹 آخر تحليل: **{analysis['video_name']}**")

        display_analysis_results(
            analysis['jumps'],
            analysis['spins'],
            analysis['summary']
        )

        # Download report button
        if st.button("📥 تحميل التقرير (PDF)", use_container_width=True):
            st.info("🚧 ميزة تحميل PDF قيد التطوير")

    else:
        st.warning("⚠️ لا توجد نتائج سابقة")
        st.info("قم بتحليل فيديو أولاً من تبويب 'تحليل جديد'")


def show_statistics_tab():
    """تبويب الإحصائيات"""
    st.subheader("📈 الإحصائيات المتقدمة")

    if 'last_analysis' in st.session_state:
        analysis = st.session_state['last_analysis']
        jumps = analysis['jumps']

        if jumps:
            # Performance over time
            st.markdown("### 📊 الأداء عبر البرنامج")

            scores = [j.get('final_score', 0) for j in jumps]
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=list(range(1, len(scores) + 1)),
                y=scores,
                mode='lines+markers',
                name='النقاط',
                line=dict(color='#667eea', width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                title='تطور النقاط خلال البرنامج',
                xaxis_title='رقم القفزة',
                yaxis_title='النقاط',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Detailed metrics
            st.markdown("### 📏 المقاييس التفصيلية")

            col1, col2, col3 = st.columns(3)

            with col1:
                avg_height = sum(j.get('height_cm', 0) for j in jumps) / len(jumps)
                st.metric("متوسط الارتفاع", f"{avg_height:.1f} cm")

            with col2:
                avg_rpm = sum(j.get('rpm', 0) for j in jumps) / len(jumps)
                st.metric("متوسط RPM", f"{avg_rpm:.0f}")

            with col3:
                avg_airtime = sum(j.get('airtime', 0) for j in jumps) / len(jumps)
                st.metric("متوسط وقت الطيران", f"{avg_airtime:.2f} s")

        else:
            st.info("لا توجد قفزات لعرض الإحصائيات")

    else:
        st.warning("⚠️ لا توجد بيانات للإحصائيات")


def show_settings_tab():
    """تبويب الإعدادات"""
    st.subheader("⚙️ إعدادات التحليل")

    st.markdown("### 🎯 معايير التقييم")

    col1, col2 = st.columns(2)

    with col1:
        st.number_input("الحد الأدنى للارتفاع (cm)", 20, 100, 30)
        st.number_input("الحد الأدنى للدورانات", 0.5, 4.0, 1.0, 0.5)

    with col2:
        st.slider("عتبة الثقة في الكشف", 0.0, 1.0, 0.7)
        st.selectbox("نظام التقييم", ["ISU", "مخصص"])

    st.markdown("### 💾 إعدادات الحفظ")

    st.checkbox("حفظ الفيديو المُعَلَّم", value=False)
    st.checkbox("حفظ البيانات الخام", value=False)
    st.checkbox("إنشاء تقرير PDF تلقائياً", value=True)

    if st.button("💾 حفظ الإعدادات", use_container_width=True):
        st.success("✅ تم حفظ الإعدادات!")


# Main entry point
if __name__ == "__main__":
    show_professional_video_analysis()
