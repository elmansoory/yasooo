"""
🎥 صفحة تحليل الفيديو الاحترافية — YASOOO Figure Skating Analysis
تحليل كامل: قفزات · دورانات · وضعية الجسم · أخطاء فنية · درجات ISU
"""

import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import re
import time
import io
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── OpenCV ──────────────────────────────────────────────────────────────────
try:
    import cv2
    CV2_OK = True
except ImportError:
    CV2_OK = False

# ── MediaPipe (Tasks API — needs OpenGL, optional) ───────────────────────────
try:
    import mediapipe as mp
    from mediapipe.tasks.python import vision as _mp_vision, BaseOptions as _MP_BaseOptions
    from mediapipe.tasks.python.vision import (
        PoseLandmarkerOptions as _PoseLandmarkerOptions,
        RunningMode as _RunningMode,
        PoseLandmarker as _PoseLandmarker,
    )
    _MP_MODEL = Path('data/models/pose_landmarker_lite.task')
    MP_OK = _MP_MODEL.exists()
except Exception:
    MP_OK = False

DB_PATH = "skating_database.db"

# ============================================================================
# ISU 2024 BASE VALUES
# ============================================================================
ISU_BASE = {
    # Single jumps
    'Axel': 1.10, '1A': 1.10,
    '2A': 3.30, 'Double Axel': 3.30,
    '3A': 8.00, 'Triple Axel': 8.00,
    '4A': 12.50, 'Quad Axel': 12.50,
    '2S': 1.30, 'Double Salchow': 1.30,
    '3S': 4.30, 'Triple Salchow': 4.30,
    '4S': 9.70, 'Quad Salchow': 9.70,
    '2T': 1.30, 'Double Toe': 1.30,
    '3T': 4.20, 'Triple Toe': 4.20,
    '4T': 9.50, 'Quad Toe': 9.50,
    '2Lo': 1.70, 'Double Loop': 1.70,
    '3Lo': 4.90, 'Triple Loop': 4.90,
    '4Lo': 10.50, 'Quad Loop': 10.50,
    '2F': 1.80, 'Double Flip': 1.80,
    '3F': 5.30, 'Triple Flip': 5.30,
    '4F': 11.00, 'Quad Flip': 11.00,
    '2Lz': 2.10, 'Double Lutz': 2.10,
    '3Lz': 5.90, 'Triple Lutz': 5.90,
    '4Lz': 11.50, 'Quad Lutz': 11.50,
    # Spins
    'USp': 1.20, 'Upright Spin': 1.20,
    'SSp': 1.70, 'Sit Spin': 1.70,
    'CSp': 1.90, 'Camel Spin': 1.90,
    'LSp': 1.50, 'Layback Spin': 1.50,
    'CCoSp': 3.50, 'Change Combination Spin': 3.50,
    'CoSp': 2.50, 'Combination Spin': 2.50,
}

# ============================================================================
# CORE ANALYSIS ENGINE (OpenCV + MediaPipe)
# ============================================================================

def _airtime_to_rotations(airtime: float) -> float:
    """Convert air time to estimated rotations."""
    # Elite skaters rotate ~3 rev/s while in the air
    return max(0.5, airtime * 3.0)

def _classify_jump(airtime: float, height_norm: float) -> Dict:
    """Classify jump type and score from biometrics."""
    rotations = _airtime_to_rotations(airtime)

    if rotations >= 3.5:
        if airtime > 0.75:
            typ = 'Quad Lutz'; code = '4Lz'
        else:
            typ = 'Quad Toe'; code = '4T'
    elif rotations >= 2.8:
        typ = 'Triple Lutz'; code = '3Lz'
    elif rotations >= 2.3:
        if airtime > 0.6:
            typ = 'Triple Axel'; code = '3A'
        else:
            typ = 'Triple Flip'; code = '3F'
    elif rotations >= 1.8:
        typ = 'Double Axel'; code = '2A'
    elif rotations >= 1.3:
        typ = 'Double Lutz'; code = '2Lz'
    else:
        typ = 'Single Axel'; code = '1A'

    base = ISU_BASE.get(code, 1.0)
    height_cm = int(height_norm * 60)  # rough: 100% screen height ≈ 60cm
    height_cm = max(15, min(70, height_cm))

    # GOE heuristic: height bonus
    goe = 1 if height_cm >= 45 else (0 if height_cm >= 30 else -1)

    return {
        'type': typ,
        'code': code,
        'rotations': round(rotations, 1),
        'height_cm': height_cm,
        'airtime': round(airtime, 3),
        'rpm': round(rotations / airtime * 60) if airtime > 0 else 0,
        'goe': goe,
        'base_value': base,
        'final_score': round(base + goe * base * 0.1, 2),
        'is_clean': goe >= 0,
    }


def _classify_spin(duration: float, rpm: float) -> Dict:
    """Classify spin based on duration and speed."""
    if rpm < 50:
        typ = 'Camel Spin'; code = 'CSp'; base = 1.90
    elif rpm < 80:
        typ = 'Sit Spin'; code = 'SSp'; base = 1.70
    elif rpm < 120:
        typ = 'Upright Spin'; code = 'USp'; base = 1.20
    else:
        typ = 'Change Combination Spin'; code = 'CCoSp'; base = 3.50

    rotations = rpm * duration / 60
    level = min(4, max(1, int(rotations / 3)))
    level_bonus = level * 0.10 * base
    goe = 1 if rotations >= 8 else (0 if rotations >= 5 else -1)

    return {
        'type': typ,
        'code': code,
        'rotations': round(rotations, 1),
        'rpm': round(rpm),
        'duration': round(duration, 1),
        'level': level,
        'goe': goe,
        'base_value': base,
        'final_score': round(base + level_bonus + goe * base * 0.1, 2),
    }


