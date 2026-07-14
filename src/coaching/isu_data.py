"""
ISU (International Skating Union) Official Data
بيانات الاتحاد الدولي للتزلج على الجليد
Based on ISU Communication 2496 (2024 Scale of Values)
"""

# ─── JUMPS BASE VALUES ───────────────────────────────────────────────
JUMPS = {
    "1T":  {"name": "Single Toe Loop",     "name_ar": "تو لوب مفرد",     "rotations": 1, "bv": 0.4,  "bv_combo": 0.4},
    "2T":  {"name": "Double Toe Loop",     "name_ar": "تو لوب مزدوج",    "rotations": 2, "bv": 1.3,  "bv_combo": 1.3},
    "3T":  {"name": "Triple Toe Loop",     "name_ar": "تو لوب ثلاثي",    "rotations": 3, "bv": 4.2,  "bv_combo": 4.2},
    "4T":  {"name": "Quad Toe Loop",       "name_ar": "تو لوب رباعي",    "rotations": 4, "bv": 9.5,  "bv_combo": 9.5},
    "1S":  {"name": "Single Salchow",      "name_ar": "سالكوف مفرد",     "rotations": 1, "bv": 0.4,  "bv_combo": 0.4},
    "2S":  {"name": "Double Salchow",      "name_ar": "سالكوف مزدوج",    "rotations": 2, "bv": 1.3,  "bv_combo": 1.3},
    "3S":  {"name": "Triple Salchow",      "name_ar": "سالكوف ثلاثي",    "rotations": 3, "bv": 4.3,  "bv_combo": 4.3},
    "4S":  {"name": "Quad Salchow",        "name_ar": "سالكوف رباعي",    "rotations": 4, "bv": 9.7,  "bv_combo": 9.7},
    "1Lo": {"name": "Single Loop",         "name_ar": "لوب مفرد",        "rotations": 1, "bv": 0.5,  "bv_combo": 0.5},
    "2Lo": {"name": "Double Loop",         "name_ar": "لوب مزدوج",       "rotations": 2, "bv": 1.7,  "bv_combo": 1.7},
    "3Lo": {"name": "Triple Loop",         "name_ar": "لوب ثلاثي",       "rotations": 3, "bv": 4.9,  "bv_combo": 4.9},
    "4Lo": {"name": "Quad Loop",           "name_ar": "لوب رباعي",       "rotations": 4, "bv": 10.5, "bv_combo": 10.5},
    "1F":  {"name": "Single Flip",         "name_ar": "فليب مفرد",       "rotations": 1, "bv": 0.5,  "bv_combo": 0.5},
    "2F":  {"name": "Double Flip",         "name_ar": "فليب مزدوج",      "rotations": 2, "bv": 1.8,  "bv_combo": 1.8},
    "3F":  {"name": "Triple Flip",         "name_ar": "فليب ثلاثي",      "rotations": 3, "bv": 5.3,  "bv_combo": 5.3},
    "4F":  {"name": "Quad Flip",           "name_ar": "فليب رباعي",      "rotations": 4, "bv": 11.0, "bv_combo": 11.0},
    "1Lz": {"name": "Single Lutz",         "name_ar": "لوتز مفرد",       "rotations": 1, "bv": 0.6,  "bv_combo": 0.6},
    "2Lz": {"name": "Double Lutz",         "name_ar": "لوتز مزدوج",      "rotations": 2, "bv": 2.1,  "bv_combo": 2.1},
    "3Lz": {"name": "Triple Lutz",         "name_ar": "لوتز ثلاثي",      "rotations": 3, "bv": 5.9,  "bv_combo": 5.9},
    "4Lz": {"name": "Quad Lutz",           "name_ar": "لوتز رباعي",      "rotations": 4, "bv": 11.5, "bv_combo": 11.5},
    "1A":  {"name": "Single Axel",         "name_ar": "أكسل مفرد",       "rotations": 1.5, "bv": 1.1, "bv_combo": 1.1},
    "2A":  {"name": "Double Axel",         "name_ar": "أكسل مزدوج",      "rotations": 2.5, "bv": 3.3, "bv_combo": 3.3},
    "3A":  {"name": "Triple Axel",         "name_ar": "أكسل ثلاثي",      "rotations": 3.5, "bv": 8.0, "bv_combo": 8.0},
    "4A":  {"name": "Quad Axel",           "name_ar": "أكسل رباعي",      "rotations": 4.5, "bv": 12.5, "bv_combo": 12.5},
}

