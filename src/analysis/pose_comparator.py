"""
مقارنة وضعية اللاعب مع المحترفين
Professional Pose Comparison Engine
"""

import math
from typing import List, Dict, Optional, Any


# ---------------------------------------------------------------------------
# Reference poses: ideal body angles for common figure skating elements
# ---------------------------------------------------------------------------
REFERENCE_POSES: Dict[str, Dict[str, float]] = {
    "axel_takeoff": {
        "knee_angle": 155.0,
        "hip_tilt": 10.0,
        "arm_extension": 170.0,
        "back_angle": 5.0,
    },
    "axel_flight": {
        "body_alignment": 95.0,
        "arm_tuck": 30.0,
        "head_position": 0.0,
    },
    "axel_landing": {
        "knee_bend": 140.0,
        "hip_position": 15.0,
        "free_leg_extension": 160.0,
    },
    "camel_spin": {
        "back_angle": 85.0,
        "free_leg_height": 90.0,
        "arm_position": 170.0,
    },
    "sit_spin": {
        "knee_angle": 80.0,
        "free_leg_extension": 90.0,
        "back_angle": 20.0,
    },
    "spiral": {
        "back_leg_height": 90.0,
        "back_angle": 10.0,
        "arm_extension": 180.0,
    },
}

# ---------------------------------------------------------------------------
# Feedback messages for common joints/angles
# Arabic first, English second
# ---------------------------------------------------------------------------
_FEEDBACK: Dict[str, Dict[str, tuple]] = {
    # (feedback_ar, feedback_en)
    "knee_angle": (
        "ثنِ ركبتك أكثر للحصول على الزاوية المثالية",
        "Bend your knee more to reach the ideal angle",
    ),
    "hip_tilt": (
        "حافظ على ميل الورك بزاوية محددة لتحسين التوازن",
        "Maintain the hip tilt at the specified angle to improve balance",
    ),
    "arm_extension": (
        "مدّ ذراعيك بالكامل للوصول إلى الوضعية المثالية",
        "Fully extend your arms to reach the ideal position",
    ),
    "back_angle": (
        "اضبط زاوية ظهرك للحصول على توافق أفضل",
        "Adjust your back angle for better alignment",
    ),
    "body_alignment": (
        "حافظ على استقامة الجسم أثناء الطيران",
        "Keep your body aligned during flight",
    ),
    "arm_tuck": (
        "اضغط ذراعيك بشكل أكبر نحو الجسم لزيادة سرعة الدوران",
        "Tuck your arms closer to your body to increase rotation speed",
    ),
    "head_position": (
        "حافظ على وضع الرأس محايداً أثناء الدوران",
        "Keep your head neutral during rotation",
    ),
    "knee_bend": (
        "اثنِ ركبتك عند الهبوط لامتصاص الصدمة",
        "Bend your knee on landing to absorb impact",
    ),
    "hip_position": (
        "اضبط وضع الورك عند الهبوط لتحسين الاستقرار",
        "Adjust hip position on landing for better stability",
    ),
    "free_leg_extension": (
        "مدّ الساق الحرة بالكامل للحصول على الشكل المثالي",
        "Fully extend your free leg for ideal form",
    ),
    "free_leg_height": (
        "ارفع الساق الحرة إلى مستوى الورك أو أعلى",
        "Raise your free leg to hip level or higher",
    ),
    "arm_position": (
        "أمسك ذراعيك في وضع أفقي لتحقيق التوازن",
        "Hold your arms in a horizontal position to maintain balance",
    ),
    "back_leg_height": (
        "ارفع الساق الخلفية أعلى للحصول على خط أفضل",
        "Raise your back leg higher for a better line",
    ),
}

_VISUAL_RATING_THRESHOLDS = [
    (90, "ممتاز / Excellent ⭐⭐⭐⭐⭐"),
    (75, "جيد جداً / Very Good ⭐⭐⭐⭐"),
    (60, "جيد / Good ⭐⭐⭐"),
    (40, "مقبول / Fair ⭐⭐"),
    (0,  "يحتاج تحسين / Needs Work ⭐"),
]


