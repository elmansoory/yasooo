"""
Referee/Coach Testing Interface
واجهة اختبار للمدربين والحكام
"""
import streamlit as st
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Check for required dependencies
DEPENDENCIES_OK = True
MISSING_DEPS = []

try:
    import mediapipe as mp
except ImportError:
    DEPENDENCIES_OK = False
    MISSING_DEPS.append("mediapipe>=0.10.8")

try:
    import tensorflow as tf
except ImportError:
    DEPENDENCIES_OK = False
    MISSING_DEPS.append("tensorflow>=2.14.0")

try:
    import torch
except ImportError:
    DEPENDENCIES_OK = False
    MISSING_DEPS.append("torch>=2.1.0")

# Try importing advanced modules
AdvancedPoseDetector = None
JumpDetector = None
DatasetManager = None
ElementAnnotation = None
ElementClassifierTrainer = None

if DEPENDENCIES_OK:
    try:
        from src.core.advanced_pose_detector import AdvancedPoseDetector
        from src.analysis.jump_detector import JumpDetector
        from src.utils.dataset_manager import DatasetManager, ElementAnnotation
        from src.models.element_classifier_trainer import ElementClassifierTrainer
    except ImportError as e:
        DEPENDENCIES_OK = False
        MISSING_DEPS.append(f"Module import error: {str(e)}")


def show_referee_testing_interface():
    """
    واجهة الاختبار للحكام والمدربين
    """
    st.title("🏅 واجهة اختبار الحكام والمدربين")
    st.markdown("### اختبر دقة النظام الآلي مقارنة بتقييمك البشري")

    # Check dependencies
    if not DEPENDENCIES_OK:
        st.error("⚠️ بعض المكتبات المطلوبة غير مثبتة")
        st.warning("This feature requires MediaPipe and other advanced dependencies.")

        st.markdown("---")
        st.subheader("📦 المكتبات المفقودة:")

        for dep in MISSING_DEPS:
            st.code(dep)

        st.markdown("---")
        st.subheader("🔧 طريقة التثبيت:")

        install_cmd = "pip install " + " ".join([d.split(">=")[0] if ">=" in d else d for d in MISSING_DEPS if not d.startswith("Module")])

        st.code(install_cmd, language="bash")

        st.info("""
        **خطوات التثبيت:**

        1. افتح Terminal أو Command Prompt
        2. انسخ والصق الأمر أعلاه
        3. اضغط Enter وانتظر التثبيت
        4. أعد تشغيل التطبيق

        **أو يمكنك تثبيت جميع المكتبات المطلوبة:**
        ```bash
        pip install -r requirements.txt
        ```
        """)

        st.markdown("---")
        st.info("💡 بعد تثبيت المكتبات، أعد تحميل الصفحة.")

        return

    st.markdown("---")

    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ الإعدادات")

        mode = st.radio(
            "اختر الوضع",
            ["🎥 تحليل فيديو جديد", "📊 مراجعة نتائج سابقة", "📝 تعليق يدوي"]
        )

        st.markdown("---")

        if mode == "🎥 تحليل فيديو جديد":
            st.subheader("خيارات التحليل")

            enable_pose = st.checkbox("Pose Detection", value=True)
            enable_jumps = st.checkbox("Jump Detection", value=True)
            enable_ml = st.checkbox("ML Classification", value=False)

    # Main content
    if mode == "🎥 تحليل فيديو جديد":
        show_video_analysis_mode(enable_pose, enable_jumps, enable_ml)

    elif mode == "📊 مراجعة نتائج سابقة":
        show_results_review_mode()

    else:  # تعليق يدوي
        show_manual_annotation_mode()


