"""
كاشف الوضعيات باستخدام MediaPipe
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging

from src.utils.logger import LoggerMixin, log_execution_time


@dataclass
class Landmark:
    """نقطة مفصل واحدة"""
    x: float
    y: float
    z: float
    visibility: float = 1.0


@dataclass
class PoseData:
    """بيانات وضعية كاملة"""
    landmarks: Dict[str, Landmark]
    angles: Dict[str, float] = field(default_factory=dict)
    distances: Dict[str, float] = field(default_factory=dict)
    center_of_mass: Tuple[float, float] = (0.0, 0.0)
    raw_landmarks: Any = None


class PoseDetector(LoggerMixin):
    """كاشف الوضعيات باستخدام MediaPipe"""

    # تعريف نقاط المفاصل الرئيسية
    LANDMARK_NAMES = {
        # الرأس والوجه
        'nose': 0,
        'left_eye_inner': 1,
        'left_eye': 2,
        'left_eye_outer': 3,
        'right_eye_inner': 4,
        'right_eye': 5,
        'right_eye_outer': 6,
        'left_ear': 7,
        'right_ear': 8,
        'mouth_left': 9,
        'mouth_right': 10,

        # الجزء العلوي من الجسم
        'left_shoulder': 11,
        'right_shoulder': 12,
        'left_elbow': 13,
        'right_elbow': 14,
        'left_wrist': 15,
        'right_wrist': 16,

        # اليدين
        'left_pinky': 17,
        'right_pinky': 18,
        'left_index': 19,
        'right_index': 20,
        'left_thumb': 21,
        'right_thumb': 22,

        # الجزء السفلي من الجسم
        'left_hip': 23,
        'right_hip': 24,
        'left_knee': 25,
        'right_knee': 26,
        'left_ankle': 27,
        'right_ankle': 28,

        # القدمين
        'left_heel': 29,
        'right_heel': 30,
        'left_foot_index': 31,
        'right_foot_index': 32,
    }

    # المفاصل الرئيسية للتزلج
    SKATING_KEY_LANDMARKS = [
        'nose',
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle',
        'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index',
    ]

    def __init__(self, config=None):
        """
        Args:
            config: كائن الإعدادات
        """
        self.config = config

        # إعداد MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # إنشاء كاشف الوضعيات
        min_detection_conf = config.POSE_MIN_DETECTION_CONFIDENCE if config else 0.5
        min_tracking_conf = config.POSE_MIN_TRACKING_CONFIDENCE if config else 0.5
        model_complexity = config.POSE_MODEL_COMPLEXITY if config else 2

        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_tracking_conf,
            enable_segmentation=True,
            smooth_landmarks=True
        )

        self.logger.info(
            f"تم تهيئة كاشف الوضعيات: complexity={model_complexity}, "
            f"detection_conf={min_detection_conf}, tracking_conf={min_tracking_conf}"
        )

    @log_execution_time
    def detect(self, frame: np.ndarray) -> Optional[PoseData]:
        """
        كشف الوضعية في إطار واحد

        Args:
            frame: الإطار (BGR format)

        Returns:
            PoseData أو None إذا لم يتم العثور على وضعية
        """
        try:
            # تحويل BGR إلى RGB
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # معالجة الصورة
            results = self.pose.process(image_rgb)

            if not results.pose_landmarks:
                return None

            # استخراج نقاط المفاصل
            landmarks = self._extract_landmarks(results.pose_landmarks, frame.shape)

            # حساب الزوايا
            angles = self._calculate_all_angles(landmarks)

            # حساب المسافات
            distances = self._calculate_all_distances(landmarks)

            # حساب مركز الكتلة
            center_of_mass = self._calculate_center_of_mass(landmarks)

            return PoseData(
                landmarks=landmarks,
                angles=angles,
                distances=distances,
                center_of_mass=center_of_mass,
                raw_landmarks=results.pose_landmarks
            )

        except Exception as e:
            self.logger.error(f"خطأ في كشف الوضعية: {e}")
            return None

    def _extract_landmarks(
        self,
        pose_landmarks,
        frame_shape: Tuple[int, int, int]
    ) -> Dict[str, Landmark]:
        """
        استخراج نقاط المفاصل

        Args:
            pose_landmarks: نتائج MediaPipe
            frame_shape: شكل الإطار (height, width, channels)

        Returns:
            قاموس المفاصل
        """
        height, width, _ = frame_shape
        landmarks = {}

        for name, idx in self.LANDMARK_NAMES.items():
            landmark = pose_landmarks.landmark[idx]

            landmarks[name] = Landmark(
                x=landmark.x * width,
                y=landmark.y * height,
                z=landmark.z * width,  # تطبيع z بناءً على العرض
                visibility=landmark.visibility
            )

        return landmarks

    def _calculate_all_angles(self, landmarks: Dict[str, Landmark]) -> Dict[str, float]:
        """حساب جميع الزوايا الرئيسية"""
        angles = {}

        # زوايا الذراعين
        angles['left_elbow'] = self._calculate_angle(
            landmarks['left_shoulder'],
            landmarks['left_elbow'],
            landmarks['left_wrist']
        )

        angles['right_elbow'] = self._calculate_angle(
            landmarks['right_shoulder'],
            landmarks['right_elbow'],
            landmarks['right_wrist']
        )

        angles['left_shoulder'] = self._calculate_angle(
            landmarks['left_hip'],
            landmarks['left_shoulder'],
            landmarks['left_elbow']
        )

        angles['right_shoulder'] = self._calculate_angle(
            landmarks['right_hip'],
            landmarks['right_shoulder'],
            landmarks['right_elbow']
        )

        # زوايا الأرجل
        angles['left_knee'] = self._calculate_angle(
            landmarks['left_hip'],
            landmarks['left_knee'],
            landmarks['left_ankle']
        )

        angles['right_knee'] = self._calculate_angle(
            landmarks['right_hip'],
            landmarks['right_knee'],
            landmarks['right_ankle']
        )

        angles['left_hip'] = self._calculate_angle(
            landmarks['left_shoulder'],
            landmarks['left_hip'],
            landmarks['left_knee']
        )

        angles['right_hip'] = self._calculate_angle(
            landmarks['right_shoulder'],
            landmarks['right_hip'],
            landmarks['right_knee']
        )

        # زاوية الكاحل
        angles['left_ankle'] = self._calculate_angle(
            landmarks['left_knee'],
            landmarks['left_ankle'],
            landmarks['left_foot_index']
        )

        angles['right_ankle'] = self._calculate_angle(
            landmarks['right_knee'],
            landmarks['right_ankle'],
            landmarks['right_foot_index']
        )

        # زاوية الجذع
        angles['torso'] = self._calculate_angle(
            landmarks['left_hip'],
            landmarks['left_shoulder'],
            landmarks['right_shoulder']
        )

        # زاوية الميل الأمامي/الخلفي للجسم
        hip_center = self._midpoint(landmarks['left_hip'], landmarks['right_hip'])
        shoulder_center = self._midpoint(landmarks['left_shoulder'], landmarks['right_shoulder'])

        # حساب زاوية الميل من العمودي
        dx = shoulder_center.x - hip_center.x
        dy = shoulder_center.y - hip_center.y
        angles['body_lean'] = np.degrees(np.arctan2(dx, dy))

        return angles

    @staticmethod
    def _calculate_angle(p1: Landmark, p2: Landmark, p3: Landmark) -> float:
        """
        حساب الزاوية بين ثلاث نقاط

        Args:
            p1: النقطة الأولى
            p2: نقطة المنتصف (الزاوية)
            p3: النقطة الثالثة

        Returns:
            الزاوية بالدرجات
        """
        # المتجهات
        v1 = np.array([p1.x - p2.x, p1.y - p2.y])
        v2 = np.array([p3.x - p2.x, p3.y - p2.y])

        # حساب الزاوية
        cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def _calculate_all_distances(self, landmarks: Dict[str, Landmark]) -> Dict[str, float]:
        """حساب جميع المسافات الرئيسية"""
        distances = {}

        # عرض الكتفين
        distances['shoulders_width'] = self._euclidean_distance(
            landmarks['left_shoulder'],
            landmarks['right_shoulder']
        )

        # عرض الوركين
        distances['hips_width'] = self._euclidean_distance(
            landmarks['left_hip'],
            landmarks['right_hip']
        )

        # طول الذراع الأيسر
        distances['left_arm_length'] = (
            self._euclidean_distance(landmarks['left_shoulder'], landmarks['left_elbow']) +
            self._euclidean_distance(landmarks['left_elbow'], landmarks['left_wrist'])
        )

        # طول الذراع الأيمن
        distances['right_arm_length'] = (
            self._euclidean_distance(landmarks['right_shoulder'], landmarks['right_elbow']) +
            self._euclidean_distance(landmarks['right_elbow'], landmarks['right_wrist'])
        )

        # طول الساق اليسرى
        distances['left_leg_length'] = (
            self._euclidean_distance(landmarks['left_hip'], landmarks['left_knee']) +
            self._euclidean_distance(landmarks['left_knee'], landmarks['left_ankle'])
        )

        # طول الساق اليمنى
        distances['right_leg_length'] = (
            self._euclidean_distance(landmarks['right_hip'], landmarks['right_knee']) +
            self._euclidean_distance(landmarks['right_knee'], landmarks['right_ankle'])
        )

        # ارتفاع الجسم (من الأنف إلى أدنى نقطة في القدمين)
        min_foot_y = min(
            landmarks['left_ankle'].y,
            landmarks['right_ankle'].y,
            landmarks['left_heel'].y,
            landmarks['right_heel'].y
        )
        distances['body_height'] = abs(landmarks['nose'].y - min_foot_y)

        # طول الجذع
        hip_center = self._midpoint(landmarks['left_hip'], landmarks['right_hip'])
        shoulder_center = self._midpoint(landmarks['left_shoulder'], landmarks['right_shoulder'])
        distances['torso_length'] = self._euclidean_distance_coords(
            shoulder_center.x, shoulder_center.y,
            hip_center.x, hip_center.y
        )

        # المسافة بين القدمين
        distances['feet_distance'] = self._euclidean_distance(
            landmarks['left_ankle'],
            landmarks['right_ankle']
        )

        return distances

    @staticmethod
    def _euclidean_distance(p1: Landmark, p2: Landmark) -> float:
        """حساب المسافة الإقليدية بين نقطتين"""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        dz = p1.z - p2.z
        return np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

    @staticmethod
    def _euclidean_distance_coords(x1: float, y1: float, x2: float, y2: float) -> float:
        """حساب المسافة الإقليدية من الإحداثيات"""
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    @staticmethod
    def _midpoint(p1: Landmark, p2: Landmark) -> Landmark:
        """حساب نقطة المنتصف بين نقطتين"""
        return Landmark(
            x=(p1.x + p2.x) / 2,
            y=(p1.y + p2.y) / 2,
            z=(p1.z + p2.z) / 2,
            visibility=(p1.visibility + p2.visibility) / 2
        )

    def _calculate_center_of_mass(self, landmarks: Dict[str, Landmark]) -> Tuple[float, float]:
        """
        حساب مركز الكتلة التقريبي

        Returns:
            (x, y) إحداثيات مركز الكتلة
        """
        # استخدام المفاصل الرئيسية فقط
        key_points = [
            landmarks['left_shoulder'],
            landmarks['right_shoulder'],
            landmarks['left_hip'],
            landmarks['right_hip'],
        ]

        total_x = sum(p.x for p in key_points)
        total_y = sum(p.y for p in key_points)

        center_x = total_x / len(key_points)
        center_y = total_y / len(key_points)

        return (center_x, center_y)

    def is_balanced(self, pose_data: PoseData, threshold: float = 0.1) -> bool:
        """
        تحديد ما إذا كان المتزلج متوازناً

        Args:
            pose_data: بيانات الوضعية
            threshold: عتبة عدم التوازن (نسبة من عرض الجسم)

        Returns:
            True إذا كان متوازناً
        """
        com_x, com_y = pose_data.center_of_mass

        # حساب مركز القاعدة (القدمين)
        left_foot = pose_data.landmarks['left_ankle']
        right_foot = pose_data.landmarks['right_ankle']

        base_center_x = (left_foot.x + right_foot.x) / 2

        # حساب الانحراف
        body_width = pose_data.distances.get('shoulders_width', 100)
        offset = abs(com_x - base_center_x)

        return offset < (body_width * threshold)

    def draw_pose(
        self,
        frame: np.ndarray,
        pose_data: PoseData,
        draw_landmarks: bool = True,
        draw_connections: bool = True,
        draw_angles: bool = False
    ) -> np.ndarray:
        """
        رسم الوضعية على الإطار

        Args:
            frame: الإطار الأصلي
            pose_data: بيانات الوضعية
            draw_landmarks: رسم نقاط المفاصل
            draw_connections: رسم الخطوط بين المفاصل
            draw_angles: رسم الزوايا

        Returns:
            الإطار مع الرسم
        """
        annotated_frame = frame.copy()

        if pose_data.raw_landmarks is None:
            return annotated_frame

        # رسم الوصلات والنقاط
        if draw_connections:
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                pose_data.raw_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
        elif draw_landmarks:
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                pose_data.raw_landmarks,
                None,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )

        # رسم الزوايا
        if draw_angles:
            for angle_name, angle_value in pose_data.angles.items():
                if angle_name in ['left_knee', 'right_knee', 'left_elbow', 'right_elbow']:
                    # الحصول على الموقع للنص
                    if angle_name in pose_data.landmarks:
                        landmark = pose_data.landmarks[angle_name]
                        position = (int(landmark.x), int(landmark.y))

                        # رسم النص
                        cv2.putText(
                            annotated_frame,
                            f"{angle_value:.1f}°",
                            position,
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 0),
                            2
                        )

        # رسم مركز الكتلة
        com_x, com_y = pose_data.center_of_mass
        cv2.circle(annotated_frame, (int(com_x), int(com_y)), 5, (0, 255, 255), -1)

        return annotated_frame

    def extract_pose_features(self, pose_data: PoseData) -> np.ndarray:
        """
        استخراج ميزات الوضعية للتصنيف

        Args:
            pose_data: بيانات الوضعية

        Returns:
            مصفوفة الميزات
        """
        features = []

        # إضافة الزوايا
        for angle_name in sorted(pose_data.angles.keys()):
            features.append(pose_data.angles[angle_name])

        # إضافة المسافات المعيارية
        body_height = pose_data.distances.get('body_height', 1.0)

        for dist_name in sorted(pose_data.distances.keys()):
            if dist_name != 'body_height':
                # تطبيع المسافات بناءً على ارتفاع الجسم
                normalized_dist = pose_data.distances[dist_name] / body_height
                features.append(normalized_dist)

        # إضافة مركز الكتلة المعياري
        com_x, com_y = pose_data.center_of_mass
        features.extend([com_x / body_height, com_y / body_height])

        return np.array(features)

    def close(self):
        """إغلاق الكاشف وتحرير الموارد"""
        if self.pose:
            self.pose.close()
            self.pose = None
            self.logger.info("تم إغلاق كاشف الوضعيات")

    def __del__(self):
        """Destructor"""
        self.close()