class PoseComparator:
    """محرك مقارنة الوضعية مع المحترفين"""

    # -----------------------------------------------------------------------
    # MediaPipe Pose landmark indices
    # -----------------------------------------------------------------------
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32

    # -----------------------------------------------------------------------
    # Angle extraction helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def calc_angle(a: Dict, b: Dict, c: Dict) -> float:
        """Calculate the angle at point b formed by vectors b->a and b->c.

        Each point is expected to be a dict with at least 'x' and 'y' keys.
        Returns angle in degrees [0, 180].
        """
        ax = a["x"] - b["x"]
        ay = a["y"] - b["y"]
        cx = c["x"] - b["x"]
        cy = c["y"] - b["y"]

        dot = ax * cx + ay * cy
        mag_a = math.sqrt(ax ** 2 + ay ** 2)
        mag_c = math.sqrt(cx ** 2 + cy ** 2)

        if mag_a < 1e-9 or mag_c < 1e-9:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot / (mag_a * mag_c)))
        return math.degrees(math.acos(cos_angle))

    @staticmethod
    def _get_kp(keypoints: List[Dict], idx: int) -> Optional[Dict]:
        """Return the keypoint dict at MediaPipe index *idx*, or None."""
        if keypoints is None or idx >= len(keypoints):
            return None
        kp = keypoints[idx]
        if kp is None:
            return None
        # Accept visibility threshold of 0.4 if the field exists
        vis = kp.get("visibility", 1.0)
        if vis < 0.4:
            return None
        return kp

    # -----------------------------------------------------------------------
    # Deviation scoring
    # -----------------------------------------------------------------------

    @staticmethod
    def _score_from_deviations(deviations: List[Dict]) -> float:
        """Compute an overall score [0, 100] from a list of deviation dicts."""
        if not deviations:
            return 100.0

        total_penalty = 0.0
        for dev in deviations:
            d = abs(dev.get("deviation", 0.0))
            # Penalty grows linearly up to 40 degrees deviation
            penalty = min(d / 40.0, 1.0) * (100.0 / len(deviations))
            total_penalty += penalty

        return max(0.0, 100.0 - total_penalty)

    # -----------------------------------------------------------------------
    # Angle extraction per element
    # -----------------------------------------------------------------------

    def _extract_angles(
        self, keypoints: List[Dict], element: str
    ) -> Dict[str, Optional[float]]:
        """Extract the relevant angles from keypoints for the given element."""
        g = self._get_kp  # shortcut

        angles: Dict[str, Optional[float]] = {}

        if element == "axel_takeoff":
            # knee_angle: hip-knee-ankle (left side)
            lh = g(keypoints, self.LEFT_HIP)
            lk = g(keypoints, self.LEFT_KNEE)
            la = g(keypoints, self.LEFT_ANKLE)
            angles["knee_angle"] = self.calc_angle(lh, lk, la) if all([lh, lk, la]) else None

            # hip_tilt: angle of hip-shoulder line relative to horizontal
            ls = g(keypoints, self.LEFT_SHOULDER)
            rh = g(keypoints, self.RIGHT_HIP)
            if ls and lh and rh:
                dx = rh["x"] - lh["x"]
                dy = rh["y"] - lh["y"]
                angles["hip_tilt"] = abs(math.degrees(math.atan2(dy, dx)))
            else:
                angles["hip_tilt"] = None

            # arm_extension: shoulder-elbow-wrist (right arm)
            rs = g(keypoints, self.RIGHT_SHOULDER)
            re = g(keypoints, self.RIGHT_ELBOW)
            rw = g(keypoints, self.RIGHT_WRIST)
            angles["arm_extension"] = (
                self.calc_angle(rs, re, rw) if all([rs, re, rw]) else None
            )

            # back_angle: shoulder-hip-knee
            ls = g(keypoints, self.LEFT_SHOULDER)
            lh2 = g(keypoints, self.LEFT_HIP)
            lk2 = g(keypoints, self.LEFT_KNEE)
            angles["back_angle"] = (
                self.calc_angle(ls, lh2, lk2) if all([ls, lh2, lk2]) else None
            )

        elif element == "axel_flight":
            # body_alignment: shoulders-hips vertical deviation
            ls = g(keypoints, self.LEFT_SHOULDER)
            rs = g(keypoints, self.RIGHT_SHOULDER)
            lh = g(keypoints, self.LEFT_HIP)
            rh = g(keypoints, self.RIGHT_HIP)
            if ls and rs and lh and rh:
                mid_sh_x = (ls["x"] + rs["x"]) / 2
                mid_sh_y = (ls["y"] + rs["y"]) / 2
                mid_hp_x = (lh["x"] + rh["x"]) / 2
                mid_hp_y = (lh["y"] + rh["y"]) / 2
                dx = mid_sh_x - mid_hp_x
                dy = mid_sh_y - mid_hp_y
                angles["body_alignment"] = 90.0 + math.degrees(math.atan2(dx, -dy))
            else:
                angles["body_alignment"] = None

            # arm_tuck: shoulder-elbow-wrist (left)
            ls2 = g(keypoints, self.LEFT_SHOULDER)
            le = g(keypoints, self.LEFT_ELBOW)
            lw = g(keypoints, self.LEFT_WRIST)
            angles["arm_tuck"] = (
                self.calc_angle(ls2, le, lw) if all([ls2, le, lw]) else None
            )

            # head_position: nose offset from shoulder midpoint
            nose = g(keypoints, self.NOSE)
            ls3 = g(keypoints, self.LEFT_SHOULDER)
            rs2 = g(keypoints, self.RIGHT_SHOULDER)
            if nose and ls3 and rs2:
                mid_x = (ls3["x"] + rs2["x"]) / 2
                angles["head_position"] = abs(nose["x"] - mid_x) * 100
            else:
                angles["head_position"] = None

        elif element == "axel_landing":
            # knee_bend: hip-knee-ankle (right / landing leg)
            rh = g(keypoints, self.RIGHT_HIP)
            rk = g(keypoints, self.RIGHT_KNEE)
            ra = g(keypoints, self.RIGHT_ANKLE)
            angles["knee_bend"] = (
                self.calc_angle(rh, rk, ra) if all([rh, rk, ra]) else None
            )

            # hip_position: hip tilt
            lh = g(keypoints, self.LEFT_HIP)
            rh2 = g(keypoints, self.RIGHT_HIP)
            if lh and rh2:
                dx = rh2["x"] - lh["x"]
                dy = rh2["y"] - lh["y"]
                angles["hip_position"] = abs(math.degrees(math.atan2(dy, dx)))
            else:
                angles["hip_position"] = None

            # free_leg_extension: hip-knee-ankle (left / free leg)
            lh2 = g(keypoints, self.LEFT_HIP)
            lk = g(keypoints, self.LEFT_KNEE)
            la = g(keypoints, self.LEFT_ANKLE)
            angles["free_leg_extension"] = (
                self.calc_angle(lh2, lk, la) if all([lh2, lk, la]) else None
            )

        elif element == "camel_spin":
            # back_angle: shoulder-hip line to horizontal
            ls = g(keypoints, self.LEFT_SHOULDER)
            lh = g(keypoints, self.LEFT_HIP)
            if ls and lh:
                dx = ls["x"] - lh["x"]
                dy = ls["y"] - lh["y"]
                angles["back_angle"] = 90.0 - abs(math.degrees(math.atan2(dy, dx)))
            else:
                angles["back_angle"] = None

            # free_leg_height: angle of free leg relative to standing leg
            lh2 = g(keypoints, self.LEFT_HIP)
            lk = g(keypoints, self.LEFT_KNEE)
            rh = g(keypoints, self.RIGHT_HIP)
            angles["free_leg_height"] = (
                self.calc_angle(lk, lh2, rh) if all([lh2, lk, rh]) else None
            )

            # arm_position: shoulder-elbow-wrist
            rs = g(keypoints, self.RIGHT_SHOULDER)
            re = g(keypoints, self.RIGHT_ELBOW)
            rw = g(keypoints, self.RIGHT_WRIST)
            angles["arm_position"] = (
                self.calc_angle(rs, re, rw) if all([rs, re, rw]) else None
            )

        elif element == "sit_spin":
            # knee_angle: hip-knee-ankle
            lh = g(keypoints, self.LEFT_HIP)
            lk = g(keypoints, self.LEFT_KNEE)
            la = g(keypoints, self.LEFT_ANKLE)
            angles["knee_angle"] = (
                self.calc_angle(lh, lk, la) if all([lh, lk, la]) else None
            )

            # free_leg_extension: right leg
            rh = g(keypoints, self.RIGHT_HIP)
            rk = g(keypoints, self.RIGHT_KNEE)
            ra = g(keypoints, self.RIGHT_ANKLE)
            angles["free_leg_extension"] = (
                self.calc_angle(rh, rk, ra) if all([rh, rk, ra]) else None
            )

            # back_angle: shoulder-hip line
            ls = g(keypoints, self.LEFT_SHOULDER)
            lh2 = g(keypoints, self.LEFT_HIP)
            if ls and lh2:
                dx = ls["x"] - lh2["x"]
                dy = ls["y"] - lh2["y"]
                angles["back_angle"] = abs(math.degrees(math.atan2(dy, dx)))
            else:
                angles["back_angle"] = None

        elif element == "spiral":
            # back_leg_height: angle of free leg above hip
            rh = g(keypoints, self.RIGHT_HIP)
            rk = g(keypoints, self.RIGHT_KNEE)
            ra = g(keypoints, self.RIGHT_ANKLE)
            if rh and rk and ra:
                dx = ra["x"] - rh["x"]
                dy = ra["y"] - rh["y"]
                angles["back_leg_height"] = abs(math.degrees(math.atan2(-dy, abs(dx))))
            else:
                angles["back_leg_height"] = None

            # back_angle: torso lean
            ls = g(keypoints, self.LEFT_SHOULDER)
            lh = g(keypoints, self.LEFT_HIP)
            if ls and lh:
                dx = ls["x"] - lh["x"]
                dy = ls["y"] - lh["y"]
                angles["back_angle"] = abs(math.degrees(math.atan2(dy, dx)))
            else:
                angles["back_angle"] = None

            # arm_extension: shoulder-elbow-wrist
            ls2 = g(keypoints, self.LEFT_SHOULDER)
            le = g(keypoints, self.LEFT_ELBOW)
            lw = g(keypoints, self.LEFT_WRIST)
            angles["arm_extension"] = (
                self.calc_angle(ls2, le, lw) if all([ls2, le, lw]) else None
            )

        return angles

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def compare_pose(self, keypoints: List[Dict], element: str) -> Dict[str, Any]:
        """Compare detected keypoints against the ideal pose for *element*.

        Parameters
        ----------
        keypoints:
            List of dicts, each with keys ``x``, ``y``, and optionally
            ``visibility``.  Indices follow MediaPipe Pose conventions.
        element:
            One of the keys in REFERENCE_POSES.

        Returns
        -------
        dict with keys:
            element, overall_score, angle_deviations, corrections_ar,
            corrections_en, visual_rating
        """
        if element not in REFERENCE_POSES:
            return {
                "element": element,
                "overall_score": 0.0,
                "angle_deviations": [],
                "corrections_ar": [f"عنصر غير معروف: {element}"],
                "corrections_en": [f"Unknown element: {element}"],
                "visual_rating": "غير معروف / Unknown",
            }

        ideal_angles = REFERENCE_POSES[element]
        actual_angles = self._extract_angles(keypoints, element)

        angle_deviations: List[Dict[str, Any]] = []
        corrections_ar: List[str] = []
        corrections_en: List[str] = []

        for joint, ideal_val in ideal_angles.items():
            actual_val = actual_angles.get(joint)
            if actual_val is None:
                # Landmark not detected — skip silently
                continue

            deviation = actual_val - ideal_val
            fb = _FEEDBACK.get(joint, ("راجع هذه الزاوية", "Check this angle"))
            feedback_ar = fb[0]
            feedback_en = fb[1]

            dev_entry = {
                "joint": joint,
                "ideal": ideal_val,
                "actual": round(actual_val, 1),
                "deviation": round(deviation, 1),
                "feedback_ar": feedback_ar,
                "feedback_en": feedback_en,
            }
            angle_deviations.append(dev_entry)

            if abs(deviation) > 20:
                corrections_ar.append(f"{joint}: {feedback_ar} (الانحراف: {deviation:+.1f}°)")
                corrections_en.append(f"{joint}: {feedback_en} (deviation: {deviation:+.1f}°)")

        overall_score = self._score_from_deviations(angle_deviations)

        # Visual rating
        visual_rating = _VISUAL_RATING_THRESHOLDS[-1][1]
        for threshold, label in _VISUAL_RATING_THRESHOLDS:
            if overall_score >= threshold:
                visual_rating = label
                break

        return {
            "element": element,
            "overall_score": round(overall_score, 1),
            "angle_deviations": angle_deviations,
            "corrections_ar": corrections_ar,
            "corrections_en": corrections_en,
            "visual_rating": visual_rating,
        }


def get_element_list() -> List[str]:
    """Return the list of available skating elements for comparison."""
    return list(REFERENCE_POSES.keys())
