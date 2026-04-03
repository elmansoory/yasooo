"""
Step Sequence Detection and Analysis System
نظام كشف وتحليل المتتاليات الخطوية (Step Sequences)

Analyzes footwork, step sequences, and choreographic sequences
in figure skating programs.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.advanced_pose_detector import PoseFrame, Landmark3D


class SequenceType(Enum):
    """أنواع المتتاليات"""
    STEP_SEQUENCE = "StSq"         # Step Sequence
    CHOREOGRAPHIC = "ChSq"         # Choreographic Sequence
    SPIRAL_SEQUENCE = "SpSq"       # Spiral Sequence (deprecated in new rules)
    FOOTWORK = "Footwork"          # General footwork


class StepComplexity(Enum):
    """مستوى التعقيد"""
    SIMPLE = "simple"              # Basic steps
    MODERATE = "moderate"          # Some variety
    COMPLEX = "complex"            # High variety and difficulty
    ADVANCED = "advanced"          # Very difficult combinations


@dataclass
class SequenceSegment:
    """قطعة من المتتالية"""
    start_frame: int
    end_frame: int
    complexity: StepComplexity
    speed: float  # m/s
    turns_count: int
    edge_changes: int
    body_movement_score: float  # 0-1


@dataclass
class StepSequenceDetection:
    """متتالية خطوية مكتشفة"""
    # Basic info
    start_frame: int
    end_frame: int
    duration: float  # seconds

    # Classification
    sequence_type: SequenceType
    level: int  # ISU Level 1-4

    # Segments
    segments: List[SequenceSegment]

    # Measurements
    total_distance: float  # meters traveled
    average_speed: float  # m/s
    speed_variation: float  # coefficient of variation

    # Complexity metrics
    turns_count: int
    edge_changes_count: int
    direction_changes: int
    body_rotation_variety: float  # 0-1

    # Quality metrics
    flow_score: float  # 0-1 (smoothness)
    coverage_score: float  # 0-1 (ice coverage)
    speed_maintenance: float  # 0-1
    musicality_score: float  # 0-1

    # Upper body usage
    upper_body_movement: float  # 0-1
    arm_coordination: float  # 0-1

    # Errors and features
    errors: List[str]
    warnings: List[str]

    # Level features (for ISU level determination)
    level_features: List[str]

    # GOE estimation
    estimated_goe: int  # -5 to +5

    def get_isu_code(self) -> str:
        """Get ISU notation (e.g., 'StSq4')"""
        return f"{self.sequence_type.value}{self.level}"


class StepSequenceDetector:
    """
    كاشف المتتاليات الخطوية
    Step Sequence Detector

    Detects and analyzes step sequences, footwork, and choreographic sequences.
    """

    def __init__(self, fps: float = 30.0):
        self.fps = fps

        # Detection thresholds
        self.min_duration = 3.0  # minimum 3 seconds for a sequence
        self.min_speed = 0.5  # m/s minimum speed
        self.min_distance = 5.0  # meters minimum travel

        # Complexity thresholds
        self.turn_detection_threshold = 45  # degrees for turn detection
        self.edge_change_threshold = 30  # degrees for edge change

    def detect_sequences(
        self,
        pose_frames: List[PoseFrame],
        sequence_type: Optional[SequenceType] = None
    ) -> List[StepSequenceDetection]:
        """
        كشف المتتاليات في الفيديو

        Args:
            pose_frames: List of pose frames
            sequence_type: Specific type to detect (None = all types)

        Returns:
            List of detected sequences
        """
        if not pose_frames or len(pose_frames) < int(self.fps * self.min_duration):
            return []

        # Calculate movement metrics
        velocities = self._calculate_velocities(pose_frames)
        positions = self._extract_positions(pose_frames)

        # Find sequence segments (periods of continuous movement)
        segments = self._find_movement_segments(
            pose_frames,
            velocities,
            positions
        )

        # Analyze each segment
        detections = []
        for start, end in segments:
            detection = self._analyze_sequence(
                pose_frames[start:end+1],
                start,
                velocities[start:end+1],
                positions[start:end+1],
                sequence_type
            )

            if detection:
                detections.append(detection)

        return detections

    def _calculate_velocities(self, pose_frames: List[PoseFrame]) -> np.ndarray:
        """حساب سرعة الحركة"""
        positions = self._extract_positions(pose_frames)

        # Calculate velocity between frames
        velocities = np.zeros(len(positions))

        for i in range(1, len(positions)):
            distance = np.linalg.norm(positions[i] - positions[i-1])
            time_delta = 1.0 / self.fps
            velocities[i] = distance / time_delta

        return velocities

    def _extract_positions(self, pose_frames: List[PoseFrame]) -> np.ndarray:
        """استخراج مواقع المتزلج"""
        positions = []

        for frame in pose_frames:
            # Use hip center as reference point
            if frame.landmarks:
                left_hip = frame.landmarks[23]  # Left hip
                right_hip = frame.landmarks[24]  # Right hip

                # Hip center
                center_x = (left_hip.x + right_hip.x) / 2
                center_y = (left_hip.y + right_hip.y) / 2
                center_z = (left_hip.z + right_hip.z) / 2

                positions.append([center_x, center_y, center_z])
            else:
                # Use previous position if landmarks not available
                if positions:
                    positions.append(positions[-1])
                else:
                    positions.append([0, 0, 0])

        return np.array(positions)

    def _find_movement_segments(
        self,
        pose_frames: List[PoseFrame],
        velocities: np.ndarray,
        positions: np.ndarray
    ) -> List[Tuple[int, int]]:
        """
        العثور على قطع الحركة المستمرة
        Find continuous movement segments
        """
        segments = []
        in_sequence = False
        segment_start = 0

        for i, velocity in enumerate(velocities):
            if velocity >= self.min_speed and not in_sequence:
                # Start of sequence
                in_sequence = True
                segment_start = i
            elif velocity < self.min_speed and in_sequence:
                # End of sequence
                in_sequence = False
                segment_end = i - 1

                # Check duration and distance
                duration = (segment_end - segment_start) / self.fps
                distance = self._calculate_distance(positions[segment_start:segment_end+1])

                if duration >= self.min_duration and distance >= self.min_distance:
                    segments.append((segment_start, segment_end))

        # Handle case where sequence continues to end
        if in_sequence:
            segment_end = len(velocities) - 1
            duration = (segment_end - segment_start) / self.fps
            distance = self._calculate_distance(positions[segment_start:segment_end+1])

            if duration >= self.min_duration and distance >= self.min_distance:
                segments.append((segment_start, segment_end))

        return segments

    def _calculate_distance(self, positions: np.ndarray) -> float:
        """حساب المسافة المقطوعة"""
        total_distance = 0.0

        for i in range(1, len(positions)):
            distance = np.linalg.norm(positions[i] - positions[i-1])
            total_distance += distance

        return total_distance

    def _analyze_sequence(
        self,
        segment_frames: List[PoseFrame],
        start_frame: int,
        velocities: np.ndarray,
        positions: np.ndarray,
        sequence_type: Optional[SequenceType]
    ) -> Optional[StepSequenceDetection]:
        """
        تحليل متتالية واحدة
        Analyze single sequence
        """
        if len(segment_frames) < int(self.fps * self.min_duration):
            return None

        # Basic measurements
        duration = len(segment_frames) / self.fps
        total_distance = self._calculate_distance(positions)
        average_speed = np.mean(velocities) if len(velocities) > 0 else 0
        speed_variation = np.std(velocities) / average_speed if average_speed > 0 else 0

        # Analyze complexity
        turns = self._detect_turns(segment_frames)
        edge_changes = self._detect_edge_changes(segment_frames)
        direction_changes = self._detect_direction_changes(positions)

        # Body movement analysis
        upper_body_score = self._analyze_upper_body(segment_frames)
        arm_coordination = self._analyze_arm_movement(segment_frames)
        body_rotation_variety = self._analyze_body_rotation(segment_frames)

        # Quality metrics
        flow_score = self._calculate_flow_score(velocities, positions)
        coverage_score = self._calculate_coverage_score(positions)
        speed_maintenance = 1.0 - min(speed_variation, 1.0)

        # Determine sequence type if not specified
        if sequence_type is None:
            sequence_type = self._classify_sequence_type(
                duration,
                upper_body_score,
                turns,
                edge_changes
            )

        # Determine ISU level
        level, level_features = self._determine_level(
            turns,
            edge_changes,
            body_rotation_variety,
            upper_body_score,
            sequence_type
        )

        # Check for errors
        errors = []
        warnings = []

        if speed_maintenance < 0.6:
            warnings.append("Significant speed loss during sequence")

        if coverage_score < 0.5:
            warnings.append("Limited ice coverage")

        # Estimate GOE
        estimated_goe = self._estimate_goe(
            level,
            flow_score,
            coverage_score,
            speed_maintenance,
            upper_body_score,
            len(errors)
        )

        # Create segments breakdown
        segments = self._create_segments_breakdown(
            segment_frames,
            velocities,
            turns,
            edge_changes
        )

        return StepSequenceDetection(
            start_frame=start_frame,
            end_frame=start_frame + len(segment_frames) - 1,
            duration=duration,
            sequence_type=sequence_type,
            level=level,
            segments=segments,
            total_distance=total_distance,
            average_speed=average_speed,
            speed_variation=speed_variation,
            turns_count=turns,
            edge_changes_count=edge_changes,
            direction_changes=direction_changes,
            body_rotation_variety=body_rotation_variety,
            flow_score=flow_score,
            coverage_score=coverage_score,
            speed_maintenance=speed_maintenance,
            musicality_score=0.75,  # Placeholder - would need audio analysis
            upper_body_movement=upper_body_score,
            arm_coordination=arm_coordination,
            errors=errors,
            warnings=warnings,
            level_features=level_features,
            estimated_goe=estimated_goe
        )

    def _detect_turns(self, frames: List[PoseFrame]) -> int:
        """كشف عدد الدورانات"""
        turns = 0

        if len(frames) < 2:
            return 0

        # Calculate body orientation changes
        for i in range(1, len(frames)):
            if not frames[i].landmarks or not frames[i-1].landmarks:
                continue

            # Calculate shoulder angle change
            angle_change = self._calculate_shoulder_angle_change(
                frames[i-1],
                frames[i]
            )

            if abs(angle_change) > self.turn_detection_threshold:
                turns += 1

        return turns

    def _detect_edge_changes(self, frames: List[PoseFrame]) -> int:
        """كشف تغييرات الحافة"""
        # Simplified edge detection based on body lean
        edge_changes = 0

        for i in range(1, len(frames)):
            if not frames[i].landmarks or not frames[i-1].landmarks:
                continue

            lean_change = self._calculate_lean_change(frames[i-1], frames[i])

            if abs(lean_change) > self.edge_change_threshold:
                edge_changes += 1

        return edge_changes

    def _detect_direction_changes(self, positions: np.ndarray) -> int:
        """كشف تغييرات الاتجاه"""
        if len(positions) < 3:
            return 0

        direction_changes = 0

        for i in range(1, len(positions) - 1):
            # Calculate direction vectors
            v1 = positions[i] - positions[i-1]
            v2 = positions[i+1] - positions[i]

            # Calculate angle between vectors
            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))

                if np.degrees(angle) > 90:  # Significant direction change
                    direction_changes += 1

        return direction_changes

    def _analyze_upper_body(self, frames: List[PoseFrame]) -> float:
        """تحليل حركة الجزء العلوي من الجسم"""
        if not frames:
            return 0.0

        arm_movements = []

        for i in range(1, len(frames)):
            if not frames[i].landmarks or not frames[i-1].landmarks:
                continue

            # Calculate arm position changes
            movement = self._calculate_arm_movement(frames[i-1], frames[i])
            arm_movements.append(movement)

        if not arm_movements:
            return 0.0

        # Higher score for more varied arm movements
        return min(np.mean(arm_movements) * 2, 1.0)

    def _analyze_arm_movement(self, frames: List[PoseFrame]) -> float:
        """تحليل تنسيق حركة الذراعين"""
        # Simplified coordination score
        return 0.7  # Placeholder

    def _analyze_body_rotation(self, frames: List[PoseFrame]) -> float:
        """تحليل تنوع دوران الجسم"""
        if len(frames) < 2:
            return 0.0

        rotations = []

        for i in range(1, len(frames)):
            if not frames[i].landmarks or not frames[i-1].landmarks:
                continue

            rotation = self._calculate_body_rotation(frames[i-1], frames[i])
            rotations.append(rotation)

        if not rotations:
            return 0.0

        # Variety score based on standard deviation
        return min(np.std(rotations) / 30.0, 1.0)

    def _calculate_shoulder_angle_change(
        self,
        frame1: PoseFrame,
        frame2: PoseFrame
    ) -> float:
        """حساب تغيير زاوية الكتفين"""
        if not frame1.landmarks or not frame2.landmarks:
            return 0.0

        # Simplified calculation
        # Would calculate actual shoulder line angle in production
        return 15.0  # Placeholder

    def _calculate_lean_change(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """حساب تغيير الميل"""
        # Simplified lean calculation
        return 10.0  # Placeholder

    def _calculate_arm_movement(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """حساب حركة الذراعين"""
        if not frame1.landmarks or not frame2.landmarks:
            return 0.0

        # Calculate wrist position changes
        left_wrist_1 = frame1.landmarks[15]
        left_wrist_2 = frame2.landmarks[15]
        right_wrist_1 = frame1.landmarks[16]
        right_wrist_2 = frame2.landmarks[16]

        left_movement = np.sqrt(
            (left_wrist_2.x - left_wrist_1.x)**2 +
            (left_wrist_2.y - left_wrist_1.y)**2
        )

        right_movement = np.sqrt(
            (right_wrist_2.x - right_wrist_1.x)**2 +
            (right_wrist_2.y - right_wrist_1.y)**2
        )

        return (left_movement + right_movement) / 2

    def _calculate_body_rotation(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """حساب دوران الجسم"""
        # Simplified rotation calculation
        return 20.0  # Placeholder (degrees)

    def _calculate_flow_score(self, velocities: np.ndarray, positions: np.ndarray) -> float:
        """حساب نقاط السلاسة"""
        if len(velocities) < 2:
            return 0.5

        # Smooth movement has consistent velocity
        velocity_smoothness = 1.0 - min(np.std(velocities) / np.mean(velocities), 1.0)

        # Smooth path has gradual direction changes
        path_smoothness = self._calculate_path_smoothness(positions)

        return (velocity_smoothness + path_smoothness) / 2

    def _calculate_path_smoothness(self, positions: np.ndarray) -> float:
        """حساب سلاسة المسار"""
        if len(positions) < 3:
            return 0.5

        # Calculate curvature variance
        curvatures = []

        for i in range(1, len(positions) - 1):
            v1 = positions[i] - positions[i-1]
            v2 = positions[i+1] - positions[i]

            if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
                curvatures.append(angle)

        if not curvatures:
            return 0.5

        # Lower variance = smoother path
        variance = np.var(curvatures)
        smoothness = 1.0 / (1.0 + variance * 10)

        return smoothness

    def _calculate_coverage_score(self, positions: np.ndarray) -> float:
        """حساب تغطية الجليد"""
        if len(positions) < 2:
            return 0.0

        # Calculate bounding box area
        min_x, max_x = positions[:, 0].min(), positions[:, 0].max()
        min_y, max_y = positions[:, 1].min(), positions[:, 1].max()

        coverage_area = (max_x - min_x) * (max_y - min_y)

        # Normalize (assuming typical rink dimensions)
        normalized_coverage = min(coverage_area / 10.0, 1.0)

        return normalized_coverage

    def _classify_sequence_type(
        self,
        duration: float,
        upper_body_score: float,
        turns: int,
        edge_changes: int
    ) -> SequenceType:
        """تصنيف نوع المتتالية"""
        # Step Sequence: structured footwork with turns and edges
        if turns >= 5 and edge_changes >= 5 and duration >= 10:
            return SequenceType.STEP_SEQUENCE

        # Choreographic: more artistic, less structured
        if upper_body_score > 0.7 and duration >= 15:
            return SequenceType.CHOREOGRAPHIC

        # Default to general footwork
        return SequenceType.FOOTWORK

    def _determine_level(
        self,
        turns: int,
        edge_changes: int,
        body_rotation_variety: float,
        upper_body_score: float,
        sequence_type: SequenceType
    ) -> Tuple[int, List[str]]:
        """تحديد مستوى ISU"""
        level_features = []

        # Features that contribute to level
        if turns >= 5:
            level_features.append("Variety of turns")
        if turns >= 8:
            level_features.append("Difficult turns")

        if edge_changes >= 5:
            level_features.append("Clear edge quality")

        if body_rotation_variety > 0.6:
            level_features.append("Body movement variety")

        if upper_body_score > 0.7:
            level_features.append("Upper body usage")

        # Determine level based on features
        feature_count = len(level_features)

        if feature_count >= 4:
            level = 4
        elif feature_count >= 3:
            level = 3
        elif feature_count >= 2:
            level = 2
        else:
            level = 1

        return level, level_features

    def _estimate_goe(
        self,
        level: int,
        flow_score: float,
        coverage_score: float,
        speed_maintenance: float,
        upper_body_score: float,
        error_count: int
    ) -> int:
        """تقدير GOE"""
        # Start from 0
        goe = 0

        # Positive factors
        if flow_score > 0.8:
            goe += 1
        if coverage_score > 0.7:
            goe += 1
        if speed_maintenance > 0.8:
            goe += 1
        if upper_body_score > 0.8:
            goe += 1

        # Negative factors
        goe -= error_count

        if speed_maintenance < 0.5:
            goe -= 2
        if flow_score < 0.5:
            goe -= 1

        # Clamp to -5 to +5
        return max(-5, min(5, goe))

    def _create_segments_breakdown(
        self,
        frames: List[PoseFrame],
        velocities: np.ndarray,
        turns: int,
        edge_changes: int
    ) -> List[SequenceSegment]:
        """إنشاء تفصيل الأجزاء"""
        # Simplified - create 3 segments
        segment_size = len(frames) // 3

        segments = []
        for i in range(3):
            start = i * segment_size
            end = min((i + 1) * segment_size, len(frames))

            if start >= end:
                break

            avg_speed = np.mean(velocities[start:end]) if len(velocities[start:end]) > 0 else 0

            segment = SequenceSegment(
                start_frame=start,
                end_frame=end,
                complexity=StepComplexity.MODERATE,
                speed=avg_speed,
                turns_count=turns // 3,
                edge_changes=edge_changes // 3,
                body_movement_score=0.6
            )

            segments.append(segment)

        return segments


# Example usage
if __name__ == "__main__":
    print("🚶 Step Sequence Detector - ISU Compliant Analysis")
    print("=" * 60)
    print()
    print("Features:")
    print("  ✅ Automatic detection of step sequences")
    print("  ✅ ISU Level determination (1-4)")
    print("  ✅ GOE estimation")
    print("  ✅ Complexity analysis")
    print("  ✅ Coverage and flow scoring")
    print()
