"""
🎥 صفحة تحليل الفيديو الاحترافية — YASOOO Figure Skating Analysis
تحليل كامل: قفزات · دورانات · وضعية الجسم · أخطاء فنية · درجات ISU
"""

import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import time
import io
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data.isu_elements_catalog import ISU_ELEMENTS_CATALOG, find_by_code

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
# PROGRAM-TYPE / LEVEL RULES (Short Program vs Free Skate, ISU 2024)
# ============================================================================
PROGRAM_TIME_LIMITS = {
    'short': {'novice': 140, 'junior': 150, 'senior': 170},
    'free':  {'novice': 180, 'junior': 210, 'senior': 240},
}
MAX_JUMP_ELEMENTS = {'short': 3, 'free': 8}
MAX_SPIN_ELEMENTS = {'short': 3, 'free': 4}
MAX_JUMP_REPEATS = 2  # an identical jump (same code) may not appear more than twice


def _map_db_level_to_isu(level_text: str) -> str:
    """Map a free-text 'level' field from the skaters table to novice/junior/senior."""
    if not level_text:
        return 'senior'
    t = str(level_text).strip().lower()
    if 'novice' in t or 'مبتدئ' in t or 'beginner' in t:
        return 'novice'
    if 'junior' in t or 'جونيور' in t or 'صغير' in t:
        return 'junior'
    return 'senior'

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

    def analyze(self, video_path: str, progress_cb=None,
                program_type: str = 'free', skater_level: str = 'senior') -> Dict:
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
        try:
            if MP_OK:
                poses, frame_scores = self._extract_poses_mediapipe(video_path, progress_cb)
            else:
                poses, frame_scores = self._extract_motion_opencv(video_path, progress_cb)
        except Exception:
            poses, frame_scores = self._extract_motion_opencv(video_path, progress_cb)

        if not poses:
            return self._error_result("No person detected in video")

        # ── Element detection — spins FIRST, then exclude spin windows from jump detection ──
        spins = self._detect_spins(poses)
        jumps = self._detect_jumps(poses, spin_windows=[(s['t_start'], s['t_end']) for s in spins])
        errors = self._detect_errors(poses, jumps)
        errors += self._detect_program_errors(program_type, skater_level, duration, jumps, spins)
        timeline = self._build_timeline(poses, jumps, spins)

        # ── Scoring ──────────────────────────────────────────────────────────
        tes = sum(j['final_score'] for j in jumps) + sum(s['final_score'] for s in spins)
        pcs = round(min(10, max(3, 8 - len(errors) * 0.5)) * 2, 2)

        return {
            'video_info': video_info,
            'jumps': jumps,
            'spins': spins,
            'errors': errors,
            'timeline': timeline,
            'total_score': round(tes + pcs, 2),
            'tes': round(tes, 2),
            'pcs': pcs,
            'pose_count': len(poses),
            'is_demo': False,
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'program_type': program_type,
            'skater_level': skater_level,
        }

    # ── Program-type / level-aware error detection ──────────────────────────
    def _detect_program_errors(self, program_type: str, skater_level: str,
                                duration: float, jumps: List[Dict],
                                spins: List[Dict]) -> List[Dict]:
        """Errors specific to the program segment (Short/Free) and skater level,
        per ISU rules: time limit, element count limits, jump repetition."""
        errors = []
        ptype = program_type if program_type in PROGRAM_TIME_LIMITS else 'free'
        plevel = skater_level if skater_level in ('novice', 'junior', 'senior') else 'senior'
        ptype_ar = 'البرنامج القصير' if ptype == 'short' else 'البرنامج الحر'
        ptype_en = 'Short Program' if ptype == 'short' else 'Free Skate'

        # 1) Time limit violation (±10s tolerance, per ISU rule)
        limit = PROGRAM_TIME_LIMITS[ptype][plevel]
        if duration > limit + 10 or duration < limit - 10:
            errors.append({
                'category': 'البرنامج', 'severity': 'متوسط',
                'title_ar': f"مخالفة زمن {ptype_ar}",
                'title_en': f"{ptype_en} Time Violation",
                'desc_ar': f"مدة الأداء {duration:.0f}ث خارج الحد المسموح ({limit}±10ث لمستوى {plevel})",
                'desc_en': f"Performance duration {duration:.0f}s is outside the allowed limit ({limit}±10s for {plevel} level)",
                'fix_ar': ['ضبط طول الموسيقى مع المدرب', 'مراجعة توقيت العناصر داخل البرنامج'],
                'fix_en': ['Adjust music length with coach', 'Review element timing within the program'],
                'goe_impact': -1, 't_start': 0, 't_end': duration,
            })

        # 2) Too many jump/spin elements for the program type
        max_jumps = MAX_JUMP_ELEMENTS[ptype]
        max_spins = MAX_SPIN_ELEMENTS[ptype]
        if len(jumps) > max_jumps:
            errors.append({
                'category': 'البرنامج', 'severity': 'منخفض',
                'title_ar': f"عدد قفزات زائد عن حد {ptype_ar}",
                'title_en': f"Jump Count Exceeds {ptype_en} Limit",
                'desc_ar': f"تم اكتشاف {len(jumps)} قفزة، والحد التقريبي لـ{ptype_ar} هو {max_jumps}",
                'desc_en': f"Detected {len(jumps)} jumps; approximate {ptype_en} limit is {max_jumps}",
                'fix_ar': ['مراجعة تركيب البرنامج مع المدرب لتفادي عناصر زائدة'],
                'fix_en': ['Review program composition with coach to avoid extra elements'],
                'goe_impact': 0, 't_start': 0, 't_end': duration,
            })
        if len(spins) > max_spins:
            errors.append({
                'category': 'البرنامج', 'severity': 'منخفض',
                'title_ar': f"عدد دورانات زائد عن حد {ptype_ar}",
                'title_en': f"Spin Count Exceeds {ptype_en} Limit",
                'desc_ar': f"تم اكتشاف {len(spins)} دوران، والحد التقريبي لـ{ptype_ar} هو {max_spins}",
                'desc_en': f"Detected {len(spins)} spins; approximate {ptype_en} limit is {max_spins}",
                'fix_ar': ['مراجعة تركيب البرنامج مع المدرب لتفادي عناصر زائدة'],
                'fix_en': ['Review program composition with coach to avoid extra elements'],
                'goe_impact': 0, 't_start': 0, 't_end': duration,
            })

        # 3) Jump repetition rule — same jump code more than twice
        code_counts: Dict[str, int] = {}
        for j in jumps:
            code = j.get('code', j.get('type', ''))
            code_counts[code] = code_counts.get(code, 0) + 1
        for code, n in code_counts.items():
            if n > MAX_JUMP_REPEATS:
                errors.append({
                    'category': 'البرنامج', 'severity': 'عالي',
                    'title_ar': f"تكرار قفزة {code} أكثر من المسموح",
                    'title_en': f"Jump {code} Repeated More Than Allowed",
                    'desc_ar': f"القفزة {code} تكررت {n} مرات؛ القاعدة ISU تسمح بتكرارها مرتين كحد أقصى",
                    'desc_en': f"Jump {code} repeated {n} times; ISU rule allows it at most twice",
                    'fix_ar': ['استبدال إحدى التكرارات بقفزة مختلفة لرفع الـ Base Value'],
                    'fix_en': ['Replace one repetition with a different jump to raise base value'],
                    'goe_impact': -1, 't_start': 0, 't_end': duration,
                })

        return errors

    # ── MediaPipe Tasks API pose extraction ─────────────────────────────────
    def _extract_poses_mediapipe(self, video_path: str, progress_cb) -> Tuple[List, List]:
        poses = []
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
        SKIP = 2

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
                        is_airborne = self._is_airborne(kp)
                        poses.append({
                            'frame': fi, 't': fi / self.fps,
                            'kp': kp, 'airborne': is_airborne,
                        })

                    if progress_cb and self.total_frames > 0:
                        progress_cb(fi / self.total_frames, fi)
                fi += 1

        cap.release()
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
                    # Lateral-travel check: real jumps move; spins stay put.
                    # If x-std in this window is < 0.03, it looks like a spin — skip.
                    seg_x = xs[jump_start_idx:i + 1]
                    lateral_travel = np.std(seg_x)
                    if lateral_travel < 0.025:
                        in_jump = False
                        continue

                    height_above = baseline - min_y_in_jump
                    height_norm = height_above / max(std_y, 0.01)

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
        Detect spins by finding periods of low lateral DRIFT + rapid oscillation.

        A spin:
        - Stays in approximately the same x-position (low drift over 1s window)
        - Body oscillates back-and-forth faster than a normal skating stride
        - Lasts at least 1.5 seconds

        Threshold is 0.07 (relaxed from 0.04) because real-world camera noise
        and bounding-box jitter during a spin can exceed 0.04.
        """
        if len(poses) < 10:
            return []

        spins = []
        WIN = int(self.fps)  # 1-second windows

        xs = []
        ys = []
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

        # Global travel baseline: how much does x move during normal skating
        global_x_std = np.std(xs)

        spin_mask = np.zeros(len(xs), dtype=bool)
        for i in range(len(xs) - WIN):
            seg_x = xs[i:i + WIN]
            seg_y = ys[i:i + WIN]
            lateral_drift = np.std(seg_x)
            vertical_drift = np.std(seg_y)

            # Spin: stays in place laterally (relative to overall movement)
            # AND does not show a single clean vertical peak (which would be a jump)
            lateral_ok = lateral_drift < max(0.07, global_x_std * 0.4)

            # During a jump, vertical std is high (goes up then comes down)
            # During a spin, vertical is relatively stable
            vertical_stable = vertical_drift < 0.08

            if lateral_ok and vertical_stable:
                spin_mask[i:i + WIN] = True

        # Extract spin segments
        in_spin = False
        sp_start_idx = 0

        for i, is_sp in enumerate(spin_mask):
            if is_sp and not in_spin:
                in_spin = True
                sp_start_idx = i
            elif not is_sp and in_spin:
                sp_end_idx = i - 1
                duration = times[sp_end_idx] - times[sp_start_idx]
                if duration >= 1.5:
                    # Estimate RPM from x-oscillation frequency
                    seg_x = xs[sp_start_idx:sp_end_idx + 1]
                    # Count zero-crossings of detrended signal
                    seg_detrended = seg_x - seg_x.mean()
                    crossings = np.where(np.diff(np.sign(seg_detrended)))[0]
                    cycles = len(crossings) / 2
                    rpm = (cycles / duration * 60) if duration > 0 else 60
                    rpm = max(40, min(300, rpm * 3))  # scale up

                    sp = _classify_spin(duration, rpm)
                    sp['t_start'] = round(times[sp_start_idx], 2)
                    sp['t_end'] = round(times[sp_end_idx], 2)
                    sp['frame_start'] = int(times[sp_start_idx] * self.fps)
                    sp['frame_end'] = int(times[sp_end_idx] * self.fps)
                    spins.append(sp)
                in_spin = False

        return spins

    # ── Error detection ──────────────────────────────────────────────────────
    def _detect_errors(self, poses: List, jumps: List) -> List[Dict]:
        errors = []

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
                })

        # 2) Posture analysis from MediaPipe poses (if available)
        if poses and poses[0].get('kp'):
            lean_frames = 0
            total_valid = 0
            arm_asymmetry_frames = 0

            for pose in poses:
                kp = pose['kp']
                if not kp:
                    continue

                def g(i):
                    p = kp[i] if i < len(kp) else None
                    return p if p and p['v'] > 0.4 else None

                ls = g(11); rs = g(12)  # shoulders
                lh = g(23); rh = g(24)  # hips
                lw = g(15); rw = g(16)  # wrists

                # Forward lean: compare shoulder-hip angle
                if ls and rs and lh and rh:
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

                # Arm asymmetry in spins
                if lw and rw and ls and rs:
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
                })

            if total_valid > 0 and arm_asymmetry_frames / total_valid > 0.25:
                errors.append({
                    'category': 'الذراعين', 'severity': 'منخفض',
                    'title_ar': 'عدم تناسق الذراعين',
                    'title_en': 'Arm Asymmetry',
                    'desc_ar': 'الذراعان غير متناسقتين في بعض الأوضاع — يؤثر على التقنية وDramatization',
                    'desc_en': 'Arms are asymmetric in some positions — affects technical marks',
                    'fix_ar': ['تمارين أمام المرآة لمحاذاة الذراعين', 'الوعي بالوضع: تصوير التدريب'],
                    'fix_en': ['Mirror exercises for arm alignment', 'Awareness: film practice sessions'],
                    'goe_impact': 0,
                    't_start': 0, 't_end': self.total_frames / self.fps,
                })

        return errors

    # ── Timeline ─────────────────────────────────────────────────────────────
    def _build_timeline(self, poses, jumps, spins) -> List[Dict]:
        timeline = []
        for j in jumps:
            timeline.append({
                'type': 'jump', 'label': j['type'],
                't': j.get('t_start', 0), 'duration': j.get('airtime', 0.3),
                'score': j['final_score'], 'goe': j['goe'],
                'color': '#22c55e' if j['goe'] >= 0 else '#ef4444',
            })
        for s in spins:
            timeline.append({
                'type': 'spin', 'label': s['type'],
                't': s.get('t_start', 0), 'duration': s.get('duration', 2),
                'score': s['final_score'], 'goe': s['goe'],
                'color': '#3b82f6',
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
             'frame_start': 108, 'frame_end': 123},
            {'type': 'Triple Lutz', 'code': '3Lz', 'rotations': 3.1, 'height_cm': 52,
             'airtime': 0.68, 'rpm': 273, 'goe': 1, 'base_value': 5.90,
             'final_score': 6.49, 'is_clean': True, 't_start': 7.0, 't_end': 7.7,
             'frame_start': 210, 'frame_end': 231},
            {'type': 'Triple Flip', 'code': '3F', 'rotations': 2.75, 'height_cm': 38,
             'airtime': 0.61, 'rpm': 270, 'goe': -1, 'base_value': 5.30,
             'final_score': 4.77, 'is_clean': False, 't_start': 12.2, 't_end': 12.8,
             'frame_start': 366, 'frame_end': 384},
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
        'total_score': 22.74, 'tes': 17.50, 'pcs': 8.00,
        'pose_count': 330,
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
        for col in ('program_type TEXT', 'skater_level TEXT'):
            try:
                conn.execute(f"ALTER TABLE analysis_results ADD COLUMN {col}")
            except Exception:
                pass
        import json
        conn.execute("""
            INSERT INTO analysis_results
            (player_name, session_note, analyzed_at, duration, total_score, tes, pcs,
             jumps_count, spins_count, errors_count, jump_details, spin_details,
             program_type, skater_level)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
            results.get('program_type', ''),
            results.get('skater_level', ''),
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

    # Header
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px">
      <h1 style="font-size:2.2em;background:linear-gradient(135deg,#1e3a5f,#2d6a9f,#4a9fd4);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
        🎥 تحليل الفيديو بالذكاء الاصطناعي
      </h1>
      <p style="color:#64748b;font-size:1.05em;margin-top:6px">
        كشف القفزات · الدورانات · الأخطاء الفنية · نقاط ISU — تلقائياً بالكامل
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Status bar
    mp_status = "✅ MediaPipe" if MP_OK else "⚠️ OpenCV فقط"
    cv_status = "✅ OpenCV" if CV2_OK else "❌ OpenCV غير متوفر"
    st.caption(f"محرك التحليل: {mp_status} | {cv_status}")
    st.markdown("---")

    tabs = st.tabs([
        "📹 رفع وتحليل",
        "🎯 تحليل عنصر واحد",
        "📊 النتائج",
        "🏅 القفزات والدورانات",
        "⚠️ الأخطاء والتصحيحات",
        "📈 الإحصائيات",
        "📄 التقارير",
        "📚 كتالوج عناصر ISU"
    ])

    with tabs[0]:
        _tab_upload(ar, lang)
    with tabs[1]:
        _tab_single_element(ar, lang)
    with tabs[2]:
        _tab_results(ar, lang)
    with tabs[3]:
        _tab_elements(ar, lang)
    with tabs[4]:
        _tab_errors(ar, lang)
    with tabs[5]:
        _tab_stats(ar, lang)
    with tabs[6]:
        _tab_reports(ar, lang)
    with tabs[7]:
        _tab_isu_catalog(ar, lang)


