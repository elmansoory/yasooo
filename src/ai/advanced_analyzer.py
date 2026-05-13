"""
Advanced AI Analysis Engine — Figure Skating
محرك التحليل المتقدم للتزلج الفني
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import cv2


# ── MediaPipe landmark indices ──────────────────────────────────────────────
LM = {
    'nose': 0,
    'left_shoulder': 11, 'right_shoulder': 12,
    'left_elbow': 13,    'right_elbow': 14,
    'left_wrist': 15,    'right_wrist': 16,
    'left_hip': 23,      'right_hip': 24,
    'left_knee': 25,     'right_knee': 26,
    'left_ankle': 27,    'right_ankle': 28,
    'left_heel': 29,     'right_heel': 30,
    'left_foot': 31,     'right_foot': 32,
}

MIN_VISIBILITY = 0.4   # discard landmarks below this confidence


class JumpType(Enum):
    AXEL     = "Axel"
    LUTZ     = "Lutz"
    FLIP     = "Flip"
    LOOP     = "Loop"
    SALCHOW  = "Salchow"
    TOE_LOOP = "Toe Loop"
    UNKNOWN  = "Unknown"


class SpinType(Enum):
    UPRIGHT     = "Upright Spin"
    SIT         = "Sit Spin"
    CAMEL       = "Camel Spin"
    LAYBACK     = "Layback Spin"
    COMBINATION = "Combination Spin"
    UNKNOWN     = "Unknown"


@dataclass
class JumpAnalysis:
    jump_type: JumpType
    rotations: float
    height_cm: float
    distance_cm: float
    airtime_seconds: float
    rotation_speed_rpm: float
    takeoff_angle: float
    landing_angle: float
    has_clear_edge: bool
    has_full_rotations: bool
    has_good_height: bool
    has_good_flow: bool
    has_clean_landing: bool
    base_value: float
    goe: int
    final_score: float
    start_frame: int
    end_frame: int
    peak_frame: int
    confidence: float


@dataclass
class SpinAnalysis:
    spin_type: SpinType
    rotations: int
    rpm: float
    duration_seconds: float
    has_centered_axis: bool
    has_good_speed: bool
    has_good_positions: bool
    has_clear_entry: bool
    has_clear_exit: bool
    base_value: float
    level: int
    goe: int
    final_score: float
    start_frame: int
    end_frame: int
    confidence: float


class AdvancedSkatingAnalyzer:

    # ISU base values (jump_type, rotations) → points
    JUMP_BASE_VALUES = {
        (JumpType.AXEL, 1): 1.10, (JumpType.AXEL, 2): 3.30,
        (JumpType.AXEL, 3): 8.00, (JumpType.AXEL, 4): 12.50,
        (JumpType.LUTZ, 1): 0.60, (JumpType.LUTZ, 2): 2.10,
        (JumpType.LUTZ, 3): 5.90, (JumpType.LUTZ, 4): 11.50,
        (JumpType.FLIP, 1): 0.50, (JumpType.FLIP, 2): 1.80,
        (JumpType.FLIP, 3): 5.30, (JumpType.FLIP, 4): 11.00,
        (JumpType.LOOP, 1): 0.50, (JumpType.LOOP, 2): 1.70,
        (JumpType.LOOP, 3): 4.90, (JumpType.LOOP, 4): 10.50,
        (JumpType.SALCHOW, 1): 0.40, (JumpType.SALCHOW, 2): 1.30,
        (JumpType.SALCHOW, 3): 4.30, (JumpType.SALCHOW, 4): 9.70,
        (JumpType.TOE_LOOP, 1): 0.40, (JumpType.TOE_LOOP, 2): 1.30,
        (JumpType.TOE_LOOP, 3): 4.20, (JumpType.TOE_LOOP, 4): 9.50,
    }

    SPIN_BASE_VALUES = {
        (SpinType.UPRIGHT, 1): 1.50, (SpinType.UPRIGHT, 2): 2.10,
        (SpinType.UPRIGHT, 3): 3.00, (SpinType.UPRIGHT, 4): 3.50,
        (SpinType.SIT, 1): 1.70, (SpinType.SIT, 2): 2.50,
        (SpinType.SIT, 3): 3.30, (SpinType.SIT, 4): 3.90,
        (SpinType.CAMEL, 1): 1.70, (SpinType.CAMEL, 2): 2.50,
        (SpinType.CAMEL, 3): 3.30, (SpinType.CAMEL, 4): 3.90,
    }

    def __init__(self):
        self.fps: float = 30.0
        self.width: int = 1920
        self.height: int = 1080

    # ── Public API ──────────────────────────────────────────────────────────

    def analyze_video(self, video_path: str) -> Dict:
        results = {
            'video_info': self._get_video_info(video_path),
            'poses': [], 'jumps': [], 'spins': [],
            'total_score': 0.0, 'analysis_summary': {}
        }
        try:
            poses = self._extract_poses(video_path)
            results['poses'] = poses

            jumps = self._detect_jumps(poses)
            results['jumps'] = jumps

            spins = self._detect_spins(poses)
            results['spins'] = spins

            results['total_score'] = (
                sum(j.final_score for j in jumps) +
                sum(s.final_score for s in spins)
            )
            results['analysis_summary'] = self._generate_summary(jumps, spins)
        except Exception as e:
            results['error'] = str(e)
        return results

    # ── Video / pose extraction ─────────────────────────────────────────────

    def _get_video_info(self, video_path: str) -> Dict:
        try:
            cap = cv2.VideoCapture(video_path)
            fps   = cap.get(cv2.CAP_PROP_FPS) or 30.0
            fc    = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            self.fps, self.width, self.height = fps, w, h
            return {'fps': fps, 'frame_count': fc, 'width': w, 'height': h,
                    'duration': fc / fps if fps > 0 else 0.0}
        except Exception as e:
            return {'error': str(e)}

    def _extract_poses(self, video_path: str) -> List[Dict]:
        try:
            import mediapipe as mp
            return self._extract_poses_mediapipe(video_path, mp)
        except ImportError:
            return []

    def _extract_poses_mediapipe(self, video_path: str, mp) -> List[Dict]:
        poses = []
        mp_pose = mp.solutions.pose

        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose_model:

            cap = cv2.VideoCapture(video_path)
            frame_idx = 0

            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose_model.process(rgb)

                if res.pose_landmarks:
                    kps = [
                        {
                            'x': lm.x, 'y': lm.y, 'z': lm.z,
                            'visibility': lm.visibility, 'index': i
                        }
                        for i, lm in enumerate(res.pose_landmarks.landmark)
                    ]
                    poses.append({
                        'frame': frame_idx,
                        'timestamp': frame_idx / self.fps,
                        'keypoints': kps,
                        'is_airborne': self._is_airborne(kps),
                        'is_spinning': False,  # filled later
                    })

                frame_idx += 1

            cap.release()

        return poses

    # ── Airborne detection ─────────────────────────────────────────────────
    # Strategy: compare ankle height to hip height.
    # On ice, ankles are near the bottom of the image (high Y value in MediaPipe,
    # where Y=0 is top, Y=1 is bottom).
    # When airborne, ankles rise — gap between hip_y and ankle_y shrinks.

    def _is_airborne(self, kps: List[Dict]) -> bool:
        def get(name):
            idx = LM[name]
            p = kps[idx]
            return p if p['visibility'] >= MIN_VISIBILITY else None

        la = get('left_ankle');  ra = get('right_ankle')
        lh = get('left_hip');    rh = get('right_hip')
        lk = get('left_knee');   rk = get('right_knee')

        if la is None and ra is None:
            return False

        # Average visible ankle Y
        ankle_ys = [p['y'] for p in [la, ra] if p is not None]
        ankle_y = np.mean(ankle_ys)

        # Average visible hip Y
        hip_ys = [p['y'] for p in [lh, rh] if p is not None]
        if not hip_ys:
            return False
        hip_y = np.mean(hip_ys)

        # Ankle-to-hip vertical gap in normalised coords
        # On ice: ankle_y >> hip_y  (ankles are much lower than hips)
        # In air: ankle_y ≈ hip_y   (gap collapses)
        gap = ankle_y - hip_y  # positive when ankles are below hips

        # Knee check — knees tuck up during jump
        knee_ys = [p['y'] for p in [lk, rk] if p is not None]
        knee_above_hip = False
        if knee_ys and hip_ys:
            knee_y = np.mean(knee_ys)
            knee_above_hip = knee_y < hip_y + 0.05  # knees near or above hips

        # Primary: gap < 0.20 means ankles are close to hip level → airborne
        # Secondary: knee confirmation adds robustness
        return gap < 0.20 or (gap < 0.28 and knee_above_hip)

    # ── Jump detection ─────────────────────────────────────────────────────

    def _detect_jumps(self, poses: List[Dict]) -> List[JumpAnalysis]:
        if not poses:
            return []

        # Smooth the airborne signal over a small window to remove noise
        airborne = np.array([1 if p['is_airborne'] else 0 for p in poses])
        smoothed = self._smooth(airborne, window=3)

        sequences: List[List[Dict]] = []
        in_seq = False
        seq: List[Dict] = []

        for i, p in enumerate(poses):
            if smoothed[i] > 0.5:
                seq.append(p)
                in_seq = True
            else:
                if in_seq and len(seq) >= 4:   # ≥4 frames at 30fps ≈ 130ms min
                    sequences.append(seq)
                seq = []
                in_seq = False

        if in_seq and len(seq) >= 4:
            sequences.append(seq)

        jumps = []
        for seq in sequences:
            j = self._analyze_jump_sequence(seq, poses)
            if j:
                jumps.append(j)
        return jumps

    def _analyze_jump_sequence(
        self, seq: List[Dict], all_poses: List[Dict]
    ) -> Optional[JumpAnalysis]:

        n = len(seq)
        airtime = n / self.fps
        if airtime < 0.13:   # too short to be a real jump (<4 frames @30fps)
            return None

        start_frame = seq[0]['frame']
        end_frame   = seq[-1]['frame']
        peak_frame  = seq[n // 2]['frame']

        # ── Height estimation ──────────────────────────────────────────────
        # The hip keypoint rises during a jump.
        # We compare peak hip Y (minimum Y = highest position) to takeoff hip Y.
        hip_ys = self._series(seq, 'left_hip', 'right_hip', 'y')
        if not hip_ys:
            return None

        baseline_hip_y = np.mean(hip_ys[:2]) if len(hip_ys) >= 2 else hip_ys[0]
        peak_hip_y     = np.min(hip_ys)
        rise_fraction  = baseline_hip_y - peak_hip_y   # positive = up

        # Convert to cm: 1 unit ≈ athlete height (~170 cm on average)
        # A triple jump rises about 50-70 cm, double ≈ 35-50 cm
        height_cm = max(5.0, min(80.0, rise_fraction * 170.0))

        # ── Rotation estimation ────────────────────────────────────────────
        # Track shoulder-line angle over the airborne sequence.
        # A full CCW rotation = +360° cumulative change.
        rotations = self._estimate_rotations_from_pose(seq)

        if rotations < 0.5:   # less than half a rotation → not a real jump
            return None

        # ── Jump type classification ───────────────────────────────────────
        # Look at the takeoff pose (1-2 frames before airborne start)
        takeoff_poses = self._get_context_before(all_poses, start_frame, n=3)
        jump_type, takeoff_angle, confidence = self._classify_jump_type(
            seq, takeoff_poses, rotations
        )

        # ── Landing quality ────────────────────────────────────────────────
        landing_poses = self._get_context_after(all_poses, end_frame, n=3)
        has_clean_landing, landing_angle = self._assess_landing(landing_poses)

        # ── GOE factors ───────────────────────────────────────────────────
        rot_count   = round(rotations)
        rot_ok      = rotations >= (rot_count - 0.25)
        height_ok   = height_cm > 30.0
        rpm         = (rotations * 60) / airtime if airtime > 0 else 0
        flow_ok     = has_clean_landing
        edge_ok     = jump_type not in (JumpType.UNKNOWN,)

        goe = self._calculate_goe(edge_ok, rot_ok, height_ok, flow_ok, has_clean_landing)

        base_value  = self.JUMP_BASE_VALUES.get((jump_type, max(1, rot_count)), 0.0)
        final_score = base_value + goe

        # Approximate distance: horizontal ankle displacement
        ankle_xs  = self._series(seq, 'left_ankle', 'right_ankle', 'x')
        dist_cm   = abs(ankle_xs[-1] - ankle_xs[0]) * 300 if len(ankle_xs) >= 2 else 80.0

        return JumpAnalysis(
            jump_type=jump_type,
            rotations=rotations,
            height_cm=round(height_cm, 1),
            distance_cm=round(dist_cm, 1),
            airtime_seconds=round(airtime, 3),
            rotation_speed_rpm=round(rpm, 1),
            takeoff_angle=round(takeoff_angle, 1),
            landing_angle=round(landing_angle, 1),
            has_clear_edge=edge_ok,
            has_full_rotations=rot_ok,
            has_good_height=height_ok,
            has_good_flow=flow_ok,
            has_clean_landing=has_clean_landing,
            base_value=base_value,
            goe=goe,
            final_score=round(final_score, 2),
            start_frame=start_frame,
            end_frame=end_frame,
            peak_frame=peak_frame,
            confidence=round(confidence, 2),
        )

    # ── Rotation tracking ─────────────────────────────────────────────────

    def _estimate_rotations_from_pose(self, seq: List[Dict]) -> float:
        """
        Count body rotations using the shoulder-line angle.
        Accumulate signed angular deltas to handle multi-turn wrapping.
        """
        angles = []
        for pose in seq:
            kps = pose['keypoints']
            ls = kps[LM['left_shoulder']]
            rs = kps[LM['right_shoulder']]
            if ls['visibility'] < MIN_VISIBILITY or rs['visibility'] < MIN_VISIBILITY:
                angles.append(None)
                continue
            dx = rs['x'] - ls['x']
            dy = rs['y'] - ls['y']
            angles.append(np.degrees(np.arctan2(dy, dx)))

        # Fill None gaps with neighbours
        valid = [a for a in angles if a is not None]
        if len(valid) < 2:
            # Fallback: airtime-based rough estimate
            return self._airtime_to_rotations(len(seq) / self.fps)

        angles = self._fill_none(angles, valid[0])

        # Accumulate unwrapped delta
        total_delta = 0.0
        for i in range(1, len(angles)):
            d = angles[i] - angles[i - 1]
            # Unwrap: bring delta into [-180, 180]
            if d > 180:  d -= 360
            if d < -180: d += 360
            total_delta += d

        rotations = abs(total_delta) / 360.0

        # Sanity-clamp: physics limits ~5 rotations per jump
        return min(5.0, max(0.0, rotations))

    @staticmethod
    def _airtime_to_rotations(duration: float) -> float:
        """Rough fallback: average skater rotation rate ≈ 3–5 rev/s in the air."""
        if duration < 0.20: return 1.0
        if duration < 0.37: return 2.0
        if duration < 0.55: return 3.0
        if duration < 0.70: return 4.0
        return 5.0

    # ── Jump type classification ──────────────────────────────────────────

    def _classify_jump_type(
        self,
        seq: List[Dict],
        takeoff_poses: List[Dict],
        rotations: float,
    ) -> Tuple[JumpType, float, float]:
        """
        Biomechanical classification using takeoff foot and body orientation.

        Rules (simplified ISU definitions):
          Axel    — forward takeoff (skater moving forward at launch)
          Loop    — back-outside edge, no toe assist, right foot
          Salchow — back-inside edge, left foot
          Toe Loop— back-outside edge with toe pick, right foot
          Flip    — back-inside edge with toe pick, left foot
          Lutz    — back-outside edge with toe pick, left foot (opposite corner)
        """
        if not takeoff_poses:
            return JumpType.UNKNOWN, 0.0, 0.5

        tp = takeoff_poses[-1]   # last grounded frame before jump
        kps = tp['keypoints']

        la = kps[LM['left_ankle']];  ra = kps[LM['right_ankle']]
        lh = kps[LM['left_hip']];    rh = kps[LM['right_hip']]
        ls = kps[LM['left_shoulder']]; rs = kps[LM['right_shoulder']]

        ok = lambda p: p['visibility'] >= MIN_VISIBILITY

        # Which foot is lower (on ice) → takeoff foot
        if ok(la) and ok(ra):
            left_foot_lower  = la['y'] > ra['y']   # higher Y = lower on screen
            right_foot_lower = ra['y'] > la['y']
        else:
            left_foot_lower = right_foot_lower = False

        # Body facing direction: compare shoulder-line vs hip-line angles
        facing_forward = False
        if ok(ls) and ok(rs) and ok(lh) and ok(rh):
            sh_angle  = np.degrees(np.arctan2(rs['y'] - ls['y'], rs['x'] - ls['x']))
            hip_angle = np.degrees(np.arctan2(rh['y'] - lh['y'], rh['x'] - lh['x']))
            twist     = abs(sh_angle - hip_angle)
            facing_forward = twist > 30   # significant twist = forward takeoff (Axel)

        takeoff_angle = np.degrees(
            np.arctan2(
                (kps[LM['right_ankle']]['y'] - kps[LM['right_hip']]['y']),
                (kps[LM['right_ankle']]['x'] - kps[LM['right_hip']]['x'])
            )
        ) if ok(ra) and ok(rh) else 45.0

        confidence = 0.6

        if facing_forward:
            return JumpType.AXEL, takeoff_angle, 0.75

        # Without ML we distinguish toe-assisted vs edge jumps by wrist position
        lw = kps[LM['left_wrist']]; rw = kps[LM['right_wrist']]
        toe_assist = False
        if ok(lw) and ok(la):
            toe_assist = abs(lw['y'] - la['y']) < 0.12   # wrist near ankle = toe pick

        if left_foot_lower:
            return (JumpType.FLIP if toe_assist else JumpType.SALCHOW), takeoff_angle, 0.65
        elif right_foot_lower:
            return (JumpType.TOE_LOOP if toe_assist else JumpType.LOOP), takeoff_angle, 0.65

        return JumpType.LUTZ, takeoff_angle, 0.50   # default to Lutz when uncertain

    # ── Landing quality ───────────────────────────────────────────────────

    def _assess_landing(
        self, landing_poses: List[Dict]
    ) -> Tuple[bool, float]:
        if not landing_poses:
            return True, 45.0

        p  = landing_poses[0]
        kps = p['keypoints']
        ra = kps[LM['right_ankle']]; rk = kps[LM['right_knee']]; rh = kps[LM['right_hip']]

        def ok(pt): return pt['visibility'] >= MIN_VISIBILITY

        if ok(ra) and ok(rk) and ok(rh):
            # Knee should be slightly bent on landing (angle 140-170°)
            ang = self._angle3(
                (ra['x'], ra['y']), (rk['x'], rk['y']), (rh['x'], rh['y'])
            )
            clean = 120 < ang < 175
            return clean, round(ang, 1)

        return True, 45.0

    # ── Spin detection ────────────────────────────────────────────────────

    def _detect_spins(self, poses: List[Dict]) -> List[SpinAnalysis]:
        """
        Detect spinning segments: rapid continuous shoulder rotation
        while NOT airborne (on ice).
        """
        if len(poses) < 10:
            return []

        # Compute shoulder-line angle per frame
        angles: List[Optional[float]] = []
        for p in poses:
            kps = p['keypoints']
            ls = kps[LM['left_shoulder']]; rs = kps[LM['right_shoulder']]
            if ls['visibility'] >= MIN_VISIBILITY and rs['visibility'] >= MIN_VISIBILITY:
                dx = rs['x'] - ls['x']; dy = rs['y'] - ls['y']
                angles.append(np.degrees(np.arctan2(dy, dx)))
            else:
                angles.append(None)

        # Compute angular velocity (degrees/frame), skip None
        ang_vel: List[float] = []
        for i in range(1, len(angles)):
            if angles[i] is None or angles[i - 1] is None:
                ang_vel.append(0.0)
                continue
            d = angles[i] - angles[i - 1]
            if d > 180:  d -= 360
            if d < -180: d += 360
            ang_vel.append(abs(d))

        ang_vel = np.array(ang_vel)

        # Threshold: spinning = > 8°/frame ≈ > 240°/s at 30fps
        SPIN_THRESH = 8.0
        MIN_SPIN_FRAMES = 15   # ≈ 0.5 s

        spinning = ang_vel > SPIN_THRESH

        spins: List[SpinAnalysis] = []
        i = 0
        while i < len(spinning):
            if spinning[i] and not poses[i]['is_airborne']:
                j = i
                while j < len(spinning) and (spinning[j] or (j - i < 5)):
                    j += 1
                seg_len = j - i
                if seg_len >= MIN_SPIN_FRAMES:
                    seg_poses  = poses[i:j]
                    seg_angles = ang_vel[i:j]
                    sp = self._analyze_spin_sequence(seg_poses, seg_angles, poses)
                    if sp:
                        spins.append(sp)
                i = j
            else:
                i += 1

        return spins

    def _analyze_spin_sequence(
        self,
        seq: List[Dict],
        ang_vel: np.ndarray,
        all_poses: List[Dict],
    ) -> Optional[SpinAnalysis]:

        duration = len(seq) / self.fps
        total_rotation = float(np.sum(ang_vel)) / 360.0
        rot_count = max(1, int(round(total_rotation)))
        rpm = (total_rotation * 60) / duration if duration > 0 else 0

        spin_type, level, confidence = self._classify_spin_type(seq)

        centered = self._is_spin_centered(seq)
        good_speed = rpm > 60   # professional spins are 80-120 rpm+

        base_value = self.SPIN_BASE_VALUES.get((spin_type, min(level, 4)), 1.50)
        goe = self._calculate_goe(
            centered, good_speed, len(seq) >= 30,
            True, True
        )
        final_score = base_value + goe

        return SpinAnalysis(
            spin_type=spin_type,
            rotations=rot_count,
            rpm=round(rpm, 1),
            duration_seconds=round(duration, 2),
            has_centered_axis=centered,
            has_good_speed=good_speed,
            has_good_positions=True,
            has_clear_entry=True,
            has_clear_exit=True,
            base_value=base_value,
            level=level,
            goe=goe,
            final_score=round(final_score, 2),
            start_frame=seq[0]['frame'],
            end_frame=seq[-1]['frame'],
            confidence=round(confidence, 2),
        )

    def _classify_spin_type(
        self, seq: List[Dict]
    ) -> Tuple[SpinType, int, float]:
        """
        Classify spin based on body shape:
        - Sit spin: knee angle < 120° (deep crouch)
        - Camel spin: body nearly horizontal (hip-shoulder line near flat)
        - Upright spin: tall, knee relatively straight
        """
        knee_angles = []
        hip_heights = []
        shoulder_heights = []

        for p in seq:
            kps = p['keypoints']
            ra = kps[LM['right_ankle']]; rk = kps[LM['right_knee']]; rh = kps[LM['right_hip']]
            ls = kps[LM['left_shoulder']]; rs = kps[LM['right_shoulder']]

            if all(pt['visibility'] >= MIN_VISIBILITY for pt in [ra, rk, rh]):
                ang = self._angle3(
                    (ra['x'], ra['y']), (rk['x'], rk['y']), (rh['x'], rh['y'])
                )
                knee_angles.append(ang)

            if rh['visibility'] >= MIN_VISIBILITY:
                hip_heights.append(rh['y'])

            if ls['visibility'] >= MIN_VISIBILITY and rs['visibility'] >= MIN_VISIBILITY:
                shoulder_heights.append((ls['y'] + rs['y']) / 2)

        if not knee_angles:
            return SpinType.UPRIGHT, 1, 0.4

        avg_knee = np.mean(knee_angles)

        if avg_knee < 115:
            return SpinType.SIT, 2, 0.70

        if hip_heights and shoulder_heights:
            avg_hip = np.mean(hip_heights)
            avg_sh  = np.mean(shoulder_heights)
            lean    = abs(avg_hip - avg_sh)
            if lean < 0.10:   # shoulders near hip level → camel
                return SpinType.CAMEL, 2, 0.65

        return SpinType.UPRIGHT, 1, 0.60

    def _is_spin_centered(self, seq: List[Dict]) -> bool:
        """Check if the spin axis stays roughly in one place (centered spin)."""
        hip_xs = self._series(seq, 'left_hip', 'right_hip', 'x')
        if len(hip_xs) < 4:
            return True
        drift = np.std(hip_xs)
        return drift < 0.04   # < 4% of frame width drift

    # ── GOE ───────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_goe(*factors: bool) -> int:
        score = sum(1 for f in factors if f) - len(factors) // 2
        return int(min(5, max(-5, score)))

    # ── Summary ───────────────────────────────────────────────────────────

    def _generate_summary(
        self, jumps: List[JumpAnalysis], spins: List[SpinAnalysis]
    ) -> Dict:
        summary: Dict = {
            'total_jumps': len(jumps),
            'total_spins': len(spins),
            'jump_breakdown': {},
            'average_goe': 0.0,
            'technical_score': 0.0,
            'strengths': [],
            'areas_for_improvement': [],
        }

        if jumps:
            for j in jumps:
                key = f"{j.jump_type.value} {int(round(j.rotations))}"
                summary['jump_breakdown'][key] = summary['jump_breakdown'].get(key, 0) + 1

            summary['average_goe'] = round(np.mean([j.goe for j in jumps]), 2)
            summary['technical_score'] = round(sum(j.final_score for j in jumps), 2)

            if summary['average_goe'] > 2:
                summary['strengths'].append("High quality jumps")
            if any(j.rotations >= 3 for j in jumps):
                summary['strengths'].append("Triple jumps mastered")
            if not all(j.has_full_rotations for j in jumps):
                summary['areas_for_improvement'].append("Full rotation completion")
            if any(j.height_cm < 35 for j in jumps):
                summary['areas_for_improvement'].append("Jump height needs improvement")
            if any(not j.has_clean_landing for j in jumps):
                summary['areas_for_improvement'].append("Landing stability")

        if spins:
            summary['technical_score'] = round(
                summary['technical_score'] + sum(s.final_score for s in spins), 2
            )
            if any(s.rpm > 100 for s in spins):
                summary['strengths'].append("Fast spin speed")

        return summary

    # ── Utility helpers ───────────────────────────────────────────────────

    def _series(
        self, poses: List[Dict], name_a: str, name_b: str, coord: str
    ) -> List[float]:
        """Extract averaged coordinate series for two landmarks across frames."""
        out = []
        for p in poses:
            kps = p['keypoints']
            vals = []
            for nm in (name_a, name_b):
                idx = LM.get(nm)
                if idx is not None:
                    pt = kps[idx]
                    if pt['visibility'] >= MIN_VISIBILITY:
                        vals.append(pt[coord])
            if vals:
                out.append(float(np.mean(vals)))
        return out

    def _get_context_before(
        self, all_poses: List[Dict], start_frame: int, n: int
    ) -> List[Dict]:
        return [p for p in all_poses
                if start_frame - n <= p['frame'] < start_frame
                and not p['is_airborne']]

    def _get_context_after(
        self, all_poses: List[Dict], end_frame: int, n: int
    ) -> List[Dict]:
        return [p for p in all_poses
                if end_frame < p['frame'] <= end_frame + n
                and not p['is_airborne']]

    @staticmethod
    def _angle3(
        a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]
    ) -> float:
        """Angle at point b formed by a-b-c, in degrees."""
        ba = np.array([a[0] - b[0], a[1] - b[1]])
        bc = np.array([c[0] - b[0], c[1] - b[1]])
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

    @staticmethod
    def _smooth(signal: np.ndarray, window: int = 3) -> np.ndarray:
        kernel = np.ones(window) / window
        return np.convolve(signal.astype(float), kernel, mode='same')

    @staticmethod
    def _fill_none(lst: List[Optional[float]], default: float) -> List[float]:
        result = []
        for v in lst:
            result.append(v if v is not None else default)
        return result