# ─── SPINS BASE VALUES ────────────────────────────────────────────────
SPINS = {
    "SSp1": {"name": "Sit Spin Lv1",           "name_ar": "سبين جلوس مستوى 1",     "bv": 0.7},
    "SSp2": {"name": "Sit Spin Lv2",           "name_ar": "سبين جلوس مستوى 2",     "bv": 1.3},
    "SSp3": {"name": "Sit Spin Lv3",           "name_ar": "سبين جلوس مستوى 3",     "bv": 1.6},
    "SSp4": {"name": "Sit Spin Lv4",           "name_ar": "سبين جلوس مستوى 4",     "bv": 1.9},
    "USp1": {"name": "Upright Spin Lv1",       "name_ar": "سبين واقف مستوى 1",     "bv": 0.6},
    "USp2": {"name": "Upright Spin Lv2",       "name_ar": "سبين واقف مستوى 2",     "bv": 1.0},
    "USp3": {"name": "Upright Spin Lv3",       "name_ar": "سبين واقف مستوى 3",     "bv": 1.2},
    "USp4": {"name": "Upright Spin Lv4",       "name_ar": "سبين واقف مستوى 4",     "bv": 1.5},
    "CSp1": {"name": "Camel Spin Lv1",         "name_ar": "سبين جمل مستوى 1",      "bv": 1.0},
    "CSp2": {"name": "Camel Spin Lv2",         "name_ar": "سبين جمل مستوى 2",      "bv": 1.5},
    "CSp3": {"name": "Camel Spin Lv3",         "name_ar": "سبين جمل مستوى 3",      "bv": 1.9},
    "CSp4": {"name": "Camel Spin Lv4",         "name_ar": "سبين جمل مستوى 4",      "bv": 2.3},
    "CCSp1":{"name": "Change Camel Spin Lv1",  "name_ar": "سبين جمل تبديل مستوى 1","bv": 1.7},
    "CCSp2":{"name": "Change Camel Spin Lv2",  "name_ar": "سبين جمل تبديل مستوى 2","bv": 2.0},
    "CCSp3":{"name": "Change Camel Spin Lv3",  "name_ar": "سبين جمل تبديل مستوى 3","bv": 2.3},
    "CCSp4":{"name": "Change Camel Spin Lv4",  "name_ar": "سبين جمل تبديل مستوى 4","bv": 2.6},
    "CCoSp1":{"name":"Change Combo Spin Lv1",  "name_ar": "سبين مجمع تبديل مستوى 1","bv": 2.5},
    "CCoSp2":{"name":"Change Combo Spin Lv2",  "name_ar": "سبين مجمع تبديل مستوى 2","bv": 3.0},
    "CCoSp3":{"name":"Change Combo Spin Lv3",  "name_ar": "سبين مجمع تبديل مستوى 3","bv": 3.5},
    "CCoSp4":{"name":"Change Combo Spin Lv4",  "name_ar": "سبين مجمع تبديل مستوى 4","bv": 4.0},
    "FCSSp1":{"name":"Flying Sit Spin Lv1",    "name_ar": "سبين طيران جلوس مستوى 1","bv": 1.7},
    "FCSSp2":{"name":"Flying Sit Spin Lv2",    "name_ar": "سبين طيران جلوس مستوى 2","bv": 2.3},
    "FCSSp3":{"name":"Flying Sit Spin Lv3",    "name_ar": "سبين طيران جلوس مستوى 3","bv": 2.6},
    "FCSSp4":{"name":"Flying Sit Spin Lv4",    "name_ar": "سبين طيران جلوس مستوى 4","bv": 3.0},
}

