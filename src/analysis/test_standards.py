"""
مكتبة معايير الاختبارات المرجعية — Test Standards Library
تسمح بإدخال معايير اختبار (من فيديوهات مرجعية أو كتب تدريب مثل ISI Freestyle)
وتقييم أداء لاعب مُحلَّل آلياً مقابلها — لمعرفة النجاح من عدمه.
"""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

DB_PATH = 'skating_database.db'

CATEGORY_JUMP = 'jump'
CATEGORY_SPIN = 'spin'
CATEGORY_POSITION = 'position'   # e.g. arabesque/spiral — no automatic detector yet
CATEGORY_SEQUENCE = 'sequence'   # step sequence — partial automatic detector (duration only)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            name_ar TEXT, name_en TEXT,
            source_note TEXT,
            elements_json TEXT,
            created_at TEXT
        )
    """)
    return conn


# ── Seed standard, extracted from the official ISI "Freestyle 4" reference video ──
ISI_FREESTYLE_4 = {
    'key': 'isi_freestyle_4',
    'name_ar': 'اختبار ISI فريستايل 4',
    'name_en': 'ISI Freestyle 4',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Freestyle 4" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'flip_jump', 'name_ar': 'قفزة Flip', 'name_en': 'Flip Jump',
            'category': CATEGORY_JUMP, 'match_codes': ['1F', '2F', '3F', 'F', 'flip'],
            'min_rotations': 1.0,
            'criteria_notes_ar': [
                'الإقلاع: حافة داخلية خلفية + مقدمة النصل',
                'دورة كاملة واحدة عبر three-turn أو mohawk في التمهيد',
                'الهبوط: القدم المقابلة، حافة خارجية خلفية',
            ],
        },
        {
            'key': 'loop_jump', 'name_ar': 'قفزة Loop', 'name_en': 'Loop Jump',
            'category': CATEGORY_JUMP, 'match_codes': ['1Lo', '2Lo', '3Lo', 'Lo', 'loop'],
            'min_rotations': 1.0,
            'criteria_notes_ar': [
                'الإقلاع: حافة خارجية خلفية',
                'دورة كاملة واحدة',
                'الهبوط: نفس القدم ونفس الحافة',
            ],
        },
        {
            'key': 'sit_spin', 'name_ar': 'دوران الجلوس Sit Spin', 'name_en': 'Sit Spin',
            'category': CATEGORY_SPIN, 'match_codes': ['SSp', 'sit'],
            'min_revolutions': 6, 'min_position_revolutions': 4, 'position': 'sit',
            'criteria_notes_ar': [
                'الانتقال (travel) لا يتجاوز 3 أطوال نصل',
                'ورك التزلج بنفس انخفاض الركبة',
                '6 دورات كحد أدنى، منها 4 في وضعية الجلوس',
            ],
        },
        {
            'key': 'half_loop_jump', 'name_ar': 'قفزة Half Loop', 'name_en': 'Half Loop Jump',
            'category': CATEGORY_JUMP, 'match_codes': ['1/2Lo', 'HLo', 'half loop'],
            'min_rotations': 0.5,
            'criteria_notes_ar': [
                'الإقلاع: حافة خارجية خلفية',
                'دورة كاملة واحدة',
                'الهبوط: القدم المقابلة، حافة داخلية خلفية',
            ],
        },
        {
            'key': 'two_backward_arabesques', 'name_ar': 'وضعيتا Arabesque خلفيتان',
            'name_en': 'Two Backward Arabesques',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'قدمان مختلفتان، أي حافة',
                'تُحفظ لمسافة 4 أضعاف طول اللاعب',
                'الساق الحرة بارتفاع الورك',
            ],
        },
        {
            'key': 'dance_step_sequence', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
            'category': CATEGORY_SEQUENCE, 'match_codes': [],
            'min_duration': 8.0,
            'criteria_notes_ar': [
                'عزل جميع الـ 4 three-turns الخلفية',
                '18 خطوة تُظهر جميع الـ 8 three-turns',
                'محور التسلسل هو المحور الطويل لحلبة الجليد',
            ],
        },
    ],
}

# ── Seed standard, extracted from the official ISI "Delta" reference video ────
# Delta is a basic-skills level test (below Freestyle) — none of its elements
# are rotation-based jumps/spins our engine classifies, so every element is
# marked CATEGORY_POSITION (explicit manual review) rather than forced through
# a detector that isn't built for them.
ISI_DELTA = {
    'key': 'isi_delta',
    'name_ar': 'اختبار ISI دلتا (Delta)',
    'name_en': 'ISI Delta',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Delta" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'forward_inside_three_turns', 'name_ar': 'Three Turns من حافة داخلية أمامية',
            'name_en': 'Forward Inside Three Turns',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'القدم اليمنى واليسرى، مهارتان منفصلتان',
                'حافة داخلية أمامية، ثم التفاف إلى حافة خارجية خلفية',
                'الالتفاف على قدم واحدة، ويجب أن يساوي طول الخطوة طول اللاعب',
            ],
        },
        {
            'key': 'forward_edges', 'name_ar': 'حواف أمامية (Forward Edges)', 'name_en': 'Forward Edges',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'حافتان: خارجية وداخلية',
                '4 أنصاف دوائر لكل حافة، بالتناوب بين القدمين',
                'يجب أن تصطف على محور واحد',
            ],
        },
        {
            'key': 'shoot_the_duck_or_lunge', 'name_ar': 'Shoot the Duck أو Lunge (اختياري)',
            'name_en': 'Choice of Shoot the Duck or Lunge',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'ورك التزلج يساوي أو أقل من الركبة',
                'تُحفظ الوضعية لمسافة 4 أضعاف طول اللاعب',
                'يجب أن ينهض اللاعب على قدم واحدة',
            ],
        },
        {
            'key': 'bunny_hop', 'name_ar': 'Bunny Hop', 'name_en': 'Bunny Hop',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'قفزة أمامية بسيطة (وثبة وليست قفزة دورانية)',
                'الإقلاع: من مقدمة نصل قدم واحدة',
                'الهبوط: على مقدمة نصل القدم الأخرى',
            ],
        },
    ],
}

_SEED_STANDARDS = [ISI_FREESTYLE_4, ISI_DELTA]


def ensure_seed_standards() -> None:
    conn = _conn()
    for std in _SEED_STANDARDS:
        cur = conn.execute("SELECT COUNT(*) FROM test_standards WHERE key=?", (std['key'],))
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO test_standards (key, name_ar, name_en, source_note, elements_json, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (
                    std['key'], std['name_ar'], std['name_en'], std['source_note'],
                    json.dumps(std['elements'], ensure_ascii=False),
                    datetime.now().strftime('%Y-%m-%d %H:%M'),
                ),
            )
    conn.commit()
    conn.close()


def list_standards() -> List[Dict]:
    ensure_seed_standards()
    conn = _conn()
    rows = conn.execute(
        "SELECT id, key, name_ar, name_en, source_note, elements_json, created_at "
        "FROM test_standards ORDER BY id"
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            'id': r[0], 'key': r[1], 'name_ar': r[2], 'name_en': r[3],
            'source_note': r[4], 'elements': json.loads(r[5]), 'created_at': r[6],
        })
    return out


def get_standard(std_id: int) -> Optional[Dict]:
    for s in list_standards():
        if s['id'] == std_id:
            return s
    return None


def save_standard(name_ar: str, name_en: str, source_note: str, elements: List[Dict], key: Optional[str] = None) -> None:
    key = key or f"custom_{int(datetime.now().timestamp())}"
    conn = _conn()
    conn.execute(
        "INSERT INTO test_standards (key, name_ar, name_en, source_note, elements_json, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (key, name_ar, name_en, source_note, json.dumps(elements, ensure_ascii=False),
         datetime.now().strftime('%Y-%m-%d %H:%M')),
    )
    conn.commit()
    conn.close()


def delete_standard(std_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM test_standards WHERE id=?", (std_id,))
    conn.commit()
    conn.close()


# ── Evaluation ──────────────────────────────────────────────────────────────

def _match_jump(el: Dict, jumps: List[Dict]) -> Optional[Dict]:
    codes = [c.lower() for c in el.get('match_codes', [])]
    for j in jumps:
        code = str(j.get('code', '')).lower()
        typ = str(j.get('type', '')).lower()
        if any(c and (c in code or c in typ) for c in codes):
            return j
    return None


def _match_spin(el: Dict, spins: List[Dict]) -> Optional[Dict]:
    codes = [c.lower() for c in el.get('match_codes', [])]
    for s in spins:
        code = str(s.get('code', '')).lower()
        typ = str(s.get('type', '')).lower()
        pos = str(s.get('ai_position', '')).lower()
        if any(c and (c in code or c in typ) for c in codes) or (el.get('position') and el['position'] == pos):
            return s
    return None


def evaluate(results: Dict, standard: Dict, manual_overrides: Optional[Dict[str, bool]] = None) -> Dict:
    """قارن نتائج تحليل فيديو بمعيار اختبار محدد، وأرجع تقريراً عنصراً بعنصر."""
    manual_overrides = manual_overrides or {}
    jumps = results.get('jumps', [])
    spins = results.get('spins', [])
    step_seqs = results.get('step_sequences', [])

    element_reports = []
    all_passed = True

    for el in standard['elements']:
        cat = el['category']
        checks: List[Dict] = []
        status = 'fail'
        matched = None

        if cat == CATEGORY_JUMP:
            matched = _match_jump(el, jumps)
            if matched:
                min_rot = el.get('min_rotations', 0)
                rot = matched.get('rotations', 0)
                ok_rot = rot >= min_rot * 0.85  # small tolerance for measurement noise
                checks.append({'label_ar': f'الدوران ({rot:.1f} من {min_rot} مطلوبة)', 'ok': ok_rot})
                clean = matched.get('is_clean', True)
                checks.append({'label_ar': 'هبوط نظيف (بدون هبوط على قدمين)', 'ok': clean})
                status = 'pass' if (ok_rot and clean) else 'warn'
            else:
                checks.append({'label_ar': 'لم يتم اكتشاف هذه القفزة في الفيديو', 'ok': False})
                status = 'fail'

        elif cat == CATEGORY_SPIN:
            matched = _match_spin(el, spins)
            if matched:
                min_rev = el.get('min_revolutions', 0)
                rev = matched.get('rotations', 0)
                ok_rev = rev >= min_rev * 0.85
                checks.append({'label_ar': f'عدد الدورات ({rev:.1f} من {min_rev} مطلوبة)', 'ok': ok_rev})
                if el.get('position'):
                    detected_pos = str(matched.get('ai_position', '—'))
                    pos_ok = detected_pos.lower() == el['position']
                    checks.append({'label_ar': f'الوضعية المكتشفة: {detected_pos}', 'ok': pos_ok})
                    status = 'pass' if (ok_rev and pos_ok) else 'warn'
                else:
                    status = 'pass' if ok_rev else 'warn'
            else:
                checks.append({'label_ar': 'لم يتم اكتشاف هذا الدوران في الفيديو', 'ok': False})
                status = 'fail'

        elif cat == CATEGORY_SEQUENCE:
            if step_seqs:
                matched = step_seqs[0]
                dur = matched.get('duration', 0)
                min_dur = el.get('min_duration', 0)
                ok_dur = dur >= min_dur
                checks.append({'label_ar': f'مدة التسلسل المكتشف ({dur:.1f}ث)', 'ok': ok_dur})
                checks.append({'label_ar': 'العدّ الدقيق للـ three-turns يتطلب مراجعة يدوية من المدرب', 'ok': None})
                status = 'warn'
            else:
                checks.append({'label_ar': 'لم يتم اكتشاف تسلسل خطوات في الفيديو', 'ok': False})
                status = 'fail'

        else:  # CATEGORY_POSITION — no automatic detector for this element type yet
            checks.append({'label_ar': 'هذا العنصر يتطلب مراجعة يدوية من المدرب — لا يوجد كاشف آلي له بعد', 'ok': None})
            status = 'manual'

        # Coach's manual override always takes precedence
        if el['key'] in manual_overrides:
            status = 'pass' if manual_overrides[el['key']] else 'fail'

        if status != 'pass':
            all_passed = False

        element_reports.append({
            'key': el['key'], 'name_ar': el.get('name_ar', el['key']), 'category': cat,
            'status': status, 'checks': checks,
            'criteria_notes_ar': el.get('criteria_notes_ar', []),
            'matched_type': matched.get('type') if matched else None,
        })

    return {
        'standard_name_ar': standard['name_ar'],
        'elements': element_reports,
        'passed': all_passed,
        'evaluated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    }
