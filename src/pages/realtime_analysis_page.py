"""
📷 تحليل مباشر من الكاميرا
Real-Time Camera Analysis
"""

import io
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Optional heavy dependencies
# ---------------------------------------------------------------------------

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    _mp_pose = getattr(mp.solutions, "pose", None)
    _mp_drawing = getattr(mp.solutions, "drawing_utils", None)
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    _mp_pose = None
    _mp_drawing = None

try:
    from src.analysis.pose_comparator import PoseComparator, get_element_list, REFERENCE_POSES
    COMPARATOR_AVAILABLE = True
except ImportError:
    COMPARATOR_AVAILABLE = False
    PoseComparator = None  # type: ignore
    get_element_list = lambda: [  # noqa: E731
        "axel_takeoff", "axel_flight", "axel_landing",
        "camel_spin", "sit_spin", "spiral",
    ]
    REFERENCE_POSES = {}

# ---------------------------------------------------------------------------
# Skeleton connectivity
# ---------------------------------------------------------------------------

# MediaPipe landmark indices used for skeleton drawing
_LM = {
    "nose": 0,
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13,    "right_elbow": 14,
    "left_wrist": 15,    "right_wrist": 16,
    "left_hip": 23,      "right_hip": 24,
    "left_knee": 25,     "right_knee": 26,
    "left_ankle": 27,    "right_ankle": 28,
}

# Pairs of landmark indices to connect with lines
_SKELETON_CONNECTIONS: List[Tuple[int, int]] = [
    # Upper body
    (11, 12),  # shoulders
    (11, 13),  # left upper arm
    (13, 15),  # left forearm
    (12, 14),  # right upper arm
    (14, 16),  # right forearm
    # Neck / head
    (0, 11),   # nose -> left shoulder
    (0, 12),   # nose -> right shoulder
    # Torso
    (11, 23),  # left shoulder -> left hip
    (12, 24),  # right shoulder -> right hip
    (23, 24),  # hips
    # Lower body
    (23, 25),  # left hip -> left knee
    (25, 27),  # left knee -> left ankle
    (24, 26),  # right hip -> right knee
    (26, 28),  # right knee -> right ankle
]

# ---------------------------------------------------------------------------
# UI text strings
# ---------------------------------------------------------------------------

_T: Dict[str, Dict[str, str]] = {
    "title": {
        "ar": "📷 التحليل المباشر من الكاميرا",
        "en": "📷 Real-Time Camera Analysis",
    },
    "subtitle": {
        "ar": "التقط صورة وحلّل وضعيتك مقارنةً بالمحترفين",
        "en": "Capture a frame and analyze your pose against professional standards",
    },
    "select_element": {
        "ar": "اختر العنصر للمقارنة",
        "en": "Select Element to Compare",
    },
    "capture_btn": {
        "ar": "📸 التقاط وتحليل",
        "en": "📸 Capture & Analyze",
    },
    "no_pose": {
        "ar": "⚠️ لم يتم اكتشاف وضعية في هذه الصورة. تأكد أن جسمك كاملٌ في الإطار.",
        "en": "⚠️ No pose detected in this image. Make sure your full body is in frame.",
    },
    "overall_score": {
        "ar": "النتيجة الإجمالية",
        "en": "Overall Score",
    },
    "rating": {
        "ar": "التقييم",
        "en": "Rating",
    },
    "angle_details": {
        "ar": "تفاصيل الزوايا",
        "en": "Angle Details",
    },
    "joint": {
        "ar": "المفصل",
        "en": "Joint",
    },
    "ideal": {
        "ar": "المثالي",
        "en": "Ideal",
    },
    "actual": {
        "ar": "الفعلي",
        "en": "Actual",
    },
    "deviation": {
        "ar": "الانحراف",
        "en": "Deviation",
    },
    "corrections": {
        "ar": "التصحيحات المطلوبة",
        "en": "Required Corrections",
    },
    "no_corrections": {
        "ar": "✅ وضعية ممتازة! لا تصحيحات مطلوبة.",
        "en": "✅ Excellent pose! No corrections needed.",
    },
    "balance_score": {
        "ar": "درجة التوازن",
        "en": "Balance Score",
    },
    "alignment_score": {
        "ar": "درجة الاستقامة",
        "en": "Body Alignment Score",
    },
    "install_title": {
        "ar": "📦 مكتبات مطلوبة",
        "en": "📦 Required Libraries",
    },
    "install_msg": {
        "ar": "لتفعيل التحليل المباشر، يرجى تثبيت المكتبات التالية:",
        "en": "To enable real-time analysis, please install the following libraries:",
    },
    "live_metrics": {
        "ar": "المقاييس الآنية",
        "en": "Live Metrics",
    },
    "skeleton_overlay": {
        "ar": "صورة مع تراكب الهيكل العظمي",
        "en": "Frame with Skeleton Overlay",
    },
    "camera_prompt": {
        "ar": "التقط صورة باستخدام الكاميرا",
        "en": "Capture a photo using the camera",
    },
}


