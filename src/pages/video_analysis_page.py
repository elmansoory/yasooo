"""
🎥 صفحة تحليل الفيديو بالذكاء الاصطناعي
AI Video Analysis Page - Error Detection & Correction
"""

import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import time
from pathlib import Path
from typing import List, Dict, Optional

import plotly.express as px
import plotly.graph_objects as go

# Check available libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

try:
    from src.analysis.error_detector import (
        PoseErrorAnalyzer, generate_correction_report,
        ErrorSeverity, SkatingError
    )
    ERROR_DETECTOR_AVAILABLE = True
except ImportError:
    ERROR_DETECTOR_AVAILABLE = False

try:
    from src.ai.advanced_analyzer import AdvancedSkatingAnalyzer
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False


# ============================================================================
# DEMO DATA — يعمل بدون MediaPipe للعرض التجريبي
# ============================================================================

def generate_demo_analysis(lang: str = 'ar') -> Dict:
    """بيانات تجريبية واقعية تُظهر إمكانيات النظام"""
    is_ar = lang == 'ar'
    return {
        'video_info': {
            'fps': 30.0,
            'frame_count': 900,
            'width': 1920,
            'height': 1080,
            'duration': 30.0,
        },
        'jumps': [
            {
                'type': 'Triple Lutz' if not is_ar else 'ثلاثي لوتز',
                'rotations': 3.0,
                'height_cm': 52,
                'airtime': 0.68,
                'rpm': 264,
                'goe': 2,
                'base_value': 5.90,
                'final_score': 6.80,
                'is_clean': True,
                'frame_start': 90,
                'frame_end': 110,
            },
            {
                'type': 'Double Axel' if not is_ar else 'مزدوج أكسل',
                'rotations': 2.5,
                'height_cm': 48,
                'airtime': 0.52,
                'rpm': 288,
                'goe': 1,
                'base_value': 3.30,
                'final_score': 3.80,
                'is_clean': True,
                'frame_start': 240,
                'frame_end': 255,
            },
            {
                'type': 'Triple Flip' if not is_ar else 'ثلاثي فليب',
                'rotations': 2.75,
                'height_cm': 38,
                'airtime': 0.65,
                'rpm': 253,
                'goe': -1,
                'base_value': 5.30,
                'final_score': 4.50,
                'is_clean': False,
                'frame_start': 420,
                'frame_end': 439,
            },
        ],
        'spins': [
            {
                'type': 'Camel Spin' if not is_ar else 'دوران الجمل',
                'rotations': 6,
                'rpm': 72,
                'duration': 5.0,
                'level': 3,
                'goe': 1,
                'base_value': 2.30,
                'final_score': 2.70,
                'frame_start': 330,
                'frame_end': 480,
            },
        ],
        'errors': [
            {
                'category': 'دوران' if is_ar else 'Rotation',
                'severity': 'عالي' if is_ar else 'HIGH',
                'title_ar': 'دوران ناقص في ثلاثي فليب',
                'title_en': 'Under-Rotation on Triple Flip',
                'description_ar': 'اكتمل 2.75 دورة من 3 مطلوبة. العجز: 0.25',
                'description_en': 'Completed 2.75 of 3 required rotations. Deficit: 0.25',
                'corrections_ar': [
                    'ضم الذراعين بشكل أسرع وأكثر إحكاماً نحو الجسم',
                    'زيادة قوة الإقلاع عن طريق دفع أقوى للحافة',
                    'تمارين الدوران في المكان على الجليد',
                ],
                'corrections_en': [
                    'Pull arms in faster and tighter toward the body',
                    'Increase takeoff power with a stronger edge push',
                    'Practice in-place spins on ice',
                ],
                'frame_start': 420,
                'frame_end': 439,
                'goe_impact': -1,
            },
            {
                'category': 'وضعية الجسم' if is_ar else 'Posture',
                'severity': 'متوسط' if is_ar else 'MEDIUM',
                'title_ar': 'انحناء طفيف للأمام',
                'title_en': 'Slight Forward Lean',
                'description_ar': 'ميل الجسم للأمام بشكل ملحوظ في الأجزاء الحرة',
                'description_en': 'Noticeable forward body lean during free skating portions',
                'corrections_ar': [
                    'تقوية عضلات الظهر السفلية',
                    'الوعي الجسدي: تخيّل خيط يسحب رأسك للأعلى',
                    'مراجعة الفيديو مع المدرب',
                ],
                'corrections_en': [
                    'Strengthen lower back muscles',
                    'Body awareness: imagine a string pulling your head upward',
                    'Review video with coach to correct posture',
                ],
                'frame_start': 0,
                'frame_end': 900,
                'goe_impact': 0,
            },
        ],
        'report': {
            'total_errors': 2,
            'overall_assessment': 'جيد - يحتاج تحسين بسيط' if is_ar else 'Good - Needs Minor Improvement',
            'score_impact': -1,
            'priority_corrections': [
                'ضم الذراعين بشكل أسرع نحو الجسم' if is_ar else 'Pull arms in faster toward the body',
                'زيادة قوة الإقلاع' if is_ar else 'Increase takeoff power',
                'تقوية عضلات الظهر' if is_ar else 'Strengthen back muscles',
            ],
        },
        'total_score': 17.80,
        'tes': 17.80,
        'is_demo': True,
    }


