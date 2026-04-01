"""
Feature Extractor for Video Analysis
استخراج المميزات من الفيديوهات

Extracts features from annotated videos for ML training
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pickle
from datetime import datetime

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from src.core.advanced_pose_detector import AdvancedPoseDetector, MEDIAPIPE_AVAILABLE
except ImportError:
    AdvancedPoseDetector = None
    MEDIAPIPE_AVAILABLE = False


@dataclass
class VideoFeatures:
    """Extracted features from a video"""
    video_path: str
    video_id: str
    category: str
    subcategory: str
    skill_level: Optional[str] = None

    # Temporal features
    duration: float = 0.0
    num_frames: int = 0
    fps: float = 0.0

    # Pose features (aggregated)
    avg_body_angle: float = 0.0
    std_body_angle: float = 0.0
    avg_center_of_mass_height: float = 0.0
    std_center_of_mass_height: float = 0.0

    # Movement features
    avg_motion_magnitude: float = 0.0
    max_motion_magnitude: float = 0.0
    total_distance_traveled: float = 0.0

    # Rotation features
    total_rotation: float = 0.0
    max_angular_velocity: float = 0.0
    avg_angular_velocity: float = 0.0

    # Jump features (if applicable)
    num_airborne_frames: int = 0
    max_jump_height: float = 0.0
    avg_jump_height: float = 0.0

    # Pose landmark features (33 landmarks × 4 coordinates = 132 features)
    # We'll store statistical aggregates
    landmark_features: Optional[np.ndarray] = None

    # Raw pose sequence (for advanced models)
    pose_sequence: Optional[List[Dict]] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        # Convert numpy arrays to lists for JSON serialization
        if self.landmark_features is not None:
            data['landmark_features'] = self.landmark_features.tolist()
        return data

    def to_feature_vector(self, include_landmarks: bool = True) -> np.ndarray:
        """Convert to flat feature vector for ML"""
        features = [
            self.duration,
            self.num_frames,
            self.fps,
            self.avg_body_angle,
            self.std_body_angle,
            self.avg_center_of_mass_height,
            self.std_center_of_mass_height,
            self.avg_motion_magnitude,
            self.max_motion_magnitude,
            self.total_distance_traveled,
            self.total_rotation,
            self.max_angular_velocity,
            self.avg_angular_velocity,
            self.num_airborne_frames,
            self.max_jump_height,
            self.avg_jump_height,
        ]

        if include_landmarks and self.landmark_features is not None:
            features.extend(self.landmark_features.tolist())

        return np.array(features, dtype=np.float32)


class FeatureExtractor:
    """
    Extracts features from videos for ML training
    """

    def __init__(
        self,
        use_pose_detector: bool = True,
        save_pose_sequences: bool = False,
        output_dir: str = 'data/features'
    ):
        """
        Initialize feature extractor

        Args:
            use_pose_detector: Use MediaPipe pose detection
            save_pose_sequences: Save full pose sequences (large files)
            output_dir: Directory to save extracted features
        """
        self.use_pose_detector = use_pose_detector and MEDIAPIPE_AVAILABLE
        self.save_pose_sequences = save_pose_sequences
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.use_pose_detector:
            if not MEDIAPIPE_AVAILABLE:
                print("⚠️ MediaPipe not available. Falling back to basic features.")
                self.use_pose_detector = False
            else:
                self.pose_detector = AdvancedPoseDetector(
                    model_complexity=1,  # Faster for batch processing
                    min_detection_confidence=0.5
                )

        self.extracted_features: List[VideoFeatures] = []

    def extract_from_video(self, video_path: str, label: Dict) -> Optional[VideoFeatures]:
        """
        Extract features from a single video

        Args:
            video_path: Path to video file
            label: Dict with category, subcategory, skill_level

        Returns:
            VideoFeatures object or None if failed
        """
        if not Path(video_path).exists():
            print(f"❌ Video not found: {video_path}")
            return None

        print(f"🔍 Extracting features from: {Path(video_path).name}")

        try:
            # Initialize features object
            features = VideoFeatures(
                video_path=video_path,
                video_id=Path(video_path).stem,
                category=label.get('category', 'unknown'),
                subcategory=label.get('subcategory', 'unknown'),
                skill_level=label.get('skill_level', 'unknown')
            )

            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Could not open video: {video_path}")
                return None

            # Basic video properties
            features.fps = cap.get(cv2.CAP_PROP_FPS)
            features.num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            features.duration = features.num_frames / features.fps if features.fps > 0 else 0

            if self.use_pose_detector:
                # Extract pose-based features
                features = self._extract_pose_features(cap, features)
            else:
                # Extract basic motion features
                features = self._extract_motion_features(cap, features)

            cap.release()

            self.extracted_features.append(features)
            print(f"✅ Extracted features: {features.video_id}")

            return features

        except Exception as e:
            print(f"❌ Error extracting features from {video_path}: {e}")
            return None

    def _extract_pose_features(self, cap, features: VideoFeatures) -> VideoFeatures:
        """Extract features using pose detection"""

        # Process video with pose detector
        pose_frames = []
        frame_idx = 0

        # Sample frames (process every Nth frame for speed)
        sample_rate = max(1, int(features.fps / 10))  # ~10 FPS sampling

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_rate == 0:
                # Detect pose
                results = self.pose_detector.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if results.pose_landmarks:
                    # Extract landmarks
                    landmarks = {}
                    for idx, landmark in enumerate(results.pose_landmarks.landmark):
                        landmarks[self.pose_detector.LANDMARK_NAMES[idx]] = {
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility
                        }

                    pose_frames.append({
                        'frame': frame_idx,
                        'landmarks': landmarks
                    })

            frame_idx += 1

        if not pose_frames:
            print("⚠️ No pose detected in video")
            return features

        # Calculate aggregate features
        body_angles = []
        com_heights = []
        angular_velocities = []

        prev_angle = None

        for pose_frame in pose_frames:
            landmarks = pose_frame['landmarks']

            # Calculate body angle
            if 'left_shoulder' in landmarks and 'left_hip' in landmarks:
                shoulder = landmarks['left_shoulder']
                hip = landmarks['left_hip']
                angle = np.arctan2(hip['y'] - shoulder['y'], hip['x'] - shoulder['x'])
                body_angles.append(angle)

                if prev_angle is not None:
                    angular_velocity = abs(angle - prev_angle) * features.fps / sample_rate
                    angular_velocities.append(angular_velocity)
                prev_angle = angle

            # Calculate center of mass height (approximate)
            if 'left_hip' in landmarks and 'right_hip' in landmarks:
                hip_y = (landmarks['left_hip']['y'] + landmarks['right_hip']['y']) / 2
                com_heights.append(1.0 - hip_y)  # Invert (higher = more airborne)

        # Aggregate statistics
        if body_angles:
            features.avg_body_angle = float(np.mean(body_angles))
            features.std_body_angle = float(np.std(body_angles))

        if com_heights:
            features.avg_center_of_mass_height = float(np.mean(com_heights))
            features.std_center_of_mass_height = float(np.std(com_heights))
            features.max_jump_height = float(np.max(com_heights))

            # Count airborne frames (above threshold)
            threshold = np.mean(com_heights) + 0.5 * np.std(com_heights)
            features.num_airborne_frames = int(np.sum(np.array(com_heights) > threshold))

            if features.num_airborne_frames > 0:
                airborne_heights = [h for h in com_heights if h > threshold]
                features.avg_jump_height = float(np.mean(airborne_heights))

        if angular_velocities:
            features.avg_angular_velocity = float(np.mean(angular_velocities))
            features.max_angular_velocity = float(np.max(angular_velocities))
            features.total_rotation = float(np.sum(angular_velocities))

        # Create landmark feature vector (statistical aggregates of all landmarks)
        landmark_stats = []
        for landmark_name in self.pose_detector.LANDMARK_NAMES.values():
            x_vals = [pf['landmarks'].get(landmark_name, {}).get('x', 0) for pf in pose_frames]
            y_vals = [pf['landmarks'].get(landmark_name, {}).get('y', 0) for pf in pose_frames]
            z_vals = [pf['landmarks'].get(landmark_name, {}).get('z', 0) for pf in pose_frames]

            # Mean and std for x, y, z
            landmark_stats.extend([
                np.mean(x_vals), np.std(x_vals),
                np.mean(y_vals), np.std(y_vals),
                np.mean(z_vals), np.std(z_vals)
            ])

        features.landmark_features = np.array(landmark_stats, dtype=np.float32)

        # Save pose sequence if requested
        if self.save_pose_sequences:
            features.pose_sequence = pose_frames

        return features

    def _extract_motion_features(self, cap, features: VideoFeatures) -> VideoFeatures:
        """Extract basic motion features without pose detection"""

        prev_gray = None
        motion_magnitudes = []

        frame_idx = 0
        sample_rate = max(1, int(features.fps / 10))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_rate == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if prev_gray is not None:
                    # Calculate optical flow
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, gray, None,
                        0.5, 3, 15, 3, 5, 1.2, 0
                    )

                    # Calculate motion magnitude
                    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                    motion_magnitudes.append(np.mean(magnitude))

                prev_gray = gray

            frame_idx += 1

        if motion_magnitudes:
            features.avg_motion_magnitude = float(np.mean(motion_magnitudes))
            features.max_motion_magnitude = float(np.max(motion_magnitudes))
            features.total_distance_traveled = float(np.sum(motion_magnitudes))

        return features

    def extract_from_annotated_videos(
        self,
        annotation_file: str,
        max_videos: Optional[int] = None
    ) -> List[VideoFeatures]:
        """
        Extract features from all annotated videos

        Args:
            annotation_file: Path to JSON file with annotations
            max_videos: Maximum number of videos to process

        Returns:
            List of VideoFeatures objects
        """
        print(f"📂 Loading annotations from: {annotation_file}")

        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        videos = data.get('videos', [])

        # Filter annotated videos
        annotated = [v for v in videos if v.get('annotated', False)]
        print(f"✅ Found {len(annotated)} annotated videos")

        if max_videos:
            annotated = annotated[:max_videos]
            print(f"📊 Processing first {max_videos} videos")

        # Extract features from each video
        for video_data in annotated:
            label = {
                'category': video_data.get('category'),
                'subcategory': video_data.get('subcategory'),
                'skill_level': video_data.get('skill_level')
            }

            self.extract_from_video(video_data['filepath'], label)

        return self.extracted_features

    def save_features(self, filename: str = 'extracted_features.pkl'):
        """Save extracted features to file"""
        output_path = self.output_dir / filename

        with open(output_path, 'wb') as f:
            pickle.dump(self.extracted_features, f)

        print(f"💾 Saved {len(self.extracted_features)} feature sets to: {output_path}")

        # Also save as JSON (without pose sequences)
        json_path = self.output_dir / filename.replace('.pkl', '.json')
        json_data = {
            'extraction_date': datetime.now().isoformat(),
            'total_videos': len(self.extracted_features),
            'features': [f.to_dict() for f in self.extracted_features]
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 Saved JSON summary to: {json_path}")

    def load_features(self, filename: str = 'extracted_features.pkl'):
        """Load previously extracted features"""
        input_path = self.output_dir / filename

        if not input_path.exists():
            print(f"❌ File not found: {input_path}")
            return

        with open(input_path, 'rb') as f:
            self.extracted_features = pickle.load(f)

        print(f"✅ Loaded {len(self.extracted_features)} feature sets from: {input_path}")

    def get_training_data(
        self,
        target: str = 'category',
        include_landmarks: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Get training data in format for sklearn

        Args:
            target: What to predict ('category', 'subcategory', 'skill_level')
            include_landmarks: Include landmark features

        Returns:
            (X, y, labels) - Features, targets, label names
        """
        X = []
        y = []
        label_set = set()

        for features in self.extracted_features:
            # Get target label
            if target == 'category':
                label = features.category
            elif target == 'subcategory':
                label = features.subcategory
            elif target == 'skill_level':
                label = features.skill_level
            else:
                raise ValueError(f"Unknown target: {target}")

            if not label or label == 'unknown':
                continue

            # Get feature vector
            feature_vec = features.to_feature_vector(include_landmarks=include_landmarks)

            X.append(feature_vec)
            y.append(label)
            label_set.add(label)

        # Convert to numpy arrays
        X = np.array(X, dtype=np.float32)

        # Encode labels
        label_list = sorted(list(label_set))
        label_to_idx = {label: idx for idx, label in enumerate(label_list)}
        y = np.array([label_to_idx[label] for label in y], dtype=np.int32)

        print(f"📊 Training data: {X.shape[0]} samples, {X.shape[1]} features, {len(label_list)} classes")

        return X, y, label_list


if __name__ == "__main__":
    # Example usage
    extractor = FeatureExtractor(use_pose_detector=True)

    # Extract from annotated videos
    extractor.extract_from_annotated_videos(
        'data/scanned_videos/scan_results.json',
        max_videos=10
    )

    # Save features
    extractor.save_features()

    # Get training data
    X, y, labels = extractor.get_training_data(target='category')
    print(f"Labels: {labels}")
