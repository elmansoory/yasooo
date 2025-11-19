"""
نموذج التعرف على الحركات - Movement Classifier
يستخدم تحليل الوضعيات والحركة للتعرف على عناصر التزلج
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MovementType(Enum):
    """أنواع الحركات"""
    JUMP = "jump"
    SPIN = "spin"
    STEP_SEQUENCE = "step_sequence"
    CHOREOGRAPHIC = "choreographic"
    SPIRAL = "spiral"
    TRANSITION = "transition"


@dataclass
class MovementFeatures:
    """خصائص الحركة المستخرجة"""
    # خصائص الموضع
    center_of_mass_height: float
    body_rotation_angle: float
    leg_extension: float
    arm_position: float

    # خصائص الحركة
    vertical_velocity: float
    rotational_velocity: float
    horizontal_velocity: float

    # خصائص القفز
    airtime: float
    takeoff_angle: float
    landing_angle: float
    rotation_count: float

    # خصائص الدوران
    spin_speed: float
    axis_stability: float
    body_position: str  # upright, sit, camel, etc.

    # خصائص عامة
    duration: float
    complexity: float


class MovementClassifier:
    """نموذج التصنيف الرئيسي للحركات"""

    def __init__(self):
        self.jump_detector = JumpDetector()
        self.spin_detector = SpinDetector()
        self.step_detector = StepSequenceDetector()

        # عتبات التصنيف
        self.thresholds = {
            'min_jump_airtime': 0.3,  # ثانية
            'min_spin_duration': 2.0,  # ثانية
            'min_spin_speed': 1.5,  # دورة/ثانية
            'min_step_complexity': 0.5
        }

    def classify_movement(self, features: MovementFeatures) -> Dict:
        """تصنيف الحركة بناءً على الخصائص"""

        # فحص القفز
        if self._is_jump(features):
            return self.jump_detector.detect_jump_type(features)

        # فحص الدوران
        elif self._is_spin(features):
            return self.spin_detector.detect_spin_type(features)

        # فحص تسلسل الخطوات
        elif self._is_step_sequence(features):
            return self.step_detector.detect_step_pattern(features)

        # حركة انتقالية أو فنية
        else:
            return {
                'type': MovementType.TRANSITION.value,
                'name': 'Transition',
                'confidence': 0.7,
                'details': self._analyze_transition(features)
            }

    def _is_jump(self, features: MovementFeatures) -> bool:
        """فحص إذا كانت الحركة قفزة"""
        return (
            features.airtime >= self.thresholds['min_jump_airtime'] and
            features.vertical_velocity > 2.0 and
            features.rotation_count >= 0.5
        )

    def _is_spin(self, features: MovementFeatures) -> bool:
        """فحص إذا كانت الحركة دوران"""
        return (
            features.duration >= self.thresholds['min_spin_duration'] and
            features.spin_speed >= self.thresholds['min_spin_speed'] and
            features.axis_stability > 0.6
        )

    def _is_step_sequence(self, features: MovementFeatures) -> bool:
        """فحص إذا كانت تسلسل خطوات"""
        return (
            features.complexity >= self.thresholds['min_step_complexity'] and
            features.duration >= 3.0 and
            features.horizontal_velocity > 1.0
        )

    def _analyze_transition(self, features: MovementFeatures) -> Dict:
        """تحليل الحركة الانتقالية"""
        return {
            'speed': features.horizontal_velocity,
            'smoothness': features.axis_stability,
            'duration': features.duration
        }


class JumpDetector:
    """كاشف القفزات - يتعرف على 24 نوع قفزة"""

    def __init__(self):
        # تعريف القفزات حسب الخصائص
        self.jump_signatures = {
            # Axel Family - من الأمام
            'A': {'rotations': 1.5, 'takeoff': 'forward', 'edge': 'outside', 'toe': False},
            '2A': {'rotations': 2.5, 'takeoff': 'forward', 'edge': 'outside', 'toe': False},
            '3A': {'rotations': 3.5, 'takeoff': 'forward', 'edge': 'outside', 'toe': False},
            '4A': {'rotations': 4.5, 'takeoff': 'forward', 'edge': 'outside', 'toe': False},

            # Lutz - حافة خارجية خلفية + مسننات
            'Lz': {'rotations': 1.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '2Lz': {'rotations': 2.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '3Lz': {'rotations': 3.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '4Lz': {'rotations': 4.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},

            # Flip - حافة داخلية خلفية + مسننات
            'F': {'rotations': 1.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': True},
            '2F': {'rotations': 2.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': True},
            '3F': {'rotations': 3.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': True},
            '4F': {'rotations': 4.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': True},

            # Loop - حافة خارجية خلفية
            'Lo': {'rotations': 1.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': False},
            '2Lo': {'rotations': 2.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': False},
            '3Lo': {'rotations': 3.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': False},
            '4Lo': {'rotations': 4.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': False},

            # Salchow - حافة داخلية خلفية
            'S': {'rotations': 1.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': False},
            '2S': {'rotations': 2.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': False},
            '3S': {'rotations': 3.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': False},
            '4S': {'rotations': 4.0, 'takeoff': 'backward', 'edge': 'inside', 'toe': False},

            # Toe Loop - حافة خارجية خلفية + مسننات
            'T': {'rotations': 1.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '2T': {'rotations': 2.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '3T': {'rotations': 3.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
            '4T': {'rotations': 4.0, 'takeoff': 'backward', 'edge': 'outside', 'toe': True},
        }

    def detect_jump_type(self, features: MovementFeatures) -> Dict:
        """التعرف على نوع القفزة"""

        # حساب عدد الدورات
        rotations = self._calculate_rotations(features)

        # تحديد خصائص الإقلاع
        takeoff_direction = self._detect_takeoff_direction(features)
        edge_type = self._detect_edge_type(features)
        uses_toe = self._detect_toe_pick_usage(features)

        # مطابقة مع قاعدة البيانات
        best_match = None
        best_score = 0

        for jump_code, signature in self.jump_signatures.items():
            score = self._match_score(
                rotations, takeoff_direction, edge_type, uses_toe,
                signature
            )

            if score > best_score:
                best_score = score
                best_match = jump_code

        # حساب GOE المقدر
        estimated_goe = self._estimate_goe(features, best_score)

        return {
            'type': MovementType.JUMP.value,
            'code': best_match,
            'name': self._get_jump_name(best_match),
            'rotations': rotations,
            'confidence': best_score,
            'estimated_goe': estimated_goe,
            'features': {
                'takeoff': takeoff_direction,
                'edge': edge_type,
                'toe_pick': uses_toe,
                'height': features.center_of_mass_height,
                'landing_quality': self._assess_landing(features)
            }
        }

    def _calculate_rotations(self, features: MovementFeatures) -> float:
        """حساب عدد الدورات"""
        # استخدام السرعة الدورانية والوقت في الهواء
        total_rotation = features.rotational_velocity * features.airtime
        return round(total_rotation * 2) / 2  # تقريب لأقرب نصف دورة

    def _detect_takeoff_direction(self, features: MovementFeatures) -> str:
        """كشف اتجاه الإقلاع"""
        return 'forward' if features.takeoff_angle > 0 else 'backward'

    def _detect_edge_type(self, features: MovementFeatures) -> str:
        """كشف نوع الحافة"""
        # تحليل زاوية الجسم عند الإقلاع
        return 'outside' if abs(features.body_rotation_angle) > 45 else 'inside'

    def _detect_toe_pick_usage(self, features: MovementFeatures) -> bool:
        """كشف استخدام المسننات"""
        # فحص نمط الإقلاع
        return features.takeoff_angle > 60  # زاوية حادة تشير لاستخدام المسننات

    def _match_score(self, rotations, takeoff, edge, toe, signature) -> float:
        """حساب درجة المطابقة"""
        score = 0.0

        # مطابقة الدورات (الأهم)
        rotation_diff = abs(rotations - signature['rotations'])
        score += max(0, 1 - rotation_diff / 2) * 0.5

        # مطابقة الخصائص الأخرى
        if takeoff == signature['takeoff']:
            score += 0.2
        if edge == signature['edge']:
            score += 0.15
        if toe == signature['toe']:
            score += 0.15

        return score

    def _estimate_goe(self, features: MovementFeatures, confidence: float) -> int:
        """تقدير GOE"""
        base_goe = 0

        # جودة الهبوط
        if features.landing_angle > 80:
            base_goe += 1
        elif features.landing_angle < 60:
            base_goe -= 1

        # الارتفاع
        if features.center_of_mass_height > 1.5:
            base_goe += 1

        # الثقة في التصنيف
        if confidence < 0.7:
            base_goe -= 1

        return max(-5, min(5, base_goe))

    def _assess_landing(self, features: MovementFeatures) -> str:
        """تقييم جودة الهبوط"""
        if features.landing_angle > 80:
            return 'excellent'
        elif features.landing_angle > 70:
            return 'good'
        elif features.landing_angle > 60:
            return 'fair'
        else:
            return 'poor'

    def _get_jump_name(self, code: str) -> str:
        """الحصول على اسم القفزة"""
        names = {
            'A': 'Axel', '2A': 'Double Axel', '3A': 'Triple Axel', '4A': 'Quad Axel',
            'Lz': 'Lutz', '2Lz': 'Double Lutz', '3Lz': 'Triple Lutz', '4Lz': 'Quad Lutz',
            'F': 'Flip', '2F': 'Double Flip', '3F': 'Triple Flip', '4F': 'Quad Flip',
            'Lo': 'Loop', '2Lo': 'Double Loop', '3Lo': 'Triple Loop', '4Lo': 'Quad Loop',
            'S': 'Salchow', '2S': 'Double Salchow', '3S': 'Triple Salchow', '4S': 'Quad Salchow',
            'T': 'Toe Loop', '2T': 'Double Toe Loop', '3T': 'Triple Toe Loop', '4T': 'Quad Toe Loop',
        }
        return names.get(code, code)


class SpinDetector:
    """كاشف الدورانات - يتعرف على 35 نوع دوران"""

    def __init__(self):
        # أنواع الدورانات الأساسية
        self.spin_types = {
            # Upright Spins - دورانات منتصبة
            'USp': {'position': 'upright', 'variations': ['basic', 'layback', 'biellmann']},

            # Sit Spins - دورانات جلوس
            'SSp': {'position': 'sit', 'variations': ['basic', 'broken_leg', 'pancake']},

            # Camel Spins - دورانات جمل
            'CSp': {'position': 'camel', 'variations': ['basic', 'donut', 'catch_foot']},

            # Flying Spins - دورانات طائرة
            'FSp': {'position': 'flying', 'variations': ['flying_camel', 'flying_sit', 'death_drop']},

            # Combination Spins - دورانات مركبة
            'CoSp': {'position': 'combination', 'variations': ['two_position', 'three_position']},
        }

        # المستويات (1-4)
        self.level_features = {
            1: ['basic_position'],
            2: ['position_change', 'edge_change'],
            3: ['difficult_variation', 'fast_spin'],
            4: ['multiple_variations', 'very_fast', 'difficult_entry']
        }

    def detect_spin_type(self, features: MovementFeatures) -> Dict:
        """التعرف على نوع الدوران"""

        # تحديد الوضعية الأساسية
        position = self._detect_position(features.body_position)

        # تحديد التنويعات
        variations = self._detect_variations(features)

        # تحديد المستوى
        level = self._determine_level(variations, features)

        # بناء الكود
        spin_code = self._build_spin_code(position, variations, level)

        # تقدير GOE
        estimated_goe = self._estimate_spin_goe(features, level)

        return {
            'type': MovementType.SPIN.value,
            'code': spin_code,
            'name': self._get_spin_name(spin_code),
            'position': position,
            'level': level,
            'confidence': 0.85,
            'estimated_goe': estimated_goe,
            'features': {
                'speed': features.spin_speed,
                'stability': features.axis_stability,
                'variations': variations,
                'duration': features.duration
            }
        }

    def _detect_position(self, body_position: str) -> str:
        """كشف الوضعية"""
        position_map = {
            'upright': 'USp',
            'sit': 'SSp',
            'camel': 'CSp',
            'flying': 'FSp',
            'combination': 'CoSp'
        }
        return position_map.get(body_position, 'USp')

    def _detect_variations(self, features: MovementFeatures) -> List[str]:
        """كشف التنويعات"""
        variations = []

        if features.leg_extension > 0.8:
            variations.append('extended_leg')

        if features.arm_position > 0.7:
            variations.append('arm_variation')

        if features.spin_speed > 3.0:
            variations.append('fast_spin')

        if features.complexity > 0.8:
            variations.append('difficult_variation')

        return variations

    def _determine_level(self, variations: List[str], features: MovementFeatures) -> int:
        """تحديد المستوى (1-4)"""
        level = 1

        # كل تنويعة ترفع المستوى
        level += min(3, len(variations))

        # السرعة العالية
        if features.spin_speed > 3.5:
            level += 1

        # الثبات
        if features.axis_stability > 0.9:
            level += 1

        return min(4, max(1, level))

    def _build_spin_code(self, position: str, variations: List[str], level: int) -> str:
        """بناء كود الدوران"""
        code = position

        # إضافة المستوى
        code += str(level)

        return code

    def _estimate_spin_goe(self, features: MovementFeatures, level: int) -> int:
        """تقدير GOE للدوران"""
        goe = 0

        # السرعة
        if features.spin_speed > 3.5:
            goe += 2
        elif features.spin_speed > 3.0:
            goe += 1

        # الثبات
        if features.axis_stability > 0.9:
            goe += 1
        elif features.axis_stability < 0.7:
            goe -= 1

        # المستوى
        if level == 4:
            goe += 1

        return max(-5, min(5, goe))

    def _get_spin_name(self, code: str) -> str:
        """الحصول على اسم الدوران"""
        base_names = {
            'USp': 'Upright Spin',
            'SSp': 'Sit Spin',
            'CSp': 'Camel Spin',
            'FSp': 'Flying Spin',
            'CoSp': 'Combination Spin'
        }

        base = code[:3] if code.startswith('Co') else code[:3]
        level = code[-1] if code[-1].isdigit() else ''

        name = base_names.get(base, code)
        if level:
            name += f' Level {level}'

        return name


class StepSequenceDetector:
    """كاشف تسلسلات الخطوات"""

    def detect_step_pattern(self, features: MovementFeatures) -> Dict:
        """كشف نمط الخطوات"""

        # تحديد المستوى
        level = self._determine_step_level(features)

        # تحديد النوع
        seq_type = 'StSq' if features.complexity > 0.7 else 'ChSq'

        return {
            'type': MovementType.STEP_SEQUENCE.value,
            'code': f'{seq_type}{level}',
            'name': f'Step Sequence Level {level}' if seq_type == 'StSq' else f'Choreographic Sequence Level {level}',
            'level': level,
            'confidence': 0.8,
            'estimated_goe': self._estimate_step_goe(features),
            'features': {
                'complexity': features.complexity,
                'speed': features.horizontal_velocity,
                'duration': features.duration
            }
        }

    def _determine_step_level(self, features: MovementFeatures) -> int:
        """تحديد مستوى الخطوات"""
        if features.complexity > 0.9:
            return 4
        elif features.complexity > 0.75:
            return 3
        elif features.complexity > 0.6:
            return 2
        else:
            return 1

    def _estimate_step_goe(self, features: MovementFeatures) -> int:
        """تقدير GOE للخطوات"""
        goe = 0

        if features.complexity > 0.85:
            goe += 2
        if features.horizontal_velocity > 2.0:
            goe += 1

        return max(-5, min(5, goe))