# ============================================================================
# REAL VIDEO ANALYSIS
# ============================================================================

def analyze_video_file(video_path: str, lang: str = 'ar') -> Dict:
    """تحليل فيديو حقيقي باستخدام MediaPipe"""
    results = {
        'video_info': {},
        'jumps': [],
        'spins': [],
        'errors': [],
        'report': {},
        'total_score': 0.0,
        'is_demo': False,
    }

    try:
        # Get video info
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()

        results['video_info'] = {
            'fps': fps, 'frame_count': frame_count,
            'width': width, 'height': height, 'duration': duration,
        }
    except Exception as e:
        results['video_info'] = {'error': str(e)}

    # Extract poses with MediaPipe
    poses = []
    if MEDIAPIPE_AVAILABLE and CV2_AVAILABLE:
        poses = _extract_poses_mediapipe(video_path, fps)

    # Run analyzer
    if ANALYZER_AVAILABLE:
        try:
            analyzer = AdvancedSkatingAnalyzer()
            ai_results = analyzer.analyze_video(video_path)
            jumps = ai_results.get('jumps', [])
            spins = ai_results.get('spins', [])
            results['total_score'] = ai_results.get('total_score', 0.0)

            results['jumps'] = [
                {
                    'type': j.jump_type.value,
                    'rotations': j.rotations,
                    'height_cm': j.height_cm,
                    'airtime': j.airtime_seconds,
                    'rpm': j.rotation_speed_rpm,
                    'goe': j.goe,
                    'base_value': j.base_value,
                    'final_score': j.final_score,
                    'is_clean': j.has_clean_landing,
                    'frame_start': j.start_frame,
                    'frame_end': j.end_frame,
                }
                for j in jumps
            ]
            results['spins'] = [
                {
                    'type': s.spin_type.value,
                    'rotations': s.rotations,
                    'rpm': s.rpm,
                    'duration': s.duration_seconds,
                    'level': s.level,
                    'goe': s.goe,
                    'base_value': s.base_value,
                    'final_score': s.final_score,
                    'frame_start': s.start_frame,
                    'frame_end': s.end_frame,
                }
                for s in spins
            ]
        except Exception:
            pass

    # Detect errors from poses
    if ERROR_DETECTOR_AVAILABLE and poses:
        try:
            analyzer_err = PoseErrorAnalyzer()
            errors = analyzer_err.analyze_poses(poses, fps)
            report = generate_correction_report(errors, lang)
            results['errors'] = [e.to_dict() for e in errors]
            results['report'] = report
        except Exception:
            pass

    return results


