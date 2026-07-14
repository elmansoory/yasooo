"""
محرك التدريب - Training Engine
يقوم بتدريب نماذج التعرف على الحركات باستخدام بيانات الوضعيات
"""
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
import pickle
from pathlib import Path

from .movement_classifier import MovementFeatures, MovementClassifier


@dataclass
class TrainingDataPoint:
    """نقطة بيانات تدريب واحدة"""
    pose_sequence: List[Dict]  # تسلسل الوضعيات
    features: MovementFeatures  # الخصائص المستخرجة
    label: str  # التصنيف الصحيح (مثل: 3A، FCSp4، StSq3)
    metadata: Dict  # معلومات إضافية


class FeatureExtractor:
    """استخراج الخصائص من بيانات الوضعيات"""

    def __init__(self):
        self.frame_rate = 30  # عدد الإطارات في الثانية

    def extract_features(self, pose_sequence: List[Dict]) -> MovementFeatures:
        """استخراج الخصائص من تسلسل الوضعيات"""

        if not pose_sequence:
            return self._get_default_features()

        # حساب الخصائص من تسلسل الوضعيات
        center_of_mass = self._calculate_center_of_mass(pose_sequence)
        velocities = self._calculate_velocities(pose_sequence)
        rotations = self._calculate_rotations(pose_sequence)
        angles = self._calculate_angles(pose_sequence)

        # خصائص القفز
        airtime = self._detect_airtime(pose_sequence)
        takeoff_angle, landing_angle = self._detect_jump_angles(pose_sequence)
        rotation_count = self._count_rotations(pose_sequence)

        # خصائص الدوران
        spin_speed = self._calculate_spin_speed(pose_sequence)
        axis_stability = self._calculate_axis_stability(pose_sequence)
        body_position = self._detect_body_position(pose_sequence)

        # خصائص عامة
        duration = len(pose_sequence) / self.frame_rate
        complexity = self._calculate_complexity(pose_sequence)

        return MovementFeatures(
            center_of_mass_height=center_of_mass['height'],
            body_rotation_angle=rotations['body_angle'],
            leg_extension=angles['leg_extension'],
            arm_position=angles['arm_position'],
            vertical_velocity=velocities['vertical'],
            rotational_velocity=velocities['rotational'],
            horizontal_velocity=velocities['horizontal'],
            airtime=airtime,
            takeoff_angle=takeoff_angle,
            landing_angle=landing_angle,
            rotation_count=rotation_count,
            spin_speed=spin_speed,
            axis_stability=axis_stability,
            body_position=body_position,
            duration=duration,
            complexity=complexity
        )

    def _calculate_center_of_mass(self, poses: List[Dict]) -> Dict:
        """حساب مركز الكتلة"""
        if not poses:
            return {'height': 0.0, 'x': 0.0, 'y': 0.0}

        # مفاتيح نقاط الجسم الرئيسية
        key_points = ['left_hip', 'right_hip', 'left_shoulder', 'right_shoulder']

        heights = []
        for pose in poses:
            if 'landmarks' in pose:
                # حساب متوسط ارتفاع النقاط الرئيسية
                y_coords = []
                for kp in key_points:
                    if kp in pose['landmarks']:
                        y_coords.append(pose['landmarks'][kp]['y'])

                if y_coords:
                    heights.append(np.mean(y_coords))

        return {
            'height': np.mean(heights) if heights else 0.5,
            'x': 0.5,
            'y': np.mean(heights) if heights else 0.5
        }

    def _calculate_velocities(self, poses: List[Dict]) -> Dict:
        """حساب السرعات"""
        if len(poses) < 2:
            return {'vertical': 0.0, 'horizontal': 0.0, 'rotational': 0.0}

        # حساب التغير في الموضع بين الإطارات
        com = [self._calculate_center_of_mass([p]) for p in poses]

        vertical_velocities = []
        horizontal_velocities = []

        for i in range(1, len(com)):
            dt = 1.0 / self.frame_rate
            dy = (com[i]['height'] - com[i-1]['height']) / dt
            dx = (com[i]['x'] - com[i-1]['x']) / dt

            vertical_velocities.append(dy)
            horizontal_velocities.append(dx)

        # السرعة الدورانية من تغير زاوية الجسم
        rotational_velocity = self._calculate_rotational_velocity(poses)

        return {
            'vertical': np.mean(np.abs(vertical_velocities)) if vertical_velocities else 0.0,
            'horizontal': np.mean(np.abs(horizontal_velocities)) if horizontal_velocities else 0.0,
            'rotational': rotational_velocity
        }

    def _calculate_rotations(self, poses: List[Dict]) -> Dict:
        """حساب الدورانات"""
        if not poses:
            return {'body_angle': 0.0}

        # حساب زاوية الجسم من موضع الكتفين
        angles = []
        for pose in poses:
            if 'landmarks' in pose:
                left_shoulder = pose['landmarks'].get('left_shoulder')
                right_shoulder = pose['landmarks'].get('right_shoulder')

                if left_shoulder and right_shoulder:
                    dx = right_shoulder['x'] - left_shoulder['x']
                    dy = right_shoulder['y'] - left_shoulder['y']
                    angle = np.arctan2(dy, dx) * 180 / np.pi
                    angles.append(angle)

        return {'body_angle': np.mean(angles) if angles else 0.0}

    def _calculate_angles(self, poses: List[Dict]) -> Dict:
        """حساب الزوايا"""
        if not poses:
            return {'leg_extension': 0.0, 'arm_position': 0.0}

        # امتداد الساق
        leg_extensions = []
        arm_positions = []

        for pose in poses:
            if 'landmarks' in pose:
                # امتداد الساق من المسافة بين الركبة والكاحل
                left_knee = pose['landmarks'].get('left_knee')
                left_ankle = pose['landmarks'].get('left_ankle')

                if left_knee and left_ankle:
                    dx = left_ankle['x'] - left_knee['x']
                    dy = left_ankle['y'] - left_knee['y']
                    extension = np.sqrt(dx**2 + dy**2)
                    leg_extensions.append(extension)

                # موضع الذراع
                left_shoulder = pose['landmarks'].get('left_shoulder')
                left_wrist = pose['landmarks'].get('left_wrist')

                if left_shoulder and left_wrist:
                    dx = left_wrist['x'] - left_shoulder['x']
                    dy = left_wrist['y'] - left_shoulder['y']
                    arm_height = abs(dy)
                    arm_positions.append(arm_height)

        return {
            'leg_extension': np.mean(leg_extensions) if leg_extensions else 0.5,
            'arm_position': np.mean(arm_positions) if arm_positions else 0.5
        }

    def _detect_airtime(self, poses: List[Dict]) -> float:
        """كشف الوقت في الهواء"""
        if len(poses) < 2:
            return 0.0

        # الكشف عن الإطارات التي لا تلامس فيها القدم الأرض
        com = [self._calculate_center_of_mass([p])['height'] for p in poses]

        # عتبة الارتفاع للكشف عن القفز
        ground_level = min(com) if com else 0.0
        threshold = ground_level + 0.1

        airborne_frames = sum(1 for h in com if h > threshold)
        airtime = airborne_frames / self.frame_rate

        return airtime

    def _detect_jump_angles(self, poses: List[Dict]) -> Tuple[float, float]:
        """كشف زوايا الإقلاع والهبوط"""
        if len(poses) < 3:
            return (0.0, 0.0)

        # تحديد نقطة الإقلاع والهبوط من ارتفاع مركز الكتلة
        heights = [self._calculate_center_of_mass([p])['height'] for p in poses]

        # الإقلاع: التغير الأكبر في الارتفاع في البداية
        takeoff_idx = np.argmax(np.diff(heights[:len(heights)//2]))
        takeoff_angle = np.arctan2(heights[takeoff_idx+1] - heights[takeoff_idx],
                                   1.0 / self.frame_rate) * 180 / np.pi

        # الهبوط: التغير الأكبر في النزول في النهاية
        landing_idx = len(heights)//2 + np.argmin(np.diff(heights[len(heights)//2:]))
        landing_angle = 90 - abs(np.arctan2(heights[landing_idx+1] - heights[landing_idx],
                                            1.0 / self.frame_rate) * 180 / np.pi)

        return (abs(takeoff_angle), abs(landing_angle))

    def _count_rotations(self, poses: List[Dict]) -> float:
        """عد الدورات"""
        if len(poses) < 2:
            return 0.0

        # حساب الدورات من التغير في زاوية الجسم
        angles = []
        for pose in poses:
            if 'landmarks' in pose:
                left_shoulder = pose['landmarks'].get('left_shoulder')
                right_shoulder = pose['landmarks'].get('right_shoulder')

                if left_shoulder and right_shoulder:
                    dx = right_shoulder['x'] - left_shoulder['x']
                    dy = right_shoulder['y'] - left_shoulder['y']
                    angle = np.arctan2(dy, dx)
                    angles.append(angle)

        if len(angles) < 2:
            return 0.0

        # عد عدد المرات التي تعبر فيها الزاوية 360 درجة
        total_rotation = 0
        for i in range(1, len(angles)):
            diff = angles[i] - angles[i-1]
            # معالجة الانتقال من -π إلى π
            if diff > np.pi:
                diff -= 2 * np.pi
            elif diff < -np.pi:
                diff += 2 * np.pi
            total_rotation += diff

        # تحويل إلى دورات
        rotations = abs(total_rotation) / (2 * np.pi)
        return rotations

    def _calculate_spin_speed(self, poses: List[Dict]) -> float:
        """حساب سرعة الدوران (دورات/ثانية)"""
        rotations = self._count_rotations(poses)
        duration = len(poses) / self.frame_rate
        return rotations / duration if duration > 0 else 0.0

    def _calculate_rotational_velocity(self, poses: List[Dict]) -> float:
        """حساب السرعة الدورانية"""
        if len(poses) < 2:
            return 0.0

        angles = []
        for pose in poses:
            if 'landmarks' in pose:
                left_shoulder = pose['landmarks'].get('left_shoulder')
                right_shoulder = pose['landmarks'].get('right_shoulder')

                if left_shoulder and right_shoulder:
                    dx = right_shoulder['x'] - left_shoulder['x']
                    dy = right_shoulder['y'] - left_shoulder['y']
                    angle = np.arctan2(dy, dx)
                    angles.append(angle)

        if len(angles) < 2:
            return 0.0

        angular_velocities = []
        for i in range(1, len(angles)):
            dt = 1.0 / self.frame_rate
            d_angle = angles[i] - angles[i-1]
            angular_velocity = d_angle / dt
            angular_velocities.append(abs(angular_velocity))

        return np.mean(angular_velocities) if angular_velocities else 0.0

    def _calculate_axis_stability(self, poses: List[Dict]) -> float:
        """حساب ثبات محور الدوران"""
        if not poses:
            return 0.0

        # حساب تغير موضع مركز الكتلة
        com_positions = [self._calculate_center_of_mass([p]) for p in poses]

        x_positions = [c['x'] for c in com_positions]
        y_positions = [c['y'] for c in com_positions]

        # الثبات = 1 - (التباين في الموضع)
        x_variance = np.var(x_positions) if x_positions else 0.0
        y_variance = np.var(y_positions) if y_positions else 0.0
        total_variance = x_variance + y_variance

        stability = max(0.0, 1.0 - total_variance * 10)
        return min(1.0, stability)

    def _detect_body_position(self, poses: List[Dict]) -> str:
        """كشف وضعية الجسم"""
        if not poses:
            return 'upright'

        # تحليل وضعية الجسم من علاقة الأطراف
        positions = []
        for pose in poses:
            if 'landmarks' in pose:
                # الحصول على نقاط رئيسية
                hip = pose['landmarks'].get('left_hip')
                knee = pose['landmarks'].get('left_knee')
                shoulder = pose['landmarks'].get('left_shoulder')

                if hip and knee and shoulder:
                    # حساب زاوية الركبة
                    knee_angle = abs(knee['y'] - hip['y'])

                    # تحديد الوضعية
                    if knee_angle < 0.2:
                        positions.append('sit')
                    elif abs(shoulder['y'] - hip['y']) < 0.1:
                        positions.append('camel')
                    else:
                        positions.append('upright')

        # الوضعية الأكثر شيوعاً
        if positions:
            return max(set(positions), key=positions.count)
        return 'upright'

    def _calculate_complexity(self, poses: List[Dict]) -> float:
        """حساب تعقيد الحركة"""
        if not poses:
            return 0.0

        # التعقيد من:
        # 1. تنوع الحركة
        # 2. السرعة
        # 3. عدد التغيرات في الاتجاه

        velocities = self._calculate_velocities(poses)
        rotations = self._count_rotations(poses)

        # متوسط السرعة
        avg_velocity = (velocities['vertical'] +
                       velocities['horizontal'] +
                       velocities['rotational']) / 3

        # عدد التغيرات في الاتجاه
        com_positions = [self._calculate_center_of_mass([p]) for p in poses]
        direction_changes = 0
        for i in range(2, len(com_positions)):
            dx1 = com_positions[i-1]['x'] - com_positions[i-2]['x']
            dx2 = com_positions[i]['x'] - com_positions[i-1]['x']
            if dx1 * dx2 < 0:  # تغير في الاتجاه
                direction_changes += 1

        complexity = min(1.0, (avg_velocity * 0.3 +
                              rotations * 0.4 +
                              direction_changes * 0.02))

        return complexity

    def _get_default_features(self) -> MovementFeatures:
        """الحصول على خصائص افتراضية"""
        return MovementFeatures(
            center_of_mass_height=0.5,
            body_rotation_angle=0.0,
            leg_extension=0.5,
            arm_position=0.5,
            vertical_velocity=0.0,
            rotational_velocity=0.0,
            horizontal_velocity=0.0,
            airtime=0.0,
            takeoff_angle=0.0,
            landing_angle=0.0,
            rotation_count=0.0,
            spin_speed=0.0,
            axis_stability=0.5,
            body_position='upright',
            duration=0.0,
            complexity=0.0
        )


class TrainingEngine:
    """محرك التدريب الرئيسي"""

    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.feature_extractor = FeatureExtractor()
        self.classifier = MovementClassifier()

        self.training_data: List[TrainingDataPoint] = []
        self.validation_data: List[TrainingDataPoint] = []

    def add_training_sample(self, pose_sequence: List[Dict], label: str,
                          metadata: Optional[Dict] = None):
        """إضافة عينة تدريب"""
        features = self.feature_extractor.extract_features(pose_sequence)

        data_point = TrainingDataPoint(
            pose_sequence=pose_sequence,
            features=features,
            label=label,
            metadata=metadata or {}
        )

        self.training_data.append(data_point)

    def load_training_data(self, data_file: str):
        """تحميل بيانات التدريب من ملف"""
        with open(data_file, 'r') as f:
            data = json.load(f)

        for sample in data['samples']:
            self.add_training_sample(
                pose_sequence=sample['pose_sequence'],
                label=sample['label'],
                metadata=sample.get('metadata', {})
            )

        print(f"تم تحميل {len(self.training_data)} عينة تدريب")

    def split_data(self, validation_ratio: float = 0.2):
        """تقسيم البيانات إلى تدريب وتحقق"""
        np.random.shuffle(self.training_data)

        split_idx = int(len(self.training_data) * (1 - validation_ratio))
        self.validation_data = self.training_data[split_idx:]
        self.training_data = self.training_data[:split_idx]

        print(f"بيانات التدريب: {len(self.training_data)}")
        print(f"بيانات التحقق: {len(self.validation_data)}")

    def evaluate(self, data_points: Optional[List[TrainingDataPoint]] = None) -> Dict:
        """تقييم أداء النموذج"""
        if data_points is None:
            data_points = self.validation_data

        if not data_points:
            return {'error': 'لا توجد بيانات للتقييم'}

        correct = 0
        total = len(data_points)

        predictions = []
        actual_labels = []

        for data_point in data_points:
            # التصنيف
            result = self.classifier.classify_movement(data_point.features)
            predicted_code = result.get('code', '')

            # المقارنة
            if predicted_code == data_point.label:
                correct += 1

            predictions.append(predicted_code)
            actual_labels.append(data_point.label)

        accuracy = correct / total if total > 0 else 0.0

        # حساب الدقة لكل فئة
        category_accuracy = self._calculate_category_accuracy(predictions, actual_labels)

        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'category_accuracy': category_accuracy,
            'predictions': predictions,
            'actual': actual_labels
        }

    def _calculate_category_accuracy(self, predictions: List[str],
                                     actual: List[str]) -> Dict:
        """حساب الدقة لكل فئة"""
        categories = {
            'jumps': [],
            'spins': [],
            'steps': []
        }

        for pred, act in zip(predictions, actual):
            # تحديد الفئة
            if any(j in act for j in ['A', 'Lz', 'F', 'Lo', 'S', 'T']):
                category = 'jumps'
            elif any(s in act for s in ['Sp', 'CoSp']):
                category = 'spins'
            elif 'Sq' in act:
                category = 'steps'
            else:
                continue

            categories[category].append(1 if pred == act else 0)

        return {
            cat: np.mean(results) if results else 0.0
            for cat, results in categories.items()
        }

    def save_model(self, filename: str = "movement_classifier.pkl"):
        """حفظ النموذج"""
        model_path = self.model_dir / filename

        model_data = {
            'classifier': self.classifier,
            'feature_extractor': self.feature_extractor,
            'thresholds': self.classifier.thresholds
        }

        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"تم حفظ النموذج في: {model_path}")

    def load_model(self, filename: str = "movement_classifier.pkl"):
        """تحميل النموذج"""
        model_path = self.model_dir / filename

        if not model_path.exists():
            print(f"النموذج غير موجود: {model_path}")
            return False

        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)

        self.classifier = model_data['classifier']
        self.feature_extractor = model_data['feature_extractor']

        print(f"تم تحميل النموذج من: {model_path}")
        return True

    def generate_report(self) -> str:
        """توليد تقرير التدريب"""
        eval_results = self.evaluate()

        report = f"""
═══════════════════════════════════════════════════════════
   تقرير تدريب نموذج التعرف على الحركات
═══════════════════════════════════════════════════════════

📊 إحصائيات البيانات:
   • عينات التدريب: {len(self.training_data)}
   • عينات التحقق: {len(self.validation_data)}

🎯 نتائج التقييم:
   • الدقة الإجمالية: {eval_results['accuracy']:.2%}
   • التنبؤات الصحيحة: {eval_results['correct']} / {eval_results['total']}

📈 الدقة حسب الفئة:
   • القفزات: {eval_results['category_accuracy']['jumps']:.2%}
   • الدورانات: {eval_results['category_accuracy']['spins']:.2%}
   • الخطوات: {eval_results['category_accuracy']['steps']:.2%}

✅ النموذج جاهز للاستخدام
═══════════════════════════════════════════════════════════
"""
        return report
