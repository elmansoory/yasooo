"""
Training Program Generator - مولّد برامج التدريب
Generates comprehensive on-ice, off-ice, and drill programs
based on ISU standards and athlete level
"""

from src.coaching.isu_data import JUMPS, SPINS, LEVEL_PROGRESSION

# ─── OFF-ICE EXERCISES DATABASE ─────────────────────────────────────
OFF_ICE_EXERCISES = {
    "strength": [
        {
            "name_ar": "القرفصاء (Squat)",
            "sets": "4", "reps": "12-15",
            "target_ar": "الفخذ، الأرداف، الأمبول",
            "skating_benefit_ar": "قوة الإقلاع في القفزات",
            "technique_ar": "ظهر مستقيم، ركبة لا تتجاوز أصابع القدم",
        },
        {
            "name_ar": "القرفصاء على ساق واحدة (Single-leg Squat)",
            "sets": "3", "reps": "10 لكل ساق",
            "target_ar": "الفخذ، التوازن، الثبات",
            "skating_benefit_ar": "التوازن على حافة واحدة، هبوط القفزات",
            "technique_ar": "ابقِ الحوض مستوياً، الركبة في اتجاه أصابع القدم",
        },
        {
            "name_ar": "التمرين البلغاري (Bulgarian Split Squat)",
            "sets": "3", "reps": "10-12 لكل ساق",
            "target_ar": "الفخذ الأمامي والخلفي، الأرداف",
            "skating_benefit_ar": "قوة الإقلاع، مرونة الورك",
            "technique_ar": "القدم الخلفية على مقعد، الجذع منتصب",
        },
        {
            "name_ar": "رفع الساق الخلفية (Glute Bridge)",
            "sets": "3", "reps": "15-20",
            "target_ar": "الأرداف، أسفل الظهر",
            "skating_benefit_ar": "قوة دفع الجليد، استقرار الجذع",
            "technique_ar": "ارفع الحوض حتى يصبح الجسم خطاً مستقيماً",
        },
        {
            "name_ar": "الرفع الأمامي للساق (Leg Raise)",
            "sets": "3", "reps": "15",
            "target_ar": "عضلات البطن، الورك",
            "skating_benefit_ar": "التحكم في وضع الجسم أثناء الدوران",
            "technique_ar": "أسفل الظهر ملتصق بالأرض طوال الوقت",
        },
        {
            "name_ar": "بلانك جانبي (Side Plank)",
            "sets": "3", "reps": "30-60 ثانية لكل جانب",
            "target_ar": "العضلات الجانبية، الثبات",
            "skating_benefit_ar": "استقرار الجذع على الحافات الجانبية",
            "technique_ar": "الجسم خط مستقيم من الرأس للقدمين",
        },
        {
            "name_ar": "القفز على صندوق (Box Jump)",
            "sets": "4", "reps": "8-10",
            "target_ar": "الفخذ، السمانة، الانفجارية",
            "skating_benefit_ar": "الانفجارية في الإقلاع، ارتفاع القفزات",
            "technique_ar": "هبوط ناعم على الأصابع، ركبة مثنية",
        },
        {
            "name_ar": "القفز الرأسي (Vertical Jump)",
            "sets": "4", "reps": "8",
            "target_ar": "القوة الانفجارية الكاملة",
            "skating_benefit_ar": "الارتفاع في القفزات التنافسية",
            "technique_ar": "استخدم الذراعين للمساعدة في الانطلاق",
        },
    ],
    "flexibility": [
        {
            "name_ar": "تمدد الإشبيغات (Split)",
            "duration_ar": "60-90 ثانية لكل جانب",
            "target_ar": "عضلات الفخذ الداخلية والخارجية، الورك",
            "skating_benefit_ar": "مرونة الوضعيات، جودة Spiral وLayback",
            "technique_ar": "تقدم تدريجياً، لا تتجاوز حد الألم",
        },
        {
            "name_ar": "تمدد الورك الأمامي (Hip Flexor Stretch)",
            "duration_ar": "45-60 ثانية لكل جانب",
            "target_ar": "عضلات الورك الأمامية",
            "skating_benefit_ar": "الوضعية المفتوحة في القفزات والسبينات",
            "technique_ar": "ركبة أمامية فوق الكعب، حوض للأمام",
        },
        {
            "name_ar": "تمدد الساق الخلفية (Hamstring Stretch)",
            "duration_ar": "45-60 ثانية",
            "target_ar": "عضلات الفخذ الخلفية",
            "skating_benefit_ar": "مرونة الساق الحرة، وضع اللف",
            "technique_ar": "ظهر مستقيم، انثنِ من الورك لا من الظهر",
        },
        {
            "name_ar": "تمدد العقرب (Scorpion Stretch)",
            "duration_ar": "30 ثانية × 3",
            "target_ar": "الظهر، الأرداف، الفخذ",
            "skating_benefit_ar": "تحسين Biellmann spin وLayback",
            "technique_ar": "أمسك بقدمك من الخلف، ارفع تدريجياً",
        },
        {
            "name_ar": "تمدد الكتف والذراع",
            "duration_ar": "30 ثانية لكل ذراع",
            "target_ar": "عضلات الكتف، المرونة العلوية",
            "skating_benefit_ar": "وضعية الذراعين في السبين والقفزات",
            "technique_ar": "اشد الذراع عبر الصدر أو من الخلف",
        },
        {
            "name_ar": "تمدد الظهر (Back Arch)",
            "duration_ar": "30-45 ثانية",
            "target_ar": "الظهر والصدر",
            "skating_benefit_ar": "الانحناء للخلف، Layback spin",
            "technique_ar": "ابدأ بوضع Cobra على الأرض، تقدم تدريجياً",
        },
    ],
    "cardio": [
        {
            "name_ar": "الركض المتقطع (HIIT)",
            "duration_ar": "20-30 دقيقة",
            "protocol_ar": "30 ثانية جري سريع + 30 ثانية مشي × 15 مرة",
            "skating_benefit_ar": "التحمل خلال البرنامج الحر (4 دقائق)",
        },
        {
            "name_ar": "الدراجة الثابتة",
            "duration_ar": "30-45 دقيقة",
            "protocol_ar": "متوسطة الشدة، نبض القلب 140-160",
            "skating_benefit_ar": "اللياقة الأساسية دون إجهاد المفاصل",
        },
        {
            "name_ar": "تمارين plyometric",
            "duration_ar": "20 دقيقة",
            "protocol_ar": "قفز على حبل، side-to-side jumps، bounding",
            "skating_benefit_ar": "الانفجارية والتحمل العضلي",
        },
        {
            "name_ar": "السباحة",
            "duration_ar": "30-45 دقيقة",
            "protocol_ar": "ألواح متنوعة، تنفس منتظم",
            "skating_benefit_ar": "الكارديو دون ضغط على المفاصل، تقوية الظهر",
        },
        {
            "name_ar": "الجمباز والحبل",
            "duration_ar": "15-20 دقيقة",
            "protocol_ar": "10 دقائق حبل + 5 دقائق جمباز",
            "skating_benefit_ar": "التحمل، التنسيق، التوازن",
        },
    ],
    "balance_coordination": [
        {
            "name_ar": "الوقوف على ألواح التوازن (Balance Board)",
            "duration_ar": "5-10 دقائق",
            "target_ar": "الكاحل، الثبات الأساسي",
            "skating_benefit_ar": "الثبات على الحافة الواحدة",
        },
        {
            "name_ar": "تمارين الدوران خارج الجليد",
            "duration_ar": "10-15 دقيقة",
            "target_ar": "الدوران، التوجيه الفراغي",
            "skating_benefit_ar": "تحسين الدوران في القفزات والسبينات",
        },
        {
            "name_ar": "التوازن على ساق واحدة مع الحركة",
            "duration_ar": "5 دقائق لكل ساق",
            "target_ar": "التوازن، قوة الكاحل",
            "skating_benefit_ar": "هبوط القفزات، الثبات على حافة واحدة",
        },
        {
            "name_ar": "تمارين حبال الاتزان (TRX)",
            "duration_ar": "15-20 دقيقة",
            "target_ar": "الجذع، التوازن الكلي",
            "skating_benefit_ar": "الثبات الأساسي طوال البرنامج",
        },
    ],
    "mental": [
        {
            "name_ar": "التخيل الذهني (Visualization)",
            "duration_ar": "10-15 دقيقة",
            "technique_ar": "تخيل تنفيذ البرنامج كاملاً بكل تفاصيله بنجاح تام",
            "skating_benefit_ar": "بناء الثقة، تقليل القلق التنافسي",
        },
        {
            "name_ar": "التنفس العميق والتأمل",
            "duration_ar": "5-10 دقائق",
            "technique_ar": "شهيق 4 ثوانٍ، حبس 4، زفير 6",
            "skating_benefit_ar": "التحكم في الأعصاب قبل وأثناء المنافسة",
        },
        {
            "name_ar": "تمرين التركيز الواحد",
            "duration_ar": "5 دقائق",
            "technique_ar": "ركز على نقطة واحدة فقط دون تشتيت",
            "skating_benefit_ar": "التركيز أثناء العناصر الصعبة",
        },
    ],
}