def _extract_poses_mediapipe(video_path: str, fps: float) -> List[Dict]:
    """استخراج الوضعيات بـ MediaPipe مع progress bar"""
    poses = []
    mp_pose = mp.solutions.pose

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose_model:
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = 0
        progress = st.progress(0, text="جارٍ تحليل الفيديو...")
        SKIP = 2  # process every 2nd frame for speed

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % SKIP == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose_model.process(rgb)
                if res.pose_landmarks:
                    kp = [
                        {
                            'x': lm.x, 'y': lm.y, 'z': lm.z,
                            'visibility': lm.visibility, 'index': i
                        }
                        for i, lm in enumerate(res.pose_landmarks.landmark)
                    ]
                    la = kp[27] if len(kp) > 27 else None
                    ra = kp[28] if len(kp) > 28 else None
                    is_air = (la and ra and (la['y'] + ra['y']) / 2 < 0.75)
                    poses.append({
                        'frame': frame_idx,
                        'timestamp': frame_idx / fps,
                        'keypoints': kp,
                        'is_airborne': is_air,
                    })
                if total > 0:
                    progress.progress(
                        min(frame_idx / total, 1.0),
                        text=f"تحليل الإطار {frame_idx} من {total}..."
                    )
            frame_idx += 1

        cap.release()
        progress.empty()

    return poses


# ============================================================================
# UI HELPERS
# ============================================================================

SEVERITY_COLOR = {
    'CRITICAL': '#dc2626', 'حرج': '#dc2626',
    'HIGH': '#ea580c',     'عالي': '#ea580c',
    'MEDIUM': '#d97706',   'متوسط': '#d97706',
    'LOW': '#65a30d',      'منخفض': '#65a30d',
}
SEVERITY_ICON = {
    'CRITICAL': '🔴', 'حرج': '🔴',
    'HIGH': '🟠',     'عالي': '🟠',
    'MEDIUM': '🟡',   'متوسط': '🟡',
    'LOW': '🟢',      'منخفض': '🟢',
}