class SkatingVideoAnalyzer:
    """Full pipeline: MediaPipe pose → jump/spin/error detection → ISU scores."""

    def __init__(self):
        self.fps = 30.0
        self.total_frames = 0
        self.width = 0
        self.height = 0

    def analyze(self, video_path: str, progress_cb=None) -> Dict:
        """Main entry point. Returns full analysis dict."""
        if not CV2_OK:
            return self._error_result("OpenCV not installed")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return self._error_result("Cannot open video file")

        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = self.total_frames / self.fps
        cap.release()

        video_info = {
            'fps': self.fps,
            'frame_count': self.total_frames,
            'width': self.width,
            'height': self.height,
            'duration': duration,
            'orientation': 'Portrait' if self.height > self.width else 'Landscape',
        }

        # ── Pose extraction ──────────────────────────────────────────────────
        self._skeleton_frames = []
        self._pose_samples = []
        self._skeleton_video_bytes = None
        used_mediapipe = True
        try:
            if MP_OK:
                poses, frame_scores = self._extract_poses_mediapipe(video_path, progress_cb)
            else:
                used_mediapipe = False
                poses, frame_scores = self._extract_motion_opencv(video_path, progress_cb)
        except Exception:
            used_mediapipe = False
            poses, frame_scores = self._extract_motion_opencv(video_path, progress_cb)

        if not poses:
            return self._error_result("No person detected in video")

        # Data-quality flag: the OpenCV contour fallback tracks a moving blob,
        # not a real skeleton — jump/spin detection on it is much less
        # reliable and more prone to false positives (shadows, other people,
        # camera motion). Real MediaPipe keypoint coverage is also checked.
        kp_coverage = (sum(1 for p in poses if p.get('kp')) / len(poses)) if poses else 0.0
        low_confidence = (not used_mediapipe) or kp_coverage < 0.5

        # ── Element detection — spins FIRST, then exclude spin windows from jump detection ──
        spins = self._detect_spins(poses)
        jumps = self._detect_jumps(poses, spin_windows=[(s['t_start'], s['t_end']) for s in spins])

        # ── Refine rotation count using real shoulder-angle tracking ─────────
        for j in jumps:
            t0, t1 = j.get('t_start', 0), j.get('t_end', 0)
            seg_kp = [p['kp'] for p in poses if t0 <= p['t'] <= t1 and 'kp' in p]
            real_rot = _compute_rotation_from_kp(seg_kp)
            if real_rot is not None:
                j['rotations'] = round(real_rot, 1)
                # Re-classify with refined rotations
                j['rpm'] = round(real_rot / j['airtime'] * 60) if j['airtime'] > 0 else j['rpm']
                # Update code/type based on measured rotations
                if real_rot >= 3.5:
                    j['code'] = '4T'; j['type'] = 'Quad Toe'
                elif real_rot >= 2.8:
                    j['code'] = '3Lz'; j['type'] = 'Triple Lutz'
                elif real_rot >= 2.3:
                    j['code'] = '3A' if j['airtime'] > 0.6 else '3F'
                    j['type'] = 'Triple Axel' if j['airtime'] > 0.6 else 'Triple Flip'
                elif real_rot >= 1.8:
                    j['code'] = '2A'; j['type'] = 'Double Axel'
                elif real_rot >= 1.3:
                    j['code'] = '2Lz'; j['type'] = 'Double Lutz'
                else:
                    j['code'] = '1A'; j['type'] = 'Single Axel'
                j['base_value'] = ISU_BASE.get(j['code'], 1.0)
                j['final_score'] = round(j['base_value'] + j['goe'] * j['base_value'] * 0.1, 2)
                j['rotation_method'] = 'shoulder_tracking'
            else:
                j['rotation_method'] = 'airtime_heuristic'

        errors = self._detect_errors(poses, jumps, spins)

        # ── AI Movement Engine enhancement ────────────────────────────────────
        step_sequences = []
        ai_status = {}
        try:
            from src.analysis.ai_movement_engine import AIMovementEngine
            engine = AIMovementEngine()
            ai_status = engine.status()
            jumps  = [engine.enhance_jump(j, poses) for j in jumps]
            spins  = [engine.enhance_spin(s, poses) for s in spins]
            step_sequences = engine.detect_step_sequences(poses, jumps, spins)
            errors += self._detect_ai_errors(jumps, spins)
        except Exception:
            pass

        timeline = self._build_timeline(poses, jumps, spins, step_sequences)

        # ── Scoring ──────────────────────────────────────────────────────────
        tes = (sum(j['final_score'] for j in jumps)
               + sum(s['final_score'] for s in spins)
               + sum(ss['final_score'] for ss in step_sequences))
        pcs = round(min(10, max(3, 8 - len(errors) * 0.5)) * 2, 2)

        return {
            'video_info': video_info,
            'jumps': jumps,
            'spins': spins,
            'step_sequences': step_sequences,
            'errors': errors,
            'timeline': timeline,
            'total_score': round(tes + pcs, 2),
            'tes': round(tes, 2),
            'pcs': pcs,
            'pose_count': len(poses),
            'skeleton_frames': self._skeleton_frames,
            'pose_samples': self._pose_samples,
            'skeleton_video_bytes': getattr(self, '_skeleton_video_bytes', None),
            'ai_status': ai_status,
            'low_confidence': low_confidence,
            'kp_coverage': round(kp_coverage, 2),
            'used_mediapipe': used_mediapipe,
            'is_demo': False,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

    # ── MediaPipe Tasks API pose extraction ─────────────────────────────────
    def _extract_poses_mediapipe(self, video_path: str, progress_cb) -> Tuple[List, List]:
        poses = []
        self._skeleton_frames = []   # base64-encoded JPEG frames with skeleton overlay
        self._pose_samples = []      # every 10th pose kp list for 3D playback
        self._skeleton_video_bytes = None  # full overlay video — the moving skeleton on the body

        options = _PoseLandmarkerOptions(
            base_options=_MP_BaseOptions(model_asset_path=str(_MP_MODEL)),
            running_mode=_RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.45,
            min_pose_presence_confidence=0.45,
            min_tracking_confidence=0.45,
        )
        cap = cv2.VideoCapture(video_path)
        fi = 0
        SKIP = 2                   # process every 2nd frame
        SKEL_EVERY = max(1, int(self.fps))   # save skeleton frame every ~1s

        # ── Full-video skeleton overlay writer ──────────────────────────────
        # Downscale to keep the file small; hold the last known skeleton on
        # skipped frames so the overlay reads as continuous motion, not a
        # flicker every other frame.
        WRITE_MAX_SEC = 120  # cap output duration to keep the file reasonable
        out_w = min(640, self.width) if self.width else 480
        out_scale = out_w / self.width if self.width else 1.0
        out_w = max(2, int(out_w) - (int(out_w) % 2))
        out_h = max(2, int(self.height * out_scale) - (int(self.height * out_scale) % 2)) if self.height else 360
        skel_video_path = None
        writer = None
        if CV2_OK and self.fps > 0:
            try:
                skel_video_path = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False).name
                for fourcc_code in ('avc1', 'H264', 'mp4v'):
                    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                    writer = cv2.VideoWriter(skel_video_path, fourcc, self.fps, (out_w, out_h))
                    if writer.isOpened():
                        break
                    writer.release()
                    writer = None
                if writer is None:
                    skel_video_path = None
            except Exception:
                writer, skel_video_path = None, None

        last_kp = None
        write_frame_limit = int(WRITE_MAX_SEC * self.fps) if self.fps > 0 else 0

        with _PoseLandmarker.create_from_options(options) as lm_model:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if fi % SKIP == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    timestamp_ms = int(fi * 1000 / self.fps)
                    result = lm_model.detect_for_video(mp_img, timestamp_ms)

                    if result.pose_landmarks:
                        lms = result.pose_landmarks[0]
                        kp = [
                            {'x': lm.x, 'y': lm.y, 'z': lm.z, 'v': lm.visibility, 'idx': i}
                            for i, lm in enumerate(lms)
                        ]
                        # Shoulder rotation angle (XZ plane) for rotation tracking
                        ls, rs = kp[11], kp[12]
                        if ls['v'] > 0.2 and rs['v'] > 0.2:
                            sh_angle = float(np.arctan2(
                                rs['z'] - ls['z'], rs['x'] - ls['x']
                            ))
                        else:
                            sh_angle = 0.0

                        is_airborne = self._is_airborne(kp)
                        pose_entry = {
                            'frame': fi, 't': fi / self.fps,
                            'kp': kp, 'airborne': is_airborne,
                            'sh_angle': sh_angle,
                        }
                        poses.append(pose_entry)
                        last_kp = kp

                        # Save skeleton overlay frame (~1 per second, max 60 frames)
                        pose_idx = len(poses) - 1
                        if pose_idx % max(1, SKEL_EVERY // SKIP) == 0 and len(self._skeleton_frames) < 60:
                            ann = _draw_skeleton_on_frame(frame, kp, self.width, self.height)
                            self._skeleton_frames.append({
                                'b64': _frame_to_b64(ann),
                                't': fi / self.fps,
                                'airborne': is_airborne,
                            })

                        # Store every 10th detected pose for 3D playback
                        if pose_idx % 10 == 0 and len(self._pose_samples) < 120:
                            self._pose_samples.append({
                                'kp': kp, 't': fi / self.fps,
                                'airborne': is_airborne,
                            })

                    if progress_cb and self.total_frames > 0:
                        progress_cb(fi / self.total_frames, fi)

                # Write this frame to the full overlay video, holding the
                # last detected skeleton across skipped/undetected frames.
                if writer is not None and fi < write_frame_limit:
                    ann_full = (
                        _draw_skeleton_on_frame(frame, last_kp, self.width, self.height)
                        if last_kp is not None else frame
                    )
                    small = cv2.resize(ann_full, (out_w, out_h), interpolation=cv2.INTER_AREA)
                    writer.write(small)

                fi += 1

        cap.release()
        if writer is not None:
            writer.release()
            try:
                if skel_video_path and os.path.getsize(skel_video_path) > 0:
                    with open(skel_video_path, 'rb') as vf:
                        self._skeleton_video_bytes = vf.read()
            except Exception:
                self._skeleton_video_bytes = None
            finally:
                try:
                    os.unlink(skel_video_path)
                except Exception:
                    pass

        return poses, []

    # ── OpenCV Advanced Motion Analysis ─────────────────────────────────────
    def _extract_motion_opencv(self, video_path: str, progress_cb) -> Tuple[List, List]:
        """
        Advanced background subtraction + optical flow to track skater.
        Builds pseudo-keypoints from bounding box geometry for downstream analysis.
        """
        poses = []
        bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=35, detectShadows=False
        )
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        cap = cv2.VideoCapture(video_path)

        # Warm-up background model
        for fi_bg in range(min(40, self.total_frames)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, fi_bg)
            ret, fr = cap.read()
            if ret:
                bg_sub.apply(fr)

        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        fi = 0
        prev_norm_y = None
        prev_norm_x = None
        velocity_y = 0.0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            fg = bg_sub.apply(frame)
            fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel_open)
            fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel_close)

            contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Largest contour = skater
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)

                if area > 300:
                    bx, by, bw, bh = cv2.boundingRect(largest)

                    # Normalize to [0,1]
                    norm_y = (by + bh * 0.5) / self.height
                    norm_x = (bx + bw * 0.5) / self.width
                    norm_h = bh / self.height
                    norm_w = bw / self.width

                    # Velocity (upward = negative delta)
                    if prev_norm_y is not None:
                        velocity_y = norm_y - prev_norm_y
                    prev_norm_y = norm_y
                    prev_norm_x = norm_x

                    # Airborne heuristic:
                    # 1. Skater is high in frame (norm_y low)
                    # 2. Body becomes compact (aspect ratio changes)
                    # 3. Upward velocity
                    ankle_y = (by + bh) / self.height
                    hip_y = (by + bh * 0.45) / self.height
                    leg_gap = ankle_y - hip_y
                    is_airborne = (leg_gap < 0.18) or (velocity_y < -0.012 and norm_y < 0.45)

                    # Build pseudo-keypoints mimicking MediaPipe format
                    # (approximate body proportions from bbox)
                    kp = self._bbox_to_pseudo_kp(bx, by, bw, bh)

                    poses.append({
                        'frame': fi,
                        't': fi / self.fps,
                        'kp': kp,
                        'norm_y': norm_y,
                        'norm_x': norm_x,
                        'bbox_h': norm_h,
                        'bbox_w': norm_w,
                        'area': area,
                        'airborne': is_airborne,
                        'velocity_y': velocity_y,
                    })

            if progress_cb and self.total_frames > 0:
                progress_cb(fi / self.total_frames, fi)
            fi += 1

        cap.release()
        return poses, []

    def _bbox_to_pseudo_kp(self, bx: int, by: int, bw: int, bh: int) -> List[Dict]:
        """
        Build 33 pseudo-keypoints normalized to [0,1] image coordinates.
        Indices match MediaPipe: 11=L-shoulder, 12=R-shoulder, 23=L-hip,
        24=R-hip, 25=L-knee, 26=R-knee, 27=L-ankle, 28=R-ankle, 15=L-wrist, 16=R-wrist
        """
        H, W = self.height, self.width

        def n(px_abs, py_abs):
            return {'x': px_abs / W, 'y': py_abs / H, 'z': 0.0, 'v': 0.8, 'idx': -1}

        shoulder_y = by + bh * 0.18
        hip_y      = by + bh * 0.50
        knee_y     = by + bh * 0.72
        ankle_y    = by + bh * 0.92
        wrist_y    = by + bh * 0.52
        cx = bx + bw * 0.5

        kp = [n(cx, by)] * 33
        kp[11] = n(cx - bw*0.12, shoulder_y)
        kp[12] = n(cx + bw*0.12, shoulder_y)
        kp[23] = n(cx - bw*0.07, hip_y)
        kp[24] = n(cx + bw*0.07, hip_y)
        kp[25] = n(cx - bw*0.07, knee_y)
        kp[26] = n(cx + bw*0.07, knee_y)
        kp[27] = n(cx - bw*0.07, ankle_y)
        kp[28] = n(cx + bw*0.07, ankle_y)
        kp[15] = n(cx - bw*0.25, wrist_y)
        kp[16] = n(cx + bw*0.25, wrist_y)
        return kp

    # ── Airborne test ────────────────────────────────────────────────────────
    @staticmethod
    def _is_airborne(kp: List) -> bool:
        MIN_VIS = 0.4

        def g(i):
            p = kp[i] if i < len(kp) else None
            return p if p and p['v'] >= MIN_VIS else None

        la = g(27); ra = g(28)
        lh = g(23); rh = g(24)
        lk = g(25); rk = g(26)

        if la is None and ra is None:
            return False

        ankle_y = np.mean([p['y'] for p in [la, ra] if p])
        hip_ys = [p['y'] for p in [lh, rh] if p]
        if not hip_ys:
            return False
        hip_y = np.mean(hip_ys)
        gap = ankle_y - hip_y
        knee_ys = [p['y'] for p in [lk, rk] if p]
        knee_near_hip = bool(knee_ys) and np.mean(knee_ys) < hip_y + 0.05
        return gap < 0.20 or (gap < 0.28 and knee_near_hip)

    # ── Jump detection ───────────────────────────────────────────────────────
    def _detect_jumps(self, poses: List, spin_windows: List = None) -> List[Dict]:
        """
        Detect jumps using vertical position tracking.
        A jump = skater moves significantly ABOVE their average vertical position,
        then returns. Spin windows are excluded to prevent false positives.

        Key discriminators vs spins:
        - Airtime SHORT (0.20–1.10s) — spins last 1.5s+
        - Body TRAVELS laterally during/after jump — spins stay in place
        - Frame does NOT fall inside a known spin window
        """
        if len(poses) < 10:
            return []

        spin_windows = spin_windows or []

        # Build vertical + horizontal position arrays
        times = np.array([p['t'] for p in poses])
        ys, xs = [], []
        for p in poses:
            if p.get('kp'):
                hip_y = [p['kp'][i]['y'] for i in [23, 24]
                         if i < len(p['kp']) and p['kp'][i]['v'] > 0.3]
                hip_x = [p['kp'][i]['x'] for i in [23, 24]
                         if i < len(p['kp']) and p['kp'][i]['v'] > 0.3]
                ys.append(np.mean(hip_y) if hip_y else p.get('norm_y', 0.5))
                xs.append(np.mean(hip_x) if hip_x else p.get('norm_x', 0.5))
            else:
                ys.append(p.get('norm_y', 0.5))
                xs.append(p.get('norm_x', 0.5))

        ys = np.array(ys)
        xs = np.array(xs)

        # Smooth vertical signal
        win = min(7, len(ys) // 4)
        kernel = np.ones(win) / win
        ys_smooth = np.convolve(ys, kernel, mode='same')

        # Baseline: 60th percentile = typical standing position
        baseline = np.percentile(ys_smooth, 60)
        std_y = np.std(ys_smooth)

        # Jump threshold: lower y = higher in frame
        jump_thresh = baseline - max(0.09, std_y * 1.1)

        # Adaptive lateral-travel floor for the jump-vs-spin discriminator below.
        # A fixed absolute threshold (e.g. 0.025) assumes a close-up shot; from a
        # wider/farther camera (common on open rinks) a real rotational jump's
        # lateral hip travel in normalized coordinates can be much smaller even
        # though the jump is genuine — duration (0.20–1.10s) already rules out
        # true spins, so this only needs to catch near-zero-motion noise blips.
        global_x_std = np.std(xs)
        min_lateral_travel = min(0.025, max(0.006, global_x_std * 0.06))

        # Build spin-occupied mask to skip those frames
        spin_occupied = np.zeros(len(times), dtype=bool)
        for t_s, t_e in spin_windows:
            spin_occupied |= (times >= t_s - 0.3) & (times <= t_e + 0.3)

        jumps = []
        in_jump = False
        jump_start_idx = None
        min_y_in_jump = 1.0
        COOLDOWN_FRAMES = int(self.fps * 0.5)
        last_jump_end = -COOLDOWN_FRAMES

        for i in range(len(ys_smooth)):
            # Skip frames inside or adjacent to a detected spin
            if spin_occupied[i]:
                if in_jump:
                    in_jump = False
                continue

            above_thresh = ys_smooth[i] < jump_thresh
            in_cooldown = (i - last_jump_end) < COOLDOWN_FRAMES

            if above_thresh and not in_jump and not in_cooldown:
                in_jump = True
                jump_start_idx = i
                min_y_in_jump = ys_smooth[i]

            elif above_thresh and in_jump:
                min_y_in_jump = min(min_y_in_jump, ys_smooth[i])

            elif not above_thresh and in_jump:
                airtime = times[i] - times[jump_start_idx]

                if 0.20 <= airtime <= 1.10:
                    window = poses[jump_start_idx:i + 1]

                    # Lateral-travel check: filters out near-zero-motion noise
                    # blips (camera shake, tracking jitter) — true spins are
                    # already excluded by duration/spin-window, not by this.
                    seg_x = xs[jump_start_idx:i + 1]
                    lateral_travel = np.std(seg_x)
                    if lateral_travel < min_lateral_travel:
                        in_jump = False
                        continue

                    # Cross-validate with the per-frame airborne flag (ankle-hip gap).
                    # A real jump must show the body actually airborne for a real
                    # fraction of the candidate window — pure vertical-position
                    # noise (camera pan, stride bounce) will fail this check.
                    airborne_flags = [p.get('airborne') for p in window if 'airborne' in p]
                    if airborne_flags:
                        airborne_ratio = sum(1 for a in airborne_flags if a) / len(airborne_flags)
                        if airborne_ratio < 0.30:
                            in_jump = False
                            continue

                    # Require a minimum fraction of frames with real detected
                    # keypoints in the window — reject windows dominated by
                    # missing/low-confidence pose data (unreliable signal).
                    valid_kp = sum(1 for p in window if p.get('kp'))
                    if window and (valid_kp / len(window)) < 0.4:
                        in_jump = False
                        continue

                    height_above = baseline - min_y_in_jump
                    height_norm = height_above / max(std_y, 0.01)

                    # Reject a shallow, borderline dip — real jumps clear the
                    # threshold with margin, not just barely cross it.
                    if height_norm < 1.3:
                        in_jump = False
                        continue

                    j = _classify_jump(airtime, min(1.0, height_norm * 0.3))
                    j['t_start'] = round(times[jump_start_idx], 2)
                    j['t_end'] = round(times[i], 2)
                    j['frame_start'] = int(times[jump_start_idx] * self.fps)
                    j['frame_end'] = int(times[i] * self.fps)
                    jumps.append(j)
                    last_jump_end = i

                in_jump = False

        return jumps

    # ── Spin detection ───────────────────────────────────────────────────────
    def _detect_spins(self, poses: List) -> List[Dict]:
        """
        Detect spins in two passes:

        1. Candidate windows: short (~1.2s) sliding windows with low lateral/
           vertical drift AND a high x-oscillation rate. A static "doesn't move
           much" test alone (the old approach) is satisfied by almost an entire
           video filmed from a distance — verified on real footage where it
           marked 1388/1389 frames as "spin-like", merging the whole clip into
           one giant segment whose diluted average oscillation rate then failed
           the frequency gate, hiding a real 8+ rotation spin inside it.

        2. Real-rotation confirmation: for each merged candidate segment,
           measure actual accumulated body rotation via the unwrapped
           shoulder-line angle (same technique as jump rotation tracking) and
           require a minimum number of full rotations. This is what actually
           separates a spin from a turn/crossover or a sway-in-place, which
           can locally oscillate in x at a similar frequency without the body
           ever completing multiple real rotations — confirmed on real
           footage: a kneeling-to-standing sway measured 0.0 net rotations,
           three-turn/crossover moments measured ~1.5-2.4, and the one
           genuine spin in that clip measured 8.8 rotations over 7.1s.
        """
        if len(poses) < 10:
            return []

        spins = []

        xs, ys = [], []
        for p in poses:
            if p.get('kp'):
                x_vals = [p['kp'][i]['x'] for i in [11, 12, 23, 24]
                          if i < len(p['kp']) and p['kp'][i]['v'] > 0.3]
                y_vals = [p['kp'][i]['y'] for i in [11, 12, 23, 24]
                          if i < len(p['kp']) and p['kp'][i]['v'] > 0.3]
                xs.append(np.mean(x_vals) if x_vals else 0.5)
                ys.append(np.mean(y_vals) if y_vals else 0.5)
            else:
                xs.append(p.get('norm_x', 0.5))
                ys.append(p.get('norm_y', 0.5))

        xs = np.array(xs)
        ys = np.array(ys)
        times = np.array([p['t'] for p in poses])

        global_x_std = np.std(xs)
        MIN_LATERAL = max(0.03, global_x_std * 0.15)

        WIN = max(4, int(self.fps * 1.2))
        STEP = max(1, WIN // 4)

        spin_mask = np.zeros(len(xs), dtype=bool)
        for i in range(0, len(xs) - WIN, STEP):
            seg_x = xs[i:i + WIN]
            seg_y = ys[i:i + WIN]
            seg_t = times[i:i + WIN]

            lateral_drift = np.std(seg_x)
            vertical_drift = np.std(seg_y)

            seg_detrended = seg_x - seg_x.mean()
            crossings = np.where(np.diff(np.sign(seg_detrended)))[0]
            dur = seg_t[-1] - seg_t[0]
            cycles_per_sec = (len(crossings) / 2) / dur if dur > 0 else 0

            lateral_ok = lateral_drift < MIN_LATERAL
            vertical_ok = vertical_drift < 0.08
            oscillating = cycles_per_sec >= 0.8

            if lateral_ok and vertical_ok and oscillating:
                spin_mask[i:i + WIN] = True

        # Merge into contiguous candidate segments
        in_spin = False
        sp_start_idx = 0
        for i, is_sp in enumerate(spin_mask):
            if is_sp and not in_spin:
                in_spin = True
                sp_start_idx = i
            elif not is_sp and in_spin:
                sp_end_idx = i - 1
                self._confirm_and_add_spin(poses, times, sp_start_idx, sp_end_idx, spins)
                in_spin = False
        if in_spin:
            self._confirm_and_add_spin(poses, times, sp_start_idx, len(spin_mask) - 1, spins)

        return spins

    def _confirm_and_add_spin(self, poses, times, sp_start_idx, sp_end_idx, spins):
        """Verify a candidate spin segment via real accumulated rotation
        (unwrapped shoulder angle) before accepting it — see _detect_spins."""
        duration = times[sp_end_idx] - times[sp_start_idx]
        if duration < 1.5:
            return

        seg_kp = [p['kp'] for p in poses
                  if times[sp_start_idx] <= p['t'] <= times[sp_end_idx] and p.get('kp')]
        real_rotations = _compute_rotation_from_kp(seg_kp)

        MIN_ROTATIONS = 2.5  # below this, treat as a turn/sway rather than a spin
        if real_rotations is None or real_rotations < MIN_ROTATIONS:
            return

        rpm = real_rotations / duration * 60
        sp = _classify_spin(duration, rpm)
        sp['rotations'] = round(real_rotations, 1)
        sp['rotation_method'] = 'shoulder_tracking'
        sp['t_start'] = round(times[sp_start_idx], 2)
        sp['t_end'] = round(times[sp_end_idx], 2)
        sp['frame_start'] = int(times[sp_start_idx] * self.fps)
        sp['frame_end'] = int(times[sp_end_idx] * self.fps)
        spins.append(sp)

    # ── Error detection ──────────────────────────────────────────────────────
    def _detect_errors(self, poses: List, jumps: List, spins: Optional[List] = None) -> List[Dict]:
        errors = []
        spins = spins or []

        # Jump/spin windows (with a small buffer) — general skating-posture
        # checks below must exclude these. A spin position (camel, layback)
        # or a jump's air/landing shape has its own required torso angle and
        # arm position by design; scoring it against a "neutral skating
        # posture" baseline would flag correct technique as a flaw. Confirmed
        # on real footage: including these frames shifted the forward-lean
        # rate from 12.6% to 14.0% — a real, if modest, contamination.
        element_windows = (
            [(j.get('t_start', 0) - 0.3, j.get('t_end', 0) + 0.3) for j in jumps]
            + [(s.get('t_start', 0) - 0.3, s.get('t_end', 0) + 0.3) for s in spins]
        )

        def _during_element(t: float) -> bool:
            return any(a <= t <= b for a, b in element_windows)

        # 1) Under-rotation: airtime < 0.5s but claimed multi-rotation
        for j in jumps:
            if j.get('rotations', 0) >= 2.0 and j.get('airtime', 0) < 0.45:
                errors.append({
                    'category': 'دوران', 'severity': 'عالي',
                    'title_ar': f"دوران ناقص — {j['type']}",
                    'title_en': f"Under-Rotation — {j['type']}",
                    'desc_ar': f"وقت الطيران {j['airtime']:.2f}ث قصير للدوران المطلوب ({j['rotations']:.1f} لفة)",
                    'desc_en': f"Airtime {j['airtime']:.2f}s too short for {j['rotations']:.1f} required rotations",
                    'fix_ar': ['ضم الذراعين بشكل أسرع نحو الجسم', 'تقوية دفعة الإقلاع من الحافة'],
                    'fix_en': ['Pull arms in faster toward body', 'Strengthen takeoff edge push'],
                    'goe_impact': -1,
                    't_start': j.get('t_start', 0), 't_end': j.get('t_end', 0),
                    'symptom_key': 'under_rotation',
                })

        # 2) Posture analysis from MediaPipe poses (if available)
        if poses and poses[0].get('kp'):
            lean_frames = 0
            total_valid = 0
            arm_asymmetry_frames = 0
            arm_valid = 0

            for pose in poses:
                kp = pose['kp']
                if not kp:
                    continue
                t = pose.get('t', 0)

                def g(i):
                    p = kp[i] if i < len(kp) else None
                    return p if p and p['v'] > 0.4 else None

                ls = g(11); rs = g(12)  # shoulders
                lh = g(23); rh = g(24)  # hips
                lw = g(15); rw = g(16)  # wrists

                # Forward lean: compare shoulder-hip angle — skip frames
                # inside a jump/spin, where a tilted torso is expected.
                if ls and rs and lh and rh and not _during_element(t):
                    total_valid += 1
                    sh_x = (ls['x'] + rs['x']) / 2
                    hi_x = (lh['x'] + rh['x']) / 2
                    sh_y = (ls['y'] + rs['y']) / 2
                    hi_y = (lh['y'] + rh['y']) / 2
                    if sh_y < hi_y:  # shoulder above hip (normal)
                        dx = sh_x - hi_x
                        dy = hi_y - sh_y
                        lean_angle = abs(np.degrees(np.arctan2(dx, dy))) if dy > 0 else 0
                        if lean_angle > 15:
                            lean_frames += 1

                # Arm asymmetry: only meaningful during a spin. Outside of
                # spins (stroking, crossovers), asymmetric arms are the
                # CORRECT technique per ISI standards ("outer arm front,
                # inside arm back") — checking it against a symmetric
                # baseline there would flag proper skating as a flaw.
                spin_windows = [(s.get('t_start', 0) - 0.3, s.get('t_end', 0) + 0.3) for s in spins]
                in_spin = any(a <= t <= b for a, b in spin_windows)
                if lw and rw and ls and rs and in_spin:
                    arm_valid += 1
                    ls_y = (ls['y'] + rs['y']) / 2
                    lw_y_diff = abs(lw['y'] - ls_y)
                    rw_y_diff = abs(rw['y'] - ls_y)
                    if abs(lw_y_diff - rw_y_diff) > 0.15:
                        arm_asymmetry_frames += 1

            if total_valid > 0 and lean_frames / total_valid > 0.3:
                errors.append({
                    'category': 'وضعية الجسم', 'severity': 'متوسط',
                    'title_ar': 'انحناء للأمام أثناء التزلج',
                    'title_en': 'Forward Lean During Skating',
                    'desc_ar': f'ظهر الانحناء في {lean_frames} إطار ({100*lean_frames//total_valid}% من الوقت)',
                    'desc_en': f'Forward lean detected in {lean_frames} frames ({100*lean_frames//total_valid}% of time)',
                    'fix_ar': ['تقوية عضلات الظهر السفلية', 'تخيّل خيط يسحب رأسك للأعلى', 'مراجعة التسجيل مع المدرب'],
                    'fix_en': ['Strengthen lower back muscles', 'Imagine a string pulling your head up', 'Review recording with coach'],
                    'goe_impact': 0,
                    't_start': 0, 't_end': self.total_frames / self.fps,
                    'symptom_key': 'axis_misalignment',
                })

            if arm_valid > 0 and arm_asymmetry_frames / arm_valid > 0.25:
                errors.append({
                    'category': 'الذراعين', 'severity': 'منخفض',
                    'title_ar': 'عدم تناسق الذراعين أثناء الدوران',
                    'title_en': 'Arm Asymmetry During Spin',
                    'desc_ar': 'الذراعان غير متناسقتين أثناء الدوران — يؤثر على تناسق الوضعية',
                    'desc_en': 'Arms are asymmetric during the spin — affects position symmetry',
                    'fix_ar': ['تمارين أمام المرآة لمحاذاة الذراعين', 'الوعي بالوضع: تصوير التدريب'],
                    'fix_en': ['Mirror exercises for arm alignment', 'Awareness: film practice sessions'],
                    'goe_impact': 0,
                    't_start': 0, 't_end': self.total_frames / self.fps,
                    'symptom_key': 'arm_shoulder_position',
                })

        return errors

    # ── AI-derived errors (uses AIMovementEngine pose_score / axis_stability) ──
    def _detect_ai_errors(self, jumps: List[Dict], spins: List[Dict]) -> List[Dict]:
        errors: List[Dict] = []

        for j in jumps:
            # pose_score is on a 0-100 scale (PoseComparator._score_from_deviations
            # returns [0,100]) — comparing it against 0.55 here meant this check
            # could practically never fire (confirmed on real footage: a genuine
            # "Fair ⭐⭐" jump scored pose_score=57.6, which is >> 0.55, so no error
            # was ever raised despite the AI rating the pose as mediocre).
            score = j.get('pose_score')
            if score is not None and score < 55:
                corrections = j.get('pose_corrections_ar', [])
                errors.append({
                    'category': 'وضعية العنصر', 'severity': 'متوسط',
                    'title_ar': f"جودة وضعية منخفضة — {j.get('type','')}",
                    'title_en': f"Low Pose Quality — {j.get('type','')}",
                    'desc_ar': f"تقييم الوضعية بالذكاء الاصطناعي: {int(round(score))}% في مرحلة {j.get('pose_phase','')}",
                    'desc_en': f"AI pose score: {int(round(score))}% at {j.get('pose_phase','')} phase",
                    'fix_ar': corrections[:3] if corrections else ['راجع محاذاة المحور والذراعين في هذه المرحلة'],
                    'fix_en': ['Review axis and arm alignment at this phase'],
                    'goe_impact': -1 if score < 40 else 0,
                    't_start': j.get('t_start', 0), 't_end': j.get('t_end', 0),
                    'symptom_key': 'checking_landing_control',
                })

        for s in spins:
            stability = s.get('axis_stability')
            if stability is not None and stability < 0.55:
                errors.append({
                    'category': 'دوران', 'severity': 'متوسط',
                    'title_ar': f"استقرار محور منخفض — {s.get('type','')}",
                    'title_en': f"Low Axis Stability — {s.get('type','')}",
                    'desc_ar': f"استقرار المحور بالذكاء الاصطناعي: {int(stability*100)}%",
                    'desc_en': f"AI axis stability: {int(stability*100)}%",
                    'fix_ar': s.get('pose_corrections_ar', []) or ['اغرس قدم الدوران وثبّت الضغط على كرة القدم'],
                    'fix_en': ['Plant the spin foot and hold ball-of-foot pressure'],
                    'goe_impact': -1,
                    't_start': s.get('t_start', 0), 't_end': s.get('t_end', 0),
                    'symptom_key': 'off_axis_spin',
                })

        return errors

    # ── Timeline ─────────────────────────────────────────────────────────────
    def _build_timeline(self, poses, jumps, spins, step_sequences=None) -> List[Dict]:
        timeline = []
        for j in jumps:
            timeline.append({
                'type': 'jump', 'label': j.get('ai_name', j['type']),
                't': j.get('t_start', 0), 'duration': j.get('airtime', 0.3),
                'score': j['final_score'], 'goe': j['goe'],
                'color': '#22c55e' if j['goe'] >= 0 else '#ef4444',
            })
        for s in spins:
            timeline.append({
                'type': 'spin', 'label': s.get('ai_name', s['type']),
                't': s.get('t_start', 0), 'duration': s.get('duration', 2),
                'score': s['final_score'], 'goe': s['goe'],
                'color': '#3b82f6',
            })
        for ss in (step_sequences or []):
            timeline.append({
                'type': 'step', 'label': ss['type'],
                't': ss.get('t_start', 0), 'duration': ss.get('duration', 5),
                'score': ss['final_score'], 'goe': ss.get('goe', 0),
                'color': '#a78bfa',
            })
        timeline.sort(key=lambda x: x['t'])
        return timeline

    @staticmethod
    def _error_result(msg: str) -> Dict:
        return {'error': msg, 'is_demo': False, 'jumps': [], 'spins': [],
                'errors': [], 'timeline': [], 'total_score': 0}


# ============================================================================
# DEMO DATA
# ============================================================================

def _demo_data(lang: str = 'ar') -> Dict:
    ar = lang == 'ar'
    return {
        'video_info': {'fps': 30, 'frame_count': 660, 'width': 678, 'height': 848,
                       'duration': 22, 'orientation': 'Portrait'},
        'jumps': [
            {'type': 'Double Axel', 'code': '2A', 'rotations': 2.5, 'height_cm': 48,
             'airtime': 0.52, 'rpm': 288, 'goe': 2, 'base_value': 3.30,
             'final_score': 3.96, 'is_clean': True, 't_start': 3.6, 't_end': 4.1,
             'frame_start': 108, 'frame_end': 123, 'rotation_method': 'shoulder_tracking'},
            {'type': 'Triple Lutz', 'code': '3Lz', 'rotations': 3.1, 'height_cm': 52,
             'airtime': 0.68, 'rpm': 273, 'goe': 1, 'base_value': 5.90,
             'final_score': 6.49, 'is_clean': True, 't_start': 7.0, 't_end': 7.7,
             'frame_start': 210, 'frame_end': 231, 'rotation_method': 'shoulder_tracking'},
            {'type': 'Triple Flip', 'code': '3F', 'rotations': 2.75, 'height_cm': 38,
             'airtime': 0.61, 'rpm': 270, 'goe': -1, 'base_value': 5.30,
             'final_score': 4.77, 'is_clean': False, 't_start': 12.2, 't_end': 12.8,
             'frame_start': 366, 'frame_end': 384, 'rotation_method': 'airtime_heuristic'},
        ],
        'spins': [
            {'type': 'Camel Spin', 'code': 'CSp', 'rotations': 7, 'rpm': 70,
             'duration': 6.0, 'level': 3, 'goe': 1, 'base_value': 1.90,
             'final_score': 2.28, 't_start': 9.0, 't_end': 15.0,
             'frame_start': 270, 'frame_end': 450},
        ],
        'errors': [
            {'category': 'دوران' if ar else 'Rotation', 'severity': 'عالي' if ar else 'HIGH',
             'title_ar': 'دوران ناقص — Triple Flip',
             'title_en': 'Under-Rotation — Triple Flip',
             'desc_ar': 'اكتمل 2.75 دورة من 3 مطلوبة. العجز 0.25 دورة.',
             'desc_en': 'Completed 2.75 of 3 required rotations. Deficit: 0.25.',
             'fix_ar': ['ضم الذراعين بشكل أسرع نحو الجسم', 'زيادة قوة الإقلاع'],
             'fix_en': ['Pull arms in faster toward body', 'Increase takeoff power'],
             'goe_impact': -1, 't_start': 12.2, 't_end': 12.8},
            {'category': 'وضعية' if ar else 'Posture', 'severity': 'متوسط' if ar else 'MEDIUM',
             'title_ar': 'انحناء طفيف للأمام',
             'title_en': 'Slight Forward Lean',
             'desc_ar': 'ميل الجسم للأمام بنسبة 35% من وقت التزلج الحر.',
             'desc_en': 'Body lean forward 35% of free skating time.',
             'fix_ar': ['تقوية عضلات الظهر', 'تمارين الوضعية'],
             'fix_en': ['Strengthen back muscles', 'Posture exercises'],
             'goe_impact': 0, 't_start': 0, 't_end': 22},
        ],
        'timeline': [
            {'type': 'jump', 'label': 'Double Axel', 't': 3.6, 'duration': 0.52, 'score': 3.96, 'goe': 2, 'color': '#22c55e'},
            {'type': 'jump', 'label': 'Triple Lutz', 't': 7.0, 'duration': 0.68, 'score': 6.49, 'goe': 1, 'color': '#22c55e'},
            {'type': 'spin', 'label': 'Camel Spin', 't': 9.0, 'duration': 6.0, 'score': 2.28, 'goe': 1, 'color': '#3b82f6'},
            {'type': 'jump', 'label': 'Triple Flip', 't': 12.2, 'duration': 0.61, 'score': 4.77, 'goe': -1, 'color': '#ef4444'},
        ],
        'step_sequences': [
            {'type': 'Step Sequence', 'code': 'StSq2', 'level': 2,
             'duration': 8.5, 't_start': 16.0, 't_end': 24.5,
             'complexity': 0.62, 'base_value': 2.60, 'final_score': 2.60,
             'goe': 0, 'color': '#a78bfa'},
        ],
        'total_score': 25.34, 'tes': 20.10, 'pcs': 8.00,
        'pose_count': 330,
        'skeleton_frames': [],
        'pose_samples': [],
        'ai_status': {'movement_classifier': False, 'lstm': False, 'pose_comparator': False},
        'is_demo': True,
        'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }


# ============================================================================
# COLORS & HELPERS
# ============================================================================

SEV_COLOR = {'حرج': '#dc2626', 'CRITICAL': '#dc2626', 'عالي': '#ea580c',
             'HIGH': '#ea580c', 'متوسط': '#d97706', 'MEDIUM': '#d97706',
             'منخفض': '#65a30d', 'LOW': '#65a30d'}
SEV_ICON = {'حرج': '🔴', 'CRITICAL': '🔴', 'عالي': '🟠', 'HIGH': '🟠',
            'متوسط': '🟡', 'MEDIUM': '🟡', 'منخفض': '🟢', 'LOW': '🟢'}

# ============================================================================
# SKELETON & 3D CONSTANTS
# ============================================================================

# MediaPipe body bone connections (index pairs)
BODY_CONNECTIONS = [
    (0, 11), (0, 12),
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (15, 17), (15, 19), (17, 19),
    (16, 18), (16, 20), (18, 20),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
    (24, 26), (26, 28), (28, 30), (28, 32), (30, 32),
]

# ── Per-segment body colors matching the MediaPipe video style ────────────────
# BGR tuples for cv2 · hex strings for Plotly 3D
_SEG = {
    #          BGR (cv2)            Hex (Plotly)
    'face':  ((255,  80, 200), '#FF50C8'),   # magenta-pink  (head/face)
    'torso': ((255, 255, 255), '#FFFFFF'),   # white         (spine/shoulders/hips)
    'l_arm': ((  0, 200, 255), '#FFC800'),   # amber/yellow  (left arm)
    'r_arm': ((255, 120,  30), '#1E78FF'),   # electric blue (right arm)
    'l_leg': (( 60, 220,  60), '#3CDC3C'),   # lime green    (left leg)
    'r_leg': ((220, 210,   0), '#00D2DC'),   # teal/cyan     (right leg)
}

# Map each BODY_CONNECTIONS pair to a segment
_CONN_SEG: dict = {
    (0,  11): 'face',  (0,  12): 'face',
    (11, 12): 'torso', (11, 23): 'torso', (12, 24): 'torso', (23, 24): 'torso',
    (11, 13): 'l_arm', (13, 15): 'l_arm',
    (15, 17): 'l_arm', (15, 19): 'l_arm', (17, 19): 'l_arm',
    (12, 14): 'r_arm', (14, 16): 'r_arm',
    (16, 18): 'r_arm', (16, 20): 'r_arm', (18, 20): 'r_arm',
    (23, 25): 'l_leg', (25, 27): 'l_leg', (27, 29): 'l_leg',
    (27, 31): 'l_leg', (29, 31): 'l_leg',
    (24, 26): 'r_leg', (26, 28): 'r_leg', (28, 30): 'r_leg',
    (28, 32): 'r_leg', (30, 32): 'r_leg',
}

# Map each joint index to its segment
_JOINT_SEG: dict = {
    **{i: 'face'  for i in range(11)},          # 0–10  face
    **{i: 'l_arm' for i in [11,13,15,17,19,21]},
    **{i: 'r_arm' for i in [12,14,16,18,20,22]},
    **{i: 'l_leg' for i in [23,25,27,29,31]},
    **{i: 'r_leg' for i in [24,26,28,30,32]},
}


def _joint_color(idx: int) -> str:
    """Return Plotly hex color for joint index (body-segment scheme)."""
    seg = _JOINT_SEG.get(idx, 'torso')
    return _SEG[seg][1]


def _draw_skeleton_on_frame(frame_bgr: np.ndarray, kp_list: list, W: int, H: int) -> np.ndarray:
    """
    Draw color-coded MediaPipe skeleton overlay on a BGR frame.
    Each body segment has a distinct color matching the video style:
      face=pink, torso=white, L-arm=yellow, R-arm=blue, L-leg=green, R-leg=teal
    """
    if not CV2_OK or not kp_list or len(kp_list) < 29:
        return frame_bgr
    out = frame_bgr.copy()

    # Draw bones with per-segment color
    for (a, b), seg in _CONN_SEG.items():
        if a >= len(kp_list) or b >= len(kp_list):
            continue
        pa, pb = kp_list[a], kp_list[b]
        if pa.get('v', 0) < 0.25 or pb.get('v', 0) < 0.25:
            continue
        x1, y1 = int(pa['x'] * W), int(pa['y'] * H)
        x2, y2 = int(pb['x'] * W), int(pb['y'] * H)
        bgr = _SEG[seg][0]
        cv2.line(out, (x1, y1), (x2, y2), bgr, 3, cv2.LINE_AA)

    # Draw joints — large white-outlined circle in segment color
    KEY = {0,11,12,13,14,15,16,23,24,25,26,27,28}
    for i, kp in enumerate(kp_list):
        if kp.get('v', 0) < 0.20:
            continue
        x, y = int(kp['x'] * W), int(kp['y'] * H)
        seg  = _JOINT_SEG.get(i, 'torso')
        bgr  = _SEG[seg][0]
        r    = 8 if i in KEY else 4
        cv2.circle(out, (x, y), r,     bgr,           -1,           cv2.LINE_AA)
        cv2.circle(out, (x, y), r + 1, (255,255,255), 1,            cv2.LINE_AA)

    return out


def _frame_to_b64(frame_bgr: np.ndarray) -> str:
    """Encode a BGR frame as a base64 JPEG string."""
    import base64
    _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 82])
    return base64.b64encode(buf.tobytes()).decode()


def _build_3d_skeleton_fig(kp_list: list, title: str = "هيكل عظمي 3D",
                            dark: bool = True) -> go.Figure:
    """Return a Plotly 3D figure for a single pose frame."""
    if not kp_list or len(kp_list) < 29:
        return None
    n = len(kp_list)
    xs = [float(p['x']) for p in kp_list]
    ys = [float(-p['y']) for p in kp_list]    # flip: screen Y is down, 3D Y up
    zs = [float(-p.get('z', 0)) for p in kp_list]  # negate depth for readable view
    joint_vis = [float(p.get('v', 1.0)) for p in kp_list]  # visibility per joint
    # Use body-segment hex colors (same scheme as 2D overlay)
    colors = [_joint_color(i) for i in range(n)]
    sizes  = [12 if i in {0,11,12,13,14,15,16,23,24,25,26,27,28} else 6 for i in range(n)]

    # opacity MUST be a scalar for scatter3d.marker — Plotly rejects lists
    MARKER_OPACITY = float(0.92)

    bg = 'rgba(8,18,30,0.97)' if dark else 'rgba(240,248,255,0.97)'
    line_c = 'rgba(80,180,255,0.6)' if dark else 'rgba(30,100,200,0.5)'
    paper = 'rgba(8,18,30,1)' if dark else 'rgba(240,248,255,1)'
    font_c = '#E8F0FA' if dark else '#0F2033'
    grid_c = 'rgba(100,150,255,0.12)'

    fig = go.Figure()

    # Bones — per-segment color matching the 2D overlay
    for a, b in BODY_CONNECTIONS:
        if a >= n or b >= n:
            continue
        if joint_vis[a] < 0.2 or joint_vis[b] < 0.2:
            continue
        seg      = _CONN_SEG.get((a, b), 'torso')
        bone_hex = _SEG[seg][1]
        fig.add_trace(go.Scatter3d(
            x=[xs[a], xs[b], None],
            y=[zs[a], zs[b], None],
            z=[ys[a], ys[b], None],
            mode='lines',
            line=dict(color=bone_hex, width=5),
            showlegend=False,
            hoverinfo='skip',
        ))

    # Joints — opacity must be a plain float scalar
    fig.add_trace(go.Scatter3d(
        x=xs, y=zs, z=ys,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=MARKER_OPACITY,
            line=dict(color='white', width=0.5),
        ),
        name='مفاصل',
        text=[f'Joint {i} ({joint_vis[i]:.2f})' for i in range(n)],
        hoverinfo='text',
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=font_c, size=14)),
        scene=dict(
            xaxis=dict(title='X', showgrid=True, gridcolor=grid_c,
                       zeroline=False, backgroundcolor=bg),
            yaxis=dict(title='عمق Z', showgrid=True, gridcolor=grid_c,
                       zeroline=False, backgroundcolor=bg),
            zaxis=dict(title='ارتفاع Y', showgrid=True, gridcolor=grid_c,
                       zeroline=False, backgroundcolor=bg),
            bgcolor=bg,
            aspectmode='data',
            camera=dict(eye=dict(x=1.4, y=-1.2, z=0.8)),
        ),
        paper_bgcolor=paper,
        font=dict(color=font_c),
        height=540,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
    )
    return fig