def _t(key: str, lang: str) -> str:
    return _T.get(key, {}).get(lang, _T.get(key, {}).get("en", key))


# ---------------------------------------------------------------------------
# Skeleton drawing helpers
# ---------------------------------------------------------------------------

def _lm_to_pixel(lm, w: int, h: int) -> Tuple[int, int]:
    """Convert a normalised MediaPipe landmark to pixel coordinates."""
    return int(lm.x * w), int(lm.y * h)


def _landmark_visibility(lm) -> float:
    return getattr(lm, "visibility", 1.0)


def draw_skeleton(image_bgr: np.ndarray, landmarks) -> np.ndarray:
    """Draw circles at landmarks and connecting lines on *image_bgr*.

    Color coding:
      - Green  (0, 220, 0)  : high-visibility landmark (>= 0.6)
      - Red    (0, 0, 220)  : low-visibility landmark   (< 0.6)
    Line colour: (0, 200, 200) cyan for good pairs, grey otherwise.
    """
    h, w = image_bgr.shape[:2]
    lm_list = landmarks.landmark

    # Draw connections first (behind dots)
    for idx_a, idx_b in _SKELETON_CONNECTIONS:
        if idx_a >= len(lm_list) or idx_b >= len(lm_list):
            continue
        vis_a = _landmark_visibility(lm_list[idx_a])
        vis_b = _landmark_visibility(lm_list[idx_b])
        if vis_a < 0.3 or vis_b < 0.3:
            continue
        pt_a = _lm_to_pixel(lm_list[idx_a], w, h)
        pt_b = _lm_to_pixel(lm_list[idx_b], w, h)
        color = (0, 200, 200) if (vis_a >= 0.6 and vis_b >= 0.6) else (130, 130, 130)
        cv2.line(image_bgr, pt_a, pt_b, color, 2, cv2.LINE_AA)

    # Draw landmark dots
    for idx in range(len(lm_list)):
        vis = _landmark_visibility(lm_list[idx])
        if vis < 0.3:
            continue
        pt = _lm_to_pixel(lm_list[idx], w, h)
        color = (0, 220, 0) if vis >= 0.6 else (0, 0, 220)
        cv2.circle(image_bgr, pt, 5, color, -1, cv2.LINE_AA)
        cv2.circle(image_bgr, pt, 5, (255, 255, 255), 1, cv2.LINE_AA)

    return image_bgr


# ---------------------------------------------------------------------------
# Pose processing helpers
# ---------------------------------------------------------------------------

def _landmarks_to_keypoints(landmarks) -> List[Dict]:
    """Convert MediaPipe landmark list to PoseComparator-compatible dicts."""
    kps = []
    for lm in landmarks.landmark:
        kps.append({
            "x": lm.x,
            "y": lm.y,
            "z": getattr(lm, "z", 0.0),
            "visibility": getattr(lm, "visibility", 1.0),
        })
    return kps


def _compute_balance_score(landmarks) -> float:
    """Simple balance heuristic: left/right hip symmetry (0-100)."""
    try:
        lm = landmarks.landmark
        lh = lm[23]
        rh = lm[24]
        la = lm[27]
        ra = lm[28]
        # Horizontal deviation from centre line
        centre_x = (lh.x + rh.x) / 2
        ankle_mid_x = (la.x + ra.x) / 2
        offset = abs(centre_x - ankle_mid_x)
        score = max(0.0, 100.0 - offset * 500)
        return round(score, 1)
    except Exception:
        return 0.0


