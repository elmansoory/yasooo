"""
Spin Detection and Analysis System
نظام كشف وتحليل الدورانات (Spins)
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.advanced_pose_detector import PoseFrame


class SpinType(Enum):
    """أنواع الدورانات"""
    UPRIGHT = "USp"      # Upright Spin
    SIT = "SSp"          # Sit Spin
    CAMEL = "CSp"        # Camel Spin
    LAYBACK = "LSp"      # Layback Spin
    COMBINATION = "CoSp" # Combination Spin
    FLYING = "FSp"       # Flying Spin
    CHANGE = "CCoSp"     # Change Combination Spin
    UNKNOWN = "Sp"


class SpinPosition(Enum):
    """وضعيات الدوران"""
    UPRIGHT = "upright"
    SIT = "sit"
    CAMEL = "camel"
    LAYBACK = "layback"
    BIELLMANN = "biellmann"
    BROKEN_LEG = "broken_leg"


@dataclass
class SpinSegment:
    """قطعة من الدوران في وضعية واحدة"""
    position: SpinPosition
    start_frame: int
    end_frame: int
    rotations: float
    rpm: float
    quality: float  # 0-1


@dataclass
class SpinDetection:
    """دوران مكتشف"""
    # Basic info
    start_frame: int
    end_frame: int
    duration: float

    # Classification
    spin_type: SpinType
    level: int  # 1-4 (ISU Level)

    # Segments (different positions)
    segments: List[SpinSegment]

    # Measurements
    total_rotations: float
    average_rpm: float
    centering_score: float  # 0-1 (traveling vs centered)

    # Quality
    entrance_quality: float
    exit_quality: float
    speed_maintenance: float  # الحفاظ على السرعة
    position_quality: float

    # Features (for level determination)
    features: List[str]  # e.g., "difficult_variation", "change_of_edge"

    # Errors
    errors: List[str]
    warnings: List[str]

    # GOE estimation
    estimated_goe: int

    def get_isu_code(self) -> str:
        """Get ISU notation (e.g., 'CCoSp4')"""
        return f"{self.spin_type.value}{self.level}"


class SpinDetector:
    """
    نظام كشف وتحليل الدورانات
    """

    def __init__(self, fps: float = 30.0):
        self.fps = fps

        # Thresholds
        self.min_rpm = 60  # minimum RPM to count as spin
        self.min_rotations = 3  # minimum total rotations
        self.min_duration = 2.0  # seconds

    def detect_spins(
        self,
        pose_frames: List[PoseFrame],
        min_rpm: Optional[float] = None
    ) -> List[SpinDetection]:
        """
        كشف جميع الدورانات في الفيديو

        Args:
            pose_frames: قائمة إطارات الوضعية
            min_rpm: الحد الأدنى للـ RPM (اختياري)

        Returns:
            قائمة الدورانات المكتشفة
        """
        if min_rpm is None:
            min_rpm = self.min_rpm

        print("🌀 Detecting spins...")

        # Step 1: Calculate rotation speed for each frame
        rotation_speeds = self._calculate_rotation_speeds(pose_frames)

        # Step 2: Find spinning segments (high RPM segments)
        spin_segments = self._find_spinning_segments(
            pose_frames,
            rotation_speeds,
            min_rpm
        )

        print(f"   Found {len(spin_segments)} spinning segments")

        # Step 3: Analyze each segment
        spins = []
        for segment_start, segment_end in spin_segments:
            segment = pose_frames[segment_start:segment_end+1]

            spin = self._analyze_spin_segment(
                segment,
                segment_start,
                rotation_speeds[segment_start:segment_end+1]
            )

            if spin:
                spins.append(spin)

        print(f"✅ Detected {len(spins)} spins")

        return spins

    def _calculate_rotation_speeds(
        self,
        pose_frames: List[PoseFrame]
    ) -> List[float]:
        """
        حساب سرعة الدوران (RPM) لكل إطار
        """
        if len(pose_frames) < 2:
            return []

        # Calculate angular velocity using body angle
        rotation_speeds = []

        window_size = int(self.fps / 2)  # نصف ثانية

        for i in range(len(pose_frames)):
            if i < window_size or i >= len(pose_frames) - window_size:
                rotation_speeds.append(0.0)
                continue

            # Get window of frames
            window = pose_frames[i-window_size:i+window_size]

            # Calculate total rotation in window
            total_rotation = 0.0
            for j in range(1, len(window)):
                if window[j].body_angle is not None and window[j-1].body_angle is not None:
                    diff = window[j].body_angle - window[j-1].body_angle

                    # Handle wrap-around
                    if diff > 180:
                        diff -= 360
                    elif diff < -180:
                        diff += 360

                    total_rotation += abs(diff)

            # Convert to rotations
            rotations = total_rotation / 360.0

            # Convert to RPM
            duration_seconds = (2 * window_size) / self.fps
            rpm = (rotations / duration_seconds) * 60

            rotation_speeds.append(rpm)

        return rotation_speeds

    def _find_spinning_segments(
        self,
        pose_frames: List[PoseFrame],
        rotation_speeds: List[float],
        min_rpm: float
    ) -> List[Tuple[int, int]]:
        """
        Find segments where skater is spinning (high RPM)
        """
        segments = []
        in_spin = False
        segment_start = 0

        for i, rpm in enumerate(rotation_speeds):
            if rpm >= min_rpm and not in_spin:
                # Start of spin
                in_spin = True
                segment_start = i
            elif rpm < min_rpm and in_spin:
                # End of spin
                in_spin = False
                segment_end = i - 1

                # Check duration
                duration = (segment_end - segment_start) / self.fps

                if duration >= self.min_duration:
                    segments.append((segment_start, segment_end))

        return segments

    def _analyze_spin_segment(
        self,
        segment: List[PoseFrame],
        segment_start: int,
        rpms: List[float]
    ) -> Optional[SpinDetection]:
        """
        تحليل قطعة دوران واحدة
        """
        if len(segment) < int(self.fps * self.min_duration):
            return None

        # Basic metrics
        duration = len(segment) / self.fps
        average_rpm = np.mean(rpms) if rpms else 0

        # Count total rotations
        total_rotations = (average_rpm * duration) / 60

        if total_rotations < self.min_rotations:
            return None

        # Detect position changes (segments)
        spin_segments = self._detect_position_segments(segment, segment_start)

        # Classify spin type
        spin_type = self._classify_spin_type(spin_segments)

        # Determine level (1-4)
        features = self._detect_spin_features(segment, spin_segments)
        level = self._determine_spin_level(features, spin_segments)

        # Calculate quality metrics
        centering_score = self._calculate_centering(segment)
        entrance_quality = self._evaluate_entrance(segment[:int(self.fps)])
        exit_quality = self._evaluate_exit(segment[-int(self.fps):])
        speed_maintenance = self._calculate_speed_maintenance(rpms)
        position_quality = self._evaluate_position_quality(segment)

        # Detect errors
        errors, warnings = self._detect_spin_errors(
            segment, rpms, centering_score, spin_segments
        )

        # Estimate GOE
        estimated_goe = self._estimate_spin_goe(
            centering_score, speed_maintenance,
            position_quality, len(errors), level
        )

        return SpinDetection(
            start_frame=segment_start,
            end_frame=segment_start + len(segment) - 1,
            duration=duration,
            spin_type=spin_type,
            level=level,
            segments=spin_segments,
            total_rotations=total_rotations,
            average_rpm=average_rpm,
            centering_score=centering_score,
            entrance_quality=entrance_quality,
            exit_quality=exit_quality,
            speed_maintenance=speed_maintenance,
            position_quality=position_quality,
            features=features,
            errors=errors,
            warnings=warnings,
            estimated_goe=estimated_goe
        )

    def _detect_position_segments(
        self,
        segment: List[PoseFrame],
        segment_start: int
    ) -> List[SpinSegment]:
        """
        Detect different positions within the spin
        """
        segments = []

        # Detect position for each frame
        positions = []
        for frame in segment:
            pos = self._detect_position(frame)
            positions.append(pos)

        # Group consecutive same positions
        if not positions:
            return segments

        current_position = positions[0]
        position_start = 0

        for i in range(1, len(positions)):
            if positions[i] != current_position:
                # Position changed
                position_end = i - 1

                # Create segment
                duration = (position_end - position_start) / self.fps
                rotations = duration * (60 / self.fps)  # rough estimate

                segments.append(SpinSegment(
                    position=current_position,
                    start_frame=segment_start + position_start,
                    end_frame=segment_start + position_end,
                    rotations=rotations,
                    rpm=rotations / duration * 60 if duration > 0 else 0,
                    quality=0.75  # placeholder
                ))

                current_position = positions[i]
                position_start = i

        # Add last segment
        duration = (len(positions) - position_start) / self.fps
        rotations = duration * (60 / self.fps)

        segments.append(SpinSegment(
            position=current_position,
            start_frame=segment_start + position_start,
            end_frame=segment_start + len(positions) - 1,
            rotations=rotations,
            rpm=rotations / duration * 60 if duration > 0 else 0,
            quality=0.75
        ))

        return segments

    def _detect_position(self, frame: PoseFrame) -> SpinPosition:
        """
        Detect spin position from pose

        This is simplified - real implementation would need:
        - Detailed body orientation analysis
        - Leg position (extended vs bent)
        - Back arch (for layback/camel)
        - etc.
        """
        if not frame.landmarks:
            return SpinPosition.UPRIGHT

        # Get key landmarks
        left_hip = frame.landmarks.get('left_hip')
        left_knee = frame.landmarks.get('left_knee')
        left_shoulder = frame.landmarks.get('left_shoulder')

        if not (left_hip and left_knee and left_shoulder):
            return SpinPosition.UPRIGHT

        # Simple heuristics
        knee_bend = abs(left_knee.y - left_hip.y)

        if knee_bend < 0.15:
            # Knees very bent - likely sit spin
            return SpinPosition.SIT
        elif abs(left_shoulder.y - left_hip.y) < 0.1:
            # Torso horizontal - likely camel
            return SpinPosition.CAMEL
        else:
            # Default to upright
            return SpinPosition.UPRIGHT

    def _classify_spin_type(
        self,
        segments: List[SpinSegment]
    ) -> SpinType:
        """
        Classify overall spin type
        """
        if len(segments) == 0:
            return SpinType.UNKNOWN

        # Get unique positions
        positions = list(set(s.position for s in segments))

        if len(positions) >= 2:
            # Multiple positions - combination spin
            return SpinType.COMBINATION
        else:
            # Single position
            pos = positions[0]

            if pos == SpinPosition.UPRIGHT:
                return SpinType.UPRIGHT
            elif pos == SpinPosition.SIT:
                return SpinType.SIT
            elif pos == SpinPosition.CAMEL:
                return SpinType.CAMEL
            elif pos == SpinPosition.LAYBACK:
                return SpinType.LAYBACK
            else:
                return SpinType.UNKNOWN

    def _detect_spin_features(
        self,
        segment: List[PoseFrame],
        spin_segments: List[SpinSegment]
    ) -> List[str]:
        """
        Detect features that contribute to spin level
        """
        features = []

        # Feature 1: Number of different positions (for combination)
        unique_positions = len(set(s.position for s in spin_segments))
        if unique_positions >= 2:
            features.append("change_of_position")
        if unique_positions >= 3:
            features.append("3_basic_positions")

        # Feature 2: Each position has enough rotations
        for seg in spin_segments:
            if seg.rotations >= 2:
                features.append(f"{seg.position.value}_2_rotations")

        # Feature 3: Difficult variation (placeholder)
        if len(segment) > self.fps * 5:  # longer than 5 seconds
            features.append("difficult_variation")

        # Feature 4: Clear position (placeholder)
        features.append("clear_position")

        return features

    def _determine_spin_level(
        self,
        features: List[str],
        segments: List[SpinSegment]
    ) -> int:
        """
        Determine ISU level (1-4) based on features
        """
        # Simplified level determination
        # Real ISU: very complex rules

        feature_count = len(features)

        if feature_count >= 4:
            return 4
        elif feature_count >= 3:
            return 3
        elif feature_count >= 2:
            return 2
        else:
            return 1

    def _calculate_centering(self, segment: List[PoseFrame]) -> float:
        """
        Calculate how well-centered the spin is (0-1)

        Centered spin = minimal traveling
        """
        if not segment:
            return 0.5

        # Track center of mass movement
        com_positions = []
        for frame in segment:
            if frame.center_of_mass:
                com_positions.append((frame.center_of_mass[0], frame.center_of_mass[1]))

        if len(com_positions) < 2:
            return 0.5

        # Calculate variance in position
        x_coords = [p[0] for p in com_positions]
        y_coords = [p[1] for p in com_positions]

        x_var = np.var(x_coords)
        y_var = np.var(y_coords)

        total_var = x_var + y_var

        # Convert to centering score (lower variance = better centering)
        centering = max(0.0, 1.0 - total_var * 50)

        return min(1.0, centering)

    def _evaluate_entrance(self, entrance_frames: List[PoseFrame]) -> float:
        """Evaluate quality of spin entrance"""
        # Placeholder - real implementation would check:
        # - Speed of entry
        # - Edge quality
        # - Body position
        return 0.75

    def _evaluate_exit(self, exit_frames: List[PoseFrame]) -> float:
        """Evaluate quality of spin exit"""
        # Placeholder
        return 0.75

    def _calculate_speed_maintenance(self, rpms: List[float]) -> float:
        """
        Calculate how well speed is maintained (0-1)

        Good spin = consistent RPM
        """
        if len(rpms) < 2:
            return 0.5

        # Calculate coefficient of variation
        mean_rpm = np.mean(rpms)
        std_rpm = np.std(rpms)

        if mean_rpm == 0:
            return 0.5

        cv = std_rpm / mean_rpm

        # Lower CV = better maintenance
        maintenance = max(0.0, 1.0 - cv)

        return min(1.0, maintenance)

    def _evaluate_position_quality(self, segment: List[PoseFrame]) -> float:
        """Evaluate overall position quality"""
        # Placeholder - would check:
        # - Leg extension
        # - Body alignment
        # - Arm position
        return 0.75

    def _detect_spin_errors(
        self,
        segment: List[PoseFrame],
        rpms: List[float],
        centering: float,
        spin_segments: List[SpinSegment]
    ) -> Tuple[List[str], List[str]]:
        """Detect errors and warnings"""
        errors = []
        warnings = []

        # Check centering
        if centering < 0.4:
            errors.append("Excessive traveling")
        elif centering < 0.6:
            warnings.append("Some traveling")

        # Check speed
        if rpms and min(rpms) < self.min_rpm * 0.8:
            warnings.append("Speed dropped below minimum")

        # Check minimum rotations per position
        for seg in spin_segments:
            if seg.rotations < 2:
                warnings.append(f"Insufficient rotations in {seg.position.value} position")

        return errors, warnings

    def _estimate_spin_goe(
        self,
        centering: float,
        speed_maintenance: float,
        position_quality: float,
        error_count: int,
        level: int
    ) -> int:
        """Estimate GOE for spin"""
        # Start from 0
        goe = 0

        # Positive factors
        if centering >= 0.8:
            goe += 1
        if speed_maintenance >= 0.8:
            goe += 1
        if position_quality >= 0.8:
            goe += 1
        if level == 4:
            goe += 1

        # Negative factors
        goe -= error_count * 2

        # Clamp
        goe = max(-5, min(5, goe))

        return goe


def test_spin_detector():
    """Test spin detection"""
    from src.core.advanced_pose_detector import AdvancedPoseDetector

    detector = AdvancedPoseDetector()
    spin_detector = SpinDetector(fps=30)

    video_path = "sample_program.mp4"

    try:
        print("Processing video...")
        pose_frames = detector.process_video(video_path, save_visualization=False)

        print("Detecting spins...")
        spins = spin_detector.detect_spins(pose_frames)

        print(f"\n📊 Results:")
        print(f"   Total spins detected: {len(spins)}")

        for i, spin in enumerate(spins, 1):
            print(f"\n🌀 Spin {i}:")
            print(f"   Code: {spin.get_isu_code()}")
            print(f"   Type: {spin.spin_type.value}")
            print(f"   Level: {spin.level}")
            print(f"   Duration: {spin.duration:.2f}s")
            print(f"   Total rotations: {spin.total_rotations:.1f}")
            print(f"   Average RPM: {spin.average_rpm:.0f}")
            print(f"   Centering: {spin.centering_score:.0%}")
            print(f"   GOE: {spin.estimated_goe:+d}")

            print(f"   Positions:")
            for seg in spin.segments:
                print(f"      {seg.position.value}: {seg.rotations:.1f} rotations")

    finally:
        detector.close()


if __name__ == "__main__":
    test_spin_detector()
