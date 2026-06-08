"""
Feature Extractor — OpenCV-based (no MediaPipe required)
Converts a video clip into a fixed-length feature vector for ML classification.
"""

from __future__ import annotations

import warnings
import os
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    warnings.warn("opencv-python not available — VideoFeatureExtractor will not work")


FEATURE_NAMES = [
    "y_mean", "y_std", "y_min", "y_max",
    "y_vel_mean", "y_vel_std", "y_vel_max",
    "y_accel_max", "y_accel_std",
    "x_std", "x_range",
    "aspect_mean", "aspect_std",
    "width_std", "height_std",
    "peak_frame_ratio",
    "duration", "fps", "frame_count",
    "motion_density", "avg_bbox_area",
]
N_FEATURES = len(FEATURE_NAMES)  # 21


class VideoFeatureExtractor:
    """Extract temporal features from skating video clips using OpenCV MOG2."""

    def __init__(self):
        self.feature_names = FEATURE_NAMES

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_clip_features(self, video_path: str) -> Optional[dict]:
        """
        Extract aggregate statistical features from a video clip.

        Returns a dict with 21 features, or None if extraction fails.
        """
        if not CV2_AVAILABLE:
            warnings.warn("cv2 not available")
            return None

        if not os.path.exists(video_path):
            warnings.warn(f"Video not found: {video_path}")
            return None

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                warnings.warn(f"Cannot open video: {video_path}")
                return None

            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if frame_w == 0 or frame_h == 0:
                cap.release()
                warnings.warn(f"Invalid frame dimensions for: {video_path}")
                return None

            fgbg = cv2.createBackgroundSubtractorMOG2(
                history=50, varThreshold=25, detectShadows=False
            )

            norm_y_list = []
            norm_x_list = []
            width_ratio_list = []
            height_ratio_list = []
            aspect_ratio_list = []
            frames_with_motion = 0
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                fgmask = fgbg.apply(frame)
                # Morphological cleanup
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(
                    fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest)
                    if area > 100:  # noise threshold
                        x, y, w, h = cv2.boundingRect(largest)
                        cx = x + w / 2
                        cy = y + h / 2
                        norm_x_list.append(cx / frame_w)
                        norm_y_list.append(cy / frame_h)
                        width_ratio_list.append(w / frame_w)
                        height_ratio_list.append(h / frame_h)
                        asp = w / h if h > 0 else 1.0
                        aspect_ratio_list.append(asp)
                        frames_with_motion += 1

                frame_idx += 1

            cap.release()

            n = len(norm_y_list)
            if n < 3:
                warnings.warn(f"Too little motion detected in: {video_path}")
                return None

            norm_y = np.array(norm_y_list, dtype=np.float32)
            norm_x = np.array(norm_x_list, dtype=np.float32)
            width_r = np.array(width_ratio_list, dtype=np.float32)
            height_r = np.array(height_ratio_list, dtype=np.float32)
            aspect = np.array(aspect_ratio_list, dtype=np.float32)

            # Velocity and acceleration
            vel_y = np.diff(norm_y)
            vel_x = np.diff(norm_x)
            accel_y = np.diff(vel_y) if len(vel_y) > 1 else np.array([0.0])

            # Peak frame (highest point = minimum norm_y since y increases downward)
            peak_idx = int(np.argmin(norm_y))
            peak_frame_ratio = peak_idx / max(n - 1, 1)

            duration = frame_idx / fps if fps > 0 else 0.0
            motion_density = frames_with_motion / max(frame_idx, 1)
            avg_bbox_area = float(np.mean(width_r * height_r))

            features = {
                "y_mean": float(np.mean(norm_y)),
                "y_std": float(np.std(norm_y)),
                "y_min": float(np.min(norm_y)),
                "y_max": float(np.max(norm_y)),
                "y_vel_mean": float(np.mean(np.abs(vel_y))),
                "y_vel_std": float(np.std(vel_y)),
                "y_vel_max": float(np.max(np.abs(vel_y))),
                "y_accel_max": float(np.max(np.abs(accel_y))),
                "y_accel_std": float(np.std(accel_y)),
                "x_std": float(np.std(norm_x)),
                "x_range": float(np.max(norm_x) - np.min(norm_x)),
                "aspect_mean": float(np.mean(aspect)),
                "aspect_std": float(np.std(aspect)),
                "width_std": float(np.std(width_r)),
                "height_std": float(np.std(height_r)),
                "peak_frame_ratio": float(peak_frame_ratio),
                "duration": float(duration),
                "fps": float(fps),
                "frame_count": float(frame_idx),
                "motion_density": float(motion_density),
                "avg_bbox_area": float(avg_bbox_area),
            }

            return features

        except Exception as e:
            warnings.warn(f"Feature extraction failed for {video_path}: {e}")
            return None

    def to_vector(self, features: dict) -> np.ndarray:
        """Convert feature dict to a flat numpy array (21 features)."""
        return np.array([features[k] for k in FEATURE_NAMES], dtype=np.float32)

    def extract_sequence_features(
        self, video_path: str, seq_len: int = 60
    ) -> Optional[np.ndarray]:
        """
        Returns (seq_len, 6) array:
        [norm_y, norm_x, velocity_y, velocity_x, aspect_ratio, bbox_area]

        Resampled to exactly seq_len frames using linear interpolation.
        """
        if not CV2_AVAILABLE:
            return None

        if not os.path.exists(video_path):
            return None

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None

            frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if frame_w == 0 or frame_h == 0:
                cap.release()
                return None

            fgbg = cv2.createBackgroundSubtractorMOG2(
                history=50, varThreshold=25, detectShadows=False
            )

            rows = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                fgmask = fgbg.apply(frame)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
                fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

                contours, _ = cv2.findContours(
                    fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                if contours:
                    largest = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest)
                    if area > 100:
                        x, y, w, h = cv2.boundingRect(largest)
                        cx = (x + w / 2) / frame_w
                        cy = (y + h / 2) / frame_h
                        asp = w / h if h > 0 else 1.0
                        bbox_area = (w / frame_w) * (h / frame_h)
                        rows.append([cy, cx, 0.0, 0.0, asp, bbox_area])
                    else:
                        rows.append([0.5, 0.5, 0.0, 0.0, 1.0, 0.0])
                else:
                    rows.append([0.5, 0.5, 0.0, 0.0, 1.0, 0.0])

            cap.release()

            if len(rows) < 2:
                return None

            seq = np.array(rows, dtype=np.float32)
            # Compute velocities
            vel = np.diff(seq[:, :2], axis=0, prepend=seq[:1, :2])
            seq[:, 2] = vel[:, 0]  # velocity_y
            seq[:, 3] = vel[:, 1]  # velocity_x

            # Resample to seq_len using linear interpolation
            T = len(seq)
            old_idx = np.linspace(0, 1, T)
            new_idx = np.linspace(0, 1, seq_len)
            result = np.zeros((seq_len, 6), dtype=np.float32)
            for col in range(6):
                result[:, col] = np.interp(new_idx, old_idx, seq[:, col])

            return result

        except Exception as e:
            warnings.warn(f"Sequence extraction failed for {video_path}: {e}")
            return None

    def batch_extract(
        self,
        video_paths: list,
        labels: list,
        verbose: bool = True,
    ) -> tuple:
        """
        Process all videos and return X (n_samples, n_features), y (n_samples,).
        Uses LABEL2IDX from src.models.lstm_classifier.
        Skips failed extractions with a warning.
        """
        try:
            from src.models.lstm_classifier import LABEL2IDX
        except ImportError:
            warnings.warn("Could not import LABEL2IDX — using local mapping")
            LABEL2IDX = {}

        X_list = []
        y_list = []
        skipped = 0

        for i, (vpath, label) in enumerate(zip(video_paths, labels)):
            if verbose:
                print(f"[{i+1}/{len(video_paths)}] Extracting: {os.path.basename(vpath)} ({label})")

            feats = self.extract_clip_features(vpath)
            if feats is None:
                warnings.warn(f"Skipping failed extraction: {vpath}")
                skipped += 1
                continue

            vec = self.to_vector(feats)
            label_idx = LABEL2IDX.get(label, -1)
            if label_idx == -1:
                # Build dynamic mapping if label not found
                all_unique = sorted(set(labels))
                dyn_map = {l: idx for idx, l in enumerate(all_unique)}
                label_idx = dyn_map.get(label, 0)

            X_list.append(vec)
            y_list.append(label_idx)

        if verbose:
            print(f"Extracted {len(X_list)} features, skipped {skipped}")

        if not X_list:
            return np.zeros((0, N_FEATURES), dtype=np.float32), np.zeros(0, dtype=np.int32)

        return (
            np.array(X_list, dtype=np.float32),
            np.array(y_list, dtype=np.int32),
        )
