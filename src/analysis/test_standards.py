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

# ── Seed standard, extracted from the official ISI "Pre-Alpha" reference video ─
# Pre-Alpha is the entry-level basic-skills test, below Alpha/Beta/Gamma/Delta.
ISI_PRE_ALPHA = {
    'key': 'isi_pre_alpha',
    'name_ar': 'اختبار ISI بري-ألفا (Pre-Alpha)',
    'name_en': 'ISI Pre-Alpha',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Pre-Alpha" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'two_foot_glide', 'name_ar': 'انزلاق بقدمين (Two-Foot Glide)',
            'name_en': 'Two-Foot Glide',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'حد أقصى 3 خطوات للتحضير',
                'تبقى القدمان على الجليد',
                'تُحفظ لمسافة تساوي طول اللاعب على الأقل',
            ],
        },
        {
            'key': 'one_foot_glide', 'name_ar': 'انزلاق بقدم واحدة (One-Foot Glide)',
            'name_en': 'One-Foot Glide',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'حد أقصى 3 خطوات للتحضير',
                'يُؤدَّى على كل قدم منفصلة',
                'تُحفظ لمسافة تساوي طول اللاعب على الأقل',
            ],
        },
        {
            'key': 'forward_swizzles', 'name_ar': 'Swizzles أمامية', 'name_en': 'Forward Swizzles',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'تُحفظ لمسافة تساوي طول اللاعب على الأقل',
                '3 حركات دخول وخروج',
                'انزلاق بقدمين بين كل حركة',
            ],
        },
        {
            'key': 'backward_wiggle', 'name_ar': 'Wiggle خلفية (Backward Wiggle)',
            'name_en': 'Backward Wiggle',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'تُؤدَّى لمسافة تساوي طول اللاعب على الأقل',
                '4 حركات متعرجة (zig-zag)',
            ],
        },
        {
            'key': 'backward_swizzles', 'name_ar': 'Swizzles خلفية', 'name_en': 'Backward Swizzles',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'تُحفظ لمسافة تساوي طول اللاعب على الأقل',
                '3 حركات دخول وخروج للخلف',
                'انزلاق بقدمين بين كل حركة',
            ],
        },
    ],
}

# ── Seed standard, extracted from the official ISI "Alpha" reference video ────
ISI_ALPHA = {
    'key': 'isi_alpha',
    'name_ar': 'اختبار ISI ألفا (Alpha)',
    'name_en': 'ISI Alpha',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Alpha" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'forward_stroking', 'name_ar': 'دفع أمامي (Forward Stroking)',
            'name_en': 'Forward Stroking',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'تبدأ الدفعة على النصل المسطّح أو الحافة الخارجية',
                'كل دفعة تساوي طول اللاعب',
                '6 دفعات متبادلة على الأقل',
            ],
        },
        {
            'key': 'forward_crossovers', 'name_ar': 'خطوات متقاطعة أمامية (Forward Crossovers)',
            'name_en': 'Forward Crossovers',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'كلا الاتجاهين، مهارتان منفصلتان',
                '10 دفعات متواصلة على الأقل',
                'الذراع الخارجية للأمام، والداخلية للخلف',
            ],
        },
        {
            'key': 'one_foot_snowplow_stop', 'name_ar': 'إيقاف Snowplow بقدم واحدة',
            'name_en': 'One Foot Snowplow Stop',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'يُؤدَّى في خط مستقيم',
                'قدم الإيقاف على الحافة الداخلية، أي قدم',
                'تُحفظ الوضعية 3 ثوانٍ بعد التوقف',
            ],
        },
    ],
}

# ── Seed standard, extracted from the official ISI "Beta" reference video ─────
ISI_BETA = {
    'key': 'isi_beta',
    'name_ar': 'اختبار ISI بيتا (Beta)',
    'name_en': 'ISI Beta',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Beta" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'backward_stroking', 'name_ar': 'دفع خلفي (Backward Stroking)',
            'name_en': 'Backward Stroking',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'الدفع بالحافة الداخلية، بدون مقدمة النصل',
                'تبدأ الدفعة على الحافة الخارجية',
                '6 دفعات، كل واحدة تساوي طول اللاعب',
            ],
        },
        {
            'key': 'backward_crossovers', 'name_ar': 'خطوات متقاطعة خلفية (Backward Crossovers)',
            'name_en': 'Backward Crossovers',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'كلا الاتجاهين، مهارتان منفصلتان',
                '10 دفعات متواصلة على الأقل',
                'الذراع الخارجية للأمام، والداخلية للخلف',
            ],
        },
        {
            'key': 't_stops', 'name_ar': 'إيقاف T (T-Stops)', 'name_en': 'T-Stops',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'كلتا القدمين، مهارتان منفصلتان',
                'توقف كامل، يُحفظ 3 ثوانٍ',
                'قدم الإيقاف تستخدم الحافة الخارجية',
            ],
        },
    ],
}

# ── Seed standard, extracted from the official ISI "Gamma" reference video ────
ISI_GAMMA = {
    'key': 'isi_gamma',
    'name_ar': 'اختبار ISI جاما (Gamma)',
    'name_en': 'ISI Gamma',
    'source_note': 'مستخرج من فيديو ISI الرسمي "Gamma" (المرجع البصري المعتمد للاختبار)',
    'elements': [
        {
            'key': 'forward_outside_three_turns', 'name_ar': 'Three Turns من حافة خارجية أمامية',
            'name_en': 'Forward Outside Three Turns',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'القدم اليمنى واليسرى، مهارتان منفصلتان',
                'حافة خارجية أمامية، ثم التفاف إلى حافة داخلية خلفية',
                'الالتفاف على قدم واحدة، ويجب أن يساوي طول الخطوة طول اللاعب',
            ],
        },
        {
            'key': 'inside_open_mohawk_combinations', 'name_ar': 'تشكيلات Mohawk داخلية مفتوحة',
            'name_en': 'Inside Open Mohawk Combinations',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'كلا الاتجاهين، مهارتان منفصلتان',
                'مهاركان (mohawks)، 7 خطوات إجمالاً',
                'نمط إلزامي محدد',
            ],
        },
        {
            'key': 'hockey_stop', 'name_ar': 'إيقاف الهوكي (Hockey Stop)', 'name_en': 'Hockey Stop',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'حافة داخلية لقدم، وخارجية للأخرى',
                'يجب أن تبقى القدمان متوازيتين',
                'يُحفظ 3 ثوانٍ بعد التوقف',
            ],
        },
    ],
}

_SEED_STANDARDS = [
    ISI_PRE_ALPHA, ISI_ALPHA, ISI_BETA, ISI_GAMMA, ISI_DELTA, ISI_FREESTYLE_4,
]


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