# ─── STEP SEQUENCES ────────────────────────────────────────────────
STEP_SEQUENCES = {
    "StSq1": {"name": "Step Sequence Lv1", "name_ar": "تسلسل خطوات مستوى 1", "bv": 1.8},
    "StSq2": {"name": "Step Sequence Lv2", "name_ar": "تسلسل خطوات مستوى 2", "bv": 2.6},
    "StSq3": {"name": "Step Sequence Lv3", "name_ar": "تسلسل خطوات مستوى 3", "bv": 3.3},
    "StSq4": {"name": "Step Sequence Lv4", "name_ar": "تسلسل خطوات مستوى 4", "bv": 3.9},
    "ChSq1": {"name": "Choreographic Sequence", "name_ar": "تسلسل كوريغرافي", "bv": 3.0},
}

# ─── GOE SCALE ────────────────────────────────────────────────────────
GOE_CRITERIA_JUMPS = {
    "positive": [
        "إقلاع قوي ونظيف وواثق",
        "جودة التنفيذ: الارتفاع العالي، المدى الواسع، السرعة المحافظة عليها",
        "هبوط نظيف على ركبة مستقيمة مع وضع ذراعين متحكم به",
        "حركات ما قبل وما بعد القفزة مرتبطة بالموسيقى",
        "تعبير إبداعي ومتنوع",
        "وضع جميل في الهواء",
        "إقلاع وهبوط بدون مساعدة ثانوية",
    ],
    "negative": [
        "إقلاع ضعيف أو غير واضح",
        "دوران ناقص (Under-rotation)",
        "هبوط مضطرب، مزدوج، أو سقوط",
        "خروج مباشر دون تدفق",
        "هبوط بيد أو يدين على الجليد",
        "خطأ في حافة الإقلاع (Edge error)",
        "توقف أو تغيير في الإيقاع",
    ],
}

GOE_VALUES = {
    -5: -5.0, -4: -4.0, -3: -3.0, -2: -2.0, -1: -1.0,
    0: 0.0,
    1: 1.0, 2: 2.0, 3: 3.0, 4: 4.0, 5: 5.0,
}

# ─── PROGRAM COMPONENTS ────────────────────────────────────────────────
PROGRAM_COMPONENTS = {
    "SK": {
        "name": "Skating Skills",
        "name_ar": "مهارات التزلج",
        "description_ar": "مستوى التزلج بشكل عام: الانزلاق، القوس، دفع الحافة، التوازن، الإيقاع",
        "criteria_ar": [
            "جودة الحافة: عمق ووضوح الحافات الداخلية والخارجية",
            "الانزلاق: السرعة والسلاسة والتدفق",
            "التوازن: الثبات على حافة واحدة لفترات طويلة",
            "توزيع الجليد: استخدام كامل مساحة الحلبة",
            "الإيقاع والتدفق: الربط السلس بين العناصر",
        ]
    },
    "TR": {
        "name": "Transitions",
        "name_ar": "التحولات والربط",
        "description_ar": "التنوع، الصعوبة، والمهارة في الحركات بين العناصر",
        "criteria_ar": [
            "تنوع الخطوات والتحولات بين العناصر",
            "صعوبة الحركات الانتقالية",
            "استمرارية التدفق طوال البرنامج",
            "حركات الذراعين والجسم بين العناصر",
            "وضع الجسم والاتجاهات المتنوعة",
        ]
    },
    "PE": {
        "name": "Performance",
        "name_ar": "الأداء",
        "description_ar": "الاتصال الجسدي والعاطفي مع الموسيقى والجمهور",
        "criteria_ar": [
            "التعبير الجسدي والعاطفي",
            "الاتصال بالجمهور والمحكمين",
            "التسليم والثقة على الجليد",
            "استخدام وضع الجسم لتعزيز الأداء",
            "الاستجابة الفورية للموسيقى",
        ]
    },
    "CO": {
        "name": "Composition",
        "name_ar": "التأليف",
        "description_ar": "البنية المعمارية للبرنامج وتوزيع العناصر",
        "criteria_ar": [
            "الفكرة المركزية وتماسك البرنامج",
            "التنوع في التصميم الكوريغرافي",
            "توازن توزيع العناصر على مساحة الجليد",
            "الاستخدام الذكي للمساحة والاتجاهات",
            "انسجام البرنامج مع الموسيقى",
        ]
    },
    "IN": {
        "name": "Interpretation",
        "name_ar": "التفسير الموسيقي",
        "description_ar": "عمق تفسير الموسيقى وانعكاسها على الحركة",
        "criteria_ar": [
            "تجسيد الطابع والأسلوب الموسيقي",
            "استجابة الجسم لتفاصيل الموسيقى (النبض، الإيقاع، اللحن)",
            "التعبير عن الحالة المزاجية والدراما",
            "التوقيت الدقيق مع النوتات الموسيقية",
            "الأصالة والإبداع في التفسير",
        ]
    },
}

