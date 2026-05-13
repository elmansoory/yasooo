"""
Advanced Pose Detection using MediaPipe
نظام متقدم لكشف الوضعيات باستخدام MediaPipe مع تحليل 3D
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# Try to import MediaPipe, handle gracefully if not available
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️ MediaPipe not available. Install with: pip install mediapipe==0.10.9")


@dataclass
class Landmark3D:
    """نقطة مرجعية 3D"""
    x: float  # normalized 0-1
    y: float  # normalized 0-1
    z: float  # depth (relative)
    visibility: float  # 0-1

    def to_dict(self) -> Dict:
        return {
            'x': float(self.x),
            'y': float(self.y),
            'z': float(self.z),
            'visibility': float(self.visibility)
        }


@dataclass
class PoseFrame:
    """إطار واحد مع بيانات الوضعية"""
    frame_number: int
    timestamp: float
    landmarks: Dict[str, Landmark3D]
    world_landmarks: Optional[Dict[str, Landmark3D]] = None

    # Calculated features
    center_of_mass: Optional[Tuple[float, float, float]] = None
    body_angle: Optional[float] = None
    is_airborne: bool = False

    def to_dict(self) -> Dict:
        return {
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'landmarks': {k: v.to_dict() for k, v in self.landmarks.items()},
            'center_of_mass': self.center_of_mass,
            'body_angle': self.body_angle,
            'is_airborne': self.is_airborne
        }


class AdvancedPoseDetector:
    """
    Advanced Pose Detection System
    يستخدم MediaPipe Pose لكشف دقيق للوضعيات مع تحليل 3D
    """

    # MediaPipe landmarks mapping
    LANDMARK_NAMES = {
        0: 'nose',
        1: 'left_eye_inner',
        2: 'left_eye',
        3: 'left_eye_outer',
        4: 'right_eye_inner',
        5: 'right_eye',
        6: 'right_eye_outer',
        7: 'left_ear',
        8: 'right_ear',
        9: 'mouth_left',
        10: 'mouth_right',
        11: 'left_shoulder',
        12: 'right_shoulder',
        13: 'left_elbow',
        14: 'right_elbow',
        15: 'left_wrist',
        16: 'right_wrist',
        17: 'left_pinky',
        18: 'right_pinky',
        19: 'left_index',
        20: 'right_index',
        21: 'left_thumb',
        22: 'right_thumb',
        23: 'left_hip',
        24: 'right_hip',
        25: 'left_knee',
        26: 'right_knee',
        27: 'left_ankle',
        28: 'right_ankle',
        29: 'left_heel',
        30: 'right_heel',
        31: 'left_foot_index',
        32: 'right_foot_index'
    }

    def __init__(
        self,
        model_complexity: int = 2,  # 0, 1, or 2 (2 = most accurate)
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
        enable_segmentation: bool = False,
        smooth_landmarks: bool = True
    ):
        """
        Initialize MediaPipe Pose detector

        Args:
            model_complexity: 0-2, higher = more accurate but slower
            min_detection_confidence: minimum confidence for detection
            min_tracking_confidence: minimum confidence for tracking
            enable_segmentation: enable person segmentation
            smooth_landmarks: enable landmark smoothing
        """
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError(
                "MediaPipe is not installed. Please install it with:\n"
                "  pip install mediapipe==0.10.9\n"
                "Or use the basic app.py instead of professional_app.py"
            )

        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.pose = self.mp_pose.Pose(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            enable_segmentation=enable_segmentation,
            smooth_landmarks=smooth_landmarks
        )

        self.frame_count = 0
        self.fps = 30  # default, will be updated

    def process_video(
        self,
        video_path: str,
        save_visualization: bool = True,
        output_path: Optional[str] = None
    ) -> List[PoseFrame]:
        """
        Process entire video and extract pose data

        Args:
            video_path: path to video file
            save_visualization: save annotated video
            output_path: output video path

        Returns:
            List of PoseFrame objects
        """
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        # Get video properties
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📹 Processing video: {video_path}")
        print(f"   FPS: {self.fps}, Resolution: {width}x{height}, Frames: {total_frames}")

        # Video writer for visualization
        writer = None
        if save_visualization and output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))

        pose_frames = []
        frame_number = 0

        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            # Process frame
            pose_frame = self.process_frame(frame, frame_number)

            if pose_frame:
                pose_frames.append(pose_frame)

                # Draw pose on frame
                if save_visualization and writer:
                    annotated_frame = self.draw_pose(frame, pose_frame)
                    writer.write(annotated_frame)

            frame_number += 1

            # Progress
            if frame_number % 30 == 0:
                progress = (frame_number / total_frames) * 100
                print(f"   Progress: {progress:.1f}% ({frame_number}/{total_frames})")

        cap.release()
        if writer:
            writer.release()

        print(f"✅ Processed {len(pose_frames)} frames")

        return pose_frames

    def process_frame(
        self,
        frame: np.ndarray,
        frame_number: int
    ) -> Optional[PoseFrame]:
        """
        Process single frame and extract pose

        Args:
            frame: BGR image
            frame_number: frame index

        Returns:
            PoseFrame or None if no pose detected
        """
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process with MediaPipe
        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return None

        # Extract landmarks
        landmarks = {}
        for idx, landmark in enumerate(results.pose_landmarks.landmark):
            name = self.LANDMARK_NAMES.get(idx, f'landmark_{idx}')
            landmarks[name] = Landmark3D(
                x=landmark.x,
                y=landmark.y,
                z=landmark.z,
                visibility=landmark.visibility
            )

        # Extract world landmarks (3D coordinates in meters)
        world_landmarks = None
        if results.pose_world_landmarks:
            world_landmarks = {}
            for idx, landmark in enumerate(results.pose_world_landmarks.landmark):
                name = self.LANDMARK_NAMES.get(idx, f'landmark_{idx}')
                world_landmarks[name] = Landmark3D(
                    x=landmark.x,
                    y=landmark.y,
                    z=landmark.z,
                    visibility=landmark.visibility
                )

        # Calculate timestamp
        timestamp = frame_number / self.fps

        # Create pose frame
        pose_frame = PoseFrame(
            frame_number=frame_number,
            timestamp=timestamp,
            landmarks=landmarks,
            world_landmarks=world_landmarks
        )

        # Calculate additional features
        pose_frame.center_of_mass = self._calculate_center_of_mass(landmarks)
        pose_frame.body_angle = self._calculate_body_angle(landmarks)
        pose_frame.is_airborne = self._detect_airborne(landmarks)

        return pose_frame

    def _calculate_center_of_mass(
        self,
        landmarks: Dict[str, Landmark3D]
    ) -> Tuple[float, float, float]:
        """Calculate approximate center of mass"""
        # Use hip and shoulder points
        key_points = ['left_hip', 'right_hip', 'left_shoulder', 'right_shoulder']

        x_coords = []
        y_coords = []
        z_coords = []

        for point in key_points:
            if point in landmarks:
                x_coords.append(landmarks[point].x)
                y_coords.append(landmarks[point].y)
                z_coords.append(landmarks[point].z)

        if not x_coords:
            return (0.5, 0.5, 0.0)

        return (
            np.mean(x_coords),
            np.mean(y_coords),
            np.mean(z_coords)
        )

    def _calculate_body_angle(
        self,
        landmarks: Dict[str, Landmark3D]
    ) -> float:
        """Calculate body rotation angle from shoulders"""
        if 'left_shoulder' not in landmarks or 'right_shoulder' not in landmarks:
            return 0.0

        left = landmarks['left_shoulder']
        right = landmarks['right_shoulder']

        dx = right.x - left.x
        dy = right.y - left.y

        angle = np.arctan2(dy, dx) * 180 / np.pi
        return angle

    def _detect_airborne(
        self,
        landmarks: Dict[str, Landmark3D],
        threshold: float = 0.15
    ) -> bool:
        """
        Detect if skater is airborne.

        Strategy: compare ankle height to hip height using relative gap.
        On ice, ankles are well below hips (large gap).
        In the air, ankles rise toward hip level (gap shrinks).
        Also confirmed by knee position (knees tuck up during jump).
        """
        MIN_VIS = 0.4

        def visible(name):
            lm = landmarks.get(name)
            return lm if lm is not None and lm.visibility >= MIN_VIS else None

        la = visible('left_ankle');  ra = visible('right_ankle')
        lh = visible('left_hip');    rh = visible('right_hip')
        lk = visible('left_knee');   rk = visible('right_knee')

        if la is None and ra is None:
            return False

        ankle_ys = [p.y for p in [la, ra] if p is not None]
        ankle_y = sum(ankle_ys) / len(ankle_ys)

        hip_ys = [p.y for p in [lh, rh] if p is not None]
        if not hip_ys:
            return False
        hip_y = sum(hip_ys) / len(hip_ys)

        # gap > 0 means ankles are below hips (normal on ice)
        gap = ankle_y - hip_y

        # Knee confirmation: knees rise toward hip level when airborne
        knee_ys = [p.y for p in [lk, rk] if p is not None]
        knee_near_hip = (
            len(knee_ys) > 0 and
            (sum(knee_ys) / len(knee_ys)) < hip_y + 0.05
        )

        return gap < 0.20 or (gap < 0.28 and knee_near_hip)

    def draw_pose(
        self,
        frame: np.ndarray,
        pose_frame: PoseFrame,
        draw_landmarks: bool = True,
        draw_info: bool = True
    ) -> np.ndarray:
        """
        Draw pose visualization on frame

        Args:
            frame: original frame
            pose_frame: pose data
            draw_landmarks: draw skeleton
            draw_info: draw text info

        Returns:
            Annotated frame
        """
        annotated = frame.copy()

        if draw_landmarks:
            # Convert landmarks back to MediaPipe format
            mp_landmarks = self.mp_pose.PoseLandmark
            landmark_list = []

            for i in range(33):
                name = self.LANDMARK_NAMES.get(i, f'landmark_{i}')
                if name in pose_frame.landmarks:
                    lm = pose_frame.landmarks[name]
                    landmark_list.append(
                        type('Landmark', (), {
                            'x': lm.x,
                            'y': lm.y,
                            'z': lm.z,
                            'visibility': lm.visibility
                        })()
                    )

            # Draw connections
            if len(landmark_list) == 33:
                pose_landmarks = type('PoseLandmarks', (), {
                    'landmark': landmark_list
                })()

                self.mp_drawing.draw_landmarks(
                    annotated,
                    pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )

        if draw_info:
            # Draw info text
            info_text = [
                f"Frame: {pose_frame.frame_number}",
                f"Time: {pose_frame.timestamp:.2f}s",
                f"Airborne: {'YES' if pose_frame.is_airborne else 'NO'}",
                f"Angle: {pose_frame.body_angle:.1f}°"
            ]

            y_offset = 30
            for text in info_text:
                cv2.putText(
                    annotated,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )
                y_offset += 25

            # Draw airborne indicator
            if pose_frame.is_airborne:
                cv2.putText(
                    annotated,
                    "🚀 AIRBORNE",
                    (annotated.shape[1] - 200, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),
                    3
                )

        return annotated

    def calculate_joint_angle(
        self,
        landmarks: Dict[str, Landmark3D],
        point1: str,
        point2: str,
        point3: str
    ) -> float:
        """
        Calculate angle between three points (joints)

        Args:
            landmarks: pose landmarks
            point1, point2, point3: landmark names

        Returns:
            Angle in degrees
        """
        if point1 not in landmarks or point2 not in landmarks or point3 not in landmarks:
            return 0.0

        # Get coordinates
        p1 = np.array([landmarks[point1].x, landmarks[point1].y])
        p2 = np.array([landmarks[point2].x, landmarks[point2].y])
        p3 = np.array([landmarks[point3].x, landmarks[point3].y])

        # Calculate vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Calculate angle
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        angle = np.arccos(np.clip(cosine, -1.0, 1.0))

        return np.degrees(angle)

    def calculate_velocity(
        self,
        pose_frames: List[PoseFrame],
        landmark_name: str
    ) -> List[float]:
        """
        Calculate velocity of a specific landmark over time

        Args:
            pose_frames: list of pose frames
            landmark_name: name of landmark to track

        Returns:
            List of velocities (pixels per frame)
        """
        velocities = []

        for i in range(1, len(pose_frames)):
            prev_frame = pose_frames[i-1]
            curr_frame = pose_frames[i]

            if landmark_name in prev_frame.landmarks and landmark_name in curr_frame.landmarks:
                prev_lm = prev_frame.landmarks[landmark_name]
                curr_lm = curr_frame.landmarks[landmark_name]

                # Calculate distance
                dx = curr_lm.x - prev_lm.x
                dy = curr_lm.y - prev_lm.y

                velocity = np.sqrt(dx**2 + dy**2)
                velocities.append(velocity)
            else:
                velocities.append(0.0)

        return velocities

    def export_to_json(
        self,
        pose_frames: List[PoseFrame],
        output_path: str
    ):
        """Export pose data to JSON file"""
        data = {
            'metadata': {
                'total_frames': len(pose_frames),
                'fps': self.fps,
                'duration': pose_frames[-1].timestamp if pose_frames else 0,
                'export_date': datetime.now().isoformat()
            },
            'frames': [frame.to_dict() for frame in pose_frames]
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ Exported pose data to: {output_path}")

    def close(self):
        """Clean up resources"""
        self.pose.close()


def test_advanced_pose_detector():
    """Test the advanced pose detector"""
    detector = AdvancedPoseDetector(
        model_complexity=2,
        min_detection_confidence=0.7
    )

    # Test with sample video
    video_path = "sample_skating.mp4"
    output_video = "output_annotated.mp4"
    output_json = "output_pose_data.json"

    try:
        # Process video
        pose_frames = detector.process_video(
            video_path,
            save_visualization=True,
            output_path=output_video
        )

        # Export to JSON
        detector.export_to_json(pose_frames, output_json)

        # Analyze airborne segments
        airborne_frames = [f for f in pose_frames if f.is_airborne]
        print(f"\n📊 Analysis:")
        print(f"   Total frames: {len(pose_frames)}")
        print(f"   Airborne frames: {len(airborne_frames)}")
        print(f"   Airborne percentage: {len(airborne_frames)/len(pose_frames)*100:.1f}%")

    finally:
        detector.close()


if __name__ == "__main__":
    test_advanced_pose_detector()