def _compute_alignment_score(landmarks) -> float:
    """Vertical alignment of shoulders and hips (0-100)."""
    try:
        lm = landmarks.landmark
        ls = lm[11]
        rs = lm[12]
        lh = lm[23]
        rh = lm[24]
        sh_mid_x = (ls.x + rs.x) / 2
        hp_mid_x = (lh.x + rh.x) / 2
        offset = abs(sh_mid_x - hp_mid_x)
        score = max(0.0, 100.0 - offset * 400)
        return round(score, 1)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Score colour helpers
# ---------------------------------------------------------------------------

def _score_color(score: float) -> str:
    if score >= 75:
        return "green"
    if score >= 50:
        return "orange"
    return "red"


def _deviation_indicator(deviation: float) -> str:
    abs_dev = abs(deviation)
    if abs_dev <= 10:
        return "🟢"
    if abs_dev <= 20:
        return "🟡"
    return "🔴"


# ---------------------------------------------------------------------------
# Install instructions when libraries are missing
# ---------------------------------------------------------------------------

def _show_install_instructions(lang: str) -> None:
    st.warning(_t("install_title", lang))
    st.info(_t("install_msg", lang))
    missing = []
    if not CV2_AVAILABLE:
        missing.append("opencv-python")
    if not MEDIAPIPE_AVAILABLE:
        missing.append("mediapipe")
    if missing:
        st.code("pip install " + " ".join(missing), language="bash")


# ---------------------------------------------------------------------------
# Main page function
# ---------------------------------------------------------------------------