def render_error_card(err: Dict, lang: str):
    sev = err.get('severity', 'LOW')
    color = SEVERITY_COLOR.get(sev, '#64748b')
    icon = SEVERITY_ICON.get(sev, '⚪')
    title = err.get('title_ar' if lang == 'ar' else 'title_en', '')
    desc = err.get('description_ar' if lang == 'ar' else 'description_en', '')
    corrections = err.get('corrections_ar' if lang == 'ar' else 'corrections_en', [])
    goe_impact = err.get('goe_impact', 0)
    cat = err.get('category', '')

    goe_text = f"GOE: {goe_impact:+d}" if goe_impact != 0 else ""

    with st.container():
        st.markdown(f"""
        <div style="border-left:5px solid {color};background:#fafafa;
                    border-radius:8px;padding:14px 18px;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="font-size:1.2em">{icon}</span>
                <span style="font-weight:700;color:{color};font-size:1em">{title}</span>
                <span style="margin-right:auto;font-size:0.75em;color:#94a3b8">{cat} {goe_text}</span>
            </div>
            <div style="color:#475569;font-size:0.88em;margin-bottom:8px">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

        if corrections:
            lbl = "التصحيحات المقترحة:" if lang == 'ar' else "Suggested Corrections:"
            with st.expander(lbl):
                for i, c in enumerate(corrections, 1):
                    st.markdown(f"**{i}.** {c}")


def render_jump_card(jump: Dict, lang: str, idx: int):
    is_clean = jump.get('is_clean', True)
    goe = jump.get('goe', 0)
    goe_color = '#16a34a' if goe > 0 else ('#dc2626' if goe < 0 else '#64748b')
    clean_icon = '✅' if is_clean else '⚠️'

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.markdown(f"**{idx}. {jump.get('type', '')}** {clean_icon}")
    with col2:
        st.metric("🔁" if lang == 'ar' else "Rot.", f"{jump.get('rotations', 0):.1f}")
    with col3:
        st.metric("📏 cm", f"{jump.get('height_cm', 0):.0f}")
    with col4:
        goe_val = jump.get('goe', 0)
        st.markdown(f"<div style='color:{goe_color};font-weight:700;font-size:1.1em;padding-top:8px'>GOE: {goe_val:+d}</div>", unsafe_allow_html=True)
    with col5:
        st.metric("Score", f"{jump.get('final_score', 0):.2f}")


# ============================================================================
# MAIN PAGE FUNCTION
# ============================================================================

def show_video_analysis_page(lang: str = 'ar'):
    is_ar = lang == 'ar'

    st.markdown(
        f'<h1>{"🎥 تحليل الفيديو بالذكاء الاصطناعي" if is_ar else "🎥 AI Video Analysis"}</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<p style="text-align:center;color:#64748b;font-size:1.1em">'
        f'{"كشف الأخطاء التقنية وتقديم التصحيحات الفورية" if is_ar else "Detect technical errors and provide instant corrections"}'
        f'</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Library status banner
    if not MEDIAPIPE_AVAILABLE or not CV2_AVAILABLE:
        st.warning(
            "⚠️ MediaPipe / OpenCV غير مثبّتة — النظام يعمل بوضع العرض التجريبي" if is_ar
            else "⚠️ MediaPipe / OpenCV not installed — running in demo mode"
        )
        with st.expander("📦 تثبيت المكتبات" if is_ar else "📦 Install Libraries"):
            st.code("pip install mediapipe opencv-python numpy")

    # Tabs
    tab_labels = (
        ["📹 رفع فيديو", "📊 النتائج", "🛠️ الأخطاء والتصحيحات", "📈 الإحصائيات"]
        if is_ar else
        ["📹 Upload Video", "📊 Results", "🛠️ Errors & Corrections", "📈 Statistics"]
    )
    tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

    with tab1:
        _tab_upload(is_ar, lang)

    with tab2:
        _tab_results(is_ar, lang)

    with tab3:
        _tab_errors(is_ar, lang)

    with tab4:
        _tab_stats(is_ar, lang)


def _tab_upload(is_ar: bool, lang: str):
    st.subheader("📹 " + ("رفع فيديو للتحليل" if is_ar else "Upload Video for Analysis"))

    # Instructions
    st.info(
        "**📋 كيفية الاستخدام:**\n"
        "1. ارفع فيديو التزلج (MP4 / AVI / MOV)\n"
        "2. اضغط 'بدء التحليل'\n"
        "3. انتظر اكتمال التحليل (30 ثانية - 3 دقائق حسب طول الفيديو)\n"
        "4. راجع النتائج والتصحيحات في التبويبات"
        if is_ar else
        "**📋 How to use:**\n"
        "1. Upload a skating video (MP4 / AVI / MOV)\n"
        "2. Press 'Start Analysis'\n"
        "3. Wait for analysis to complete (30 sec – 3 min depending on video length)\n"
        "4. Review results and corrections in the tabs"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded = st.file_uploader(
            "اختر ملف الفيديو" if is_ar else "Choose video file",
            type=['mp4', 'avi', 'mov', 'mkv'],
            key='video_upload'
        )
    with col2:
        demo_btn = st.button(
            "🎭 عرض تجريبي" if is_ar else "🎭 Demo Mode",
            use_container_width=True,
            help="شاهد النظام بدون رفع فيديو" if is_ar else "See the system without uploading a video"
        )

    if demo_btn:
        with st.spinner("جارٍ تحميل البيانات التجريبية..." if is_ar else "Loading demo data..."):
            time.sleep(1)
            st.session_state['analysis_results'] = generate_demo_analysis(lang)
        st.success("✅ " + ("تم تحميل العرض التجريبي — راجع التبويبات الأخرى" if is_ar else "Demo loaded — check the other tabs"))

    if uploaded is not None:
        st.video(uploaded)
        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            player_name = st.text_input(
                "اسم اللاعب (اختياري)" if is_ar else "Player Name (optional)"
            )
        with col_b:
            session_note = st.text_input(
                "ملاحظة الجلسة" if is_ar else "Session Note"
            )

        if st.button(
            "🚀 بدء التحليل" if is_ar else "🚀 Start Analysis",
            type="primary", use_container_width=True
        ):
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded.name).suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            try:
                with st.spinner("جارٍ تحليل الفيديو... قد يستغرق بضع دقائق" if is_ar else "Analyzing video... may take a few minutes"):
                    if MEDIAPIPE_AVAILABLE and CV2_AVAILABLE:
                        results = analyze_video_file(tmp_path, lang)
                    else:
                        time.sleep(2)
                        results = generate_demo_analysis(lang)
                        results['is_demo'] = False

                results['player_name'] = player_name
                results['session_note'] = session_note
                st.session_state['analysis_results'] = results
                st.success("✅ " + ("اكتمل التحليل! راجع التبويبات الأخرى" if is_ar else "Analysis complete! Check other tabs"))
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass


def _tab_results(is_ar: bool, lang: str):
    st.subheader("📊 " + ("نتائج التحليل" if is_ar else "Analysis Results"))

    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً" if is_ar else "Upload a video or use Demo Mode first")
        return

    if results.get('is_demo'):
        st.caption("🎭 " + ("عرض تجريبي — ليست بيانات حقيقية" if is_ar else "Demo data — not real analysis"))

    vi = results.get('video_info', {})
    if vi and 'duration' in vi:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⏱️ " + ("المدة" if is_ar else "Duration"), f"{vi['duration']:.1f}s")
        with col2:
            st.metric("🎬 FPS", f"{vi.get('fps', 0):.0f}")
        with col3:
            st.metric("📐 " + ("الدقة" if is_ar else "Resolution"), f"{vi.get('width', 0)}x{vi.get('height', 0)}")
        with col4:
            st.metric("🏆 " + ("النتيجة الكلية" if is_ar else "Total Score"), f"{results.get('total_score', 0):.2f}")

    st.markdown("---")

    # Jumps
    jumps = results.get('jumps', [])
    if jumps:
        st.subheader("🦘 " + ("القفزات" if is_ar else "Jumps"))
        for i, j in enumerate(jumps, 1):
            render_jump_card(j, lang, i)
        st.markdown("---")

    # Spins
    spins = results.get('spins', [])
    if spins:
        st.subheader("🌀 " + ("الدورانات" if is_ar else "Spins"))
        for sp in spins:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"**{sp.get('type', '')}**")
            with c2:
                st.metric("🔁", f"{sp.get('rotations', 0)}")
            with c3:
                st.metric("⚡ RPM", f"{sp.get('rpm', 0):.0f}")
            with c4:
                st.metric("Score", f"{sp.get('final_score', 0):.2f}")


def _tab_errors(is_ar: bool, lang: str):
    st.subheader("🛠️ " + ("الأخطاء والتصحيحات" if is_ar else "Errors & Corrections"))

    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً" if is_ar else "Upload a video or use Demo Mode first")
        return

    errors = results.get('errors', [])
    report = results.get('report', {})

    # Summary banner
    total = report.get('total_errors', len(errors))
    assessment = report.get('overall_assessment', '')
    score_impact = report.get('score_impact', 0)

    assessment_color = (
        '#16a34a' if total == 0 else
        '#d97706' if total <= 3 else
        '#dc2626'
    )

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#667eea22,#764ba222);
                border-radius:12px;padding:20px;margin-bottom:20px;
                border:1px solid #667eea44">
        <div style="font-size:1.3em;font-weight:700;color:{assessment_color}">{assessment}</div>
        <div style="color:#64748b;margin-top:6px">
            {'إجمالي الأخطاء' if is_ar else 'Total Errors'}: <b>{total}</b>
            {'  |  تأثير على النقاط' if is_ar else '  |  Score Impact'}: <b style="color:#dc2626">{score_impact:+d} GOE</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not errors:
        st.success("🎉 " + ("لم يتم اكتشاف أخطاء تقنية!" if is_ar else "No technical errors detected!"))
        return

    # Priority corrections box
    priority = report.get('priority_corrections', [])
    if priority:
        with st.expander("⭐ " + ("أولويات التصحيح" if is_ar else "Priority Corrections"), expanded=True):
            for i, c in enumerate(priority, 1):
                st.markdown(f"**{i}.** {c}")

    st.markdown("---")

    # Filter by severity
    all_label = "الكل" if is_ar else "All"
    sev_options = [all_label] + (['حرج', 'عالي', 'متوسط', 'منخفض'] if is_ar else ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
    chosen_sev = st.selectbox(
        "فلتر حسب الخطورة" if is_ar else "Filter by severity",
        sev_options, label_visibility='collapsed'
    )

    filtered_errors = errors if chosen_sev == all_label else [
        e for e in errors if e.get('severity') == chosen_sev
    ]

    for err in filtered_errors:
        render_error_card(err, lang)


def _tab_stats(is_ar: bool, lang: str):
    st.subheader("📈 " + ("الإحصائيات التحليلية" if is_ar else "Analytical Statistics"))

    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً" if is_ar else "Upload a video or use Demo Mode first")
        return

    jumps = results.get('jumps', [])
    errors = results.get('errors', [])

    col1, col2 = st.columns(2)

    with col1:
        # Jump scores bar chart
        if jumps:
            labels = [j.get('type', '') for j in jumps]
            scores = [j.get('final_score', 0) for j in jumps]
            colors = ['#16a34a' if j.get('is_clean', True) else '#dc2626' for j in jumps]

            fig = go.Figure(go.Bar(
                x=labels, y=scores,
                marker_color=colors,
                text=[f"{s:.2f}" for s in scores],
                textposition='outside',
            ))
            fig.update_layout(
                title="🦘 " + ("درجات القفزات" if is_ar else "Jump Scores"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Error severity donut
        if errors:
            sev_count = {}
            for e in errors:
                sev = e.get('severity', 'LOW')
                sev_count[sev] = sev_count.get(sev, 0) + 1

            colors_sev = [SEVERITY_COLOR.get(s, '#64748b') for s in sev_count.keys()]
            fig = go.Figure(go.Pie(
                labels=list(sev_count.keys()),
                values=list(sev_count.values()),
                hole=0.55,
                marker_colors=colors_sev,
            ))
            fig.update_layout(
                title="🛠️ " + ("توزيع الأخطاء" if is_ar else "Error Distribution"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=40, b=0),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

    # GOE breakdown
    if jumps:
        st.subheader("🏅 " + ("تحليل GOE لكل قفزة" if is_ar else "GOE Breakdown per Jump"))
        goe_data = pd.DataFrame({
            'Jump': [j.get('type', '') for j in jumps],
            'Base Value': [j.get('base_value', 0) for j in jumps],
            'GOE': [j.get('goe', 0) for j in jumps],
            'Final Score': [j.get('final_score', 0) for j in jumps],
            'Height (cm)': [j.get('height_cm', 0) for j in jumps],
            'RPM': [round(j.get('rpm', 0)) for j in jumps],
        })
        st.dataframe(goe_data, use_container_width=True, hide_index=True)

    # Radar chart — strengths vs weaknesses
    if jumps:
        avg_goe = sum(j.get('goe', 0) for j in jumps) / len(jumps)
        avg_height = sum(j.get('height_cm', 0) for j in jumps) / len(jumps)
        avg_rpm = sum(j.get('rpm', 0) for j in jumps) / len(jumps)
        clean_ratio = sum(1 for j in jumps if j.get('is_clean', True)) / len(jumps)
        error_ratio = max(0, 1 - len(errors) / 10)

        categories = (
            ['GOE', 'الارتفاع', 'السرعة', 'الهبوط النظيف', 'الدقة الفنية']
            if is_ar else
            ['GOE', 'Height', 'Speed', 'Clean Landing', 'Technical Accuracy']
        )
        values = [
            min(10, max(0, (avg_goe + 5))),
            min(10, avg_height / 8),
            min(10, avg_rpm / 30),
            clean_ratio * 10,
            error_ratio * 10,
        ]
        values_norm = [round(v, 1) for v in values]

        fig = go.Figure(go.Scatterpolar(
            r=values_norm + [values_norm[0]],
            theta=categories + [categories[0]],
            fill='toself',
            fillcolor='rgba(102,126,234,0.25)',
            line=dict(color='#667eea', width=2),
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            title="🕸️ " + ("ملف الأداء" if is_ar else "Performance Profile"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=380,
            margin=dict(l=40, r=40, t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)