# ============================================================================
# TAB: UPLOAD & ANALYZE
# ============================================================================

def _tab_upload(ar: bool, lang: str):
    st.subheader("📹 رفع فيديو للتحليل الكامل")

    col_info, col_demo = st.columns([3, 1])

    with col_info:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#e0f2fe,#bfdbfe);border-radius:12px;padding:18px">
          <b>كيف يعمل النظام:</b><br>
          ① ارفع فيديو التزلج (MP4 · AVI · MOV · MKV)<br>
          ② يستخرج النظام تلقائياً وضعيات الجسم (33 نقطة) بـ MediaPipe<br>
          ③ يكتشف القفزات والدورانات والأخطاء التقنية<br>
          ④ يحسب نقاط ISU الرسمية (GOE + Base Value)<br>
          ⑤ يولّد تقريراً مفصلاً قابلاً للطباعة والتصدير
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
            program_type = st.selectbox(
                "🎯 نوع البرنامج", ['short', 'free'],
                format_func=lambda x: '🎯 برنامج قصير (Short)' if x == 'short' else '🎭 برنامج حر (Free Skate)'
            )
            skater_level = st.selectbox(
                "📊 مستوى اللاعب", ['auto', 'novice', 'junior', 'senior'],
                format_func=lambda x: {
                    'auto': '🔍 تلقائي (من ملف اللاعب)', 'novice': 'مبتدئ (Novice)',
                    'junior': 'جونيور (Junior)', 'senior': 'سينيور (Senior)'
                }[x]
            )
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

                resolved_level = skater_level
                if resolved_level == 'auto':
                    resolved_level = 'senior'
                    if player_name:
                        try:
                            conn = sqlite3.connect(DB_PATH)
                            row = conn.execute(
                                "SELECT level FROM skaters WHERE name = ?", (player_name,)
                            ).fetchone()
                            conn.close()
                            if row and row[0]:
                                resolved_level = _map_db_level_to_isu(row[0])
                        except Exception:
                            pass

                analyzer = SkatingVideoAnalyzer()
                results = analyzer.analyze(tmp_path, progress_cb=update_progress,
                                            program_type=program_type, skater_level=resolved_level)

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

    vi = results.get('video_info', {})
    player_name = results.get('player_name', '')

    # Top metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
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
    st.subheader(f"🦘 القفزات ({len(jumps)})")

    if jumps:
        for i, j in enumerate(jumps, 1):
            clean = j.get('is_clean', True)
            goe = j.get('goe', 0)
            goe_color = '#16a34a' if goe > 0 else ('#dc2626' if goe < 0 else '#64748b')
            border = '#22c55e' if clean else '#ef4444'

            with st.container():
                st.markdown(f"""
                <div style="border:2px solid {border};border-radius:12px;
                            padding:14px 18px;margin-bottom:12px;
                            background:{'#f0fdf4' if clean else '#fff1f2'}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-size:1.25em;font-weight:700">
                      {'✅' if clean else '⚠️'} {i}. {j.get('type','')}
                      <span style="font-size:0.75em;color:#94a3b8;margin-right:8px">({j.get('code','')})</span>
                    </span>
                    <span style="font-size:1.5em;font-weight:800;color:{goe_color}">
                      {j.get('final_score',0):.2f} pts
                    </span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("🔁 دورات", f"{j.get('rotations',0):.1f}")
                c2.metric("📏 ارتفاع", f"{j.get('height_cm',0)} cm")
                c3.metric("⏱️ طيران", f"{j.get('airtime',0):.2f}s")
                c4.metric("⚡ RPM", f"{j.get('rpm',0):.0f}")
                c5.metric("📌 Base", f"{j.get('base_value',0):.2f}")
                c6.markdown(f"<div style='text-align:center;padding-top:12px;"
                            f"color:{goe_color};font-weight:700;font-size:1.1em'>"
                            f"GOE: {goe:+d}</div>", unsafe_allow_html=True)

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
    st.subheader(f"🌀 الدورانات ({len(spins)})")

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
    else:
        st.info("لم يتم اكتشاف دورانات في هذا الفيديو")


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

    for err in filtered:
        sev = err.get('severity', 'LOW')
        color = SEV_COLOR.get(sev, '#64748b')
        icon = SEV_ICON.get(sev, '⚪')
        title = err.get('title_ar', err.get('title_en', ''))
        desc = err.get('desc_ar', err.get('desc_en', err.get('description_ar', '')))
        fixes = err.get('fix_ar', err.get('corrections_ar', []))
        goe_impact = err.get('goe_impact', 0)
        cat = err.get('category', '')

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


# ============================================================================
# TAB: SINGLE ELEMENT ANALYSIS
# ============================================================================

def _tab_single_element(ar: bool, lang: str):
    st.subheader("🎯 تحليل عنصر واحد (قفزة أو دوران فقط)")
    st.caption("ارفع لقطة قصيرة تحتوي على عنصر واحد فقط — قفزة أو دوران — "
               "للحصول على تحليل مفصّل له بدون حساب نقاط برنامج كامل.")

    uploaded = st.file_uploader(
        "اختر لقطة قصيرة (2-10 ثوانٍ)",
        type=['mp4', 'avi', 'mov', 'mkv'],
        key='single_element_upload',
    )
    expected = st.selectbox(
        "🔎 العنصر المتوقع",
        ['auto', 'jump', 'spin'],
        format_func=lambda x: {'auto': '🔍 تلقائي', 'jump': '🦘 قفزة', 'spin': '🌀 دوران'}[x]
    )

    if not uploaded:
        return

    st.video(uploaded)
    if not st.button("🚀 حلّل هذا العنصر", type="primary", use_container_width=True):
        return

    suffix = Path(uploaded.name).suffix or '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    try:
        with st.spinner("جارٍ تحليل العنصر..."):
            analyzer = SkatingVideoAnalyzer()
            results = analyzer.analyze(tmp_path)

        if 'error' in results:
            st.error(f"خطأ: {results['error']}")
            return

        jumps = results.get('jumps', [])
        spins = results.get('spins', [])

        element = None
        kind = None
        if expected == 'jump' and jumps:
            element, kind = jumps[0], 'jump'
        elif expected == 'spin' and spins:
            element, kind = spins[0], 'spin'
        elif jumps and spins:
            # Pick whichever scored higher (more confidently detected)
            if jumps[0].get('final_score', 0) >= spins[0].get('final_score', 0):
                element, kind = jumps[0], 'jump'
            else:
                element, kind = spins[0], 'spin'
        elif jumps:
            element, kind = jumps[0], 'jump'
        elif spins:
            element, kind = spins[0], 'spin'

        if not element:
            st.warning("⚠️ لم يتمكن النظام من اكتشاف عنصر واضح في هذه اللقطة. "
                       "جرّب لقطة أقصر/أوضح تحتوي على عنصر واحد فقط.")
            return

        catalog_entry = find_by_code(element.get('code', ''))

        st.success(f"✅ تم اكتشاف: **{element.get('type', '')}**"
                   f" ({'قفزة' if kind == 'jump' else 'دوران'})")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔢 الكود ISU", element.get('code', '—'))
        c2.metric("💰 القيمة الأساسية", f"{element.get('base_value', 0):.2f}")
        c3.metric("📊 GOE", f"{element.get('goe', 0):+d}")
        c4.metric("🏆 النقاط النهائية", f"{element.get('final_score', 0):.2f}")

        st.markdown("---")
        if kind == 'jump':
            d1, d2, d3 = st.columns(3)
            d1.metric("🌀 عدد اللفات", f"{element.get('rotations', 0):.1f}")
            d2.metric("📏 الارتفاع التقديري", f"{element.get('height_cm', 0)} cm")
            d3.metric("⏱️ وقت الطيران", f"{element.get('airtime', 0):.2f}s")
        else:
            d1, d2, d3 = st.columns(3)
            d1.metric("🌀 عدد اللفات", f"{element.get('rotations', 0):.1f}")
            d2.metric("⚡ السرعة", f"{element.get('rpm', 0):.0f} RPM")
            d3.metric("📈 المستوى", element.get('level', '—'))

        if catalog_entry:
            st.info(f"📚 مرجع كتالوج ISU: **{catalog_entry['name_ar']}** "
                   f"({catalog_entry['name_en']}) — القيمة الأساسية الرسمية: "
                   f"{catalog_entry['base_value']:.2f}")

        related_errors = [e for e in results.get('errors', [])
                           if e.get('t_start', 0) <= element.get('t_start', 0) + 0.5
                           and e.get('t_end', 1e9) >= element.get('t_start', 0) - 0.5]
        if related_errors:
            st.markdown("**⚠️ ملاحظات تقنية على هذا العنصر:**")
            for e in related_errors:
                st.warning(f"**{e.get('title_ar','')}** — {e.get('desc_ar','')}")
                for fx in e.get('fix_ar', []):
                    st.caption(f"✏️ {fx}")
        else:
            st.success("🎉 لا توجد ملاحظات تقنية سلبية على هذا العنصر.")

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


# ============================================================================
# TAB: ISU ELEMENT CATALOG
# ============================================================================

def _tab_isu_catalog(ar: bool, lang: str):
    st.subheader("📚 كتالوج عناصر الاتحاد الدولي للتزلج (ISU)")
    st.caption(f"إجمالي العناصر المسجّلة: {len(ISU_ELEMENTS_CATALOG)} — "
               "قفزات · دورانات · متتاليات خطوات · متتالية كوريوغرافيا")

    cats = ['الكل'] + sorted(set(r['category'] for r in ISU_ELEMENTS_CATALOG))
    col_f, col_s = st.columns([1, 2])
    with col_f:
        chosen_cat = st.selectbox("فلتر حسب الفئة:", cats)
    with col_s:
        search = st.text_input("🔍 بحث بالاسم أو الكود:", placeholder="مثال: Lutz, CCoSp, StSq")

    rows = ISU_ELEMENTS_CATALOG
    if chosen_cat != 'الكل':
        rows = [r for r in rows if r['category'] == chosen_cat]
    if search:
        s = search.strip().lower()
        rows = [r for r in rows if s in r['code'].lower()
                or s in r['name_ar'].lower() or s in r['name_en'].lower()]

    df = pd.DataFrame([{
        'الكود': r['code'],
        'الاسم (عربي)': r['name_ar'],
        'الاسم (English)': r['name_en'],
        'الفئة': r['category'],
        'المستوى': r['level'],
        'القيمة الأساسية': r['base_value'],
    } for r in rows]).sort_values(['الفئة', 'القيمة الأساسية'])

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"عدد العناصر المعروضة: {len(rows)}")
