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

FEDERATION_ISI = 'ISI'
FEDERATION_ISU = 'ISU'


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            name_ar TEXT, name_en TEXT,
            source_note TEXT,
            elements_json TEXT,
            federation TEXT DEFAULT 'ISI',
            created_at TEXT
        )
    """)
    # Older DBs created before the federation column existed
    try:
        conn.execute("ALTER TABLE test_standards ADD COLUMN federation TEXT DEFAULT 'ISI'")
    except sqlite3.OperationalError:
        pass  # column already exists

    conn.execute("""
        CREATE TABLE IF NOT EXISTS reference_video_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            federation TEXT,
            level_name TEXT,
            note TEXT,
            file_path TEXT,
            linked_standard_key TEXT,
            uploaded_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS standard_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            federation TEXT,
            standard_key TEXT,
            standard_name TEXT,
            player_name TEXT,
            video_note TEXT,
            passed INTEGER,
            report_json TEXT,
            created_at TEXT
        )
    """)
    return conn


# ══════════════════════════════════════════════════════════════════════════
# The following ISI standards (Pre-Alpha through Freestyle 10) are extracted
# verbatim from the official "The Ice Sports Industry (ISI) Handbook" (2018
# Edition), pages 28-60 — the same book ISI uses to certify examiners. This
# replaces the earlier video-derived seed data with the authoritative text.
# ══════════════════════════════════════════════════════════════════════════

_HANDBOOK_SRC = 'مستخرج من الكتاب الرسمي "The Ice Sports Industry (ISI) Handbook" (2018 Edition), صفحة {}'

ISI_PRE_ALPHA = {
    'key': 'isi_pre_alpha',
    'name_ar': 'اختبار ISI بري-ألفا (Pre-Alpha)',
    'name_en': 'ISI Pre-Alpha',
    'source_note': _HANDBOOK_SRC.format('29'),
    'elements': [
        {
            'key': 'two_foot_glide', 'name_ar': 'انزلاق بقدمين (Two-Foot Glide)',
            'name_en': 'Two-Foot Glide', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'أثناء الانزلاق بوضعية منتصبة، لمسافة لا تقل عن طول اللاعب على قدمين',
                'بعد أخذ 3 خطوات تحضيرية فقط كحد أقصى',
            ],
        },
        {
            'key': 'one_foot_glide', 'name_ar': 'انزلاق بقدم واحدة (One-Foot Glide)',
            'name_en': 'One-Foot Glide', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'لمسافة لا تقل عن طول اللاعب على كل قدم منفصلة (يمنى ويسرى)',
                'بعد أخذ 3 خطوات تحضيرية فقط كحد أقصى',
            ],
        },
        {
            'key': 'forward_swizzle', 'name_ar': 'Swizzle أمامية', 'name_en': 'Forward Swizzle',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['لمسافة لا تقل عن طول اللاعب في 3 حركات دخول وخروج (in-and-out)'],
        },
        {
            'key': 'backward_wiggle', 'name_ar': 'Wiggle خلفية (Backward Wiggle)',
            'name_en': 'Backward Wiggle', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['لمسافة لا تقل عن طول اللاعب في 4 حركات متعرجة (zig-zag)'],
        },
        {
            'key': 'backward_swizzle', 'name_ar': 'Swizzle خلفية', 'name_en': 'Backward Swizzle',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['لمسافة لا تقل عن طول اللاعب في 3 حركات دخول وخروج للخلف'],
        },
    ],
}

ISI_ALPHA = {
    'key': 'isi_alpha',
    'name_ar': 'اختبار ISI ألفا (Alpha)',
    'name_en': 'ISI Alpha',
    'source_note': _HANDBOOK_SRC.format('30'),
    'elements': [
        {
            'key': 'forward_stroking', 'name_ar': 'دفع أمامي (Forward Stroking)',
            'name_en': 'Forward Stroking', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'الدفع بالحافة الداخلية بدون استخدام مقدمة النصل',
                'كل دفعة بمسافة لا تقل عن طول اللاعب، الساق الحرة فوق الحافة الخلفية',
                '6 دفعات متبادلة متواصلة على الأقل بدون انقطاع',
            ],
        },
        {
            'key': 'right_forward_crossovers', 'name_ar': 'خطوات متقاطعة أمامية — يمنى فوق يسرى',
            'name_en': 'Right Forward Crossovers (Right Over Left)',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'القدم الخارجية (اليمنى) تدفع بالحافة الداخلية وتُعبَر أمام الأخرى',
                'القدم الداخلية (اليسرى) تدفع بالحافة الخارجية (بدون مقدمة النصل)',
                'الكتف/الذراع الخارجي للأمام، والداخلي للخلف — 10 دفعات (5 عبورات) على الأقل',
            ],
        },
        {
            'key': 'left_forward_crossovers', 'name_ar': 'خطوات متقاطعة أمامية — يسرى فوق يمنى',
            'name_en': 'Left Forward Crossovers (Left Over Right)',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
        {
            'key': 'one_foot_snowplow_stop', 'name_ar': 'إيقاف Snowplow بقدم واحدة',
            'name_en': 'One Foot Snowplow Stop', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'توقف كامل بتوازن جيد باستخدام الحافة الداخلية لأي قدم، في خط مستقيم',
                'يُحفظ الوضع بعد التوقف لمدة 3 ثوانٍ',
            ],
        },
    ],
}

ISI_BETA = {
    'key': 'isi_beta',
    'name_ar': 'اختبار ISI بيتا (Beta)',
    'name_en': 'ISI Beta',
    'source_note': _HANDBOOK_SRC.format('30-31'),
    'elements': [
        {
            'key': 'backward_stroking', 'name_ar': 'دفع خلفي (Backward Stroking)',
            'name_en': 'Backward Stroking', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'الدفع بالحافة الداخلية بدون مقدمة النصل، تبدأ الدفعة من الحافة الخارجية',
                '6 دفعات على الأقل، كل واحدة بمسافة لا تقل عن طول اللاعب',
            ],
        },
        {
            'key': 'right_backward_crossover_strokes', 'name_ar': 'خطوات متقاطعة خلفية — يمنى فوق يسرى',
            'name_en': 'Right Backward Crossover Strokes (Right Over Left)',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                '10 دفعات (5 عبورات) على الأقل بدون انقطاع، كل دفعة بطول اللاعب',
                'ملاحظة: Cutbacks (بقاء القدم الخارجية على الجليد أثناء العبور) لا تُحتسب',
            ],
        },
        {
            'key': 'left_backward_crossover_strokes', 'name_ar': 'خطوات متقاطعة خلفية — يسرى فوق يمنى',
            'name_en': 'Left Backward Crossover Strokes (Left Over Right)',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
        {
            'key': 't_stop_right', 'name_ar': 'إيقاف T — الحافة الخارجية للقدم اليمنى',
            'name_en': 'T-Stop, Right Foot Outside Edge', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['قدم الإيقاف (اليمنى) خلف القدم الأخرى، الحافة الخارجية — يُحفظ 3 ثوانٍ'],
        },
        {
            'key': 't_stop_left', 'name_ar': 'إيقاف T — الحافة الخارجية للقدم اليسرى',
            'name_en': 'T-Stop, Left Foot Outside Edge', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
    ],
}

ISI_GAMMA = {
    'key': 'isi_gamma',
    'name_ar': 'اختبار ISI جاما (Gamma)',
    'name_en': 'ISI Gamma',
    'source_note': _HANDBOOK_SRC.format('31-32'),
    'elements': [
        {
            'key': 'right_forward_outside_three_turn', 'name_ar': 'Three Turn خارجي أمامي — قدم يمنى',
            'name_en': 'Right Forward Outside Three Turn', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'طول الانزلاق الكلي لا يقل عن ضعف طول اللاعب',
                'الالتفاف من حافة خارجية أمامية إلى حافة داخلية خلفية، في منتصف الخطوة',
            ],
        },
        {
            'key': 'left_forward_outside_three_turn', 'name_ar': 'Three Turn خارجي أمامي — قدم يسرى',
            'name_en': 'Left Forward Outside Three Turn', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
        {
            'key': 'right_forward_inside_open_mohawk', 'name_ar': 'تشكيلة Mohawk داخلية مفتوحة — يمنى',
            'name_en': 'Right Forward Inside Open Mohawk Combination',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'مهاركان (mohawks) بإجمالي 7 خطوات، بنمط إلزامي محدد',
                'قطر المنحنى لا يقل عن ضعف طول اللاعب، وكل خطوة بطول اللاعب على الأقل',
            ],
        },
        {
            'key': 'left_forward_inside_open_mohawk', 'name_ar': 'تشكيلة Mohawk داخلية مفتوحة — يسرى',
            'name_en': 'Left Forward Inside Open Mohawk Combination',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
        {
            'key': 'hockey_stop', 'name_ar': 'إيقاف الهوكي (Hockey Stop)', 'name_en': 'Hockey Stop',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'حافة داخلية لقدم وخارجية للأخرى، القدمان متوازيتان والكتفان متوازيان معهما',
                'يُحفظ الوضع بعد التوقف لمدة 3 ثوانٍ',
            ],
        },
    ],
}

ISI_DELTA = {
    'key': 'isi_delta',
    'name_ar': 'اختبار ISI دلتا (Delta)',
    'name_en': 'ISI Delta',
    'source_note': _HANDBOOK_SRC.format('33-34'),
    'elements': [
        {
            'key': 'right_forward_inside_three_turn', 'name_ar': 'Three Turn داخلي أمامي — قدم يمنى',
            'name_en': 'Right Forward Inside Three Turn', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'طول الانزلاق الكلي لا يقل عن ضعف طول اللاعب',
                'الالتفاف من حافة داخلية أمامية إلى حافة خارجية خلفية، مع "check" لإيقاف الدوران',
            ],
        },
        {
            'key': 'left_forward_inside_three_turn', 'name_ar': 'Three Turn داخلي أمامي — قدم يسرى',
            'name_en': 'Left Forward Inside Three Turn', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس الحركة السابقة بجميع الاتجاهات معكوسة'],
        },
        {
            'key': 'forward_outside_edges', 'name_ar': 'حواف خارجية أمامية (سلسلة)',
            'name_en': 'Forward Outside Edges', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'سلسلة لا تقل عن 4 أنصاف دوائر، بالتناوب بين القدمين، على محور واحد',
                'قطر كل نصف دائرة بين طول اللاعب وثلاثة أضعافه، بدون دفع بمقدمة النصل',
            ],
        },
        {
            'key': 'forward_inside_edges', 'name_ar': 'حواف داخلية أمامية (سلسلة)',
            'name_en': 'Forward Inside Edges', 'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': ['نفس متطلبات الحواف الخارجية الأمامية أعلاه، على الحافة الداخلية'],
        },
        {
            'key': 'shoot_the_duck_or_lunge', 'name_ar': 'Shoot-the-Duck أو Lunge (اختياري)',
            'name_en': 'Shoot-the-Duck or Lunge (Choice of One)',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'المسافة لا تقل عن 4 أضعاف طول اللاعب',
                'Shoot-the-Duck: ورك التزلج لا يعلو الركبة؛ Lunge: القدم الحرة تلمس الجليد بجانب القدم فقط',
            ],
        },
        {
            'key': 'bunny_hop', 'name_ar': 'Bunny Hop', 'name_en': 'Bunny Hop',
            'category': CATEGORY_POSITION, 'match_codes': [],
            'criteria_notes_ar': [
                'أثناء الانزلاق الأمامي بقدم واحدة، وثبة من مقدمة نصل القدم المتزلجة',
                'الهبوط على مقدمة نصل القدم الأخرى، ثم عودة فورية للانزلاق الأمامي',
            ],
        },
    ],
}

# ── ISI Freestyle Tests 1-10 (compulsory maneuvers), verbatim from the 2018
# ISI Handbook. Genuine single jumps/spins carry match_codes + min rotations
# for automatic evaluation; multi-element combinations, choreographed jump/
# turn/spin sequences, and "choice of one" bundles are marked CATEGORY_POSITION
# for manual coach review — our detector recognizes isolated jumps/spins, not
# choreographed combinations, so claiming automatic detection for those would
# be dishonest about what the system can actually verify.

ISI_FREESTYLE_1 = {
    'key': 'isi_freestyle_1',
    'name_ar': 'اختبار ISI فريستايل 1', 'name_en': 'ISI Freestyle 1',
    'source_note': _HANDBOOK_SRC.format('38-39'),
    'elements': [
        {'key': 'forward_inside_pivot', 'name_ar': 'Pivot داخلي أمامي', 'name_en': 'Forward Inside Pivot',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['مقدمة نصل قدم ثابتة، والأخرى تدور حولها على الحافة الداخلية لـ1.5 دورة على الأقل بدون توقف أو ضخ']},
        {'key': 'two_foot_spin', 'name_ar': 'دوران بقدمين', 'name_en': 'Two-Foot Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['two-foot spin', '2 foot spin', '2-foot spin'],
         'min_revolutions': 6,
         'criteria_notes_ar': ['القدمان على الجليد لـ6 دورات متواصلة على الأقل، انتقال لا يتجاوز 3 أطوال نصل']},
        {'key': 'forward_arabesque', 'name_ar': 'وضعية Arabesque أمامية', 'name_en': 'Forward Arabesque',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['بقدم واحدة، لمسافة 4 أضعاف طول اللاعب؛ الساق الحرة بارتفاع الورك على الأقل']},
        {'key': 'backward_outside_edges_fs1', 'name_ar': 'حواف خارجية خلفية (سلسلة)', 'name_en': 'Backward Outside Edges',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['4 أنصاف دوائر على الأقل، بالتناوب بين القدمين، على محور واحد']},
        {'key': 'backward_inside_edges_fs1', 'name_ar': 'حواف داخلية خلفية (سلسلة)', 'name_en': 'Backward Inside Edges',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['نفس متطلبات الحواف الخارجية الخلفية أعلاه']},
        {'key': 'one_half_flip', 'name_ar': 'قفزة نصف Flip', 'name_en': 'One-Half Flip',
         'category': CATEGORY_JUMP, 'match_codes': ['1/2f', 'half flip', 'one-half flip'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['الإقلاع: حافة داخلية خلفية + مقدمة نصل القدم الأخرى؛ الهبوط أمامي على مقدمة النصل المقابلة']},
        {'key': 'waltz_jump_fs1', 'name_ar': 'قفزة Waltz', 'name_en': 'Waltz Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1a', 'waltz', 'waltz jump'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية أمامية؛ الهبوط: حافة خارجية خلفية للقدم المقابلة']},
    ],
}

ISI_FREESTYLE_2 = {
    'key': 'isi_freestyle_2',
    'name_ar': 'اختبار ISI فريستايل 2', 'name_en': 'ISI Freestyle 2',
    'source_note': _HANDBOOK_SRC.format('40-41'),
    'elements': [
        {'key': 'ballet_jump', 'name_ar': 'قفزة Ballet', 'name_en': 'Ballet Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['ballet jump'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['إقلاع خلفي بقدم واحدة، وثبة على المقدمة بنصف دورة، هبوط على نفس المقدمة ثم انزلاق أمامي داخلي']},
        {'key': 'jump_seq_waltz_taptoe_3turn_halfflip', 'name_ar': 'تسلسل قفزات: Waltz/Tap-Toe/3-turn أو Mohawk/نصف Flip',
         'name_en': 'Jump Sequence: Waltz/Tap-Toe/3-turn or Mohawk/One-Half Flip',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 قفزات بالترتيب المحدد بدون خطوات إضافية بينها']},
        {'key': 'one_half_lutz', 'name_ar': 'قفزة نصف Lutz', 'name_en': 'One-Half Lutz',
         'category': CATEGORY_JUMP, 'match_codes': ['1/2lz', 'half lutz'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية خلفية + مقدمة النصل، دوران للجهة المقابلة؛ الهبوط أمامي على المقدمة المقابلة']},
        {'key': 'one_foot_spin', 'name_ar': 'دوران بقدم واحدة', 'name_en': 'One-Foot Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['one-foot spin', '1 foot spin', '1-foot spin'],
         'min_revolutions': 6,
         'criteria_notes_ar': ['وضعية منتصبة، 6 دورات على الأقل، وضعية الساق الحرة اختيارية']},
        {'key': 'two_forward_arabesques', 'name_ar': 'وضعيتا Arabesque أماميتان', 'name_en': 'Two Forward Arabesques',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['نمطان على حافتين مختلفتين، لمسافة 4 أضعاف طول اللاعب لكل منهما']},
        {'key': 'dance_step_sequence_fs2', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي من 10 خطوات، يتضمن Mohawk داخلي أمامي وخلفي؛ يمكن أداؤه بأي اتجاه']},
    ],
}

ISI_FREESTYLE_3 = {
    'key': 'isi_freestyle_3',
    'name_ar': 'اختبار ISI فريستايل 3', 'name_en': 'ISI Freestyle 3',
    'source_note': _HANDBOOK_SRC.format('41-42'),
    'elements': [
        {'key': 'backward_pivot_choice', 'name_ar': 'Pivot خلفي خارجي أو داخلي (اختياري)',
         'name_en': 'Backward Outside or Backward Inside Pivot (Choice of One)',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['1.5 دورة على الأقل بدون توقف أو ضخ']},
        {'key': 'salchow_jump', 'name_ar': 'قفزة Salchow', 'name_en': 'Salchow Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1s', 'salchow'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['الإقلاع: حافة داخلية خلفية؛ الهبوط: حافة خارجية خلفية للقدم الأخرى']},
        {'key': 'change_foot_spin', 'name_ar': 'دوران بتغيير القدم', 'name_en': 'Change Foot Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['change foot spin', 'change-foot spin'],
         'min_revolutions': 9,
         'criteria_notes_ar': ['3 دورات على قدم + 3 على الأخرى + 3 على القدم الأصلية = 9 دورات على الأقل']},
        {'key': 'backward_arabesque', 'name_ar': 'وضعية Arabesque خلفية', 'name_en': 'Backward Arabesque',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['بقدم واحدة، أي حافة، لمسافة 4 أضعاف طول اللاعب']},
        {'key': 'toe_loop_or_walley', 'name_ar': 'قفزة Toe Loop أو Toe Walley (اختياري)',
         'name_en': 'Toe Loop Jump or Toe Walley Jump (Choice of One)',
         'category': CATEGORY_JUMP, 'match_codes': ['1t', 'toe loop', 'toe walley'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية خلفية (Toe Loop) أو داخلية خلفية (Toe Walley) + مقدمة النصل؛ الهبوط: حافة خارجية خلفية لنفس القدم']},
        {'key': 'dance_step_sequence_fs3', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي من 9 خطوات، يتضمن Open Mohawk خارجي أمامي وMohawk خارجي خلفي؛ يمكن أداؤه بأي اتجاه']},
    ],
}

ISI_FREESTYLE_4 = {
    'key': 'isi_freestyle_4',
    'name_ar': 'اختبار ISI فريستايل 4', 'name_en': 'ISI Freestyle 4',
    'source_note': _HANDBOOK_SRC.format('42-43'),
    'elements': [
        {'key': 'flip_jump', 'name_ar': 'قفزة Flip', 'name_en': 'Flip Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1f', 'flip'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['الإقلاع: حافة داخلية خلفية + مقدمة النصل؛ الهبوط: حافة خارجية خلفية للقدم المقابلة']},
        {'key': 'loop_jump', 'name_ar': 'قفزة Loop', 'name_en': 'Loop Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1lo', 'loop'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية خلفية؛ الهبوط: نفس القدم ونفس الحافة']},
        {'key': 'sit_spin', 'name_ar': 'دوران الجلوس Sit Spin', 'name_en': 'Sit Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['ssp', 'sit'], 'min_revolutions': 6, 'position': 'sit',
         'criteria_notes_ar': [
             'الدخول من حافة خارجية أمامية، 6 دورات على الأقل منها 4 وورك التزلج لا يعلو الركبة',
             'الساق الحرة للأمام (غير ملتفة حول القدم المتزلجة)، الظهر مستقيم',
         ]},
        {'key': 'half_loop_jump', 'name_ar': 'قفزة Half Loop', 'name_en': 'One-Half Loop Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1/2lo', 'half loop'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['نفس إقلاع Loop، لكن الهبوط على الحافة الداخلية الخلفية للقدم المقابلة، بدون دوران على المقدمة']},
        {'key': 'two_backward_arabesques', 'name_ar': 'وضعيتا Arabesque خلفيتان', 'name_en': 'Two Backward Arabesques',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['نمطان (قدم لكل منهما)، لمسافة 4 أضعاف طول اللاعب لكل منهما']},
        {'key': 'backward_three_turns_fs4', 'name_ar': 'Three Turns خلفية (خارجية وداخلية)',
         'name_en': 'Backward Outside and Backward Inside Three Turns',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['أربعة Three Turns خلفية (يمنى/يسرى × خارجي/داخلي)، طول الانزلاق ضعف طول اللاعب لكل منها']},
        {'key': 'dance_step_sequence_fs4', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['على المحور الطويل للحلبة؛ لا يجوز عكس النمط — راجع الملحق (Appendix) للرسم الإلزامي']},
    ],
}

ISI_FREESTYLE_5 = {
    'key': 'isi_freestyle_5',
    'name_ar': 'اختبار ISI فريستايل 5', 'name_en': 'ISI Freestyle 5',
    'source_note': _HANDBOOK_SRC.format('44-45'),
    'elements': [
        {'key': 'lutz_jump', 'name_ar': 'قفزة Lutz', 'name_en': 'Lutz Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1lz', 'lutz'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية خلفية + مقدمة النصل؛ دوران للجهة المعاكسة لمنحنى الإقلاع']},
        {'key': 'axel_jump', 'name_ar': 'قفزة Axel', 'name_en': 'Axel Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['1a', 'axel'], 'min_rotations': 1.5,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية أمامية؛ 1.5 دورة؛ الهبوط: حافة خارجية خلفية للقدم المقابلة']},
        {'key': 'camel_spin', 'name_ar': 'دوران Camel', 'name_en': 'Camel Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['csp', 'camel'], 'min_revolutions': 6, 'position': 'camel',
         'criteria_notes_ar': ['الدخول من حافة خارجية أمامية؛ 6 دورات على الأقل منها 4 في وضعية الـ Camel']},
        {'key': 'camel_sit_upright_spin', 'name_ar': 'دوران مركّب Camel-Sit-Upright',
         'name_en': 'Camel-Sit-Upright Spin', 'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 دورات Camel + 3 Sit + 3 Upright بدون تغيير قدم، كل وضعية تستوفي معيارها']},
        {'key': 'fast_back_scratch_spin', 'name_ar': 'دوران Scratch خلفي سريع', 'name_en': 'Fast Back Scratch Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['scratch spin', 'back scratch spin'],
         'min_revolutions': 9,
         'criteria_notes_ar': ['الدخول من حافة داخلية أمامية، اتجاه خلفي خارجي، 9 دورات على الأقل، القدم الحرة متقاطعة أمام القدم المتزلجة في النهاية']},
        {'key': 'fs5_turns_combo', 'name_ar': 'تشكيلة التفافات: Choctaw/Bracket/Twizzle',
         'name_en': 'Choctaw, Bracket, and Twizzle Combination',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['6 التفافات منفصلة: Swing Closed Choctaw، Open Choctaw، Bracket (يمنى ويسرى)، Twizzle أمامي وخلفي']},
        {'key': 'dance_step_sequence_fs5', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي — لا يجوز عكسه — راجع الملحق (Appendix)']},
    ],
}

ISI_FREESTYLE_6 = {
    'key': 'isi_freestyle_6',
    'name_ar': 'اختبار ISI فريستايل 6', 'name_en': 'ISI Freestyle 6',
    'source_note': _HANDBOOK_SRC.format('46-48'),
    'elements': [
        {'key': 'split_jump', 'name_ar': 'قفزة Split', 'name_en': 'Split Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['split jump'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['نصف دورة، زاوية الساقين في الهواء 90° على الأقل (أو Russian split بارتفاع الورك)']},
        {'key': 'split_falling_leaf_jump', 'name_ar': 'قفزة Split Falling Leaf', 'name_en': 'Split Falling Leaf Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['falling leaf', 'split falling leaf'], 'min_rotations': 0.5,
         'criteria_notes_ar': ['انزلاق خلفي على حافة خارجية، وثبة بنصف دورة، زاوية الساقين 90° على الأقل']},
        {'key': 'jump_combo_axel_halfloop_flip', 'name_ar': 'تسلسل قفزات: Axel/نصف Loop/Flip',
         'name_en': 'Jump Combination: Axel/One-Half Loop/Flip Jump',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 قفزات بالترتيب المحدد بدون خطوات إضافية بينها']},
        {'key': 'double_salchow_jump', 'name_ar': 'قفزة Double Salchow', 'name_en': 'Double Salchow Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['2s', 'double salchow'], 'min_rotations': 2.0,
         'criteria_notes_ar': ['الإقلاع: حافة داخلية خلفية؛ دورتان؛ الهبوط: حافة خارجية خلفية للقدم الأخرى']},
        {'key': 'fs6_spin_choice', 'name_ar': 'دوران Cross-Foot أو Layback أو Sit-Change-Sit (اختياري)',
         'name_en': 'Cross-Foot, Layback, or Sit-Change-Sit Spin (Choice of One)',
         'category': CATEGORY_SPIN, 'match_codes': ['cross-foot', 'layback', 'sit-change-sit'],
         'min_revolutions': 6,
         'criteria_notes_ar': ['Cross-Foot/Layback: 6 دورات على الأقل؛ Sit-Change-Sit: 3+3+3 = 9 دورات على الأقل']},
        {'key': 'spin_combo_3positions_changefoot', 'name_ar': 'دوران مركّب من 3 وضعيات مع تغيير قدم',
         'name_en': 'Spin Combination with 3 Positions and Change of Foot',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 وضعيات مختلفة من: Sit/Back Sit/Camel/Back Camel/Layback — 3 دورات لكل وضعية على الأقل، وتغيير قدم واحد']},
        {'key': 'fs6_turns_combo', 'name_ar': 'تشكيلة التفافات: Rocker/Counter/Loop',
         'name_en': 'Rocker, Counter, and Loop Combination', 'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['4 التفافات منفصلة: Outside Rocker، Inside Counter، Inside Loop (يمنى ويسرى)']},
        {'key': 'dance_step_sequence_fs6', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي — لا يجوز عكسه — راجع الملحق (Appendix)']},
    ],
}

ISI_FREESTYLE_7 = {
    'key': 'isi_freestyle_7',
    'name_ar': 'اختبار ISI فريستايل 7', 'name_en': 'ISI Freestyle 7',
    'source_note': _HANDBOOK_SRC.format('48-50'),
    'elements': [
        {'key': 'double_toe_loop_or_walley', 'name_ar': 'قفزة Double Toe Loop أو Double Toe Walley (اختياري)',
         'name_en': 'Double Toe Loop or Double Toe Walley Jump (Choice of One)',
         'category': CATEGORY_JUMP, 'match_codes': ['2t', 'double toe loop', 'double toe walley'],
         'min_rotations': 2.0,
         'criteria_notes_ar': ['دورتان في الهواء؛ الهبوط: حافة خارجية خلفية لنفس القدم']},
        {'key': 'two_walley_jumps_in_a_row', 'name_ar': 'قفزتا Walley متتاليتان', 'name_en': 'Two Walley Jumps in a Row',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['تغيير من الحافة الخارجية للداخلية بدون لمس القدم الأخرى للجليد، ثم تكرار القفزة']},
        {'key': 'combo_spin_changefoot_position', 'name_ar': 'دوران مركّب بتغيير قدم ووضعية',
         'name_en': 'Combination Spin with Change of Foot and Position',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['دوران طائر (flying) بـ4 وضعيات على الأقل وتغيير قدم واحد على الأقل، 3 دورات لكل وضعية']},
        {'key': 'flying_camel_spin', 'name_ar': 'دوران Flying Camel', 'name_en': 'Flying Camel Spin',
         'category': CATEGORY_SPIN, 'match_codes': ['flying camel'], 'min_revolutions': 6, 'position': 'camel',
         'criteria_notes_ar': ['قفزة في الهواء بوضعية شبه أفقية، ثم 6 دورات متواصلة على الأقل في وضعية Camel']},
        {'key': 'jump_seq_onefootaxel_quarterflip_axel', 'name_ar': 'تسلسل قفزات: Axel بقدم واحدة/ربع Flip/Axel',
         'name_en': 'Jump Sequence: One-Foot Axel/One-Quarter Flip/Axel',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 قفزات بالترتيب المحدد بإيقاع متواصل']},
        {'key': 'opposite_jump_fs7', 'name_ar': 'قفزة بالاتجاه المعاكس: Flip أو Loop أو Lutz (اختياري)',
         'name_en': 'Opposite Jump: Flip, Loop, or Lutz (Choice of One)',
         'category': CATEGORY_JUMP, 'match_codes': ['flip', 'loop', 'lutz'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['نفس متطلبات القفزة الأصلية لكن بالاتجاه المعاكس لاتجاه القفز المعتاد للاعب']},
        {'key': 'fs7_turns_combo', 'name_ar': 'تشكيلة التفافات: Counter/Rocker/Twizzle مضاعف',
         'name_en': 'Counter, Rocker, and Double Twizzle Combination',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['5 التفافات منفصلة تشمل Inside Counter (يمنى ويسرى)، Inside Rocker، Twizzle مزدوج، Twizzle 1.5']},
        {'key': 'dance_step_sequence_fs7', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي — لا يجوز عكسه — يُحكَّم هذا المستوى بثلاثة حكّام على الأقل']},
    ],
}

ISI_FREESTYLE_8 = {
    'key': 'isi_freestyle_8',
    'name_ar': 'اختبار ISI فريستايل 8', 'name_en': 'ISI Freestyle 8',
    'source_note': _HANDBOOK_SRC.format('51-53'),
    'elements': [
        {'key': 'double_loop_jump', 'name_ar': 'قفزة Double Loop', 'name_en': 'Double Loop Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['2lo', 'double loop'], 'min_rotations': 2.0,
         'criteria_notes_ar': ['الإقلاع: حافة خارجية خلفية؛ دورتان؛ الهبوط: نفس القدم ونفس الحافة']},
        {'key': 'double_flip_jump', 'name_ar': 'قفزة Double Flip', 'name_en': 'Double Flip Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['2f', 'double flip'], 'min_rotations': 2.0,
         'criteria_notes_ar': ['الإقلاع: حافة داخلية خلفية + مقدمة النصل؛ دورتان؛ الهبوط: حافة خارجية خلفية للقدم الأخرى']},
        {'key': 'split_lutz_jump', 'name_ar': 'قفزة Split Lutz', 'name_en': 'Split Lutz Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['split lutz'], 'min_rotations': 1.0,
         'criteria_notes_ar': ['دورة واحدة، زاوية الساقين في الهواء 90° على الأقل']},
        {'key': 'flying_sit_or_axel_sit_spin', 'name_ar': 'دوران Flying Sit أو Axel Sit (اختياري)',
         'name_en': 'Flying Sit Spin or Axel Sit Spin (Choice of One)',
         'category': CATEGORY_SPIN, 'match_codes': ['flying sit spin', 'axel sit spin', 'open axel sit spin'],
         'min_revolutions': 6, 'position': 'sit',
         'criteria_notes_ar': ['قفزة إقلاع بدوران في الهواء، ثم 6 دورات متواصلة على الأقل في وضعية Sit']},
        {'key': 'jump_seq_flip125_flip125_dsalchow', 'name_ar': 'تسلسل قفزات: Flip 1.25/Flip 1.25/Double Salchow',
         'name_en': 'Jump Sequence: One and One-Quarter Flip/One and One-Quarter Flip/Double Salchow',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 قفزات بالترتيب المحدد بدون دفعات أو خطوات إضافية']},
        {'key': 'camel_jump_camel_spin', 'name_ar': 'دوران Camel-Jump-Camel', 'name_en': 'Camel-Jump-Camel Spin',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['4 دورات Camel، ثم قفزة للقدم الأخرى مع البقاء بوضعية Camel، ثم 4 دورات إضافية على الأقل']},
        {'key': 'fs8_turns_combo', 'name_ar': 'تشكيلة التفافات: Bracket/Twizzle/Loop',
         'name_en': 'Bracket, Twizzle, and Loop Combination', 'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['4 التفافات منفصلة: Inside Bracket، Outside Twizzle (يمنى ويسرى)، Outside Loop']},
        {'key': 'dance_step_sequence_fs8', 'name_ar': 'تسلسل خطوات Dance', 'name_en': 'Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي — يُحكَّم بثلاثة حكّام مختارين من ISI، ويُصوَّر ويُرسَل لمقر ISI للتحكيم إن لم يتوفر حكّام محليون']},
    ],
}

ISI_FREESTYLE_9 = {
    'key': 'isi_freestyle_9',
    'name_ar': 'اختبار ISI فريستايل 9', 'name_en': 'ISI Freestyle 9',
    'source_note': _HANDBOOK_SRC.format('53-55'),
    'elements': [
        {'key': 'opposite_spin_fs9', 'name_ar': 'دوران بالاتجاه المعاكس: Sit أو Camel أو Layback (اختياري)',
         'name_en': 'Opposite Spin: Sit, Camel, or Layback (Choice of One)',
         'category': CATEGORY_SPIN, 'match_codes': ['sit', 'camel', 'layback'], 'min_revolutions': 4,
         'criteria_notes_ar': ['4 دورات على الأقل بالاتجاه المعاكس لاتجاه دوران اللاعب المعتاد']},
        {'key': 'double_lutz_jump', 'name_ar': 'قفزة Double Lutz', 'name_en': 'Double Lutz Jump',
         'category': CATEGORY_JUMP, 'match_codes': ['2lz', 'double lutz'], 'min_rotations': 2.0,
         'criteria_notes_ar': ['دورتان بالاتجاه المعاكس لمنحنى الإقلاع؛ الهبوط: حافة خارجية خلفية لنفس القدم']},
        {'key': 'axel_double_loop_combo', 'name_ar': 'تسلسل: Axel/Double Loop', 'name_en': 'Axel-Double Loop Jump Combination',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['قفزتان بالترتيب المحدد بدون خطوات أو دورات بينهما']},
        {'key': 'axel_opposite_or_double_axel', 'name_ar': 'Axel بالاتجاه المعاكس أو Double Axel (اختياري)',
         'name_en': 'Axel Jump in Opposite Direction or Double Axel Jump (Choice of One)',
         'category': CATEGORY_JUMP, 'match_codes': ['axel', '2a', 'double axel'], 'min_rotations': 1.5,
         'criteria_notes_ar': ['Axel بالاتجاه المعاكس (1.5 دورة) أو Double Axel (2.5 دورة)؛ الهبوط: حافة خارجية خلفية للقدم المقابلة']},
        {'key': 'jump_combo_rocker_toe_doubleloop', 'name_ar': 'تسلسل: Rocker أو Counter/قفزة مساعدة بالمقدمة/Double Loop',
         'name_en': 'Jump Combination: Rocker or Counter Jump/Double Toe Assisted Jump/Double Loop',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 عناصر بالترتيب المحدد بدون خطوات بينها']},
        {'key': 'flying_camel_into_jump_sit_spin', 'name_ar': 'دوران Flying Camel إلى Jump Sit',
         'name_en': 'Flying Camel Spin into a Jump Sit Spin', 'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['قفزة إقلاع بوضعية Camel، ثم قفزة أخرى للانتقال لوضعية Sit، بـ4 دورات لكل وضعية على الأقل']},
        {'key': 'dance_step_sequence_fs9', 'name_ar': 'تسلسل خطوات Dance — نمط خط مستقيم',
         'name_en': 'Dance Step Sequence - Straight Line Pattern', 'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['نمط إلزامي — لا يجوز عكسه — يُحكَّم بثلاثة حكّام مختارين من ISI']},
    ],
}

ISI_FREESTYLE_10 = {
    'key': 'isi_freestyle_10',
    'name_ar': 'اختبار ISI فريستايل 10', 'name_en': 'ISI Freestyle 10',
    'source_note': _HANDBOOK_SRC.format('55-57'),
    'elements': [
        {'key': 'double_axel_double_toeloop_combo', 'name_ar': 'تسلسل: Double Axel/Double Toe Loop',
         'name_en': 'Double Axel/Double Toe Loop Jump Combination',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['قفزتان بالترتيب المحدد بدون خطوات أو دورات بينهما']},
        {'key': 'triple_edge_jump', 'name_ar': 'قفزة Triple (اختيار اللاعب)', 'name_en': 'Triple Edge Jump (Skater\'s Choice)',
         'category': CATEGORY_JUMP, 'match_codes': ['triple', '3lo', '3s', '3t', '3f', '3lz'], 'min_rotations': 3.0,
         'criteria_notes_ar': ['3 دورات على حافة متحركة، الهبوط على حافة قدم واحدة']},
        {'key': 'death_drop', 'name_ar': 'Death Drop', 'name_en': 'Death Drop',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['قفزة أفقية شبه بدورة واحدة على الأقل، ثم سقوط للقدم الأخرى في دوران Back Sit لـ6 دورات على الأقل']},
        {'key': 'four_axels_or_triple_toe_assisted', 'name_ar': '4 Axel متتالية أو قفزة مساعدة ثلاثية (اختياري)',
         'name_en': 'Four Alternating Axels in a Row or Triple Toe Assisted Jump (Choice of One)',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['4 قفزات Axel بالتناوب بحد أقصى خطوتين بينها، أو قفزة ثلاثية واحدة مساعدة بالمقدمة']},
        {'key': 'double_jumps_or_triple_toe_double_loop', 'name_ar': 'قفزتان مزدوجتان (يمين ويسار) أو تسلسل ثلاثي/مزدوج (اختياري)',
         'name_en': 'Double Jump Right and Left or Triple Toe Assisted/Double Loop Combination (Choice of One)',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['قفزتان مزدوجتان لكل اتجاه (غير متتاليتين)، أو تسلسل قفزة ثلاثية ثم Double Loop بدون خطوات بينهما']},
        {'key': 'arabian_cartwheel_or_butterfly', 'name_ar': '3 Arabian Cartwheel أو Butterfly متتالية (اختياري)',
         'name_en': 'Three Arabian Cartwheels or Butterfly Jumps in a Row (Choice of One)',
         'category': CATEGORY_POSITION, 'match_codes': [],
         'criteria_notes_ar': ['3 قفزات بحد أقصى 3 دفعات بين كل قفزتين']},
        {'key': 'creative_dance_step_sequence', 'name_ar': 'تسلسل خطوات إبداعي', 'name_en': 'Creative Dance Step Sequence',
         'category': CATEGORY_SEQUENCE, 'match_codes': [],
         'criteria_notes_ar': ['تصميم خاص باللاعب يغطي كامل مساحة الحلبة؛ يُحكَّم بخمسة حكّام مختارين من ISI (يكفي اجتياز 3 منهم)']},
    ],
}

# ── Seed standard, grounded in Module 3 "Jump & Spin Technique Library" —
# the ISU-side technical breakdown (entry/takeoff/landing + root-cause
# correction) we already extracted for these three jumps. Unlike the ISI
# basic-skills levels above, these ARE rotation-based jumps our engine
# classifies, so they carry real match_codes/min_rotations for automatic
# evaluation, not just manual review.
ISU_JUMP_BASICS = {
    'key': 'isu_jump_basics',
    'name_ar': 'معايير عناصر ISU الأساسية — القفزات',
    'name_en': 'ISU Basic Jump Elements',
    'source_note': 'مستخرج من Module 3 (Jump & Spin Technique Library) — Figure Skating Coach Ready™',
    'federation': FEDERATION_ISU,
    'elements': [
        {
            'key': 'waltz_jump', 'name_ar': 'قفزة Waltz', 'name_en': 'Waltz Jump',
            'category': CATEGORY_JUMP, 'match_codes': ['1A', 'waltz', 'axel'],
            'min_rotations': 0.5,
            'criteria_notes_ar': [
                'الدخول: حافة خارجية أمامية، قوس حقيقي وليس خطاً مستقيماً',
                'الإقلاع: الركبة تنثني ثم تمتد الساق مع تأرجح الساق الحرة للأمام وللأعلى',
                'الهبوط: حافة خارجية خلفية للقدم المقابلة، الركبة منثنية لامتصاص الصدمة',
            ],
        },
        {
            'key': 'toe_loop', 'name_ar': 'قفزة Toe Loop', 'name_en': 'Toe Loop',
            'category': CATEGORY_JUMP, 'match_codes': ['1T', '2T', '3T', 'toe loop', 'toeloop'],
            'min_rotations': 1.0,
            'criteria_notes_ar': [
                'الدخول: حافة خارجية خلفية بقوس حقيقي',
                'وضع المقدمة خلف الجسم مباشرة، بزاوية 45 درجة تقريباً',
                'تأرجح الساق الحرة اليمنى للأمام وعبر الجسم يولّد الزخم الدوراني',
                'الهبوط: نفس الحافة الخارجية الخلفية التي بدأت منها القفزة',
            ],
        },
        {
            'key': 'salchow', 'name_ar': 'قفزة Salchow', 'name_en': 'Salchow',
            'category': CATEGORY_JUMP, 'match_codes': ['1S', '2S', '3S', 'salchow'],
            'min_rotations': 1.0,
            'criteria_notes_ar': [
                'الدخول: حافة داخلية خلفية، بدون مساعدة مقدمة النصل',
                'انثناء عميق للركبة ثم امتداد كامل للساق يدفع الجسم للأعلى',
                'الساق الحرة تتأرجح من خلف الجسم إلى أمامه وعبره',
                'الخروج: من الحافة الداخلية لنصل القدم اليسرى',
            ],
        },
    ],
}

_SEED_STANDARDS = [
    (ISI_PRE_ALPHA, FEDERATION_ISI), (ISI_ALPHA, FEDERATION_ISI), (ISI_BETA, FEDERATION_ISI),
    (ISI_GAMMA, FEDERATION_ISI), (ISI_DELTA, FEDERATION_ISI),
    (ISI_FREESTYLE_1, FEDERATION_ISI), (ISI_FREESTYLE_2, FEDERATION_ISI), (ISI_FREESTYLE_3, FEDERATION_ISI),
    (ISI_FREESTYLE_4, FEDERATION_ISI), (ISI_FREESTYLE_5, FEDERATION_ISI), (ISI_FREESTYLE_6, FEDERATION_ISI),
    (ISI_FREESTYLE_7, FEDERATION_ISI), (ISI_FREESTYLE_8, FEDERATION_ISI), (ISI_FREESTYLE_9, FEDERATION_ISI),
    (ISI_FREESTYLE_10, FEDERATION_ISI),
    (ISU_JUMP_BASICS, FEDERATION_ISU),
]


def ensure_seed_standards() -> None:
    """Insert seeded standards that don't exist yet, and keep existing seeded rows
    in sync with the latest extracted data (so a corrected/expanded seed — e.g.
    switching from video-derived data to the official ISI Handbook text —
    reaches databases that were already seeded with the older version).
    Coach-added custom standards (keys not in _SEED_STANDARDS) are never touched."""
    conn = _conn()
    for std, federation in _SEED_STANDARDS:
        cur = conn.execute("SELECT COUNT(*) FROM test_standards WHERE key=?", (std['key'],))
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO test_standards (key, name_ar, name_en, source_note, elements_json, federation, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    std['key'], std['name_ar'], std['name_en'], std['source_note'],
                    json.dumps(std['elements'], ensure_ascii=False), federation,
                    datetime.now().strftime('%Y-%m-%d %H:%M'),
                ),
            )
        else:
            conn.execute(
                "UPDATE test_standards SET name_ar=?, name_en=?, source_note=?, elements_json=?, federation=? "
                "WHERE key=?",
                (
                    std['name_ar'], std['name_en'], std['source_note'],
                    json.dumps(std['elements'], ensure_ascii=False), federation, std['key'],
                ),
            )
    conn.commit()
    conn.close()


def list_standards(federation: Optional[str] = None) -> List[Dict]:
    ensure_seed_standards()
    conn = _conn()
    if federation:
        rows = conn.execute(
            "SELECT id, key, name_ar, name_en, source_note, elements_json, federation, created_at "
            "FROM test_standards WHERE federation=? ORDER BY id", (federation,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, key, name_ar, name_en, source_note, elements_json, federation, created_at "
            "FROM test_standards ORDER BY id"
        ).fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append({
            'id': r[0], 'key': r[1], 'name_ar': r[2], 'name_en': r[3],
            'source_note': r[4], 'elements': json.loads(r[5]),
            'federation': r[6] or FEDERATION_ISI, 'created_at': r[7],
        })
    return out


def get_standard(std_id: int) -> Optional[Dict]:
    for s in list_standards():
        if s['id'] == std_id:
            return s
    return None


def save_standard(name_ar: str, name_en: str, source_note: str, elements: List[Dict],
                   key: Optional[str] = None, federation: str = FEDERATION_ISI) -> None:
    key = key or f"custom_{int(datetime.now().timestamp())}"
    conn = _conn()
    conn.execute(
        "INSERT INTO test_standards (key, name_ar, name_en, source_note, elements_json, federation, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (key, name_ar, name_en, source_note, json.dumps(elements, ensure_ascii=False), federation,
         datetime.now().strftime('%Y-%m-%d %H:%M')),
    )
    conn.commit()
    conn.close()


def delete_standard(std_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM test_standards WHERE id=?", (std_id,))
    conn.commit()
    conn.close()


# ── Reference-video uploads (the "biggest possible library" upload flow) ───────

def save_reference_upload(federation: str, level_name: str, note: str, file_path: str,
                           linked_standard_key: Optional[str] = None) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO reference_video_uploads (federation, level_name, note, file_path, "
        "linked_standard_key, uploaded_at) VALUES (?,?,?,?,?,?)",
        (federation, level_name, note, file_path, linked_standard_key,
         datetime.now().strftime('%Y-%m-%d %H:%M')),
    )
    conn.commit()
    conn.close()


def list_reference_uploads(federation: Optional[str] = None) -> List[Dict]:
    conn = _conn()
    if federation:
        rows = conn.execute(
            "SELECT id, federation, level_name, note, file_path, linked_standard_key, uploaded_at "
            "FROM reference_video_uploads WHERE federation=? ORDER BY id DESC", (federation,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, federation, level_name, note, file_path, linked_standard_key, uploaded_at "
            "FROM reference_video_uploads ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [
        {'id': r[0], 'federation': r[1], 'level_name': r[2], 'note': r[3],
         'file_path': r[4], 'linked_standard_key': r[5], 'uploaded_at': r[6]}
        for r in rows
    ]


# ── Evaluation history (feeds the model-training data hub) ─────────────────────

def _json_default(o):
    """Fallback for json.dumps: report/results dicts here are built from video
    analysis output, which can carry numpy scalar types (numpy.bool_,
    numpy.float64, ...) that json can't serialize natively — coerce them to
    plain Python types instead of crashing the whole page over a stray type."""
    if hasattr(o, 'item'):  # numpy scalar (bool_, float64, int64, ...)
        return o.item()
    return str(o)


def save_evaluation(federation: str, standard: Dict, report: Dict,
                     player_name: str = '', video_note: str = '') -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO standard_evaluations (federation, standard_key, standard_name, player_name, "
        "video_note, passed, report_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (federation, standard.get('key', ''), standard.get('name_ar', ''), player_name, video_note,
         1 if report.get('passed') else 0, json.dumps(report, ensure_ascii=False, default=_json_default),
         datetime.now().strftime('%Y-%m-%d %H:%M')),
    )
    conn.commit()
    conn.close()


def list_evaluations(federation: Optional[str] = None) -> List[Dict]:
    conn = _conn()
    if federation:
        rows = conn.execute(
            "SELECT id, federation, standard_key, standard_name, player_name, video_note, "
            "passed, report_json, created_at FROM standard_evaluations WHERE federation=? "
            "ORDER BY id DESC", (federation,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, federation, standard_key, standard_name, player_name, video_note, "
            "passed, report_json, created_at FROM standard_evaluations ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [
        {'id': r[0], 'federation': r[1], 'standard_key': r[2], 'standard_name': r[3],
         'player_name': r[4], 'video_note': r[5], 'passed': bool(r[6]),
         'report': json.loads(r[7]), 'created_at': r[8]}
        for r in rows
    ]


def export_training_dataset() -> Dict:
    """يجمع كل المعايير والتقييمات المحفوظة في حزمة واحدة — أساس أي تدريب مستقبلي للنموذج."""
    return {
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'standards': list_standards(),
        'evaluations': list_evaluations(),
        'reference_uploads': list_reference_uploads(),
    }


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


def suggest_standard(results: Dict, standards: List[Dict]) -> Optional[Dict]:
    """يقترح أنسب معيار مرجعي لنتائج فيديو مُحلَّل، بمقارنة العناصر المكتشفة فعلياً
    (قفزات/دورانات) بفئات عناصر كل معيار — لمنع اختيار معيار غير مناسب (كمقارنة
    فيديو مستوى أساسي بلا قفزات مقابل معيار Freestyle الذي يتطلبها)."""
    if not standards:
        return None

    n_jumps = len(results.get('jumps', []))
    n_spins = len(results.get('spins', []))
    has_rotational_elements = n_jumps > 0 or n_spins > 0

    def score(std: Dict) -> float:
        cats = [el['category'] for el in std['elements']]
        n_jump_els = cats.count(CATEGORY_JUMP)
        n_spin_els = cats.count(CATEGORY_SPIN)
        n_position_els = cats.count(CATEGORY_POSITION)
        std_needs_rotation = (n_jump_els + n_spin_els) > 0

        if has_rotational_elements and std_needs_rotation:
            # More matched jump/spin elements against what this standard needs = better fit.
            matched_jumps = sum(1 for el in std['elements'] if el['category'] == CATEGORY_JUMP
                                 and _match_jump(el, results.get('jumps', [])))
            matched_spins = sum(1 for el in std['elements'] if el['category'] == CATEGORY_SPIN
                                 and _match_spin(el, results.get('spins', [])))
            return 10 + matched_jumps * 2 + matched_spins * 2
        if not has_rotational_elements and not std_needs_rotation:
            # No rotation detected in the video, and this standard is pure basic-skills
            # (glides/edges/turns) — with no other signal to rank by, default to the
            # earliest/simplest level in the list (standards are ordered Pre-Alpha
            # first) rather than whichever happens to have the most elements.
            return 10.0
        # Mismatch: video has jumps/spins but standard doesn't need them, or vice versa.
        return 0.0

    best = max(standards, key=score)
    return best if score(best) > 0 else standards[0]


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
                # bool(...) matters here: rot/clean can come from numpy comparisons
                # upstream (numpy.bool_, numpy.float64, ...), which json.dumps can't
                # serialize — coerce to native Python types before they reach the DB.
                ok_rot = bool(rot >= min_rot * 0.85)  # small tolerance for measurement noise
                checks.append({'label_ar': f'الدوران ({float(rot):.1f} من {min_rot} مطلوبة)', 'ok': ok_rot})
                clean = bool(matched.get('is_clean', True))
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
                ok_rev = bool(rev >= min_rev * 0.85)
                checks.append({'label_ar': f'عدد الدورات ({float(rev):.1f} من {min_rev} مطلوبة)', 'ok': ok_rev})
                if el.get('position'):
                    detected_pos = str(matched.get('ai_position', '—'))
                    pos_ok = bool(detected_pos.lower() == el['position'])
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
                ok_dur = bool(dur >= min_dur)
                checks.append({'label_ar': f'مدة التسلسل المكتشف ({float(dur):.1f}ث)', 'ok': ok_dur})
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
