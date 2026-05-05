"""
نظام كشف الأخطاء التقنية وتقديم التصحيحات
Technical Error Detection and Correction System
"""
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class ErrorSeverity(Enum):
    LOW = "منخفض"
    MEDIUM = "متوسط"
    HIGH = "عالي"
    CRITICAL = "حرج"


class ErrorCategory(Enum):
    JUMP = "قفزة"
    SPIN = "دوران"
    POSTURE = "وضعية الجسم"
    BALANCE = "التوازن"
    EDGE = "الحافة"
    LANDING = "الهبوط"
    TAKEOFF = "الإقلاع"
    ROTATION = "الدوران"
    ARM = "ذراعين"
    KNEE = "الركبة"


@dataclass
class SkatingError:
    """خطأ تقني مكتشف"""
    category: ErrorCategory
    severity: ErrorSeverity
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    corrections_ar: List[str]
    corrections_en: List[str]
    frame_start: int = 0
    frame_end: int = 0
    confidence: float = 0.8
    goe_impact: int = 0  # تأثير على GOE (-5 إلى 0)

    def to_dict(self) -> Dict:
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'title_ar': self.title_ar,
            'title_en': self.title_en,
            'description_ar': self.description_ar,
            'description_en': self.description_en,
            'corrections_ar': self.corrections_ar,
            'corrections_en': self.corrections_en,
            'frame_start': self.frame_start,
            'frame_end': self.frame_end,
            'confidence': self.confidence,
            'goe_impact': self.goe_impact,
        }


# ============================================================================
# ERROR LIBRARY - قاموس الأخطاء الشامل
# ============================================================================