# ─── ON-ICE DRILLS ───────────────────────────────────────────────────
ON_ICE_DRILLS = {
    "jump_drills": {
        "Alpha_Beta": [
            {
                "name_ar": "تمرين الإقلاع من الوقوف",
                "description_ar": "الوقوف على حافة خارجية ثم القفز والهبوط على نفس القدم",
                "duration_ar": "10 دقائق",
                "focus_ar": "الحافة الصحيحة، وضع الجسم",
                "sets": 10, "reps_per_set": 5,
            },
            {
                "name_ar": "Waltz Jump بالحائط",
                "description_ar": "تنفيذ Waltz Jump بمساعدة الحائط أو حاجز الحلبة",
                "duration_ar": "10 دقائق",
                "focus_ar": "الإقلاع، نصف الدوران، الهبوط",
                "sets": 10, "reps_per_set": 5,
            },
            {
                "name_ar": "Half jump drills",
                "description_ar": "تنفيذ نصف القفزة فقط (إقلاع وبداية دوران) لتعلم الوضع الصحيح",
                "duration_ar": "15 دقيقة",
                "focus_ar": "الإقلاع القوي، لف الذراعين، تجميع الجسم",
                "sets": 15, "reps_per_set": 3,
            },
        ],
        "Gamma_Delta": [
            {
                "name_ar": "تمرين تجميعة 3+2",
                "description_ar": "تدريب مكثف على تجميع قفزتين متتاليتين",
                "duration_ar": "20 دقيقة",
                "focus_ar": "الارتداد الفوري، الحفاظ على السرعة",
                "sets": 8, "reps_per_set": 3,
            },
            {
                "name_ar": "تمرين Axel مزدوج من الخطوات",
                "description_ar": "الدخول للأكسل من خطوات متنوعة (forward inside edge, back outside edge)",
                "duration_ar": "20 دقيقة",
                "focus_ar": "تنوع الدخول، السرعة عند الإقلاع",
                "sets": 10, "reps_per_set": 3,
            },
            {
                "name_ar": "تمرين القفز في منتصف Step sequence",
                "description_ar": "تضمين قفزات ضمن تسلسل خطوات لمحاكاة البرنامج الحقيقي",
                "duration_ar": "15 دقيقة",
                "focus_ar": "الانتقال الطبيعي بين الخطوات والقفزات",
                "sets": 5, "reps_per_set": 2,
            },
        ],
        "Advanced": [
            {
                "name_ar": "تمرين القفزة الرباعية من توقف",
                "description_ar": "تنفيذ الرباعية من وضع شبه ثابت لدراسة الميكانيكا",
                "duration_ar": "30 دقيقة",
                "focus_ar": "الإغلاق الكامل، الدوران الأقصى، الهبوط الثابت",
                "sets": 10, "reps_per_set": 2,
            },
            {
                "name_ar": "تمرين الإطالة في الهواء",
                "description_ar": "قفزات ثلاثية مع التركيز على الإطالة القصوى في الهواء قبل الفتح",
                "duration_ar": "20 دقيقة",
                "focus_ar": "رفع نسبة الوقت في الهواء، الهبوط على الغني",
                "sets": 8, "reps_per_set": 3,
            },
            {
                "name_ar": "تمرين في النصف الثاني من البرنامج",
                "description_ar": "تنفيذ العناصر الصعبة بعد 3 دقائق من التدريب المتواصل (محاكاة الإرهاق)",
                "duration_ar": "3 دقائق run + عناصر",
                "focus_ar": "التقنية تحت الإرهاق، الثبات العقلي",
                "sets": 4, "reps_per_set": 1,
            },
        ],
    },
    "spin_drills": [
        {
            "name_ar": "تمرين المحور (Axis training)",
            "description_ar": "الدوران في مكان واحد دون تحرك عبر الجليد",
            "duration_ar": "10 دقيقة",
            "focus_ar": "المحور الرأسي الثابت، السرعة المتزايدة",
        },
        {
            "name_ar": "تمرين سرعة الدوران",
            "description_ar": "تمارين تجميع الذراعين والجسم لزيادة السرعة",
            "duration_ar": "10 دقيقة",
            "focus_ar": "التجميع السريع، الحفاظ على المحور",
        },
        {
            "name_ar": "تمرين الانتقال بين المواضع",
            "description_ar": "التغيير بين Camel → Sit → Upright بسلاسة",
            "duration_ar": "15 دقيقة",
            "focus_ar": "السلاسة في الانتقال، عدم فقدان السرعة",
        },
        {
            "name_ar": "تمرين الدخول المتنوع للسبين",
            "description_ar": "الدخول من خطوة مختلفة، Back entrance، Flying entrance",
            "duration_ar": "15 دقيقة",
            "focus_ar": "تنوع الدخول حسب متطلبات البرنامج",
        },
    ],
    "steps_and_skating": [
        {
            "name_ar": "تمرين الحافات العميقة",
            "description_ar": "الانزلاق على حافة داخلية وخارجية مع تعميق الزاوية تدريجياً",
            "duration_ar": "10 دقيقة",
            "focus_ar": "عمق الحافة، الاستقرار، الانزلاق الطويل",
        },
        {
            "name_ar": "Brackets, Rockers, Counters",
            "description_ar": "تمرين الحركات الأحادية الصعبة بالتكرار",
            "duration_ar": "15 دقيقة",
            "focus_ar": "دقة الحافة، النظافة التقنية",
        },
        {
            "name_ar": "تمرين سرعة الـ Crossovers",
            "description_ar": "Crossovers سريعة في دوائر ضيقة لبناء السرعة",
            "duration_ar": "10 دقيقة",
            "focus_ar": "الدفع القوي، المحافظة على وضع الجسم",
        },
        {
            "name_ar": "تمرين Step sequence إيقاعي",
            "description_ar": "تنفيذ خطوات متنوعة مع الموسيقى بالتزامن التام",
            "duration_ar": "20 دقيقة",
            "focus_ar": "التوقيت الموسيقي، التعبير، التنوع",
        },
        {
            "name_ar": "تمرين التزلج الكامل للحلبة",
            "description_ar": "التزلج بسرعة قصوى مع الحفاظ على وضع الجسم الصحيح",
            "duration_ar": "10 دقيقة",
            "focus_ar": "السرعة، توزيع الجليد، الاقتصاد في الطاقة",
        },
    ],
    "choreography": [
        {
            "name_ar": "تمرين ربط العناصر بالموسيقى",
            "description_ar": "أداء كل عنصر في اللحظة الموسيقية المحددة له",
            "duration_ar": "30 دقيقة",
            "focus_ar": "التوقيت، التعبير، الانتقالات الطبيعية",
        },
        {
            "name_ar": "تمرين التعبير عن المشاعر",
            "description_ar": "أداء قطع موسيقية مختلفة الطابع (حزينة، فرحة، درامية) بتعبير حقيقي",
            "duration_ar": "15 دقيقة",
            "focus_ar": "التعبير الوجهي والجسدي الحقيقي",
        },
        {
            "name_ar": "تمرين Transitions مبتكرة",
            "description_ar": "إضافة حركات انتقالية صعبة ومبتكرة بين كل عنصر",
            "duration_ar": "20 دقيقة",
            "focus_ar": "الإبداع، التنوع، الصعوبة التقنية",
        },
    ],
}