def show_video_analysis_mode(enable_pose: bool, enable_jumps: bool, enable_ml: bool):
    """وضع تحليل الفيديو"""
    st.header("🎥 تحليل فيديو جديد")

    # File uploader
    uploaded_file = st.file_uploader(
        "ارفع فيديو البرنامج",
        type=['mp4', 'avi', 'mov'],
        help="ارفع فيديو برنامج تزلج كامل"
    )

    if uploaded_file is not None:
        # Save uploaded file
        video_path = f"temp/{uploaded_file.name}"
        Path("temp").mkdir(exist_ok=True)

        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"✅ تم رفع الفيديو: {uploaded_file.name}")

        # Video info
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("المدة", f"{duration:.1f}s")
        with col2:
            st.metric("الإطارات", total_frames)
        with col3:
            st.metric("FPS", f"{fps:.1f}")
        with col4:
            st.metric("الدقة", f"{width}x{height}")

        st.markdown("---")

        # Analysis button
        if st.button("🚀 ابدأ التحليل", type="primary"):
            with st.spinner("جاري التحليل..."):
                results = analyze_video(
                    video_path,
                    enable_pose,
                    enable_jumps,
                    enable_ml
                )

                if results:
                    display_analysis_results(results)

        # Manual scoring section
        st.markdown("---")
        st.subheader("✍️ التقييم اليدوي (للمقارنة)")

        with st.form("manual_scoring"):
            st.markdown("**أدخل تقييمك كحكم:**")

            col1, col2 = st.columns(2)

            with col1:
                manual_tech_score = st.number_input(
                    "Technical Score",
                    min_value=0.0,
                    max_value=200.0,
                    value=50.0,
                    step=0.01
                )

                manual_components = st.number_input(
                    "Components Score",
                    min_value=0.0,
                    max_value=100.0,
                    value=40.0,
                    step=0.01
                )

            with col2:
                manual_deductions = st.number_input(
                    "Deductions",
                    min_value=0.0,
                    max_value=20.0,
                    value=0.0,
                    step=0.5
                )

                manual_total = manual_tech_score + manual_components - manual_deductions

                st.metric("Total Score", f"{manual_total:.2f}")

            submitted = st.form_submit_button("💾 حفظ التقييم اليدوي")

            if submitted:
                st.success("✅ تم حفظ التقييم اليدوي")


def analyze_video(
    video_path: str,
    enable_pose: bool,
    enable_jumps: bool,
    enable_ml: bool
) -> dict:
    """
    Analyze video with enabled components

    Returns:
        Analysis results dictionary
    """
    results = {}

    try:
        # Pose detection
        if enable_pose:
            st.info("🔍 جاري تحليل الوضعيات...")
            pose_detector = AdvancedPoseDetector(
                model_complexity=2,
                min_detection_confidence=0.7
            )

            pose_frames = pose_detector.process_video(
                video_path,
                save_visualization=True,
                output_path=f"temp/annotated_{Path(video_path).name}"
            )

            pose_detector.close()

            results['pose_frames'] = pose_frames
            st.success(f"✅ تم تحليل {len(pose_frames)} إطار")

        # Jump detection
        if enable_jumps and 'pose_frames' in results:
            st.info("🦘 جاري كشف القفزات...")

            jump_detector = JumpDetector(fps=30)
            jumps = jump_detector.detect_jumps(results['pose_frames'])

            results['jumps'] = jumps
            st.success(f"✅ تم كشف {len(jumps)} قفزة")

        # ML classification
        if enable_ml:
            st.info("🤖 جاري التصنيف بالذكاء الاصطناعي...")

            try:
                classifier = ElementClassifierTrainer()
                classifier.load_model("models/element_classifier")

                # Classify each jump
                if 'jumps' in results:
                    for jump in results['jumps']:
                        features = {
                            'duration': jump.duration,
                            'frame_count': jump.end_frame - jump.start_frame,
                            'is_jump': 1,
                            'is_spin': 0,
                            'is_step': 0,
                            'rotations': jump.rotations,
                            'level': 0,
                            'base_value': 0,  # unknown
                            'goe': 0
                        }

                        predicted, confidence = classifier.predict(features)
                        jump.ml_prediction = predicted
                        jump.ml_confidence = confidence

                st.success("✅ تم التصنيف بالذكاء الاصطناعي")

            except Exception as e:
                st.warning(f"⚠️ ML classification failed: {e}")

        return results

    except Exception as e:
        st.error(f"❌ خطأ في التحليل: {e}")
        return None