def error_under_rotation(rotations_done: float, rotations_expected: float,
                         frame_start: int, frame_end: int) -> SkatingError:
    deficit = rotations_expected - rotations_done
    severity = ErrorSeverity.CRITICAL if deficit > 0.5 else ErrorSeverity.HIGH
    return SkatingError(
        category=ErrorCategory.ROTATION,
        severity=severity,
        title_ar="دوران ناقص",
        title_en="Under-Rotation",
        description_ar=f"اكتمل {rotations_done:.1f} دورة من {rotations_expected:.0f} دورات مطلوبة. العجز: {deficit:.2f}",
        description_en=f"Completed {rotations_done:.1f} of {rotations_expected:.0f} required rotations. Deficit: {deficit:.2f}",
        corrections_ar=[
            "زيادة قوة الإقلاع عن طريق دفع أقوى للحافة",
            "ضم الذراعين بشكل أسرع وأكثر إحكاماً نحو الجسم",
            "تمركز الوزن على المحور العمودي قبل الدخول في الدوران",
            "تمارين تقوية عضلات القلب لتحسين قوة الالتفاف",
            "التدرب على الدوران في المكان على الجليد لتحسين الإحساس بالمحور",
        ],
        corrections_en=[
            "Increase takeoff power with a stronger edge push",
            "Pull arms in faster and tighter toward the body",
            "Center weight on vertical axis before entering rotation",
            "Core strengthening exercises to improve rotation power",
            "Practice in-place spins on ice to improve axis awareness",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.90,
        goe_impact=-2 if deficit > 0.5 else -1,
    )


def error_two_foot_landing(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.LANDING,
        severity=ErrorSeverity.HIGH,
        title_ar="هبوط على القدمين",
        title_en="Two-Foot Landing",
        description_ar="لمست القدم الثانية الجليد عند الهبوط مما يُفقد القفزة نقاطاً",
        description_en="Second foot touched the ice upon landing, reducing jump score",
        corrections_ar=[
            "الحفاظ على ساق الهبوط الأمامية مرفوعة خلف الجسم لمدة أطول",
            "التركيز على الهبوط على حافة خارجية نظيفة على قدم واحدة",
            "تمارين الإطار على قدم واحدة لتقوية العضلات",
            "تدريب على الهبوط ببطء من قفزات منخفضة لبناء العادة الصحيحة",
            "المراجعة مع المدرب لتحليل ميل الجسم لحظة الهبوط",
        ],
        corrections_en=[
            "Keep the free leg raised behind the body longer upon landing",
            "Focus on landing on a clean outside back edge on one foot",
            "Single-leg balance exercises to strengthen stabilizer muscles",
            "Practice landing slowly from low jumps to build correct habit",
            "Review with coach to analyze body lean at moment of landing",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.88,
        goe_impact=-2,
    )


def error_fall(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.LANDING,
        severity=ErrorSeverity.CRITICAL,
        title_ar="سقوط",
        title_en="Fall",
        description_ar="سقط اللاعب عند الهبوط - أكبر خصم في النقاط",
        description_en="Skater fell on landing - maximum point deduction",
        corrections_ar=[
            "تحليل سبب السقوط: ضعف في التوازن أم دوران ناقص؟",
            "العودة للتدرب على قفزات مفردة قبل مضاعفتها",
            "تمارين التوازن على لوحة التوازن خارج الجليد",
            "تقوية عضلات الكاحل والفخذ",
            "تدريبات المطاطية لتحسين مرونة مفصل الكاحل",
        ],
        corrections_en=[
            "Analyze the cause: balance failure or under-rotation?",
            "Return to training singles before attempting multiples",
            "Off-ice balance board exercises",
            "Ankle and quadriceps strengthening",
            "Flexibility training to improve ankle joint mobility",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.95,
        goe_impact=-5,
    )


def error_wrong_edge(jump_name: str, frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.EDGE,
        severity=ErrorSeverity.HIGH,
        title_ar=f"حافة خاطئة في {jump_name}",
        title_en=f"Wrong Edge on {jump_name}",
        description_ar=f"قفزة {jump_name} نُفِّذت على الحافة الخاطئة، مما يُسبب خصماً في GOE",
        description_en=f"{jump_name} executed on wrong edge, causing GOE deduction",
        corrections_ar=[
            f"للـ{jump_name}: التأكد من استخدام الحافة الداخلية الخلفية للقدم اليسرى",
            "تمارين الحواف البطيئة لتطوير الإحساس بالحافة الصحيحة",
            "استخدام الدوائر على الجليد لتدريب الحواف",
            "التركيز على زاوية الكاحل وميل الجسم قبل الإقلاع",
            "طلب ملاحظات فورية من المدرب عند كل محاولة",
        ],
        corrections_en=[
            f"For {jump_name}: ensure back inside edge of left foot at takeoff",
            "Slow edge exercises to develop correct edge feel",
            "Use circle patterns on ice to train edges",
            "Focus on ankle angle and body lean before takeoff",
            "Request immediate coach feedback on each attempt",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.82,
        goe_impact=-1,
    )


def error_low_jump_height(height_cm: float, frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.JUMP,
        severity=ErrorSeverity.MEDIUM,
        title_ar="ارتفاع قفزة منخفض",
        title_en="Low Jump Height",
        description_ar=f"ارتفاع القفزة {height_cm:.0f} سم — المطلوب أكثر من 40 سم للتقييم الجيد",
        description_en=f"Jump height {height_cm:.0f} cm — above 40 cm needed for good evaluation",
        corrections_ar=[
            "تقوية عضلات الأرجل بتمارين القفز خارج الجليد (Box Jumps, Squat Jumps)",
            "تعميق الانحناء (تحمير الركبة) قبل الإقلاع للحصول على طاقة أكبر",
            "استخدام قوة الذراعين بشكل متزامن للدفع للأعلى",
            "تحسين سرعة المزلق قبل القفزة لزيادة الزخم",
            "تدريب على قفزات الليكرة لتحسين الانطلاق العمودي",
        ],
        corrections_en=[
            "Strengthen leg muscles with off-ice jump training (Box Jumps, Squat Jumps)",
            "Deepen the knee bend (knee spring) before takeoff for more energy",
            "Use arm swing simultaneously to push upward",
            "Improve approach speed before the jump to increase momentum",
            "Practice waltz jumps to improve vertical takeoff",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.85,
        goe_impact=-1,
    )


def error_bent_back(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.POSTURE,
        severity=ErrorSeverity.MEDIUM,
        title_ar="انحناء الظهر",
        title_en="Bent Back / Forward Lean",
        description_ar="يميل الجسم للأمام بشكل مفرط مما يؤثر على المظهر والتوازن",
        description_en="Excessive forward body lean affecting aesthetics and balance",
        corrections_ar=[
            "تقوية عضلات الظهر السفلية بتمارين Dead Lift والسباحة",
            "تمارين اليوغا لتحسين مرونة العمود الفقري",
            "الوعي الجسدي: تخيّل خيط يسحب رأسك للأعلى أثناء الزلق",
            "مراجعة الفيديو مع المدرب لتصحيح الوضعية",
            "تمارين الإطار أمام المرآة خارج الجليد",
        ],
        corrections_en=[
            "Strengthen lower back muscles with Dead Lifts and swimming",
            "Yoga exercises to improve spinal flexibility",
            "Body awareness: imagine a string pulling your head upward while skating",
            "Review video with coach to correct posture",
            "Off-ice mirror exercises for posture awareness",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.78,
        goe_impact=0,
    )


def error_arms_not_controlled(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.ARM,
        severity=ErrorSeverity.LOW,
        title_ar="ذراعان غير منضبطتان",
        title_en="Uncontrolled Arms",
        description_ar="حركة الذراعين غير منتظمة أو خارجة عن السيطرة أثناء الحركة",
        description_en="Irregular or uncontrolled arm movement during skating",
        corrections_ar=[
            "تدريبات التنسيق بين الذراعين وحركة الجسم خارج الجليد",
            "مراقبة الفيديو لتحديد لحظات عدم التحكم",
            "التدرب على وضعيات الذراعين ببطء أمام المرآة",
            "دمج حركات الذراعين في التمارين البدنية اليومية",
            "التنفس المنتظم يساعد على ضبط حركة الذراعين",
        ],
        corrections_en=[
            "Off-ice arm and body coordination drills",
            "Watch video to identify moments of loss of control",
            "Practice arm positions slowly in front of a mirror",
            "Incorporate arm movements into daily fitness exercises",
            "Regular breathing helps regulate arm movement",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.72,
        goe_impact=0,
    )


def error_knee_not_bent_on_landing(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.KNEE,
        severity=ErrorSeverity.HIGH,
        title_ar="ركبة مستقيمة عند الهبوط",
        title_en="Straight Knee on Landing",
        description_ar="عدم ثني الركبة عند الهبوط يزيد من خطر الإصابة ويُقلل الدرجات",
        description_en="Not bending the knee on landing increases injury risk and reduces scores",
        corrections_ar=[
            "التركيز على ثني الركبة فور لمس الجليد لامتصاص الصدمة",
            "تمارين الهبوط من ارتفاعات منخفضة مع التركيز على الامتصاص",
            "تقوية عضلات الفخذ الأمامية (Quadriceps) لدعم الركبة",
            "التكرار البطيء: التدرب على هبوطات بطيئة ومتعمدة",
            "استخدام أحذية التزلج الصحيحة التي توفر دعماً كافياً للكاحل",
        ],
        corrections_en=[
            "Focus on bending the knee immediately upon touching the ice to absorb shock",
            "Practice landing from low heights focusing on absorption",
            "Strengthen quadricep muscles to support the knee",
            "Slow repetition: practice slow and deliberate landings",
            "Use proper skating boots that provide adequate ankle support",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.86,
        goe_impact=-1,
    )


def error_off_center_spin(frame_start: int, frame_end: int) -> SkatingError:
    return SkatingError(
        category=ErrorCategory.SPIN,
        severity=ErrorSeverity.MEDIUM,
        title_ar="دوران خارج المركز",
        title_en="Traveling Spin",
        description_ar="يتحرك الدوران من مكانه عوضاً عن البقاء في نقطة ثابتة",
        description_en="Spin travels across the ice instead of staying in one spot",
        corrections_ar=[
            "التركيز على نقطة ثابتة على الجليد قبل الدخول في الدوران",
            "الدخول في الدوران على حافة داخلية نظيفة",
            "تمارين الدوران البطيء في المكان لتطوير الإحساس بالمحور",
            "تقليل قوة الدخول مؤقتاً للتركيز على المركزية",
            "تمارين الدوران مع العيون مفتوحة على نقطة أمامية ثابتة",
        ],
        corrections_en=[
            "Focus on a fixed spot on the ice before entering the spin",
            "Enter the spin on a clean inside edge",
            "Practice slow in-place spins to develop axis awareness",
            "Temporarily reduce entry power to focus on centering",
            "Spin with eyes open fixed on a stationary point ahead",
        ],
        frame_start=frame_start,
        frame_end=frame_end,
        confidence=0.80,
        goe_impact=-1,
    )


# ============================================================================
# POSE-BASED ERROR ANALYSIS ENGINE
# ============================================================================

class PoseErrorAnalyzer:
    """
    يحلل بيانات الوضعية من MediaPipe ويكتشف الأخطاء التقنية
    """

    # MediaPipe landmark indices
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_FOOT = 31
    RIGHT_FOOT = 32

    def __init__(self):
        self.fps = 30.0

    def analyze_poses(self, poses: List[Dict], fps: float = 30.0) -> List[SkatingError]:
        """تحليل تسلسل كامل من الوضعيات"""
        self.fps = fps
        errors: List[SkatingError] = []

        if not poses:
            return errors

        # Detect airborne sequences (potential jumps)
        airborne_seqs = self._find_airborne_sequences(poses)

        for seq_start, seq_end in airborne_seqs:
            seq = poses[seq_start:seq_end + 1]
            frame_s = poses[seq_start]['frame']
            frame_e = poses[seq_end]['frame']
            duration = (frame_e - frame_s) / self.fps

            # Check for under-rotation
            rotations = self._estimate_rotations_from_duration(duration)
            expected = round(rotations)
            if rotations < expected - 0.25 and expected >= 2:
                errors.append(error_under_rotation(rotations, expected, frame_s, frame_e))

            # Check landing quality
            if seq_end + 3 < len(poses):
                landing_poses = poses[seq_end: seq_end + 5]
                landing_errors = self._check_landing(landing_poses, frame_e)
                errors.extend(landing_errors)

            # Check jump height
            height = self._estimate_height_from_poses(seq)
            if height < 30:
                errors.append(error_low_jump_height(height, frame_s, frame_e))

        # Check posture throughout
        posture_errors = self._check_posture_sequence(poses)
        errors.extend(posture_errors)

        # Check arm control
        arm_errors = self._check_arm_control(poses)
        errors.extend(arm_errors)

        # Detect spinning sequences
        spin_seqs = self._find_spin_sequences(poses)
        for seq_start, seq_end in spin_seqs:
            frame_s = poses[seq_start]['frame']
            frame_e = poses[seq_end]['frame']
            if self._check_spin_traveling(poses[seq_start:seq_end + 1]):
                errors.append(error_off_center_spin(frame_s, frame_e))

        return errors

    def _get_kp(self, keypoints: List[Dict], idx: int) -> Optional[Dict]:
        if idx < len(keypoints):
            return keypoints[idx]
        return None

    def _find_airborne_sequences(self, poses: List[Dict]) -> List[Tuple[int, int]]:
        sequences = []
        in_air = False
        start_idx = 0
        MIN_FRAMES = 8

        for i, pose in enumerate(poses):
            is_air = pose.get('is_airborne', False)
            if is_air and not in_air:
                in_air = True
                start_idx = i
            elif not is_air and in_air:
                in_air = False
                if i - start_idx >= MIN_FRAMES:
                    sequences.append((start_idx, i - 1))

        return sequences

    def _find_spin_sequences(self, poses: List[Dict]) -> List[Tuple[int, int]]:
        """كشف تسلسلات الدوران باستخدام حركة الكتف"""
        sequences = []
        WINDOW = 20
        MIN_FRAMES = 30

        shoulder_angles = []
        for pose in poses:
            kp = pose.get('keypoints', [])
            ls = self._get_kp(kp, self.LEFT_SHOULDER)
            rs = self._get_kp(kp, self.RIGHT_SHOULDER)
            if ls and rs:
                angle = np.arctan2(rs['y'] - ls['y'], rs['x'] - ls['x'])
                shoulder_angles.append(angle)
            else:
                shoulder_angles.append(None)

        in_spin = False
        start_idx = 0
        for i in range(WINDOW, len(shoulder_angles)):
            window = [a for a in shoulder_angles[i - WINDOW:i] if a is not None]
            if len(window) < WINDOW // 2:
                continue
            variance = np.var(window)
            is_spinning = variance > 0.05
            if is_spinning and not in_spin:
                in_spin = True
                start_idx = i - WINDOW
            elif not is_spinning and in_spin:
                in_spin = False
                if i - start_idx >= MIN_FRAMES:
                    sequences.append((start_idx, i - 1))

        return sequences

    def _check_spin_traveling(self, spin_poses: List[Dict]) -> bool:
        """هل يتنقل الدوران من مكانه؟"""
        positions_x = []
        positions_y = []
        for pose in spin_poses:
            kp = pose.get('keypoints', [])
            lh = self._get_kp(kp, self.LEFT_HIP)
            rh = self._get_kp(kp, self.RIGHT_HIP)
            if lh and rh:
                positions_x.append((lh['x'] + rh['x']) / 2)
                positions_y.append((lh['y'] + rh['y']) / 2)
        if len(positions_x) < 5:
            return False
        range_x = max(positions_x) - min(positions_x)
        range_y = max(positions_y) - min(positions_y)
        return range_x > 0.15 or range_y > 0.15

    def _estimate_rotations_from_duration(self, duration: float) -> float:
        if duration < 0.3:
            return 1.0
        elif duration < 0.5:
            return 2.0
        elif duration < 0.7:
            return 3.0
        elif duration < 0.9:
            return 3.5
        else:
            return 4.0

    def _estimate_height_from_poses(self, seq: List[Dict]) -> float:
        min_y = 1.0
        for pose in seq:
            kp = pose.get('keypoints', [])
            nose = self._get_kp(kp, self.NOSE)
            if nose and nose.get('visibility', 0) > 0.5:
                min_y = min(min_y, nose['y'])
        return (1.0 - min_y) * 100

    def _check_landing(self, landing_poses: List[Dict], frame_start: int) -> List[SkatingError]:
        errors = []

        for pose in landing_poses:
            kp = pose.get('keypoints', [])
            lk = self._get_kp(kp, self.LEFT_KNEE)
            rk = self._get_kp(kp, self.RIGHT_KNEE)
            la = self._get_kp(kp, self.LEFT_ANKLE)
            ra = self._get_kp(kp, self.RIGHT_ANKLE)
            lh = self._get_kp(kp, self.LEFT_HIP)
            rh = self._get_kp(kp, self.RIGHT_HIP)

            # Check two-foot landing
            if la and ra and la.get('visibility', 0) > 0.5 and ra.get('visibility', 0) > 0.5:
                y_diff = abs(la['y'] - ra['y'])
                if y_diff < 0.05:
                    errors.append(error_two_foot_landing(frame_start, frame_start + 5))
                    break

            # Check knee bend
            if lk and la and lh and lk.get('visibility', 0) > 0.5:
                knee_angle = self._calc_angle(
                    (lh['x'], lh['y']), (lk['x'], lk['y']), (la['x'], la['y'])
                )
                if knee_angle > 160:  # nearly straight
                    errors.append(error_knee_not_bent_on_landing(frame_start, frame_start + 5))
                    break

        return errors

    def _check_posture_sequence(self, poses: List[Dict]) -> List[SkatingError]:
        errors = []
        bent_count = 0
        sample_step = max(1, len(poses) // 30)

        for i in range(0, len(poses), sample_step):
            pose = poses[i]
            kp = pose.get('keypoints', [])
            ls = self._get_kp(kp, self.LEFT_SHOULDER)
            rs = self._get_kp(kp, self.RIGHT_SHOULDER)
            lh = self._get_kp(kp, self.LEFT_HIP)
            rh = self._get_kp(kp, self.RIGHT_HIP)
            nose = self._get_kp(kp, self.NOSE)

            if ls and rs and lh and rh and nose:
                shoulder_y = (ls['y'] + rs['y']) / 2
                hip_y = (lh['y'] + rh['y']) / 2
                nose_y = nose['y']

                # Forward lean: nose much lower relative to shoulders
                if nose_y > shoulder_y + 0.08:
                    bent_count += 1

        if bent_count > len(poses) // (sample_step * 3):
            mid = poses[len(poses) // 2]['frame']
            errors.append(error_bent_back(poses[0]['frame'], poses[-1]['frame']))

        return errors

    def _check_arm_control(self, poses: List[Dict]) -> List[SkatingError]:
        arm_y_vals = []
        sample_step = max(1, len(poses) // 40)

        for i in range(0, len(poses), sample_step):
            kp = poses[i].get('keypoints', [])
            lw = self._get_kp(kp, self.LEFT_WRIST)
            rw = self._get_kp(kp, self.RIGHT_WRIST)
            if lw and rw and lw.get('visibility', 0) > 0.5 and rw.get('visibility', 0) > 0.5:
                arm_y_vals.append(abs(lw['y'] - rw['y']))

        if len(arm_y_vals) > 5:
            variance = np.var(arm_y_vals)
            if variance > 0.02:
                return [error_arms_not_controlled(poses[0]['frame'], poses[-1]['frame'])]

        return []

    def _calc_angle(self, a: Tuple, b: Tuple, c: Tuple) -> float:
        """حساب الزاوية عند النقطة b"""
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])
        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return np.degrees(np.arccos(np.clip(cosine, -1, 1)))


# ============================================================================
# CORRECTION REPORT GENERATOR
# ============================================================================

def generate_correction_report(errors: List[SkatingError], lang: str = 'ar') -> Dict:
    """توليد تقرير شامل للتصحيحات"""
    if not errors:
        return {
            'total_errors': 0,
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'priority_corrections': [],
            'overall_assessment': 'ممتاز' if lang == 'ar' else 'Excellent',
            'score_impact': 0,
        }

    critical = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
    high = [e for e in errors if e.severity == ErrorSeverity.HIGH]
    medium = [e for e in errors if e.severity == ErrorSeverity.MEDIUM]
    low = [e for e in errors if e.severity == ErrorSeverity.LOW]

    score_impact = sum(e.goe_impact for e in errors)

    # Prioritize corrections
    priority = []
    for e in critical + high:
        if lang == 'ar':
            priority.extend(e.corrections_ar[:2])
        else:
            priority.extend(e.corrections_en[:2])

    if len(errors) <= 1:
        assessment = 'ممتاز' if lang == 'ar' else 'Excellent'
    elif len(errors) <= 3:
        assessment = 'جيد - يحتاج تحسين بسيط' if lang == 'ar' else 'Good - Needs Minor Improvement'
    elif len(errors) <= 5:
        assessment = 'متوسط - تحتاج تدريباً مركزاً' if lang == 'ar' else 'Average - Needs Focused Training'
    else:
        assessment = 'يحتاج عملاً كبيراً' if lang == 'ar' else 'Needs Significant Work'

    return {
        'total_errors': len(errors),
        'critical': [e.to_dict() for e in critical],
        'high': [e.to_dict() for e in high],
        'medium': [e.to_dict() for e in medium],
        'low': [e.to_dict() for e in low],
        'priority_corrections': list(dict.fromkeys(priority))[:6],
        'overall_assessment': assessment,
        'score_impact': score_impact,
    }