# ─── WEEKLY TRAINING PLANS ───────────────────────────────────────────
def generate_weekly_plan(level: str, goal: str, sessions_per_week: int = 6) -> dict:
    """Generate a comprehensive weekly training plan"""

    is_beginner = level in ["Alpha", "Beta"]
    is_intermediate = level in ["Gamma", "Delta"]
    is_advanced = level in ["Pre-Free", "Free Skate 1", "Free Skate 2", "Free Skate 3", "Advanced"]

    if is_beginner:
        on_ice_minutes = 60
        off_ice_minutes = 45
    elif is_intermediate:
        on_ice_minutes = 90
        off_ice_minutes = 60
    else:
        on_ice_minutes = 120
        off_ice_minutes = 90

    weekly_plan = {
        "الأحد (Sunday)": {
            "focus_ar": "قفزات + سبينات",
            "on_ice": {
                "duration": on_ice_minutes,
                "sessions": [
                    {"time": "10 دقائق", "activity_ar": "إحماء: انزلاق خفيف + تمارين حافات"},
                    {"time": "30 دقائق", "activity_ar": "تدريب القفزات المستهدفة (مع تكرار × 20 لكل قفزة)"},
                    {"time": "20 دقائق", "activity_ar": "تدريب السبينات (كل أنواع السبينات)"},
                    {"time": "15 دقائق", "activity_ar": "أجزاء من البرنامج التنافسي"},
                    {"time": "5 دقائق", "activity_ar": "تهدئة وتمدد خفيف"},
                ]
            },
            "off_ice": {
                "duration": off_ice_minutes,
                "sessions": [
                    {"time": "10 دقائق", "activity_ar": "إحماء ديناميكي"},
                    {"time": "25 دقائق", "activity_ar": "تمارين القوة (Squats, Lunges, Plyo jumps)"},
                    {"time": "10 دقائق", "activity_ar": "تمارين الجذع والتوازن"},
                ]
            }
        },
        "الإثنين (Monday)": {
            "focus_ar": "خطوات + تزلج + كوريغرافيا",
            "on_ice": {
                "duration": on_ice_minutes,
                "sessions": [
                    {"time": "10 دقائق", "activity_ar": "إحماء مع Crossovers سريعة"},
                    {"time": "20 دقائق", "activity_ar": "Step sequences وتمارين الحافات العميقة"},
                    {"time": "20 دقائق", "activity_ar": "Footwork وTransitions"},
                    {"time": "20 دقائق", "activity_ar": "مراجعة البرنامج القصير كاملاً"},
                    {"time": "10 دقائق", "activity_ar": "عمل كوريغرافي مع الموسيقى"},
                ]
            },
            "off_ice": {
                "duration": off_ice_minutes,
                "sessions": [
                    {"time": "15 دقائق", "activity_ar": "تمارين مرونة (Split, Hip flexors, Back stretch)"},
                    {"time": "20 دقائق", "activity_ar": "Cardio: HIIT أو حبل"},
                    {"time": "10 دقائق", "activity_ar": "تمارين الدوران خارج الجليد"},
                ]
            }
        },
        "الثلاثاء (Tuesday)": {
            "focus_ar": "البرنامج الحر الكامل",
            "on_ice": {
                "duration": on_ice_minutes,
                "sessions": [
                    {"time": "15 دقائق", "activity_ar": "إحماء شامل"},
                    {"time": "20 دقائق", "activity_ar": "مراجعة العناصر الصعبة"},
                    {"time": f"{on_ice_minutes - 40} دقيقة", "activity_ar": "أداء البرنامج الحر كاملاً × 2 مرات"},
                    {"time": "5 دقائق", "activity_ar": "مراجعة الأخطاء والملاحظات"},
                ]
            },
            "off_ice": {
                "duration": off_ice_minutes,
                "sessions": [
                    {"time": "20 دقائق", "activity_ar": "تمارين القوة: الجزء العلوي (Push-ups, Rows)"},
                    {"time": "15 دقائق", "activity_ar": "تمارين التوازن على ساق واحدة"},
                    {"time": "10 دقائق", "activity_ar": "تمرين ذهني: تخيل البرنامج (Visualization)"},
                ]
            }
        },
        "الأربعاء (Wednesday)": {
            "focus_ar": "راحة نشطة",
            "on_ice": {"duration": 0, "sessions": []},
            "off_ice": {
                "duration": 45,
                "sessions": [
                    {"time": "30 دقيقة", "activity_ar": "سباحة أو دراجة ثابتة (كارديو خفيف)"},
                    {"time": "15 دقيقة", "activity_ar": "تمدد كامل للجسم"},
                ]
            }
        },
        "الخميس (Thursday)": {
            "focus_ar": "قفزات + تقنية متقدمة",
            "on_ice": {
                "duration": on_ice_minutes,
                "sessions": [
                    {"time": "10 دقائق", "activity_ar": "إحماء"},
                    {"time": "40 دقيقة", "activity_ar": "تدريب مكثف على القفزات الأهم (Triple/Quad)"},
                    {"time": "20 دقائق", "activity_ar": "تجميعات القفزات"},
                    {"time": "20 دقائق", "activity_ar": "البرنامج القصير + ملاحظات"},
                ]
            },
            "off_ice": {
                "duration": off_ice_minutes,
                "sessions": [
                    {"time": "25 دقيقة", "activity_ar": "تمارين القوة الانفجارية (Box Jumps, Bounding)"},
                    {"time": "15 دقيقة", "activity_ar": "تمارين المرونة"},
                    {"time": "10 دقائق", "activity_ar": "تمرين التنفس والتركيز الذهني"},
                ]
            }
        },
        "الجمعة (Friday)": {
            "focus_ar": "محاكاة المنافسة",
            "on_ice": {
                "duration": on_ice_minutes,
                "sessions": [
                    {"time": "15 دقائق", "activity_ar": "إحماء تنافسي (كما في يوم المنافسة)"},
                    {"time": "5 دقائق", "activity_ar": "6-minute warm-up محاكاة"},
                    {"time": "5 دقائق", "activity_ar": "البرنامج القصير بشكل تنافسي كامل"},
                    {"time": "10 دقائق", "activity_ar": "استراحة + إحماء"},
                    {"time": "4-5 دقائق", "activity_ar": "البرنامج الحر كاملاً بشكل تنافسي"},
                    {"time": "15 دقائق", "activity_ar": "مراجعة الفيديو + ملاحظات التحسين"},
                ]
            },
            "off_ice": {
                "duration": 30,
                "sessions": [
                    {"time": "20 دقيقة", "activity_ar": "تمدد شامل للتعافي"},
                    {"time": "10 دقائق", "activity_ar": "مراجعة ذهنية للأداء وتدوين الملاحظات"},
                ]
            }
        },
        "السبت (Saturday)": {
            "focus_ar": "إبداع + مرونة",
            "on_ice": {
                "duration": 60,
                "sessions": [
                    {"time": "10 دقائق", "activity_ar": "إحماء حر"},
                    {"time": "25 دقيقة", "activity_ar": "تجريب حركات جديدة وإبداعية"},
                    {"time": "25 دقيقة", "activity_ar": "تمرين الكوريغرافيا والتعبير الموسيقي"},
                ]
            },
            "off_ice": {
                "duration": 60,
                "sessions": [
                    {"time": "30 دقيقة", "activity_ar": "تمارين مرونة شاملة (Yoga/Pilates)"},
                    {"time": "15 دقيقة", "activity_ar": "تمارين الجذع"},
                    {"time": "15 دقيقة", "activity_ar": "Visualization + تخطيط الأسبوع القادم"},
                ]
            }
        },
    }

    return weekly_plan