def display_analysis_results(results: dict):
    """Display analysis results"""
    st.markdown("---")
    st.header("📊 نتائج التحليل")

    # Pose detection results
    if 'pose_frames' in results:
        st.subheader("1️⃣ Pose Detection")

        airborne_frames = [f for f in results['pose_frames'] if f.is_airborne]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("إجمالي الإطارات", len(results['pose_frames']))

        with col2:
            st.metric("إطارات في الهواء", len(airborne_frames))

        with col3:
            airborne_pct = len(airborne_frames) / len(results['pose_frames']) * 100
            st.metric("نسبة الطيران", f"{airborne_pct:.1f}%")

        # Show annotated video
        annotated_video_path = f"temp/annotated_{Path(results.get('video_path', 'video.mp4')).name}"

        if Path(annotated_video_path).exists():
            st.video(annotated_video_path)

    # Jump detection results
    if 'jumps' in results:
        st.markdown("---")
        st.subheader("2️⃣ Jump Detection Results")

        jumps = results['jumps']

        if len(jumps) == 0:
            st.info("لم يتم كشف أي قفزات")
        else:
            st.success(f"✅ تم كشف {len(jumps)} قفزة")

            # Table
            jumps_data = []
            for i, jump in enumerate(jumps, 1):
                jumps_data.append({
                    '#': i,
                    'ISU Code': jump.get_isu_code(),
                    'Type': jump.jump_type.value,
                    'Rotations': f"{jump.rotations:.2f}",
                    'Height (cm)': f"{jump.height_cm:.1f}",
                    'Airtime (s)': f"{jump.airtime:.2f}",
                    'RPM': f"{jump.rotation_speed:.0f}",
                    'GOE Est.': f"{jump.estimated_goe:+d}",
                    'Clean': '✅' if jump.is_clean else '❌',
                    'ML Pred': getattr(jump, 'ml_prediction', '—'),
                    'ML Conf': f"{getattr(jump, 'ml_confidence', 0):.0%}"
                })

            df_jumps = pd.DataFrame(jumps_data)
            st.dataframe(df_jumps, width='stretch')

            # Detailed view
            st.markdown("---")
            st.subheader("تفاصيل القفزات")

            selected_jump = st.selectbox(
                "اختر قفزة للتفاصيل",
                range(len(jumps)),
                format_func=lambda i: f"Jump {i+1}: {jumps[i].get_isu_code()}"
            )

            if selected_jump is not None:
                jump = jumps[selected_jump]

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("**📊 القياسات:**")
                    st.write(f"- الارتفاع: {jump.height_cm:.1f} cm")
                    st.write(f"- المسافة: {jump.distance_m:.2f} m")
                    st.write(f"- وقت الطيران: {jump.airtime:.2f}s")
                    st.write(f"- السرعة الدورانية: {jump.rotation_speed:.0f} RPM")
                    st.write(f"- ثبات المحور: {jump.axis_stability:.0%}")

                    st.markdown("**🎯 التقييم:**")
                    st.write(f"- GOE المقدر: {jump.estimated_goe:+d}")
                    st.write(f"- هبوط نظيف: {'✅ نعم' if jump.is_clean else '❌ لا'}")

                with col2:
                    if jump.goe_positive_factors:
                        st.markdown("**✅ عوامل إيجابية:**")
                        for factor in jump.goe_positive_factors:
                            st.write(f"- {factor}")

                    if jump.goe_negative_factors:
                        st.markdown("**❌ عوامل سلبية:**")
                        for factor in jump.goe_negative_factors:
                            st.write(f"- {factor}")

                    if jump.errors:
                        st.markdown("**⚠️ أخطاء:**")
                        for error in jump.errors:
                            st.error(error)

                # Comparison with manual scoring
                st.markdown("---")
                st.subheader("مقارنة التقييم")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("تقييم النظام", f"{jump.estimated_goe:+d}")

                with col2:
                    manual_goe = st.number_input(
                        "تقييمك (GOE)",
                        min_value=-5,
                        max_value=5,
                        value=0,
                        key=f"manual_goe_{selected_jump}"
                    )

                with col3:
                    difference = abs(jump.estimated_goe - manual_goe)
                    st.metric("الفرق", f"{difference}")

                    if difference == 0:
                        st.success("✅ تطابق كامل!")
                    elif difference <= 1:
                        st.info("ℹ️ فرق بسيط")
                    else:
                        st.warning("⚠️ فرق كبير")