# ─── LEVELS & PROGRESSION ────────────────────────────────────────────
LEVEL_PROGRESSION = {
    "Alpha": {
        "name_ar": "ألفا (المبتدئ)",
        "description_ar": "المستوى الأول - تعلم الأساسيات",
        "required_jumps": ["1T", "1S"],
        "required_spins": ["USp1"],
        "skills_ar": [
            "المشي والانزلاق للأمام",
            "التوقف (Two-foot stop)",
            "الانزلاق للخلف",
            "السقوط الآمن والنهوض",
            "الدوران الأولي",
        ],
        "target_competition": "محلي/نادي",
    },
    "Beta": {
        "name_ar": "بيتا",
        "description_ar": "المستوى الثاني - تطوير الأساسيات",
        "required_jumps": ["1T", "1S", "1Lo"],
        "required_spins": ["USp1", "SSp1"],
        "skills_ar": [
            "الانزلاق بالحافتين",
            "Crossovers للأمام والخلف",
            "Snowplow stop",
            "Waltz jump",
            "Two-foot spin",
        ],
        "target_competition": "محلي/إقليمي",
    },
    "Gamma": {
        "name_ar": "غاما",
        "description_ar": "المستوى الثالث - تقنيات متوسطة",
        "required_jumps": ["1A", "2T", "2S"],
        "required_spins": ["SSp2", "CSp1"],
        "skills_ar": [
            "Axel مفرد",
            "القفزات المزدوجة الأساسية",
            "Sit spin",
            "Camel spin",
            "Step sequences أساسية",
        ],
        "target_competition": "إقليمي/وطني",
    },
    "Delta": {
        "name_ar": "دلتا",
        "description_ar": "المستوى الرابع - تقنيات متقدمة",
        "required_jumps": ["2A", "3T", "3S", "3Lo"],
        "required_spins": ["CSp3", "CCSp2", "SSp3"],
        "skills_ar": [
            "كل القفزات المزدوجة",
            "البدء بالقفزات الثلاثية",
            "Combination spins",
            "Step sequences معقدة",
            "Flying spins",
        ],
        "target_competition": "وطني/دولي",
    },
    "Pre-Free": {
        "name_ar": "قبل البطولي",
        "description_ar": "مستوى ما قبل البطولة الدولية",
        "required_jumps": ["3A", "3Lz", "3F", "3T+3T"],
        "required_spins": ["CCoSp4", "CCSp4", "FCSSp3"],
        "skills_ar": [
            "أكسل ثلاثي",
            "تجميعات قفزات ثلاثية",
            "Combination spins مستوى 4",
            "Step sequences مستوى 3-4",
        ],
        "target_competition": "بطولات دولية جونيور",
    },
    "Free Skate 1": {
        "name_ar": "البطولي 1",
        "description_ar": "مستوى البطولات الدولية السينيور",
        "required_jumps": ["4T أو 4S", "3A", "3Lz+3T"],
        "required_spins": ["CCoSp4", "CCSp4", "FCSSp4"],
        "skills_ar": [
            "قفزة رباعية واحدة",
            "جميع القفزات الثلاثية",
            "Combination spins مستوى 4",
            "Step sequences مستوى 4",
        ],
        "target_competition": "Grand Prix / بطولات عالمية",
    },
}

