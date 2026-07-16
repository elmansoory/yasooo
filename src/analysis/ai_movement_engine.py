"""
محرك التحليل الذكي للحركات - AI Movement Analysis Engine
يربط: MovementClassifier + LSTMClassifier + PoseComparator
"""
from __future__ import annotations

import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

LSTM_MODEL_PATH = 'data/models/lstm_model.pkl'

# ── Safe imports ──────────────────────────────────────────────────────────────

def _load_movement_classifier():
    try:
        from src.models.movement_classifier import MovementClassifier, MovementFeatures
        return MovementClassifier(), MovementFeatures
    except Exception:
        return None, None


def _load_lstm():
    try:
        from src.models.lstm_classifier import LSTMClassifier
        if Path(LSTM_MODEL_PATH).exists():
            return LSTMClassifier.load(LSTM_MODEL_PATH)
    except Exception:
        pass
    return None


def _load_comparator():
    try:
        from src.analysis.pose_comparator import PoseComparator
        return PoseComparator()
    except Exception:
        return None


# ── ISU step sequence base values ─────────────────────────────────────────────
_STEP_BASE = {1: 1.50, 2: 2.60, 3: 3.30, 4: 3.90}


class AIMovementEngine:
    """
    يُحسِّن نتائج تحليل الفيديو بثلاثة نماذج ذكاء اصطناعي:
    1. MovementClassifier — تصنيف دقيق لنوع القفزة/الدوران واتجاه الإقلاع
    2. LSTMClassifier    — تصنيف تسلسلي بعمق 60 إطار (32 فئة)
    3. PoseComparator    — مقارنة الوضعية بالمراجع ومقترحات تصحيح فورية
    """

    def __init__(self):
        self._mc, self._MF = _load_movement_classifier()
        self._lstm = _load_lstm()
        self._cmp = _load_comparator()

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> Dict:
        return {
            'movement_classifier': self._mc is not None,
            'lstm': self._lstm is not None,
            'pose_comparator': self._cmp is not None,
        }

    # ── Public: enhance detected elements ─────────────────────────────────────

    def enhance_jump(self, jump: Dict, poses: List[Dict]) -> Dict:
        """Add AI fields to a detected jump dict."""
        t0, t1 = jump.get('t_start', 0), jump.get('t_end', 0)
        seg = [p for p in poses if t0 <= p['t'] <= t1 and p.get('kp')]
        if not seg:
            return jump

        out = jump.copy()

        # 1. MovementClassifier
        if self._mc and self._MF:
            try:
                feats = self._build_jump_features(jump, seg)
                mc = self._mc.jump_detector.detect_jump_type(feats)
                out['ai_code']       = mc.get('code', jump.get('code', '?'))
                out['ai_name']       = mc.get('name', jump.get('type', '?'))
                out['ai_confidence'] = round(mc.get('confidence', 0), 2)
                out['ai_takeoff']    = mc.get('features', {}).get('takeoff', '?')
                out['ai_edge']       = mc.get('features', {}).get('edge', '?')
                out['ai_toe_pick']   = mc.get('features', {}).get('toe_pick', False)
                out['ai_landing']    = mc.get('features', {}).get('landing_quality', '?')
                out['ai_goe']        = mc.get('estimated_goe', jump.get('goe', 0))
            except Exception as e:
                out['ai_mc_error'] = str(e)

        # 2. LSTM
        if self._lstm:
            try:
                seq = _kp_to_seq(seg)
                if seq is not None:
                    label, conf = self._lstm.predict(seq)
                    out['lstm_label']      = label
                    out['lstm_confidence'] = round(conf, 2)
                    top3 = self._lstm.predict_top3(seq)
                    out['lstm_top3'] = [(l, round(c, 2)) for l, c in top3]
            except Exception:
                pass

        # 3. PoseComparator
        if self._cmp:
            try:
                peak = _peak_frame(seg)
                if peak:
                    # Choose phase from relative position in jump
                    t_range = max(t1 - t0, 0.01)
                    t_rel   = (peak['t'] - t0) / t_range
                    phase   = ('axel_takeoff' if t_rel < 0.25
                               else 'axel_flight' if t_rel < 0.75
                               else 'axel_landing')
                    cmp_r = self._cmp.compare_pose(peak['kp'], phase)
                    out['pose_score']          = cmp_r.get('overall_score', 0)
                    out['pose_rating']         = cmp_r.get('visual_rating', '')
                    out['pose_corrections_ar'] = cmp_r.get('corrections_ar', [])
                    out['pose_corrections_en'] = cmp_r.get('corrections_en', [])
                    out['pose_deviations']     = cmp_r.get('angle_deviations', [])
                    out['pose_phase']          = phase
            except Exception:
                pass

        return out

    def enhance_spin(self, spin: Dict, poses: List[Dict]) -> Dict:
        """Add AI fields to a detected spin dict."""
        t0, t1 = spin.get('t_start', 0), spin.get('t_end', 0)
        seg = [p for p in poses if t0 <= p['t'] <= t1 and p.get('kp')]
        if not seg:
            return spin

        out = spin.copy()

        # Spin position from joint angles
        position = _detect_spin_position(seg)
        out['ai_position'] = position

        # Axis stability
        xs = [_hip_x(p) for p in seg if _hip_x(p) is not None]
        out['axis_stability'] = round(max(0.0, 1.0 - np.std(xs) * 20), 2) if xs else 0.5

        # MovementClassifier
        if self._mc and self._MF:
            try:
                feats = self._build_spin_features(spin, seg, position)
                mc = self._mc.spin_detector.detect_spin_type(feats)
                out['ai_code']  = mc.get('code', spin.get('code', '?'))
                out['ai_name']  = mc.get('name', spin.get('type', '?'))
                out['ai_level'] = mc.get('level', spin.get('level', 1))
                out['ai_goe']   = mc.get('estimated_goe', spin.get('goe', 0))
            except Exception:
                pass

        # PoseComparator
        if self._cmp and position in ('camel', 'sit'):
            try:
                mid = seg[len(seg) // 2]
                elem = f'{position}_spin'
                cmp_r = self._cmp.compare_pose(mid['kp'], elem)
                out['pose_score']          = cmp_r.get('overall_score', 0)
                out['pose_rating']         = cmp_r.get('visual_rating', '')
                out['pose_corrections_ar'] = cmp_r.get('corrections_ar', [])
            except Exception:
                pass

        return out

    def detect_step_sequences(
        self,
        poses: List[Dict],
        jumps: List[Dict],
        spins: List[Dict],
    ) -> List[Dict]:
        """Detect step-sequence segments (active, non-jump, non-spin skating)."""
        if len(poses) < 20:
            return []

        # Build exclusion windows
        excl = (
            [(j.get('t_start', 0) - 0.5, j.get('t_end', 0) + 0.5) for j in jumps]
            + [(s.get('t_start', 0) - 0.3, s.get('t_end', 0) + 0.3) for s in spins]
        )

        def is_free(t: float) -> bool:
            return not any(a <= t <= b for a, b in excl)

        times  = np.array([p['t'] for p in poses])
        active = np.array([
            1 if is_free(p['t']) and not p.get('airborne') and _has_kp(p)
            else 0
            for p in poses
        ])

        results: List[Dict] = []
        in_seq = False
        seg_start = 0

        for i, a in enumerate(active):
            if a and not in_seq:
                in_seq = True
                seg_start = i
            elif not a and in_seq:
                duration = times[i - 1] - times[seg_start]
                if duration >= 3.0:
                    seg_poses = poses[seg_start:i]
                    complexity = _footwork_complexity(seg_poses)
                    lvl  = (4 if complexity > 0.9 else
                            3 if complexity > 0.7 else
                            2 if complexity > 0.5 else 1)
                    bv   = _STEP_BASE[lvl]
                    results.append({
                        'type':       'Step Sequence',
                        'code':       f'StSq{lvl}',
                        'level':      lvl,
                        'duration':   round(duration, 1),
                        't_start':    round(float(times[seg_start]), 2),
                        't_end':      round(float(times[i - 1]), 2),
                        'complexity': round(complexity, 2),
                        'base_value': bv,
                        'final_score': round(bv, 2),
                        'goe':        0,
                        'color':      '#a78bfa',
                    })
                in_seq = False

        return results

    # ── Feature builders ──────────────────────────────────────────────────────

    def _build_jump_features(self, jump: Dict, seg: List[Dict]):
        MF = self._MF
        airtime   = jump.get('airtime', 0.4)
        rotations = jump.get('rotations', 1.0)

        v_vels, h_vels, sh_angles = [], [], []
        arm_positions, leg_exts, heights = [], [], []

        prev_t = prev_hy = prev_hx = None

        for p in seg:
            kp = p['kp']
            if len(kp) < 29:
                continue
            t = p['t']
            hy = (kp[23]['y'] + kp[24]['y']) / 2
            hx = (kp[23]['x'] + kp[24]['x']) / 2

            if prev_t and (t - prev_t) > 0:
                dt = t - prev_t
                v_vels.append((prev_hy - hy) / dt)
                h_vels.append(abs(hx - prev_hx) / dt)
            prev_t, prev_hy, prev_hx = t, hy, hx

            ls, rs = kp[11], kp[12]
            if ls.get('v', 0) > 0.2 and rs.get('v', 0) > 0.2:
                sh_angles.append(np.arctan2(
                    rs.get('z', 0) - ls.get('z', 0),
                    rs['x'] - ls['x']
                ))

            # Arm distance (tuck)
            if all(kp[i].get('v', 0) > 0.2 for i in [11, 12, 15, 16]):
                arm_positions.append(abs(kp[15]['x'] - kp[16]['x']))

            # Leg tuck: hip-to-ankle y-gap
            if all(kp[i].get('v', 0) > 0.2 for i in [23, 27]):
                leg_exts.append(abs(kp[27]['y'] - kp[23]['y']))

            if kp[0].get('v', 0) > 0.3:
                heights.append(1.0 - kp[0]['y'])

        rot_vel = (
            abs(np.unwrap(np.array(sh_angles))[-1] - np.unwrap(np.array(sh_angles))[0])
            / max(airtime, 0.01) / (2 * np.pi)
            if len(sh_angles) > 2 else rotations / max(airtime, 0.01)
        )

        # Landing angle from last quarter
        land_seg = seg[3 * len(seg) // 4:] if len(seg) > 4 else seg
        land_angles = []
        for p in land_seg:
            kp = p['kp']
            if len(kp) > 28 and all(kp[i].get('v', 0) > 0.2 for i in [24, 26, 28]):
                va = np.array([kp[24]['x']-kp[26]['x'], kp[24]['y']-kp[26]['y']])
                vc = np.array([kp[28]['x']-kp[26]['x'], kp[28]['y']-kp[26]['y']])
                cos_a = np.dot(va, vc) / (np.linalg.norm(va) * np.linalg.norm(vc) + 1e-9)
                land_angles.append(float(np.degrees(np.arccos(np.clip(cos_a, -1, 1)))))

        return MF(
            center_of_mass_height=float(np.mean(heights)) if heights else 0.6,
            body_rotation_angle=float(np.degrees(np.mean(sh_angles))) if sh_angles else 0.0,
            leg_extension=float(np.mean(leg_exts)) if leg_exts else 0.4,
            arm_position=float(np.mean(arm_positions)) if arm_positions else 0.3,
            vertical_velocity=float(np.mean(v_vels)) if v_vels else 2.0,
            rotational_velocity=float(rot_vel),
            horizontal_velocity=float(np.mean(h_vels)) if h_vels else 1.0,
            airtime=airtime,
            takeoff_angle=45.0 if rotations >= 1.5 else -45.0,
            landing_angle=float(np.mean(land_angles)) if land_angles else 70.0,
            rotation_count=rotations,
            spin_speed=0.0,
            axis_stability=0.5,
            body_position='upright',
            duration=airtime,
            complexity=min(1.0, rotations / 4.0),
        )

    def _build_spin_features(self, spin: Dict, seg: List[Dict], position: str):
        MF = self._MF
        duration  = spin.get('duration', 3.0)
        rpm       = spin.get('rpm', 60.0)
        spin_spd  = rpm / 60.0

        xs = [_hip_x(p) for p in seg if _hip_x(p) is not None]
        stability = max(0.0, 1.0 - np.std(xs) * 20) if xs else 0.7

        return MF(
            center_of_mass_height=0.5,
            body_rotation_angle=0.0,
            leg_extension=0.6 if position == 'camel' else 0.3,
            arm_position=0.4,
            vertical_velocity=0.0,
            rotational_velocity=spin_spd,
            horizontal_velocity=0.1,
            airtime=0.0,
            takeoff_angle=0.0,
            landing_angle=0.0,
            rotation_count=spin.get('rotations', 5.0),
            spin_speed=spin_spd,
            axis_stability=float(stability),
            body_position=position,
            duration=duration,
            complexity=min(1.0, spin_spd / 4.0),
        )


# ── Module-level helpers ───────────────────────────────────────────────────────

def _kp_to_seq(seg: List[Dict]) -> Optional[np.ndarray]:
    try:
        from src.models.lstm_classifier import INPUT_DIM
    except Exception:
        INPUT_DIM = 99
    rows = []
    for p in seg:
        kp = p.get('kp', [])
        if len(kp) < 33:
            continue
        row = np.zeros(INPUT_DIM, dtype=np.float32)
        for i, k in enumerate(kp[:33]):
            if k.get('v', 0) >= 0.25:
                row[i*3]   = k['x']
                row[i*3+1] = k['y']
                row[i*3+2] = k.get('z', 0.0)
        rows.append(row)
    return np.array(rows, dtype=np.float32) if len(rows) >= 4 else None


def _peak_frame(seg: List[Dict]) -> Optional[Dict]:
    """Return frame where hip Y is lowest (highest on screen = peak of jump)."""
    best, best_y = None, 1.0
    for p in seg:
        kp = p.get('kp', [])
        if len(kp) > 24 and kp[23].get('v', 0) > 0.2 and kp[24].get('v', 0) > 0.2:
            hy = (kp[23]['y'] + kp[24]['y']) / 2
            if hy < best_y:
                best_y, best = hy, p
    return best


def _hip_x(p: Dict) -> Optional[float]:
    kp = p.get('kp', [])
    if len(kp) > 24 and kp[23].get('v', 0) > 0.2 and kp[24].get('v', 0) > 0.2:
        return (kp[23]['x'] + kp[24]['x']) / 2
    return None


def _has_kp(p: Dict) -> bool:
    return bool(p.get('kp'))


def _detect_spin_position(seg: List[Dict]) -> str:
    camel, sit = [], []
    for p in seg:
        kp = p.get('kp', [])
        if len(kp) < 29:
            continue
        ls, lh = kp[11], kp[23]
        la = kp[27]
        if ls.get('v', 0) > 0.3 and lh.get('v', 0) > 0.3:
            dy = abs(ls['y'] - lh['y'])
            dx = abs(ls['x'] - lh['x'])
            ang = abs(np.degrees(np.arctan2(dy, dx + 1e-9)))
            camel.append(1.0 if ang < 30 else 0.0)  # nearly horizontal torso
        if lh.get('v', 0) > 0.3 and la.get('v', 0) > 0.3:
            gap = abs(lh['y'] - la['y'])
            sit.append(1.0 if gap < 0.12 else 0.0)  # hip near ankle
    camel_r = float(np.mean(camel)) if camel else 0.0
    sit_r   = float(np.mean(sit))   if sit   else 0.0
    if camel_r > 0.45:
        return 'camel'
    if sit_r > 0.45:
        return 'sit'
    return 'upright'


def _footwork_complexity(seg: List[Dict]) -> float:
    """Estimate footwork complexity from lateral movement variability."""
    xs = []
    for p in seg:
        kp = p.get('kp', [])
        if len(kp) > 24 and kp[23].get('v', 0) > 0.2 and kp[24].get('v', 0) > 0.2:
            xs.append((kp[23]['x'] + kp[24]['x']) / 2)
    if len(xs) < 3:
        return 0.4
    # Direction changes = complexity proxy
    diffs = np.diff(xs)
    sign_changes = np.sum(np.diff(np.sign(diffs)) != 0)
    complexity = min(1.0, sign_changes / max(len(xs) * 0.3, 1))
    return float(complexity)