def show_results_review_mode():
    """وضع مراجعة النتائج السابقة"""
    st.header("📊 مراجعة نتائج سابقة")

    # Load dataset
    dm = DatasetManager("data/skating_dataset")

    video_ids = list(dm.index['videos'].keys())

    if len(video_ids) == 0:
        st.info("لا توجد فيديوهات مُحللة بعد")
        return

    # Select video
    selected_video = st.selectbox(
        "اختر فيديو",
        video_ids,
        format_func=lambda vid: f"{vid} - {dm.index['videos'][vid].get('status', 'unknown')}"
    )

    if selected_video:
        annotation = dm.get_annotation(selected_video)

        if annotation:
            st.subheader(f"📹 {annotation.skater_name}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**المسابقة:** {annotation.competition}")
                st.write(f"**نوع البرنامج:** {annotation.program_type}")

            with col2:
                st.write(f"**المدة:** {annotation.duration:.1f}s")
                st.write(f"**العناصر:** {len(annotation.elements)}")

            with col3:
                st.write(f"**النقاط:** {annotation.total_score:.2f}")
                st.write(f"**الحالة:** {annotation.status}")

            # Elements table
            if annotation.elements:
                st.markdown("---")
                st.subheader("📋 العناصر")

                elements_data = []
                for elem in annotation.elements:
                    elements_data.append({
                        'ISU Code': elem.isu_code,
                        'Type': elem.element_type,
                        'Base Value': elem.base_value,
                        'GOE': f"{elem.goe:+d}",
                        'Total': elem.total_score,
                        'Verified': '✅' if elem.verified else '⏳'
                    })

                df_elements = pd.DataFrame(elements_data)
                st.dataframe(df_elements, width='stretch')


def show_manual_annotation_mode():
    """وضع التعليق اليدوي"""
    st.header("📝 تعليق يدوي")

    st.info("💡 استخدم هذا الوضع لإضافة تعليقات يدوية دقيقة لتدريب النموذج")

    # Load dataset
    dm = DatasetManager("data/skating_dataset")

    # Upload new video
    with st.expander("➕ إضافة فيديو جديد"):
        uploaded_file = st.file_uploader("ارفع فيديو", type=['mp4', 'avi', 'mov'])

        if uploaded_file:
            if st.button("إضافة للمجموعة"):
                video_path = f"temp/{uploaded_file.name}"
                Path("temp").mkdir(exist_ok=True)

                with open(video_path, "wb") as f:
                    f.write(uploaded_file.read())

                video_id = dm.add_video(video_path, copy_video=True)

                st.success(f"✅ تم إضافة الفيديو: {video_id}")

    # Select video to annotate
    video_ids = list(dm.index['videos'].keys())

    if len(video_ids) > 0:
        selected_video = st.selectbox("اختر فيديو للتعليق", video_ids)

        if selected_video:
            annotation = dm.get_annotation(selected_video)

            st.subheader(f"🎥 {selected_video}")

            # Add element annotation
            with st.form("add_element"):
                st.markdown("**إضافة عنصر جديد:**")

                col1, col2, col3 = st.columns(3)

                with col1:
                    element_type = st.selectbox(
                        "نوع العنصر",
                        ["jump", "spin", "step_sequence", "spiral"]
                    )

                    isu_code = st.text_input("ISU Code", value="3A")

                with col2:
                    start_frame = st.number_input("Start Frame", min_value=0, value=0)
                    end_frame = st.number_input("End Frame", min_value=0, value=100)

                with col3:
                    base_value = st.number_input("Base Value", min_value=0.0, value=8.0, step=0.1)
                    goe = st.number_input("GOE", min_value=-5, max_value=5, value=0)

                submitted = st.form_submit_button("➕ إضافة العنصر")

                if submitted:
                    from src.utils.dataset_manager import AnnotationTool

                    tool = AnnotationTool(dm)
                    tool.load_video(selected_video)

                    tool.annotate_element(
                        element_type=element_type,
                        isu_code=isu_code,
                        start_frame=start_frame,
                        end_frame=end_frame,
                        base_value=base_value,
                        goe=goe,
                        annotator_name=st.session_state.get('annotator_name', 'Manual')
                    )

                    st.success(f"✅ تم إضافة {isu_code}")
                    st.rerun()

            # Show current annotations
            if annotation and annotation.elements:
                st.markdown("---")
                st.subheader("📋 العناصر المُعلّقة")

                for i, elem in enumerate(annotation.elements):
                    with st.expander(f"{elem.isu_code} ({elem.start_frame}-{elem.end_frame})"):
                        st.write(f"Type: {elem.element_type}")
                        st.write(f"Base Value: {elem.base_value}")
                        st.write(f"GOE: {elem.goe:+d}")
                        st.write(f"Total: {elem.total_score:.2f}")


if __name__ == "__main__":
    show_referee_testing_interface()