def show_realtime_analysis_page(lang: str = "ar") -> None:
    """Render the real-time camera analysis Streamlit page.

    Parameters
    ----------
    lang : str
        'ar' for Arabic, 'en' for English.
    """
    is_ar = lang == "ar"

    # Page title
    st.title(_t("title", lang))
    st.caption(_t("subtitle", lang))

    # Dependency check – cv2 is always required
    if not CV2_AVAILABLE:
        _show_install_instructions(lang)
        st.stop()
        return

    # -------------------------------------------------------------------------
    # Sidebar / controls
    # -------------------------------------------------------------------------
    element_options = get_element_list()
    element_labels = {e: e.replace("_", " ").title() for e in element_options}

    col_ctrl, col_main = st.columns([1, 2])

    with col_ctrl:
        st.subheader("⚙️" + ("  الإعدادات" if is_ar else "  Settings"))
        selected_element = st.selectbox(
            _t("select_element", lang),
            options=element_options,
            format_func=lambda e: element_labels[e],
        )

        show_skeleton = st.checkbox(
            "عرض الهيكل العظمي" if is_ar else "Show Skeleton Overlay",
            value=True,
        )

        st.markdown("---")
        st.caption(
            "📌 " + ("اضغط 'التقاط وتحليل' بعد التقاط الصورة" if is_ar
                     else "Press 'Capture & Analyze' after taking a photo")
        )

    # -------------------------------------------------------------------------
    # Camera input
    # -------------------------------------------------------------------------
    with col_main:
        camera_image = st.camera_input(
            _t("camera_prompt", lang),
            label_visibility="collapsed",
        )

        analyze_clicked = st.button(
            _t("capture_btn", lang),
            use_container_width=True,
            type="primary",
            disabled=(camera_image is None),
        )

    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------
    if camera_image is None:
        st.info(
            "📸 " + ("قم بالتقاط صورة للبدء في التحليل" if is_ar
                     else "Capture a photo to start analysis")
        )
        return

    # Decode image
    pil_image = Image.open(io.BytesIO(camera_image.getvalue())).convert("RGB")
    frame_rgb = np.array(pil_image)
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    # Run MediaPipe Pose (only when mp.solutions.pose is available)
    landmarks = None
    if _mp_pose is None:
        # MediaPipe is installed but mp.solutions.pose was removed in this version.
        display_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        st.subheader(_t("skeleton_overlay", lang))
        st.image(display_rgb, use_container_width=True)
        st.warning(
            "⚠️ تحليل الوضعية الكامل يتطلب MediaPipe مع دعم mp.solutions.pose. "
            "يرجى تثبيت إصدار متوافق (مثال: pip install mediapipe==0.10.14)."
            if lang == "ar" else
            "⚠️ Full pose analysis requires MediaPipe with mp.solutions.pose support. "
            "Please install a compatible version (e.g. pip install mediapipe==0.10.14)."
        )
        return
    else:
        with _mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
        ) as pose:
            results = pose.process(frame_rgb)

        landmarks = results.pose_landmarks if results else None

    # Draw skeleton overlay
    display_frame = frame_bgr.copy()
    if landmarks and show_skeleton:
        display_frame = draw_skeleton(display_frame, landmarks)

    display_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)

    # Show annotated image
    st.subheader(_t("skeleton_overlay", lang))
    st.image(display_rgb, use_container_width=True)

    if landmarks is None:
        st.warning(_t("no_pose", lang))
        return

    # -------------------------------------------------------------------------
    # Live metrics (always shown when pose is detected)
    # -------------------------------------------------------------------------
    balance = _compute_balance_score(landmarks)
    alignment = _compute_alignment_score(landmarks)

    st.subheader(_t("live_metrics", lang))
    m1, m2 = st.columns(2)
    m1.metric(_t("balance_score", lang), f"{balance:.0f} / 100")
    m2.metric(_t("alignment_score", lang), f"{alignment:.0f} / 100")

    # -------------------------------------------------------------------------
    # Full comparison (when button clicked)
    # -------------------------------------------------------------------------
    if not analyze_clicked:
        st.info(
            "🔎 " + (f"اضغط 'التقاط وتحليل' لمقارنة الوضعية مع {element_labels[selected_element]}"
                     if is_ar else
                     f"Press 'Capture & Analyze' to compare against {element_labels[selected_element]}")
        )
        return

    if not COMPARATOR_AVAILABLE:
        st.error(
            "مقارنة الوضعية غير متاحة حالياً (pose_comparator لم يُحمَّل)."
            if is_ar else
            "Pose comparison unavailable (pose_comparator failed to load)."
        )
        return

    keypoints = _landmarks_to_keypoints(landmarks)
    comparator = PoseComparator()
    result = comparator.compare_pose(keypoints, selected_element)

    overall_score: float = result.get("overall_score", 0.0)
    visual_rating: str = result.get("visual_rating", "")
    angle_deviations: List[Dict] = result.get("angle_deviations", [])
    corrections = result.get("corrections_ar" if is_ar else "corrections_en", [])

    # ---- Score banner -------------------------------------------------------
    score_color = _score_color(overall_score)
    st.markdown(
        f"""
        <div style="
            background-color: {score_color};
            padding: 16px 24px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 12px;
        ">
            <h2 style="color:white; margin:0;">
                {_t('overall_score', lang)}: {overall_score:.0f} / 100
            </h2>
            <p style="color:white; margin:4px 0 0;">
                {_t('rating', lang)}: {visual_rating}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Angle deviation table ----------------------------------------------
    if angle_deviations:
        st.subheader(_t("angle_details", lang))
        rows = []
        for dev in angle_deviations:
            indicator = _deviation_indicator(dev.get("deviation", 0))
            rows.append({
                _t("joint", lang): indicator + "  " + dev.get("joint", ""),
                _t("ideal", lang): f"{dev.get('ideal', 0):.0f}°",
                _t("actual", lang): f"{dev.get('actual', 0):.0f}°",
                _t("deviation", lang): f"{dev.get('deviation', 0):+.1f}°",
            })

        import pandas as pd
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ---- Corrections --------------------------------------------------------
    st.subheader(_t("corrections", lang))
    if corrections:
        for correction in corrections:
            st.markdown(f"• {correction}")
    else:
        st.success(_t("no_corrections", lang))

    # ---- Per-deviation feedback (expanded) ----------------------------------
    with st.expander(
        "عرض ملاحظات تفصيلية" if is_ar else "Show Detailed Feedback",
        expanded=False,
    ):
        for dev in angle_deviations:
            abs_dev = abs(dev.get("deviation", 0))
            indicator = _deviation_indicator(dev.get("deviation", 0))
            feedback = dev.get("feedback_ar" if is_ar else "feedback_en", "")
            joint = dev.get("joint", "")
            color = "green" if abs_dev <= 10 else ("orange" if abs_dev <= 20 else "red")
            st.markdown(
                f'{indicator} **{joint}** — '
                f'<span style="color:{color}">{feedback}</span>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Module entry point for direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    show_realtime_analysis_page(lang="ar")
