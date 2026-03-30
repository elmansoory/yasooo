"""
Jump Detection and Classification System
نظام كشف وتصنيف القفزات في التزلج
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from src.core.advanced_pose_detector import PoseFrame, Landmark3D


class JumpType(Enum):
    """أنواع القفزات"""
    AXEL = "A"
    LUTZ = "Lz"
    FLIP = "F"
    LOOP = "Lo"
    SALCHOW = "S"
    TOE_LOOP = "T"
    UNKNOWN = "?"


class JumpRotations(Enum):
    """عدد الدورات"""
    SINGLE = 1
    DOUBLE = 2
    TRIPLE = 3
    QUAD = 4


@dataclass
class JumpPhase:
    """مرحلة من مراحل القفزة"""
    name: str  # preparation, takeoff, flight, landing, exit
    start_frame: int
    end_frame: int
    duration: float  # seconds


@dataclass
class JumpDetection:
    """قفزة مكتشفة"""
    # Basic info
    start_frame: int
    end_frame: int
    peak_frame: int  # أعلى نقطة
    duration: float  # seconds

    # Jump classification
    jump_type: JumpType
    rotations: float  # عدد الدورات (مثل 3.5 للAxel)
    is_clean: bool  # هبوط نظيف؟

    # Phases
    phases: List[JumpPhase]

    # Measurements
    height_cm: float  # ارتفاع القفزة
    distance_m: float  # مسافة القفزة
    airtime: float  # وقت في الهواء
    takeoff_velocity: float
    landing_velocity: float

    # Angles
    takeoff_angle: float  # زاوية الإقلاع
    landing_angle: float  # زاوية الهبوط

    # Quality metrics
    rotation_speed: float  # RPM
    axis_stability: float  # 0-1
    extension_quality: float  # 0-1

    # Errors detected
    errors: List[str]
    warnings: List[str]

    # GOE factors
    goe_positive_factors: List[str]
    goe_negative_factors: List[str]
    estimated_goe: int  # -5 to +5

    def to_dict(self) -> Dict:
        return {
            'start_frame': self.start_frame,
            'end_frame': self.end_frame,
            'peak_frame': self.peak_frame,
            'duration': self.duration,
            'jump_type': self.jump_type.value,
            'rotations': self.rotations,
            'is_clean': self.is_clean,
            'height_cm': self.height_cm,
            'distance_m': self.distance_m,
            'airtime': self.airtime,
            'takeoff_angle': self.takeoff_angle,
            'landing_angle': self.landing_angle,
            'rotation_speed': self.rotation_speed,
            'errors': self.errors,
            'warnings': self.warnings,
            'estimated_goe': self.estimated_goe
        }

    def get_isu_code(self) -> str:
        """Get ISU notation (e.g., '3A', '4T', '2Lz')"""
        if self.jump_type == JumpType.UNKNOWN:
            return "?"

        rotations_int = int(self.rotations)
        return f"{rotations_int}{self.jump_type.value}"


class JumpDetector:
    """
    نظام كشف القفزات الذكي
    """

    def __init__(self, fps: float = 30.0):
        self.fps = fps

        # Thresholds
        self.min_airtime = 0.3  # seconds
        self.min_height_threshold = 0.1  # normalized
        self.rotation_threshold = 0.5  # minimum rotations to count as jump

    def detect_jumps(
        self,
        pose_frames: List[PoseFrame],
        calibration: Optional[Dict] = None
    ) -> List[JumpDetection]:
        """
        كشف جميع القفزات في الفيديو

        Args:
            pose_frames: قائمة إطارات الوضعية
            calibration: معلومات المعايرة (للقياسات الحقيقية)

        Returns:
            قائمة القفزات المكتشفة
        """
        print("🔍 Detecting jumps...")

        # Step 1: Find airborne segments
        airborne_segments = self._find_airborne_segments(pose_frames)
        print(f"   Found {len(airborne_segments)} airborne segments")

        # Step 2: Filter and analyze each segment
        jumps = []
        for segment_start, segment_end in airborne_segments:
            segment = pose_frames[segment_start:segment_end+1]

            # Analyze segment
            jump = self._analyze_jump_segment(segment, segment_start, calibration)

            if jump:
                jumps.append(jump)

        print(f"✅ Detected {len(jumps)} jumps")

        return jumps

    def _find_airborne_segments(
        self,
        pose_frames: List[PoseFrame]
    ) -> List[Tuple[int, int]]:
        """
        Find all airborne segments in the video

        Returns:
            List of (start_frame, end_frame) tuples
        """
        segments = []
        in_air = False
        segment_start = 0

        for i, frame in enumerate(pose_frames):
            if frame.is_airborne and not in_air:
                # Start of airborne segment
                in_air = True
                segment_start = i
            elif not frame.is_airborne and in_air:
                # End of airborne segment
                in_air = False
                segment_end = i - 1

                # Calculate duration
                duration = (segment_end - segment_start) / self.fps

                # Filter by minimum airtime
                if duration >= self.min_airtime:
                    segments.append((segment_start, segment_end))

        return segments

    def _analyze_jump_segment(
        self,
        segment: List[PoseFrame],
        segment_start: int,
        calibration: Optional[Dict] = None
    ) -> Optional[JumpDetection]:
        """
        تحليل قطعة من الفيديو لاستخراج بيانات القفزة

        Args:
            segment: إطارات القفزة
            segment_start: رقم الإطار الأول
            calibration: معايرة

        Returns:
            JumpDetection أو None
        """
        if len(segment) < 3:
            return None

        # Calculate basic metrics
        start_frame = segment_start
        end_frame = segment_start + len(segment) - 1
        duration = len(segment) / self.fps

        # Find peak (highest point)
        peak_frame_idx = self._find_peak_frame(segment)
        peak_frame = segment_start + peak_frame_idx

        # Calculate height
        height_cm = self._calculate_height(segment, peak_frame_idx, calibration)

        # Calculate distance
        distance_m = self._calculate_distance(segment, calibration)

        # Count rotations
        rotations = self._count_rotations(segment)

        # Classify jump type
        jump_type = self._classify_jump_type(segment, rotations)

        # Analyze takeoff and landing
        takeoff_angle = self._calculate_takeoff_angle(segment)
        landing_angle = self._calculate_landing_angle(segment)

        # Calculate velocities
        takeoff_velocity = self._calculate_velocity(segment[:3])
        landing_velocity = self._calculate_velocity(segment[-3:])

        # Rotation speed (RPM)
        rotation_speed = (rotations / duration) * 60 if duration > 0 else 0

        # Detect errors and warnings
        errors, warnings = self._detect_errors(segment, rotations)

        # Check if clean landing
        is_clean = len(errors) == 0 and 'landing' not in ''.join(warnings).lower()

        # Calculate quality metrics
        axis_stability = self._calculate_axis_stability(segment)
        extension_quality = self._calculate_extension_quality(segment)

        # Estimate GOE
        goe_positive, goe_negative = self._analyze_goe_factors(
            segment, height_cm, rotations, is_clean,
            axis_stability, extension_quality
        )
        estimated_goe = self._estimate_goe(goe_positive, goe_negative)

        # Detect phases
        phases = self._detect_jump_phases(segment, peak_frame_idx, segment_start)

        return JumpDetection(
            start_frame=start_frame,
            end_frame=end_frame,
            peak_frame=peak_frame,
            duration=duration,
            jump_type=jump_type,
            rotations=rotations,
            is_clean=is_clean,
            phases=phases,
            height_cm=height_cm,
            distance_m=distance_m,
            airtime=duration,
            takeoff_velocity=takeoff_velocity,
            landing_velocity=landing_velocity,
            takeoff_angle=takeoff_angle,
            landing_angle=landing_angle,
            rotation_speed=rotation_speed,
            axis_stability=axis_stability,
            extension_quality=extension_quality,
            errors=errors,
            warnings=warnings,
            goe_positive_factors=goe_positive,
            goe_negative_factors=goe_negative,
            estimated_goe=estimated_goe
        )

    def _find_peak_frame(self, segment: List[PoseFrame]) -> int:
        """Find frame with highest center of mass"""
        heights = []
        for frame in segment:
            if frame.center_of_mass:
                heights.append(frame.center_of_mass[1])
            else:
                heights.append(0.5)

        # Lower y = higher in image
        peak_idx = np.argmin(heights)
        return peak_idx

    def _calculate_height(
        self,
        segment: List[PoseFrame],
        peak_idx: int,
        calibration: Optional[Dict]
    ) -> float:
        """Calculate jump height in cm"""
        if not segment or not segment[0].center_of_mass:
            return 0.0

        # Get heights (y coordinates)
        ground_y = segment[0].center_of_mass[1]  # takeoff height
        peak_y = segment[peak_idx].center_of_mass[1]  # peak height

        # Height in normalized coordinates (0-1)
        height_normalized = abs(ground_y - peak_y)

        # Convert to cm using calibration
        if calibration and 'pixels_per_cm' in calibration:
            height_cm = height_normalized * calibration['reference_height_cm']
        else:
            # Estimate: assume average person height ~170cm
            # and they occupy ~0.7 of frame height
            estimated_person_height = 170  # cm
            height_cm = height_normalized * (estimated_person_height / 0.7)

        return height_cm

    def _calculate_distance(
        self,
        segment: List[PoseFrame],
        calibration: Optional[Dict]
    ) -> float:
        """Calculate horizontal distance of jump"""
        if not segment or not segment[0].center_of_mass:
            return 0.0

        start_x = segment[0].center_of_mass[0]
        end_x = segment[-1].center_of_mass[0]

        distance_normalized = abs(end_x - start_x)

        # Convert to meters
        if calibration and 'pixels_per_m' in calibration:
            distance_m = distance_normalized * calibration['reference_width_m']
        else:
            # Estimate: assume rink width ~30m, frame width ~0.8 of rink
            distance_m = distance_normalized * (30 / 0.8)

        return distance_m

    def _count_rotations(self, segment: List[PoseFrame]) -> float:
        """Count number of rotations during jump"""
        if len(segment) < 2:
            return 0.0

        # Track shoulder line rotation
        angles = []
        for frame in segment:
            if frame.body_angle is not None:
                angles.append(frame.body_angle)

        if len(angles) < 2:
            return 0.0

        # Calculate total rotation
        total_rotation = 0.0
        for i in range(1, len(angles)):
            diff = angles[i] - angles[i-1]

            # Handle angle wrap-around (-180 to 180)
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360

            total_rotation += diff

        # Convert to rotations (360° = 1 rotation)
        rotations = abs(total_rotation) / 360.0

        return rotations

    def _classify_jump_type(
        self,
        segment: List[PoseFrame],
        rotations: float
    ) -> JumpType:
        """
        Classify type of jump (Axel, Lutz, etc.)

        This is a SIMPLIFIED version - real classification needs
        much more sophisticated analysis of:
        - Takeoff edge (inside/outside)
        - Toe pick usage
        - Entry direction
        - etc.
        """
        # For now, return UNKNOWN
        # Real implementation would need:
        # 1. Foot/skate tracking
        # 2. Edge detection
        # 3. Entry pattern analysis
        # 4. ML classification model

        # Simple heuristic: if rotations > 2.5, likely an Axel (since Axel has +0.5)
        if rotations > 2.3 and rotations < 2.7:
            return JumpType.AXEL  # Double Axel (2.5 rotations)
        elif rotations > 3.3 and rotations < 3.7:
            return JumpType.AXEL  # Triple Axel (3.5 rotations)

        return JumpType.UNKNOWN

    def _calculate_takeoff_angle(self, segment: List[PoseFrame]) -> float:
        """Calculate takeoff angle"""
        if len(segment) < 3:
            return 0.0

        # Use first few frames
        heights = [f.center_of_mass[1] for f in segment[:3] if f.center_of_mass]

        if len(heights) < 2:
            return 0.0

        # Calculate angle from height change
        dh = heights[-1] - heights[0]
        dt = len(heights) / self.fps

        # Rough angle calculation
        angle = np.arctan2(abs(dh), dt) * 180 / np.pi

        return angle

    def _calculate_landing_angle(self, segment: List[PoseFrame]) -> float:
        """Calculate landing angle"""
        if len(segment) < 3:
            return 0.0

        # Use last few frames
        heights = [f.center_of_mass[1] for f in segment[-3:] if f.center_of_mass]

        if len(heights) < 2:
            return 0.0

        # Calculate angle
        dh = heights[-1] - heights[0]
        dt = len(heights) / self.fps

        angle = np.arctan2(abs(dh), dt) * 180 / np.pi

        return angle

    def _calculate_velocity(self, frames: List[PoseFrame]) -> float:
        """Calculate average velocity"""
        if len(frames) < 2:
            return 0.0

        velocities = []
        for i in range(1, len(frames)):
            if frames[i].center_of_mass and frames[i-1].center_of_mass:
                dx = frames[i].center_of_mass[0] - frames[i-1].center_of_mass[0]
                dy = frames[i].center_of_mass[1] - frames[i-1].center_of_mass[1]

                velocity = np.sqrt(dx**2 + dy**2)
                velocities.append(velocity)

        return np.mean(velocities) if velocities else 0.0

    def _calculate_axis_stability(self, segment: List[PoseFrame]) -> float:
        """Calculate how stable the rotation axis is (0-1)"""
        if not segment:
            return 0.5

        # Track center of mass movement
        com_positions = [f.center_of_mass for f in segment if f.center_of_mass]

        if len(com_positions) < 2:
            return 0.5

        x_coords = [p[0] for p in com_positions]
        y_coords = [p[1] for p in com_positions]

        # Calculate variance (lower = more stable)
        x_var = np.var(x_coords)
        y_var = np.var(y_coords)

        total_var = x_var + y_var

        # Convert to stability score (0-1)
        stability = max(0.0, 1.0 - total_var * 20)

        return min(1.0, stability)

    def _calculate_extension_quality(self, segment: List[PoseFrame]) -> float:
        """Calculate quality of body extension during jump (0-1)"""
        # This would need more sophisticated analysis of:
        # - Leg extension
        # - Arm position
        # - Body line

        # Simplified version
        return 0.75  # placeholder

    def _detect_errors(
        self,
        segment: List[PoseFrame],
        rotations: float
    ) -> Tuple[List[str], List[str]]:
        """
        Detect errors and warnings

        Returns:
            (errors, warnings)
        """
        errors = []
        warnings = []

        # Check for under-rotation
        expected_rotations = round(rotations)
        if rotations < expected_rotations - 0.25:
            errors.append(f"Under-rotated (q mark - {rotations:.2f} rotations)")

        # Check for two-foot landing (simplified - needs better detection)
        # Would need to track both feet separately

        # Check for low height
        # This would be done in _analyze_goe_factors

        return errors, warnings

    def _detect_jump_phases(
        self,
        segment: List[PoseFrame],
        peak_idx: int,
        start_frame: int
    ) -> List[JumpPhase]:
        """Detect different phases of the jump"""
        phases = []

        total_frames = len(segment)

        # Simple phase detection
        # Takeoff: first 20% before peak
        takeoff_end = max(1, peak_idx // 2)
        phases.append(JumpPhase(
            name='takeoff',
            start_frame=start_frame,
            end_frame=start_frame + takeoff_end,
            duration=takeoff_end / self.fps
        ))

        # Flight: around peak
        flight_start = takeoff_end
        flight_end = peak_idx + (total_frames - peak_idx) // 2
        phases.append(JumpPhase(
            name='flight',
            start_frame=start_frame + flight_start,
            end_frame=start_frame + flight_end,
            duration=(flight_end - flight_start) / self.fps
        ))

        # Landing: rest
        phases.append(JumpPhase(
            name='landing',
            start_frame=start_frame + flight_end,
            end_frame=start_frame + total_frames - 1,
            duration=(total_frames - flight_end) / self.fps
        ))

        return phases

    def _analyze_goe_factors(
        self,
        segment: List[PoseFrame],
        height_cm: float,
        rotations: float,
        is_clean: bool,
        axis_stability: float,
        extension_quality: float
    ) -> Tuple[List[str], List[str]]:
        """Analyze factors affecting GOE"""
        positive = []
        negative = []

        # Height
        if height_cm > 40:
            positive.append("Good height and distance")
        elif height_cm < 25:
            negative.append("Low jump height")

        # Rotations
        expected = round(rotations)
        if abs(rotations - expected) < 0.1:
            positive.append("Clean rotations")
        elif rotations < expected - 0.25:
            negative.append("Under-rotated")

        # Landing
        if is_clean:
            positive.append("Clean landing")
        else:
            negative.append("Landing issues")

        # Axis stability
        if axis_stability > 0.8:
            positive.append("Good axis control")
        elif axis_stability < 0.5:
            negative.append("Unstable rotation axis")

        # Extension
        if extension_quality > 0.8:
            positive.append("Good extension")

        return positive, negative

    def _estimate_goe(
        self,
        positive_factors: List[str],
        negative_factors: List[str]
    ) -> int:
        """Estimate GOE from factors"""
        # Start from 0
        goe = 0

        # Add for positive factors
        goe += len(positive_factors)

        # Subtract for negative factors
        goe -= len(negative_factors) * 2  # Negative factors hurt more

        # Clamp to -5 to +5
        goe = max(-5, min(5, goe))

        return goe


def test_jump_detector():
    """Test jump detection"""
    from src.core.advanced_pose_detector import AdvancedPoseDetector

    # Initialize
    pose_detector = AdvancedPoseDetector()
    jump_detector = JumpDetector(fps=30)

    # Process video
    video_path = "sample_program.mp4"

    try:
        print("Processing video...")
        pose_frames = pose_detector.process_video(video_path, save_visualization=False)

        print("Detecting jumps...")
        jumps = jump_detector.detect_jumps(pose_frames)

        print(f"\n📊 Results:")
        print(f"   Total jumps detected: {len(jumps)}")

        for i, jump in enumerate(jumps, 1):
            print(f"\n🔹 Jump {i}:")
            print(f"   Code: {jump.get_isu_code()}")
            print(f"   Frames: {jump.start_frame} - {jump.end_frame}")
            print(f"   Height: {jump.height_cm:.1f} cm")
            print(f"   Rotations: {jump.rotations:.2f}")
            print(f"   Airtime: {jump.airtime:.2f}s")
            print(f"   Rotation speed: {jump.rotation_speed:.0f} RPM")
            print(f"   Estimated GOE: {jump.estimated_goe:+d}")
            print(f"   Clean: {'✅' if jump.is_clean else '❌'}")

            if jump.errors:
                print(f"   ❌ Errors: {', '.join(jump.errors)}")

    finally:
        pose_detector.close()


if __name__ == "__main__":
    test_jump_detector()