def _compute_rotation_from_kp(kp_segment: list) -> Optional[float]:
    """
    Estimate rotation count during a jump from the shoulder-line angle
    change in the XZ plane (x = lateral, z = depth).
    Returns None if insufficient data.
    """
    angles = []
    for kp in kp_segment:
        if not kp:
            continue
        ls = kp[11] if len(kp) > 12 else None
        rs = kp[12] if len(kp) > 12 else None
        if ls and rs and ls.get('v', 0) > 0.2 and rs.get('v', 0) > 0.2:
            dx = rs['x'] - ls['x']
            dz = rs.get('z', 0) - ls.get('z', 0)
            angles.append(np.arctan2(dz, dx))
    if len(angles) < 4:
        return None
    unwrapped = np.unwrap(np.array(angles))
    total = abs(unwrapped[-1] - unwrapped[0]) / (2 * np.pi)
    return max(0.3, total)


def _save_to_db(results: Dict, player_name: str, session_note: str):
    """Save analysis results to training_videos table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT,
                session_note TEXT,
                analyzed_at TEXT,
                duration REAL,
                total_score REAL,
                tes REAL,
                pcs REAL,
                jumps_count INTEGER,
                spins_count INTEGER,
                errors_count INTEGER,
                jump_details TEXT,
                spin_details TEXT
            )
        """)
        import json
        conn.execute("""
            INSERT INTO analysis_results
            (player_name, session_note, analyzed_at, duration, total_score, tes, pcs,
             jumps_count, spins_count, errors_count, jump_details, spin_details)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            player_name, session_note,
            results.get('analyzed_at', ''),
            results.get('video_info', {}).get('duration', 0),
            results.get('total_score', 0),
            results.get('tes', 0),
            results.get('pcs', 0),
            len(results.get('jumps', [])),
            len(results.get('spins', [])),
            len(results.get('errors', [])),
            json.dumps(results.get('jumps', []), ensure_ascii=False),
            json.dumps(results.get('spins', []), ensure_ascii=False),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


def _to_excel(results: Dict) -> bytes:
    buf = io.BytesIO()
    try:
        with pd.ExcelWriter(buf, engine='openpyxl') as w:
            # Jumps sheet
            if results.get('jumps'):
                pd.DataFrame(results['jumps']).to_excel(w, sheet_name='Jumps', index=False)
            # Spins sheet
            if results.get('spins'):
                pd.DataFrame(results['spins']).to_excel(w, sheet_name='Spins', index=False)
            # Errors sheet
            if results.get('errors'):
                pd.DataFrame(results['errors']).to_excel(w, sheet_name='Errors', index=False)
            # Summary
            vi = results.get('video_info', {})
            summary = pd.DataFrame([{
                'Duration (s)': vi.get('duration', 0),
                'Resolution': f"{vi.get('width')}x{vi.get('height')}",
                'FPS': vi.get('fps', 0),
                'Total Score': results.get('total_score', 0),
                'TES': results.get('tes', 0),
                'PCS': results.get('pcs', 0),
                'Jumps': len(results.get('jumps', [])),
                'Spins': len(results.get('spins', [])),
                'Errors': len(results.get('errors', [])),
                'Analyzed At': results.get('analyzed_at', ''),
            }])
            summary.to_excel(w, sheet_name='Summary', index=False)
        return buf.getvalue()
    except Exception:
        return b''


def _to_html_report(results: Dict, player_name: str) -> str:
    """Generate printable HTML report."""
    vi = results.get('video_info', {})
    jumps = results.get('jumps', [])
    spins = results.get('spins', [])
    errors = results.get('errors', [])

    jump_rows = ''.join(f"""
        <tr>
            <td>{j.get('type','')}</td>
            <td>{j.get('rotations',0):.1f}</td>
            <td>{j.get('height_cm',0)} cm</td>
            <td>{j.get('airtime',0):.2f}s</td>
            <td>{j.get('rpm',0):.0f}</td>
            <td style="color:{'green' if j.get('goe',0)>=0 else 'red'}">{j.get('goe',0):+d}</td>
            <td>{j.get('base_value',0):.2f}</td>
            <td><b>{j.get('final_score',0):.2f}</b></td>
        </tr>
    """ for j in jumps)

    spin_rows = ''.join(f"""
        <tr>
            <td>{s.get('type','')}</td>
            <td>{s.get('rotations',0):.1f}</td>
            <td>{s.get('rpm',0):.0f}</td>
            <td>{s.get('duration',0):.1f}s</td>
            <td>L{s.get('level',0)}</td>
            <td><b>{s.get('final_score',0):.2f}</b></td>
        </tr>
    """ for s in spins)

    error_rows = ''.join(f"""
        <tr>
            <td>{e.get('category','')}</td>
            <td style="color:{SEV_COLOR.get(e.get('severity','LOW'),'#333')}">
                {e.get('severity','')}
            </td>
            <td>{e.get('title_ar','')}</td>
            <td>{e.get('goe_impact',0):+d}</td>
        </tr>
    """ for e in errors)

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<title>تقرير التحليل — {player_name}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; direction: rtl; }}
  h1 {{ color: #1e3a5f; border-bottom: 3px solid #1e3a5f; padding-bottom: 10px; }}
  h2 {{ color: #2d6a9f; margin-top: 30px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
  th {{ background: #1e3a5f; color: white; padding: 10px; }}
  td {{ padding: 8px; border: 1px solid #ddd; }}
  tr:nth-child(even) {{ background: #f5f7fa; }}
  .score-box {{ display: inline-block; background: #1e3a5f; color: white;
               padding: 15px 30px; border-radius: 10px; font-size: 2em; margin: 10px 5px; }}
  .score-label {{ font-size: 0.5em; display: block; color: #aad; }}
  @media print {{ .no-print {{ display: none; }} }}
</style>
</head>
<body>
  <h1>🏆 تقرير تحليل التزلج الفني — YASOOO</h1>
  <p><b>اللاعب:</b> {player_name or 'غير محدد'} &nbsp;&nbsp;
     <b>التاريخ:</b> {results.get('analyzed_at','')} &nbsp;&nbsp;
     <b>المدة:</b> {vi.get('duration',0):.1f} ثانية</p>

  <div>
    <div class="score-box">{results.get('total_score',0):.2f}<span class="score-label">إجمالي النقاط</span></div>
    <div class="score-box">{results.get('tes',0):.2f}<span class="score-label">TES عناصر</span></div>
    <div class="score-box">{results.get('pcs',0):.2f}<span class="score-label">PCS أداء</span></div>
    <div class="score-box">{len(jumps)}<span class="score-label">قفزات</span></div>
    <div class="score-box">{len(spins)}<span class="score-label">دورانات</span></div>
  </div>

  <h2>🦘 القفزات</h2>
  <table>
    <tr><th>النوع</th><th>الدورات</th><th>الارتفاع</th><th>وقت الطيران</th><th>RPM</th><th>GOE</th><th>القيمة الأساسية</th><th>النقاط</th></tr>
    {jump_rows or '<tr><td colspan="8">لا توجد قفزات</td></tr>'}
  </table>

  <h2>🌀 الدورانات</h2>
  <table>
    <tr><th>النوع</th><th>الدورات</th><th>RPM</th><th>المدة</th><th>المستوى</th><th>النقاط</th></tr>
    {spin_rows or '<tr><td colspan="6">لا توجد دورانات</td></tr>'}
  </table>

  <h2>⚠️ الأخطاء والتصحيحات</h2>
  <table>
    <tr><th>الفئة</th><th>الخطورة</th><th>الخطأ</th><th>تأثير GOE</th></tr>
    {error_rows or '<tr><td colspan="4">لا توجد أخطاء</td></tr>'}
  </table>

  <br><hr>
  <p style="color:#999;font-size:0.85em">تم إنشاء هذا التقرير بنظام YASOOO لتحليل التزلج الفني — جميع النتائج تقريبية للمساعدة في التدريب</p>
  <script>window.print();</script>
</body></html>"""


# ============================================================================
# MAIN PAGE
# ============================================================================

def show_video_analysis_page(lang: str = 'ar'):
    ar = lang == 'ar'

    try:
        from src.utils.ysoo_theme import inject_theme_css
        st.markdown(inject_theme_css(), unsafe_allow_html=True)
    except Exception:
        pass

    # Header
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px">
      <h1 style="font-size:2.2em;background:linear-gradient(135deg,#1e3a5f,#2d6a9f,#4a9fd4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        🧪 مختبر تحليل الفيديو
      </h1>
      <p style="color:#64748b;font-size:1.05em;margin-top:6px">
        ارفع الفيديو → شاهد الهيكل العظمي المتحرك فوق الجسم → اعرف الحركة المرجّحة
        والأخطاء الفنية وخطوات الإصلاح — مبني على بيانات الحركة الفعلية مع نسب الثقة
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Status bar
    mp_status = "✅ MediaPipe + هيكل 3D" if MP_OK else "⚠️ OpenCV فقط (بدون هيكل 3D)"
    cv_status = "✅ OpenCV" if CV2_OK else "❌ OpenCV غير متوفر"
    rot_status = "✅ تتبع دوران حقيقي" if MP_OK else "⚠️ تقدير الدوران بالوقت"
    st.caption(f"محرك التحليل: {mp_status} | {cv_status} | {rot_status}")
    st.markdown("---")

    tabs = st.tabs([
        "📹 رفع وتحليل",
        "📊 النتائج",
        "🏅 القفزات والدورانات",
        "⚠️ الأخطاء والتصحيحات",
        "🦴 الهيكل العظمي المتحرك",
        "📈 الإحصائيات",
        "📄 التقارير"
    ])

    with tabs[0]:
        _tab_upload(ar, lang)
    with tabs[1]:
        _tab_results(ar, lang)
    with tabs[2]:
        _tab_elements(ar, lang)
    with tabs[3]:
        _tab_errors(ar, lang)
    with tabs[4]:
        _tab_skeleton_3d(ar, lang)
    with tabs[5]:
        _tab_stats(ar, lang)
    with tabs[6]:
        _tab_reports(ar, lang)


# ============================================================================
# TAB: UPLOAD & ANALYZE
# ============================================================================

def _tab_upload(ar: bool, lang: str):
    st.subheader("📹 رفع فيديو للتحليل الكامل")

    col_info, col_demo = st.columns([3, 1])

    with col_info:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#e0f2fe,#bfdbfe);border-radius:12px;padding:18px">
          <b>كيف يعمل المختبر:</b><br>
          ① ارفع فيديو التزلج (MP4 · AVI · MOV · MKV)<br>
          ② يستخرج النظام وضعيات الجسم (33 نقطة) بـ MediaPipe إطاراً بإطار<br>
          ③ شاهد فيديو الهيكل العظمي المتحرك فوق الجسم + عرض 3D تفاعلي<br>
          ④ يحدد الحركة المرجّحة والأخطاء الفنية مع نسبة الثقة وحدود اللقطة<br>
          ⑤ يقترح خطوات إصلاح عملية ويحسب نقاط ISU الرسمية (GOE + Base Value)<br>
          ⑥ يولّد تقريراً مفصلاً قابلاً للطباعة والتصدير
        </div>
        """, unsafe_allow_html=True)

    with col_demo:
        if st.button("🎭 عرض تجريبي", use_container_width=True,
                     help="شاهد النتائج بدون رفع فيديو"):
            st.session_state['analysis_results'] = _demo_data(lang)
            st.success("✅ تم تحميل العرض التجريبي — راجع التبويبات الأخرى")

    st.markdown("---")

    uploaded = st.file_uploader(
        "اختر ملف الفيديو",
        type=['mp4', 'avi', 'mov', 'mkv'],
        key='video_upload',
        help="الحجم الأقصى: 200MB | مدة مثالية: 10-120 ثانية"
    )

    if uploaded:
        col_v, col_m = st.columns([2, 1])
        with col_v:
            st.video(uploaded)
        with col_m:
            player_name = st.text_input("👤 اسم اللاعب", placeholder="اختياري")
            session_note = st.text_input("📝 ملاحظة", placeholder="تدريب / منافسة / مراجعة")
            st.markdown("---")
            analyze_btn = st.button("🚀 بدء التحليل الكامل", type="primary",
                                    use_container_width=True)

        if analyze_btn:
            suffix = Path(uploaded.name).suffix or '.mp4'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            try:
                prog_bar = st.progress(0, text="جارٍ تحليل الفيديو...")
                status_txt = st.empty()

                def update_progress(frac: float, frame: int):
                    prog_bar.progress(min(frac, 1.0),
                                      text=f"تحليل الإطار {frame} ...")
                    status_txt.caption(f"⚡ تشغيل محرك MediaPipe... {int(frac*100)}%")

                analyzer = SkatingVideoAnalyzer()
                results = analyzer.analyze(tmp_path, progress_cb=update_progress)

                prog_bar.progress(1.0, text="✅ اكتمل التحليل")
                status_txt.empty()

                if 'error' in results:
                    st.error(f"خطأ: {results['error']}")
                else:
                    results['player_name'] = player_name
                    results['session_note'] = session_note
                    st.session_state['analysis_results'] = results

                    # Save to DB
                    _save_to_db(results, player_name, session_note)

                    # Summary popup
                    j_count = len(results.get('jumps', []))
                    s_count = len(results.get('spins', []))
                    e_count = len(results.get('errors', []))
                    score = results.get('total_score', 0)

                    st.success(f"✅ اكتمل التحليل! "
                               f"| {j_count} قفزات | {s_count} دورانات "
                               f"| {e_count} أخطاء | النقاط: {score:.2f}")
                    st.balloons()

            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


# ============================================================================
# TAB: RESULTS OVERVIEW
# ============================================================================

def _tab_results(ar: bool, lang: str):
    st.subheader("📊 نظرة عامة على النتائج")
    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً")
        return

    if results.get('is_demo'):
        st.caption("🎭 عرض تجريبي — بيانات للتوضيح فقط")

    # AI engine status banner
    ai_status = results.get('ai_status', {})
    if ai_status:
        active = [k for k, v in ai_status.items() if v]
        if active:
            model_names = {
                'movement_classifier': 'MovementClassifier',
                'lstm': 'LSTM',
                'pose_comparator': 'PoseComparator',
            }
            active_labels = " · ".join(model_names.get(k, k) for k in active)
            st.success(f"🤖 الذكاء الاصطناعي نشط: {active_labels}")
        else:
            st.info("ℹ️ نماذج AI غير محملة — النتائج بالخوارزميات الأساسية فقط")

    # ── Confidence & shot-limitation panel — always shown, not just on low confidence ──
    if not results.get('is_demo'):
        cov = int(results.get('kp_coverage', 0) * 100)
        low_conf = results.get('low_confidence', False)
        used_mp = results.get('used_mediapipe', True)
        panel_icon = '⚠️' if low_conf else '✅'
        with st.expander(f"{panel_icon} دقة التحليل وحدود اللقطة — تغطية الهيكل العظمي: {cov}%", expanded=low_conf):
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("🎯 تغطية النقاط المرجعية", f"{cov}%",
                       help="نسبة الإطارات التي تم فيها استخراج هيكل عظمي فعلي بثقة كافية")
            pc2.metric("🧍 إطارات محلَّلة", f"{results.get('pose_count', 0):,}")
            pc3.metric("🔬 محرك الكشف", "MediaPipe" if used_mp else "احتياطي (تقريبي)")

            if not used_mp:
                st.warning(
                    "⚠️ تعذّر استخدام MediaPipe لهذا الفيديو — تم استخدام تتبع حركة "
                    "احتياطي (كشف الشكل بـ OpenCV)، وهو أقل دقة بكثير ولا يعتمد على "
                    "هيكل عظمي حقيقي. أي قفزات أو دورانات معروضة هنا **تقديرية وغير "
                    "مؤكدة** — قد تنتج عن ظلال أو أشخاص آخرين أو حركة الكاميرا."
                )
            elif low_conf:
                st.warning(
                    f"⚠️ نسبة اكتشاف الهيكل العظمي منخفضة ({cov}% فقط من الإطارات) — "
                    "هذا يقلل من دقة كشف القفزات والدورانات والأخطاء. الأسباب "
                    "الشائعة: اللاعب بعيد جداً أو خارج الإطار جزئياً، إضاءة ضعيفة، "
                    "أو زاوية كاميرا غير مناسبة."
                )
            else:
                st.success(
                    "الهيكل العظمي مكتشف بثقة عالية في معظم إطارات الفيديو — "
                    "النتائج أدناه مبنية على بيانات حركة فعلية مستخرجة من اللقطة."
                )

            st.caption(
                "تذكير: كل نتيجة في هذا التقرير (نوع الحركة، الأخطاء، النقاط) هي "
                "**استدلال مبني على بيانات الحركة المرصودة** ضمن حدود جودة هذه "
                "اللقطة تحديداً — وليست حكماً قطعياً. راجع النسب المئوية للثقة "
                "المعروضة مع كل عنصر."
            )

    vi = results.get('video_info', {})
    player_name = results.get('player_name', '')

    # Top metrics — KPI tiles
    try:
        from src.utils.ysoo_theme import kpi_row_html
        st.markdown(kpi_row_html([
            ('⏱️', 'المدة', f"{vi.get('duration', 0):.1f}s"),
            ('🏆', 'النقاط الكلية', f"{results.get('total_score', 0):.2f}"),
            ('⚡', 'TES', f"{results.get('tes', 0):.2f}"),
            ('🎭', 'PCS', f"{results.get('pcs', 0):.2f}"),
            ('🦘', 'قفزات', str(len(results.get('jumps', [])))),
            ('🌀', 'دورانات', str(len(results.get('spins', [])))),
            ('👣', 'خطوات', str(len(results.get('step_sequences', [])))),
        ]), unsafe_allow_html=True)
    except Exception:
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            st.metric("⏱️ المدة", f"{vi.get('duration', 0):.1f}s")
        with col2:
            st.metric("🏆 النقاط الكلية", f"{results.get('total_score', 0):.2f}")
        with col3:
            st.metric("⚡ TES", f"{results.get('tes', 0):.2f}")
        with col4:
            st.metric("🎭 PCS", f"{results.get('pcs', 0):.2f}")
        with col5:
            st.metric("🦘 قفزات", len(results.get('jumps', [])))
        with col6:
            st.metric("🌀 دورانات", len(results.get('spins', [])))
        with col7:
            st.metric("👣 خطوات", len(results.get('step_sequences', [])))

    st.markdown("---")

    # Score breakdown gauge
    col_g, col_t = st.columns(2)

    with col_g:
        score = results.get('total_score', 0)
        max_score = 50  # arbitrary display max
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "النقاط الإجمالية", 'font': {'size': 18}},
            gauge={
                'axis': {'range': [0, max_score]},
                'bar': {'color': '#1e3a5f'},
                'steps': [
                    {'range': [0, 15], 'color': '#fef2f2'},
                    {'range': [15, 30], 'color': '#fef9c3'},
                    {'range': [30, max_score], 'color': '#f0fdf4'},
                ],
                'threshold': {
                    'line': {'color': '#16a34a', 'width': 4},
                    'thickness': 0.75,
                    'value': 35
                }
            },
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_t:
        # TES vs PCS breakdown
        categories = ['TES (عناصر)', 'PCS (أداء)']
        values = [results.get('tes', 0), results.get('pcs', 0)]
        fig_pie = go.Figure(go.Pie(
            labels=categories, values=values,
            hole=0.5,
            marker_colors=['#1e3a5f', '#4a9fd4'],
            textinfo='label+percent+value',
        ))
        fig_pie.update_layout(
            title="توزيع النقاط",
            height=280, margin=dict(l=0, r=0, t=50, b=0)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Video info
    if vi:
        st.markdown("**معلومات الفيديو:**")
        cols = st.columns(4)
        infos = [
            ("📐 الدقة", f"{vi.get('width', 0)}×{vi.get('height', 0)}"),
            ("🎬 FPS", f"{vi.get('fps', 0):.0f}"),
            ("📱 الاتجاه", vi.get('orientation', '—')),
            ("🔬 إطارات محللة", f"{results.get('pose_count', 0):,}"),
        ]
        for col, (label, val) in zip(cols, infos):
            col.metric(label, val)

    # Timeline chart
    timeline = results.get('timeline', [])
    if timeline:
        st.markdown("---")
        st.subheader("📅 الخط الزمني للعناصر")
        dur = vi.get('duration', 30)

        fig_tl = go.Figure()
        for elem in timeline:
            fig_tl.add_trace(go.Scatter(
                x=[elem['t'], elem['t'] + elem['duration']],
                y=[elem['type'], elem['type']],
                mode='lines+markers',
                line=dict(color=elem['color'], width=18),
                marker=dict(size=8, color=elem['color']),
                name=elem['label'],
                hovertemplate=(
                    f"<b>{elem['label']}</b><br>"
                    f"الوقت: {elem['t']:.1f}s – {elem['t']+elem['duration']:.1f}s<br>"
                    f"النقاط: {elem['score']:.2f}<br>"
                    f"GOE: {elem['goe']:+d}"
                ),
            ))

        fig_tl.update_layout(
            xaxis_title="الوقت (ثانية)",
            xaxis=dict(range=[0, dur]),
            height=200,
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=40),
            plot_bgcolor='rgba(248,250,252,1)',
        )
        st.plotly_chart(fig_tl, use_container_width=True)


# ============================================================================
# TAB: ELEMENTS (JUMPS + SPINS)
# ============================================================================

def _tab_elements(ar: bool, lang: str):
    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً")
        return

    jumps = results.get('jumps', [])
    spins = results.get('spins', [])

    # ── JUMPS ────────────────────────────────────────────────────────────────
    st.subheader(f"🦘 القفزات المرجّحة ({len(jumps)})")
    if jumps:
        st.caption(
            "التصنيف أدناه هو **أرجح نوع** بناءً على بيانات الحركة المستخرجة "
            "(الدوران، وقت الطيران، الارتفاع) — وليس تعرّفاً قطعياً. راجع نسبة "
            "الثقة على كل بطاقة."
        )

    if jumps:
        for i, j in enumerate(jumps, 1):
            clean = j.get('is_clean', True)
            goe = j.get('goe', 0)
            goe_color = '#16a34a' if goe > 0 else ('#dc2626' if goe < 0 else '#64748b')
            border = '#22c55e' if clean else '#ef4444'
            ai_conf = j.get('ai_confidence')
            conf_badge = (
                f"<span style='font-size:0.7em;background:#e0f2fe;color:#0369a1;"
                f"border-radius:999px;padding:2px 9px;margin-right:6px'>"
                f"ثقة {int(ai_conf*100)}%</span>"
                if ai_conf is not None else
                "<span style='font-size:0.7em;background:#f1f5f9;color:#64748b;"
                "border-radius:999px;padding:2px 9px;margin-right:6px'>تقدير أولي</span>"
            )

            with st.container():
                st.markdown(f"""
                <div style="border:2px solid {border};border-radius:12px;
                            padding:14px 18px;margin-bottom:12px;
                            background:{'#f0fdf4' if clean else '#fff1f2'}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.25em;font-weight:700">
                      {'✅' if clean else '⚠️'} {i}. الحركة المرجّحة: {j.get('type','')}
                      <span style="font-size:0.75em;color:#94a3b8;margin-right:8px">({j.get('code','')})</span>
                      {conf_badge}
                    </span>
                    <span style="font-size:1.5em;font-weight:800;color:{goe_color}">
                      {j.get('final_score',0):.2f} pts
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4, c5, c6 = st.columns(6)
                rot_method = j.get('rotation_method', 'airtime_heuristic')
                rot_icon = '🎯' if rot_method == 'shoulder_tracking' else '📐'
                rot_label = f"{j.get('rotations',0):.1f} {rot_icon}"
                c1.metric("🔁 دورات", rot_label,
                          help="🎯 = تتبع كتفين فعلي | 📐 = تقدير بالوقت")
                c2.metric("📏 ارتفاع", f"{j.get('height_cm',0)} cm")
                c3.metric("⏱️ طيران", f"{j.get('airtime',0):.2f}s")
                c4.metric("⚡ RPM", f"{j.get('rpm',0):.0f}")
                c5.metric("📌 Base", f"{j.get('base_value',0):.2f}")
                c6.markdown(f"<div style='text-align:center;padding-top:12px;"
                            f"color:{goe_color};font-weight:700;font-size:1.1em'>"
                            f"GOE: {goe:+d}</div>", unsafe_allow_html=True)

                # AI-enhanced details
                ai_code = j.get('ai_code')
                if ai_code:
                    with st.expander(f"🤖 تحليل الذكاء الاصطناعي — {ai_code}", expanded=False):
                        a1, a2, a3, a4 = st.columns(4)
                        a1.metric("🏷️ كود AI", j.get('ai_code', '—'))
                        conf_pct = int(j.get('ai_confidence', 0) * 100)
                        a2.metric("📊 ثقة", f"{conf_pct}%")
                        a3.metric("↗️ إقلاع", j.get('ai_takeoff', '—'))
                        a4.metric("⚡ حافة", j.get('ai_edge', '—'))

                        lstm_label = j.get('lstm_label')
                        if lstm_label:
                            st.markdown(f"**🧠 LSTM:** `{lstm_label}`"
                                        f" ({int(j.get('lstm_confidence',0)*100)}%)")
                            top3 = j.get('lstm_top3', [])
                            if top3:
                                top3_str = " · ".join(f"{lb} {int(c*100)}%" for lb, c in top3)
                                st.caption(f"أعلى 3: {top3_str}")

                        pose_score = j.get('pose_score')
                        if pose_score is not None:
                            rating = j.get('pose_rating', '')
                            phase_map = {
                                'axel_takeoff': 'الإقلاع',
                                'axel_flight':  'الطيران',
                                'axel_landing': 'الهبوط',
                            }
                            phase_label = phase_map.get(j.get('pose_phase',''), j.get('pose_phase',''))
                            # pose_score is on a 0-100 scale (PoseComparator._score_from_deviations),
                            # not 0-1 — don't multiply by 100 again.
                            st.markdown(f"**🦴 جودة الوضعية ({phase_label}):** "
                                        f"`{int(round(pose_score))}%` {rating}")
                            corrections = j.get('pose_corrections_ar', [])
                            if corrections:
                                for corr in corrections[:3]:
                                    st.markdown(f"   • {corr}")

        # Jump comparison chart
        st.markdown("---")
        labels = [f"{i}.{j.get('type','')}" for i, j in enumerate(jumps, 1)]
        base_vals = [j.get('base_value', 0) for j in jumps]
        goe_vals = [j.get('goe', 0) * j.get('base_value', 0) * 0.1 for j in jumps]
        colors = ['#22c55e' if j.get('is_clean', True) else '#ef4444' for j in jumps]

        fig = go.Figure()
        fig.add_trace(go.Bar(name='القيمة الأساسية', x=labels, y=base_vals,
                             marker_color='#3b82f6'))
        fig.add_trace(go.Bar(name='GOE', x=labels, y=goe_vals,
                             marker_color=['#22c55e' if g >= 0 else '#ef4444' for g in goe_vals]))
        fig.update_layout(barmode='stack', height=300,
                          title="نقاط القفزات (Base + GOE)",
                          margin=dict(l=0, r=0, t=50, b=0))
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("لم يتم اكتشاف قفزات في هذا الفيديو")

    st.markdown("---")

    # ── SPINS ────────────────────────────────────────────────────────────────
    st.subheader(f"🌀 الدورانات المرجّحة ({len(spins)})")

    if spins:
        for i, s in enumerate(spins, 1):
            goe = s.get('goe', 0)
            goe_color = '#16a34a' if goe > 0 else ('#dc2626' if goe < 0 else '#64748b')

            with st.container():
                st.markdown(f"""
                <div style="border:2px solid #3b82f6;border-radius:12px;
                            padding:14px 18px;margin-bottom:12px;background:#eff6ff">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.2em;font-weight:700">
                      🌀 {i}. {s.get('type','')}
                      <span style="font-size:0.75em;color:#94a3b8;margin-right:8px">
                        ({s.get('code','')}) Level {s.get('level',0)}
                      </span>
                    </span>
                    <span style="font-size:1.5em;font-weight:800;color:{goe_color}">
                      {s.get('final_score',0):.2f} pts
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("🔁 دورات", f"{s.get('rotations',0):.1f}")
                c2.metric("⚡ RPM", f"{s.get('rpm',0):.0f}")
                c3.metric("⏱️ المدة", f"{s.get('duration',0):.1f}s")
                c4.metric("🏅 المستوى", f"L{s.get('level',0)}")
                c5.markdown(f"<div style='text-align:center;padding-top:12px;"
                            f"color:{goe_color};font-weight:700;font-size:1.1em'>"
                            f"GOE: {goe:+d}</div>", unsafe_allow_html=True)

                # AI spin details
                ai_code_s = s.get('ai_code')
                if ai_code_s:
                    with st.expander(f"🤖 تحليل الذكاء الاصطناعي — {ai_code_s}", expanded=False):
                        b1, b2, b3 = st.columns(3)
                        b1.metric("🎭 وضعية", s.get('ai_position', '—'))
                        stab = s.get('axis_stability', 0)
                        b2.metric("🎯 استقرار المحور", f"{int(stab*100)}%")
                        b3.metric("🏅 مستوى AI", f"L{s.get('ai_level', s.get('level',1))}")

                        pose_score_s = s.get('pose_score')
                        if pose_score_s is not None:
                            # pose_score is already 0-100 (see note above) — don't rescale.
                            st.markdown(f"**🦴 جودة الوضعية:** `{int(round(pose_score_s))}%` "
                                        f"{s.get('pose_rating','')}")
                            corrs_s = s.get('pose_corrections_ar', [])
                            for corr in corrs_s[:3]:
                                st.markdown(f"   • {corr}")
    else:
        st.info("لم يتم اكتشاف دورانات في هذا الفيديو")

    # ── STEP SEQUENCES ────────────────────────────────────────────────────────
    step_seqs = results.get('step_sequences', [])
    if step_seqs:
        st.markdown("---")
        st.subheader(f"👣 تسلسلات الخطوات ({len(step_seqs)})")
        for i, ss in enumerate(step_seqs, 1):
            with st.container():
                st.markdown(f"""
                <div style="border:2px solid #a78bfa;border-radius:12px;
                            padding:14px 18px;margin-bottom:12px;background:#faf5ff">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.1em;font-weight:700">
                      👣 {i}. {ss.get('type','Step Sequence')}
                      <span style="font-size:0.75em;color:#94a3b8;margin-right:8px">
                        ({ss.get('code','')}) Level {ss.get('level',1)}
                      </span>
                    </span>
                    <span style="font-size:1.4em;font-weight:800;color:#7c3aed">
                      {ss.get('final_score',0):.2f} pts
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                s1, s2, s3, s4 = st.columns(4)
                s1.metric("⏱️ المدة", f"{ss.get('duration',0):.1f}s")
                s2.metric("🏅 المستوى", f"L{ss.get('level',1)}")
                s3.metric("📌 Base Value", f"{ss.get('base_value',0):.2f}")
                s4.metric("🔀 تعقيد", f"{int(ss.get('complexity',0)*100)}%")


# ============================================================================
# TAB: ERRORS & CORRECTIONS
# ============================================================================

def _tab_errors(ar: bool, lang: str):
    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً")
        return

    errors = results.get('errors', [])
    total_goe_impact = sum(e.get('goe_impact', 0) for e in errors)

    # Summary
    sev_map = {'حرج': 0, 'CRITICAL': 0, 'عالي': 1, 'HIGH': 1,
               'متوسط': 2, 'MEDIUM': 2, 'منخفض': 3, 'LOW': 3}
    counts = [0, 0, 0, 0]
    for e in errors:
        idx = sev_map.get(e.get('severity', 'LOW'), 3)
        counts[idx] += 1

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 إجمالي الأخطاء", len(errors))
    col2.metric("🔴 حرج", counts[0])
    col3.metric("🟠 عالي", counts[1])
    col4.metric("🟡 متوسط", counts[2])
    col5.metric("🟢 منخفض", counts[3])

    if total_goe_impact != 0:
        st.warning(f"تأثير الأخطاء على النقاط: **{total_goe_impact:+d} GOE**")

    if not errors:
        st.success("🎉 ممتاز! لم يتم اكتشاف أخطاء تقنية في هذا الأداء.")
        return

    st.markdown("---")

    # Filter
    all_sevs = list(dict.fromkeys(e.get('severity', '') for e in errors))
    chosen = st.selectbox("فلتر:", ['الكل'] + all_sevs, label_visibility='collapsed')
    filtered = errors if chosen == 'الكل' else [e for e in errors if e.get('severity') == chosen]

    try:
        from src.analysis.coaching_knowledge import (
            resolve_symptom_key, get_symptom_info, get_physical_prep,
            CORRECTION_PROTOCOL_AR,
        )
        CK_OK = True
    except Exception:
        CK_OK = False

    try:
        from src.utils.ysoo_theme import error_card_html, normalize_severity
        THEME_OK = True
    except Exception:
        THEME_OK = False

    for err in filtered:
        sev = err.get('severity', 'LOW')
        color = SEV_COLOR.get(sev, '#64748b')
        icon = SEV_ICON.get(sev, '⚪')
        title = err.get('title_ar', err.get('title_en', ''))
        desc = err.get('desc_ar', err.get('desc_en', err.get('description_ar', '')))
        fixes = err.get('fix_ar', err.get('corrections_ar', []))
        goe_impact = err.get('goe_impact', 0)
        cat = err.get('category', '')

        if THEME_OK:
            tier = normalize_severity(sev)
            conf = {'critical': 92, 'major': 82, 'minor': 70}[tier]
            # Real AI-derived confidence, when the error carries one
            m = re.search(r'(\d{1,3})%', desc)
            if m:
                conf = int(m.group(1))
            correction_html = '<br>'.join(f"• {fx}" for fx in fixes) if fixes else None
            extra_stats = f"GOE: {goe_impact:+d}" if goe_impact != 0 else None
            st.markdown(
                error_card_html(
                    title=title, severity=sev, phase_label=cat, phase_key=None,
                    confidence=conf, tech_details=desc, correction=correction_html,
                    extra_stats=extra_stats,
                ), unsafe_allow_html=True
            )
        else:
            st.markdown(f"""
            <div style="border-right:5px solid {color};background:#fafafa;
                        border-radius:8px;padding:16px 20px;margin-bottom:14px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06)">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                <span style="font-size:1.3em">{icon}</span>
                <span style="font-weight:700;color:{color};font-size:1.05em">{title}</span>
                <span style="margin-right:auto;font-size:0.78em;color:#94a3b8">
                  {cat} {'| GOE: ' + str(goe_impact) if goe_impact != 0 else ''}
                </span>
              </div>
              <div style="color:#475569;font-size:0.9em">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            if fixes:
                with st.expander(f"✏️ التصحيحات المقترحة ({len(fixes)})"):
                    for n, fix in enumerate(fixes, 1):
                        st.markdown(f"**{n}.** {fix}")

        # ── Coaching knowledge base: root cause + cue library + physical prep ──
        if CK_OK:
            symptom_key = err.get('symptom_key') or resolve_symptom_key(err)
            info = get_symptom_info(symptom_key) if symptom_key else None
            if info:
                with st.expander(f"🧠 التشخيص الفني الكامل — {info['title_ar']}"):
                    st.markdown(
                        f"<div style='background:#fff7ed;border-right:4px solid #f97316;"
                        f"border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:0.88em'>"
                        f"<b>🔬 السبب الجذري (قاعدة المرحلة السابقة):</b><br>{info['root_cause_ar']}"
                        f"</div>", unsafe_allow_html=True
                    )

                    st.markdown("**🗣️ جمل تدريب فورية جاهزة:**")
                    for cue in info.get('cues', []):
                        st.markdown(f"- {cue['ar']}")

                    drill = info.get('drill_ar')
                    if drill:
                        st.markdown(f"**🏋️ تمرين التصحيح المعزول:** {drill}")

                    prep = get_physical_prep(symptom_key)
                    if prep:
                        st.markdown(f"**💪 تمرين بدني مكمّل:** {prep['ar']}")

    if CK_OK and filtered:
        with st.expander("📋 بروتوكول التصحيح ثلاثي الخطوات (عند فشل التلميح اللفظي)"):
            for step_title, step_desc in CORRECTION_PROTOCOL_AR:
                st.markdown(f"**{step_title}** — {step_desc}")


# ============================================================================
# TAB: STATISTICS
# ============================================================================

def _tab_stats(ar: bool, lang: str):
    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً")
        return

    jumps = results.get('jumps', [])
    spins = results.get('spins', [])
    errors = results.get('errors', [])

    if not jumps and not spins:
        st.info("لا توجد بيانات كافية للإحصاءات")
        return

    col1, col2 = st.columns(2)

    # ── Radar chart ──────────────────────────────────────────────────────────
    with col1:
        if jumps:
            avg_goe = np.mean([j.get('goe', 0) for j in jumps])
            avg_h = np.mean([j.get('height_cm', 0) for j in jumps])
            avg_rpm = np.mean([j.get('rpm', 0) for j in jumps])
            clean_r = np.mean([1 if j.get('is_clean', True) else 0 for j in jumps])
            err_ratio = max(0, 1 - len(errors) / 8)

            cats = ['GOE', 'الارتفاع', 'السرعة', 'هبوط نظيف', 'الدقة']
            vals = [
                min(10, max(0, (avg_goe + 3) * 2)),
                min(10, avg_h / 7),
                min(10, avg_rpm / 30),
                clean_r * 10,
                err_ratio * 10,
            ]
            vals = [round(v, 1) for v in vals]

            fig_r = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats + [cats[0]],
                fill='toself',
                fillcolor='rgba(30,58,95,0.2)',
                line=dict(color='#1e3a5f', width=2),
                name='الأداء'
            ))
            fig_r.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                title="🕸️ ملف الأداء",
                height=380, margin=dict(l=40, r=40, t=60, b=40)
            )
            st.plotly_chart(fig_r, use_container_width=True)

    # ── Error pie ────────────────────────────────────────────────────────────
    with col2:
        if errors:
            sev_count: Dict[str, int] = {}
            for e in errors:
                sev_count[e.get('severity', 'LOW')] = sev_count.get(e.get('severity', 'LOW'), 0) + 1

            fig_e = go.Figure(go.Pie(
                labels=list(sev_count.keys()),
                values=list(sev_count.values()),
                hole=0.55,
                marker_colors=[SEV_COLOR.get(s, '#64748b') for s in sev_count],
            ))
            fig_e.update_layout(
                title="توزيع الأخطاء حسب الخطورة",
                height=380, margin=dict(l=0, r=0, t=60, b=0)
            )
            st.plotly_chart(fig_e, use_container_width=True)

    # ── Jump height bar ──────────────────────────────────────────────────────
    if jumps:
        st.markdown("---")
        fig_h = px.bar(
            x=[f"{i}.{j.get('type','')}" for i, j in enumerate(jumps, 1)],
            y=[j.get('height_cm', 0) for j in jumps],
            color=[j.get('height_cm', 0) for j in jumps],
            color_continuous_scale='Blues',
            labels={'x': 'القفزة', 'y': 'الارتفاع (cm)', 'color': 'cm'},
            title="📏 ارتفاع كل قفزة",
            text=[f"{j.get('height_cm',0)} cm" for j in jumps],
        )
        fig_h.update_layout(height=300, margin=dict(l=0, r=0, t=60, b=0),
                            coloraxis_showscale=False)
        fig_h.update_traces(textposition='outside')
        st.plotly_chart(fig_h, use_container_width=True)

    # ── Detailed table ───────────────────────────────────────────────────────
    if jumps:
        st.subheader("📋 جدول القفزات التفصيلي")
        df_j = pd.DataFrame([{
            'النوع': j.get('type', ''),
            'الكود': j.get('code', ''),
            'الدورات': j.get('rotations', 0),
            'الارتفاع (cm)': j.get('height_cm', 0),
            'وقت الطيران (s)': j.get('airtime', 0),
            'RPM': j.get('rpm', 0),
            'Base Value': j.get('base_value', 0),
            'GOE': j.get('goe', 0),
            'النقاط': j.get('final_score', 0),
            'هبوط نظيف': '✅' if j.get('is_clean', True) else '❌',
        } for j in jumps])
        st.dataframe(df_j, use_container_width=True, hide_index=True)


# ============================================================================
# TAB: REPORTS
# ============================================================================

# ============================================================================
# TAB: SKELETON 3D
# ============================================================================

def _tab_skeleton_3d(ar: bool, lang: str):
    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً" if ar else
                "Upload a video or use demo first")
        return

    is_demo = results.get('is_demo', False)
    skel_frames = results.get('skeleton_frames', [])
    pose_samples = results.get('pose_samples', [])

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);
                border-radius:14px;padding:20px 24px;margin-bottom:20px;color:white">
      <h3 style="margin:0 0 6px;font-size:1.3em">🦴 الحركة مع الهيكل العظمي المتحرك</h3>
      <p style="margin:0;opacity:.75;font-size:.9em">
        شاهد فيديو التزلج مع هيكل عظمي متحرك فوق الجسم (33 نقطة مرجعية من MediaPipe)،
        بالإضافة إلى عرض تفاعلي ثلاثي الأبعاد لأي لحظة تختارها
      </p>
    </div>
    """, unsafe_allow_html=True)

    if is_demo or (not skel_frames and not pose_samples):
        # Show demo 3D skeleton
        st.info("⚡ عرض تجريبي — ارفع فيديو حقيقي للحصول على هيكل عظمي مُحلَّل فعلياً")
        _show_demo_skeleton_3d()
        return

    # ── SECTION 0: Full video with the moving skeleton overlay ──────────────
    skel_video = results.get('skeleton_video_bytes')
    if skel_video:
        st.subheader("🎬 فيديو الحركة مع الهيكل العظمي")
        st.video(skel_video)
        st.caption(
            "الهيكل العظمي مرسوم فوق الجسم لحظة بلحظة استناداً إلى نقاط الاستدلال "
            "المُستخرجة فعلياً من الفيديو — وليس تخميناً. عند غياب نقطة موثوقة "
            "لإطار معين، يُعرض آخر وضعية مؤكدة حتى يعود الاكتشاف."
        )
    else:
        st.info(
            "ℹ️ تعذّر توليد فيديو الهيكل العظمي المتحرك لهذا التحليل "
            "(قد يكون بسبب عدم توفر مُرمِّز فيديو متوافق على الجهاز) — "
            "استخدم العرض التفاعلي ثلاثي الأبعاد أدناه أو معرض الإطارات كبديل."
        )

    st.markdown("---")

    # ── SECTION 1: 3D Interactive Skeleton ───────────────────────────────────
    if pose_samples:
        st.subheader("🔵 هيكل عظمي تفاعلي — اختر الإطار")

        sample_count = len(pose_samples)
        frame_idx = st.slider(
            "الإطار الزمني",
            min_value=0, max_value=max(0, sample_count - 1),
            value=0, step=1,
            format="إطار %d",
            key='skel_frame_slider'
        )

        sample = pose_samples[frame_idx]
        t_sec = sample.get('t', 0)
        is_air = sample.get('airborne', False)

        # Build 3D figure
        try:
            fig3d = _build_3d_skeleton_fig(
                sample['kp'],
                title=f"الهيكل العظمي عند {t_sec:.1f}ث {'🟡 في الهواء' if is_air else '⬇️ على الأرض'}"
            )
            if fig3d:
                st.plotly_chart(fig3d, use_container_width=True)
        except Exception as _e3d:
            st.warning(f"تعذّر رسم الهيكل العظمي 3D: {_e3d}")

        # Joint angles readout
        kp = sample['kp']
        st.markdown("**📐 زوايا المفاصل الرئيسية:**")

        def ang3(a, b, c):
            """Angle at joint b formed by a-b-c."""
            try:
                va = np.array([kp[a]['x']-kp[b]['x'], kp[a]['y']-kp[b]['y'], kp[a].get('z',0)-kp[b].get('z',0)])
                vc = np.array([kp[c]['x']-kp[b]['x'], kp[c]['y']-kp[b]['y'], kp[c].get('z',0)-kp[b].get('z',0)])
                cos = np.dot(va,vc)/(np.linalg.norm(va)*np.linalg.norm(vc)+1e-9)
                return round(np.degrees(np.arccos(np.clip(cos,-1,1))), 1)
            except Exception:
                return None

        joint_angles = {
            'كوع أيسر':  ang3(11, 13, 15),
            'كوع أيمن':  ang3(12, 14, 16),
            'ركبة يسرى': ang3(23, 25, 27),
            'ركبة يمنى': ang3(24, 26, 28),
            'ورك أيسر':  ang3(11, 23, 25),
            'ورك أيمن':  ang3(12, 24, 26),
        }

        angle_cols = st.columns(6)
        for (name, deg), col in zip(joint_angles.items(), angle_cols):
            if deg is not None:
                color = '#10B981' if 150 <= deg <= 180 else ('#F59E0B' if 100 <= deg < 150 else '#EF4444')
                col.markdown(
                    f"<div style='text-align:center;background:#1e293b;border-radius:10px;"
                    f"padding:10px 6px;color:{color}'>"
                    f"<div style='font-size:1.4em;font-weight:800'>{deg}°</div>"
                    f"<div style='font-size:.72em;color:#94a3b8;margin-top:2px'>{name}</div></div>",
                    unsafe_allow_html=True
                )

        # Airborne timeline bar
        if sample_count > 1:
            st.markdown("**📈 حالة الجسم عبر الزمن:**")
            ts = [s.get('t', i/10) for i, s in enumerate(pose_samples)]
            air = [1 if s.get('airborne') else 0 for s in pose_samples]
            fig_air = go.Figure()
            fig_air.add_trace(go.Scatter(
                x=ts, y=air, mode='lines', fill='tozeroy',
                line=dict(color='#60A5FA', width=2),
                fillcolor='rgba(96,165,250,0.25)',
                name='في الهواء'
            ))
            fig_air.add_vline(x=t_sec, line_width=2, line_dash='dash', line_color='#F59E0B')
            fig_air.update_layout(
                height=120, margin=dict(l=0,r=0,t=10,b=0),
                yaxis=dict(tickvals=[0,1], ticktext=['أرض','هواء'], range=[-0.1, 1.3]),
                xaxis_title='الوقت (ث)',
                plot_bgcolor='rgba(15,23,42,1)',
                paper_bgcolor='rgba(15,23,42,1)',
                font_color='#94a3b8',
            )
            st.plotly_chart(fig_air, use_container_width=True)

    st.markdown("---")

    # ── SECTION 2: Skeleton overlay frames ───────────────────────────────────
    if skel_frames:
        st.subheader("📸 إطارات مع الهيكل العظمي")
        st.caption(f"تم حفظ {len(skel_frames)} إطار خلال التحليل")

        # Controls
        col_flt, col_jump = st.columns([3, 1])
        with col_flt:
            show_all = st.checkbox("إظهار جميع الإطارات", value=False)
        with col_jump:
            jump_only = st.checkbox("إطارات الطيران فقط", value=False)

        filtered = skel_frames
        if jump_only:
            filtered = [f for f in skel_frames if f.get('airborne')]
        if not show_all:
            filtered = filtered[:12]

        if not filtered:
            st.info("لا توجد إطارات مطابقة")
        else:
            num_cols = 3
            for row_start in range(0, len(filtered), num_cols):
                row = filtered[row_start:row_start + num_cols]
                cols = st.columns(num_cols)
                for col, frm in zip(cols, row):
                    with col:
                        t_val = frm.get('t', 0)
                        air_badge = "🟡 طيران" if frm.get('airborne') else "⬇️ أرض"
                        st.markdown(
                            f"<img src='data:image/jpeg;base64,{frm['b64']}' "
                            f"style='width:100%;border-radius:10px;border:2px solid "
                            f"{'#F59E0B' if frm.get('airborne') else '#334155'}'>",
                            unsafe_allow_html=True
                        )
                        st.caption(f"{t_val:.1f}ث — {air_badge}")

    else:
        st.info("الهيكل العظمي على الإطارات يتطلب MediaPipe — الملف لم يُعالَج بالكامل بـ MediaPipe")

    st.markdown("---")

    # ── SECTION 3: Rotation tracking chart ───────────────────────────────────
    jumps = results.get('jumps', [])
    if jumps and pose_samples:
        st.subheader("🔄 تتبع الدوران بمحاذاة الكتفين")
        times_ps = [s.get('t', 0) for s in pose_samples]
        sh_angles = []
        for s in pose_samples:
            kp = s.get('kp', [])
            if len(kp) > 12:
                ls, rs = kp[11], kp[12]
                if ls.get('v', 0) > 0.2 and rs.get('v', 0) > 0.2:
                    sh_angles.append(float(np.degrees(np.arctan2(
                        rs.get('z', 0) - ls.get('z', 0),
                        rs['x'] - ls['x']
                    ))))
                else:
                    sh_angles.append(None)
            else:
                sh_angles.append(None)

        valid = [(t, a) for t, a in zip(times_ps, sh_angles) if a is not None]
        if valid:
            vt, va = zip(*valid)
            fig_rot = go.Figure()
            fig_rot.add_trace(go.Scatter(
                x=list(vt), y=list(va),
                mode='lines', name='زاوية الكتفين',
                line=dict(color='#A78BFA', width=2)
            ))
            # Mark jump windows
            for j in jumps:
                fig_rot.add_vrect(
                    x0=j.get('t_start', 0), x1=j.get('t_end', 0),
                    fillcolor='rgba(245,158,11,0.15)',
                    layer='below', line_width=0,
                    annotation_text=j.get('code', ''), annotation_position='top left'
                )
            fig_rot.update_layout(
                height=260, margin=dict(l=0,r=0,t=30,b=0),
                xaxis_title='الوقت (ث)',
                yaxis_title='زاوية الكتف (°)',
                plot_bgcolor='rgba(15,23,42,1)',
                paper_bgcolor='rgba(15,23,42,1)',
                font_color='#94a3b8',
            )
            st.plotly_chart(fig_rot, use_container_width=True)
            st.caption("المناطق البرتقالية = نوافذ القفز. تذبذبات الزاوية خلالها = دورانات فعلية")


def _show_demo_skeleton_3d():
    """Show a synthetic demo skeleton when no real data available."""
    import math
    # T-pose synthetic keypoints
    demo_kp = []
    defs = {
        0:  (0.50, 0.08, 0.00, 1.0),  # nose
        11: (0.40, 0.25, 0.00, 1.0), 12: (0.60, 0.25, 0.00, 1.0),  # shoulders
        13: (0.32, 0.40, 0.00, 1.0), 14: (0.68, 0.40, 0.00, 1.0),  # elbows
        15: (0.24, 0.52, 0.00, 1.0), 16: (0.76, 0.52, 0.00, 1.0),  # wrists
        23: (0.43, 0.55, 0.00, 1.0), 24: (0.57, 0.55, 0.00, 1.0),  # hips
        25: (0.42, 0.72, 0.00, 1.0), 26: (0.58, 0.72, 0.00, 1.0),  # knees
        27: (0.41, 0.88, 0.00, 1.0), 28: (0.59, 0.88, 0.00, 1.0),  # ankles
        29: (0.40, 0.92, 0.00, 1.0), 30: (0.60, 0.92, 0.00, 1.0),  # heels
        31: (0.38, 0.95, 0.00, 1.0), 32: (0.62, 0.95, 0.00, 1.0),  # foot index
    }
    for i in range(33):
        if i in defs:
            x, y, z, v = defs[i]
        else:
            x, y, z, v = 0.5, 0.5, 0.0, 0.3
        demo_kp.append({'x': x, 'y': y, 'z': z, 'v': v, 'idx': i})

    try:
        fig = _build_3d_skeleton_fig(demo_kp, title="هيكل عظمي تجريبي — وضع T-Pose")
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    except Exception as _e_demo:
        st.warning(f"تعذّر رسم الهيكل التجريبي: {_e_demo}")

    st.markdown("""
    <div style="background:#1e293b;border-radius:10px;padding:14px;color:#94a3b8;font-size:.85em">
    <b style="color:#60A5FA">كيف تعمل تقنية الهيكل العظمي 3D:</b><br>
    • MediaPipe يستخرج 33 نقطة مرجعية (مفصل) من كل إطار فيديو<br>
    • كل نقطة لها إحداثيات X (أفقي) وY (رأسي) وZ (العمق)<br>
    • يتم رصد زاوية الكتفين عبر الزمن لحساب الدورانات الفعلية في الهواء<br>
    • الإطارات المحفوظة تُظهر الهيكل العظمي مرسوماً فوق الفيديو الأصلي
    </div>
    """, unsafe_allow_html=True)


def _tab_reports(ar: bool, lang: str):
    st.subheader("📄 التقارير والتصدير")

    results = st.session_state.get('analysis_results')
    if not results:
        st.info("ارفع فيديو أو استخدم العرض التجريبي أولاً")
        return

    player_name = results.get('player_name', 'اللاعب')

    col1, col2, col3 = st.columns(3)

    # ── Excel export ──────────────────────────────────────────────────────────
    with col1:
        excel_bytes = _to_excel(results)
        if excel_bytes:
            st.download_button(
                "📥 تصدير Excel",
                data=excel_bytes,
                file_name=f"analysis_{player_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    # ── HTML printable report ─────────────────────────────────────────────────
    with col2:
        html_report = _to_html_report(results, player_name)
        st.download_button(
            "🖨️ تقرير للطباعة (HTML)",
            data=html_report.encode('utf-8'),
            file_name=f"report_{player_name}_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
        )

    # ── JSON export ───────────────────────────────────────────────────────────
    with col3:
        import json
        json_data = json.dumps(results, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            "📦 تصدير JSON",
            data=json_data.encode('utf-8'),
            file_name=f"raw_data_{player_name}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")

    # ── Preview of printable report ───────────────────────────────────────────
    st.subheader("معاينة التقرير")
    vi = results.get('video_info', {})
    jumps = results.get('jumps', [])
    spins = results.get('spins', [])
    errors = results.get('errors', [])

    # Score summary
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e3a5f,#2d6a9f);
                border-radius:14px;padding:24px;color:white;margin-bottom:20px">
      <div style="font-size:1.5em;font-weight:700;margin-bottom:12px">
        🏆 ملخص أداء {player_name}
      </div>
      <div style="display:flex;gap:30px;flex-wrap:wrap">
        <div><div style="font-size:2.5em;font-weight:800">{results.get('total_score',0):.2f}</div>
             <div style="opacity:0.8;font-size:0.9em">النقاط الكلية</div></div>
        <div><div style="font-size:2.5em;font-weight:800">{results.get('tes',0):.2f}</div>
             <div style="opacity:0.8;font-size:0.9em">TES</div></div>
        <div><div style="font-size:2.5em;font-weight:800">{results.get('pcs',0):.2f}</div>
             <div style="opacity:0.8;font-size:0.9em">PCS</div></div>
        <div><div style="font-size:2.5em;font-weight:800">{len(jumps)}</div>
             <div style="opacity:0.8;font-size:0.9em">قفزات</div></div>
        <div><div style="font-size:2.5em;font-weight:800">{len(spins)}</div>
             <div style="opacity:0.8;font-size:0.9em">دورانات</div></div>
        <div><div style="font-size:2.5em;font-weight:800">{len(errors)}</div>
             <div style="opacity:0.8;font-size:0.9em">أخطاء</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Tables
    if jumps:
        st.markdown("**🦘 القفزات:**")
        df_j = pd.DataFrame([{
            'النوع': j.get('type', ''),
            'الدورات': j.get('rotations', 0),
            'الارتفاع': f"{j.get('height_cm',0)} cm",
            'وقت الطيران': f"{j.get('airtime',0):.2f}s",
            'GOE': f"{j.get('goe',0):+d}",
            'النقاط': f"{j.get('final_score',0):.2f}",
        } for j in jumps])
        st.dataframe(df_j, use_container_width=True, hide_index=True)

    if errors:
        st.markdown("**⚠️ الأخطاء:**")
        df_e = pd.DataFrame([{
            'الفئة': e.get('category', ''),
            'الخطورة': e.get('severity', ''),
            'الخطأ': e.get('title_ar', ''),
            'التصحيح الأول': e.get('fix_ar', e.get('corrections_ar', ['—']))[0],
        } for e in errors])
        st.dataframe(df_e, use_container_width=True, hide_index=True)