def generate_monthly_plan(level: str, weeks: int = 4) -> list:
    """Generate monthly periodized training plan"""
    phases = [
        {
            "week": 1,
            "name_ar": "أسبوع البناء الأساسي",
            "intensity": "متوسطة (70%)",
            "focus_ar": "بناء القاعدة التقنية وتصحيح الأخطاء",
            "priority_elements_ar": ["مراجعة كل العناصر", "تصحيح الأخطاء التقنية", "بناء اللياقة"],
        },
        {
            "week": 2,
            "name_ar": "أسبوع التكثيف",
            "intensity": "عالية (85%)",
            "focus_ar": "زيادة التكرار والتركيز على العناصر الصعبة",
            "priority_elements_ar": ["التكرار المكثف للقفزات", "محاكاة أجزاء من البرنامج", "بناء القوة"],
        },
        {
            "week": 3,
            "name_ar": "أسبوع الذروة",
            "intensity": "قصوى (95%)",
            "focus_ar": "محاكاة المنافسة الكاملة",
            "priority_elements_ar": ["أداء البرنامجين كاملاً يومياً", "التركيز الذهني", "تنقيح التفاصيل"],
        },
        {
            "week": 4,
            "name_ar": "أسبوع التخفيف (Tapering)",
            "intensity": "منخفضة (60%)",
            "focus_ar": "الراحة وتجميع الطاقة للمنافسة",
            "priority_elements_ar": ["تخفيف الحجم مع الحفاظ على الجودة", "الراحة والاسترداد", "التحضير الذهني"],
        },
    ]
    return phases[:weeks]


def calculate_program_score(elements: list) -> dict:
    """Calculate estimated TES score for a set of elements"""
    total_bv = 0
    details = []

    for elem in elements:
        jump_code = elem.get("code", "")
        goe = elem.get("goe", 0)

        bv = 0
        if jump_code in JUMPS:
            bv = JUMPS[jump_code]["bv"]
            name = JUMPS[jump_code]["name_ar"]
        elif jump_code in SPINS:
            bv = SPINS[jump_code]["bv"]
            name = SPINS[jump_code]["name_ar"]
        else:
            name = jump_code

        goe_value = goe * 1.0
        element_score = bv + goe_value
        total_bv += element_score

        details.append({
            "code": jump_code,
            "name_ar": name,
            "bv": bv,
            "goe": goe,
            "score": element_score,
        })

    return {"total_tes": total_bv, "details": details}