# ─── ISU JUDGING RULES SUMMARY ────────────────────────────────────────
JUDGING_RULES = {
    "short_program": {
        "name_ar": "البرنامج القصير",
        "duration_ar": "2 دقيقة و50 ثانية (±10 ثوانٍ)",
        "elements_ar": [
            "قفزة واحدة Axel (2A أو 3A)",
            "قفزة واحدة من مجموعة محددة (Lutz/Flip/Loop)",
            "تجميعة قفزات 3+3 أو 3+2",
            "Spin واقف (Level 3 أو 4)",
            "Spin جلوس (Level 3 أو 4)",
            "Spin مجمع (Level 3 أو 4)",
            "Step Sequence (Level 3 أو 4)",
        ],
        "scoring_ar": "TES (نقاط العناصر التقنية) + PCS × 1.0",
    },
    "free_skate": {
        "name_ar": "البرنامج الحر",
        "duration_ar": "4 دقائق (±10 ثوانٍ) للسيدات / 4.5 دقائق للرجال",
        "elements_ar": [
            "7 قفزات (بما فيها Axel واحد على الأقل)",
            "3 Spins (واقف، جلوس، مجمع)",
            "Step Sequence واحد",
            "Choreographic Sequence واحد (اختياري)",
            "القفزات في النصف الثاني تحصل على زيادة 10% في القيمة الأساسية",
        ],
        "scoring_ar": "TES (نقاط العناصر التقنية) + PCS × 2.0",
    },
    "under_rotation": {
        "name_ar": "الدوران الناقص",
        "rules_ar": [
            "q: نقص أقل من ¼ دورة - قيمة GOE تُخفض",
            "<: نقص من ¼ إلى ½ دورة - تُخفض القيمة الأساسية 70%",
            "<<: نقص أكثر من ½ دورة - تُعامل كقفزة أقل دورة",
        ]
    },
    "deductions": {
        "name_ar": "الخصومات",
        "rules_ar": [
            "السقوط: -1.0 نقطة لكل سقوط (حد أقصى -5.0)",
            "تجاوز الوقت: -1.0 لكل 5 ثوانٍ زيادة",
            "عناصر محظورة: -2.0 نقطة",
            "موسيقى بكلمات (في بعض المسابقات): -1.0",
        ]
    }
}

# ─── COMMON INJURIES & PREVENTION ────────────────────────────────────
INJURY_PREVENTION = {
    "common_injuries_ar": [
        "إجهاد الكاحل والقدم",
        "آلام الركبة (وتر الرباط الجانبي)",
        "آلام أسفل الظهر",
        "إصابات الورك (Hip flexor strain)",
        "كسر الإجهاد في الساق",
        "آلام الكتف من السقوط",
    ],
    "prevention_ar": [
        "إحماء شامل 15-20 دقيقة قبل كل تدريب",
        "تمارين تقوية العضلات المستهدفة يومياً",
        "تمدد ما بعد التدريب 10-15 دقيقة",
        "ارتداء ملابس دافئة لحماية العضلات",
        "الراحة الكافية وعدم الإفراط في التدريب",
        "الوقوف الصحيح داخل الحذاء",
    ]
}
