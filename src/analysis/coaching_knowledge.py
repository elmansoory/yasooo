"""
قاعدة معرفة التدريب الفني — Technical Coaching Knowledge Base
مبنية على "Figure Skating Coach Ready™" — Module 3 (Jump & Spin Technique Library)
و Bonus 2 (Technical Corrections & Coaching Cue Library) و Bonus 3 (Elite Physical Preparation Vault).

تربط كل خطأ مكتشف تلقائياً بـ:
  1. السبب الجذري الحقيقي (قاعدة "المرحلة السابقة" — Module 3 p.10)
  2. 4-6 جمل تدريب فورية جاهزة (Bonus 2)
  3. تمرين تصحيحي بدني مقترح (Bonus 3)
"""
from __future__ import annotations
from typing import Dict, List, Optional

# ── Section 2: Symptom-based cue library (Bonus 2) + root-cause phase (Module 3) ──

SYMPTOM_LIBRARY: Dict[str, Dict] = {

    'under_rotation': {
        'title_ar': 'دوران ناقص', 'title_en': 'Under-Rotation',
        'root_cause_ar': (
            'الخطأ يظهر في الهواء، لكن السبب الجذري الحقيقي في مرحلة الإقلاع — '
            'زخم دوراني غير كافٍ عند مغادرة الجليد (قاعدة "المرحلة السابقة": '
            'كل خطأ ظاهر جذره غالباً في المرحلة التي تسبقه).'
        ),
        'root_cause_en': (
            'Visible in the air, but the true root is at TAKEOFF — insufficient '
            'angular momentum built before leaving the ice.'
        ),
        'cues': [
            {'ar': '"اربط بسرعة" — اسحب الذراعين بإحكام نحو الجسم فور دفع مقدمة النصل، لا تنتظر حتى الهواء.',
             'en': '"Zip up fast" — pull arms tight to the body the instant the toe pick drives.'},
            {'ar': '"اضغط على العلبة" — تخيل أنك تمسك علبة بين مرفقيك، حافظ على الضغط طوال الهواء.',
             'en': '"Squeeze the can" — imagine holding a can between your elbows through the air.'},
            {'ar': '"مقدمة ثم سحب" — لحظة ملامسة المقدمة الجليد هي إشارتك: اسحب كل شيء للداخل فوراً.',
             'en': '"Pick and pull" — the pick hitting the ice is your signal to pull inward immediately.'},
            {'ar': '"أكمل الدوران قبل أن تبحث عن الهبوط" — النظر المبكر للهبوط يسحبك خارج الدوران.',
             'en': '"Finish the turn before you look for the landing."'},
            {'ar': '"ابقَ ملتفاً لفترة أطول" — حافظ على شد ما قبل الدوران خلال ثني الركبة.',
             'en': '"Stay wound longer" — hold pre-rotation tension through the knee bend.'},
        ],
        'drill_ar': 'تمارين اللف المشدود خارج الجليد (off-ice tuck drills) — الخطوة 2 من بروتوكول التصحيح ثلاثي الخطوات.',
        'drill_en': 'Off-ice tuck drills — isolate the tight air position before returning to the full jump.',
    },

    'two_footed_landing': {
        'title_ar': 'هبوط على قدمين / هبوط ثقيل', 'title_en': 'Two-Footed / Heavy Landing',
        'root_cause_ar': (
            'المشكلة تظهر عند الهبوط، لكن جذرها غالباً انحناء للأمام في الهواء '
            '(القفص الصدري يميل فوق الركبة) — وليس ضعفاً في تقنية الهبوط نفسها.'
        ),
        'root_cause_en': 'Root is usually forward lean in the AIR PHASE, not the landing itself.',
        'cues': [
            {'ar': '"أمسكها ثم أوقفها" — التلامس أولاً، ثم افتح وضعية الإيقاف بعد لحظة — ليسا في نفس الوقت.',
             'en': '"Catch it, then check it" — blade first, then open the check a beat later.'},
            {'ar': '"اجلس فيها" — اثنِ ركبة الهبوط بقوة لامتصاص الصدمة بدلاً من مقاومتها.',
             'en': '"Sit into it" — bend the landing knee aggressively to absorb impact.'},
            {'ar': '"الساق الحرة تبقى متقاطعة حتى الهبوط" — لا تفردها مبكراً أثناء النزول.',
             'en': '"Free leg stays crossed until you\'re down."'},
            {'ar': '"نصل واحد، لحظة واحدة" — يجب أن يكون هناك صوت تلامس واحد نظيف فقط.',
             'en': '"One blade, one moment" — exactly one clean contact sound.'},
            {'ar': '"اهبط على الكعب أولاً" — يمنع هبوط المقدمة (toe-rake) ويقلل رد فعل القدمين الاثنتين.',
             'en': '"Land on the heel first" — prevents toe-rake landing and the two-foot reflex.'},
        ],
        'drill_ar': 'كرر وضعية الهبوط بعد كل قفزة فردية والثبات عليها 3 ثوانٍ — يبني نمط الامتصاص الصحيح.',
        'drill_en': 'Hold the landing position for 3 seconds after every attempt to rebuild absorption pattern.',
    },

    'off_axis_spin': {
        'title_ar': 'دوران خارج المحور / دوران متنقل', 'title_en': 'Off-Axis / Traveling Spin',
        'root_cause_ar': (
            'الدوران يبدو "متنقلاً" في مرحلة الوضعية، لكن الجذر الحقيقي غالباً في حافة '
            'الدخول (entry edge) — حافة مسطحة لا تعطي عمقاً كافياً لتثبيت المركز.'
        ),
        'root_cause_en': 'Traveling in the position phase, but the true root is a flat/shallow entry edge.',
        'cues': [
            {'ar': '"اغرس قدمك كالوتد" — قدم الدوران تُدفع في الجليد وتبقى ثابتة، لا تنزلق عند الدخول.',
             'en': '"Plant your foot like a stake" — the spin foot drives in and stays.'},
            {'ar': '"دُر على قطعة نقدية" — تخيّل عملة على الجليد وابقِ كرة القدم عليها طوال الدوران.',
             'en': '"Spin on a dime" — keep the ball of the blade on one spot.'},
            {'ar': '"الكتف يقود، ليس الورك" — الجزء العلوي يبدأ الدوران أولاً، والورك يتبعه.',
             'en': '"Lead with the shoulder, not the hip."'},
            {'ar': '"الساق الحرة تطفو، لا تُقذف" — حركة متحكمة، فالقذف يخلق عزماً خارج المحور.',
             'en': '"Free leg floats — it doesn\'t fling."'},
        ],
        'drill_ar': 'اعمق حافة الدخول أولاً بخمس دقائق تزلج معزول على الحافة قبل أي دوران — يحل غالباً المشكلة دون تمارين إضافية.',
        'drill_en': 'Deepen the entry edge with isolated edge stroking before adding the spin.',
    },

    'shallow_entry_edge': {
        'title_ar': 'حافة دخول ضحلة أو مسطحة', 'title_en': 'Shallow or Flat Entry Edge',
        'root_cause_ar': 'الجذر يكون عادة في ضغط الكاحل غير الصحيح على النصل، أو خوف من السرعة يدفع اللاعب لتسطيح الحافة شعورياً.',
        'root_cause_en': 'Root is usually incorrect ankle pressure, or speed anxiety flattening the edge.',
        'cues': [
            {'ar': '"احفر أخدوداً، لا تتزلج فوقه" — يجب أن تشعر بأن الحافة تقطع الجليد لا تنزلق عليه.',
             'en': '"Carve a groove, don\'t skate on top of it."'},
            {'ar': '"اضغط بالكاحل لا بالركبة" — عمق الحافة يبدأ من مفصل الكاحل.',
             'en': '"Press the ankle, not the knee."'},
            {'ar': '"ثق بالمنحنى" — يعالج مباشرة تسطيح الحافة الناتج عن القلق من السرعة.',
             'en': '"Ride the curve — trust it."'},
            {'ar': '"تحقق من أثر النصل — يجب أن يكون قوساً لا خطاً مستقيماً."',
             'en': '"Check your tracing — it should be an arc, not a straight line."'},
        ],
        'drill_ar': 'تزلج معزول على الحافة (بدون قفزة/دوران) لخمس دقائق، ثم أعد إضافة العنصر.',
        'drill_en': 'Isolated edge stroking (no jump/spin) for 5 min, then reintroduce the element.',
    },

    'rotation_timing': {
        'title_ar': 'توقيت دوران مبكر أو متأخر', 'title_en': 'Early or Late Rotation Timing',
        'root_cause_ar': 'الدوران المبكر جذره كتف/ورك يبدأ الالتفاف قبل مغادرة المقدمة الجليد. الدوران المتأخر جذره ذراعان بطيئتا الانطواء عند الإقلاع.',
        'root_cause_en': 'Early: shoulder/hip turns before the pick leaves the ice. Late: arms not snapping in fast enough.',
        'cues': [
            {'ar': '"أمسك الحافة — لا تدر عليها" — التزم بحافة الإقلاع حتى تغادر النصل الجليد تماماً.',
             'en': '"Hold the edge — don\'t turn off it."'},
            {'ar': '"مقدمة ثم انطلاق — ليس مقدمة ثم دوران" — المقدمة منصة إقلاع لا بداية دوران.',
             'en': '"Pick and launch — not pick and spin."'},
            {'ar': '"جمّد الكتفين حتى تغادر المقدمة" — الكتفان مؤشر بداية الدوران.',
             'en': '"Freeze the shoulders until the blade is off."'},
            {'ar': '"الذراعان تنطويان عند المقدمة — لا بعدها" (لتصحيح الدوران المتأخر).',
             'en': '"Arms in at the pick — not after" (for late rotation).'},
        ],
        'drill_ar': 'امشِ على الإقلاع ببطء شديد على الجليد (بدون قفزة) للتحقق من بقاء الكتفين مربعين حتى مغادرة المقدمة.',
        'drill_en': 'Walk through the takeoff in slow motion on the ice, no jump — shoulders stay square until ice-off.',
    },

    'arm_shoulder_position': {
        'title_ar': 'خطأ وضعية الذراعين والكتفين', 'title_en': 'Arm & Shoulder Position Errors',
        'root_cause_ar': 'الجذر غالباً توتر عصبي (الكتفان يرتفعان والذراعان تتصلبان) عند محاولة صعوبة جديدة أو تحت الضغط.',
        'root_cause_en': 'Root is usually tension — shoulders rise and arms tighten under pressure or a new difficulty.',
        'cues': [
            {'ar': '"الكتفان لأسفل، الصدر مفتوح" — إجراءان معاً: أنزل الكتفين وافتح القص للأمام.',
             'en': '"Shoulders down, chest open."'},
            {'ar': '"الذراعان إطار، لا ترفرفان" — تحافظان على شكل بيضاوي ثابت مع الجسم.',
             'en': '"Arms frame — they don\'t flap."'},
            {'ar': '"اسحب الذراعين بنفس السرعة تماماً" — السحب غير المتماثل هو السبب الأشهر لميلان المحور في الهواء.',
             'en': '"Pull both arms at exactly the same speed."'},
            {'ar': '"أين مرفقاك الآن؟" — وعي لحظي، لأن ارتفاع المرفقين = ارتفاع الكتفين.',
             'en': '"Check: where are your elbows right now?"'},
        ],
        'drill_ar': 'تمرين أمام المرآة لمحاذاة الذراعين مع تسجيل فيديو للمقارنة.',
        'drill_en': 'Mirror exercises for arm alignment; film and review.',
    },

    'free_leg_position': {
        'title_ar': 'خطأ وضعية الساق الحرة', 'title_en': 'Free Leg Position Errors',
        'root_cause_ar': 'الجذر غالباً ضعف في عضلات مثنية الورك أو الأرداف، أو اعتماد على الزخم بدل التحكم العضلي المباشر.',
        'root_cause_en': 'Root is usually insufficient hip flexor/glute strength, or reliance on momentum over active control.',
        'cues': [
            {'ar': '"اسحب الركبة لأعلى وللداخل" — ركبة عريضة = حزمة عريضة = دوران بطيء.',
             'en': '"Pull the knee up and in — don\'t let it drift out."'},
            {'ar': '"ارفع من الورك لا من الركبة" — الرفع من الركبة يخلق اهتزازاً.',
             'en': '"Lift from the hip — not from the knee."'},
            {'ar': '"لا تدع الساق الحرة تكون كسولة" — يجب أن تُمسك بنشاط طوال الدوران.',
             'en': '"Hold it still — don\'t let the free leg be lazy."'},
        ],
        'drill_ar': 'تقوية مثنيات الورك والأرداف خارج الجليد قبل العمل على وضعية الساق الحرة على الجليد.',
        'drill_en': 'Off-ice hip flexor/glute strengthening before drilling on-ice free-leg positions.',
    },

    'popped_jump': {
        'title_ar': 'قفزة "منبثقة" (إجهاض الدوران)', 'title_en': 'Popped Jump (Aborted Rotation)',
        'root_cause_ar': 'الجذر نفسي غالباً — فقدان ثقة في منتصف الهواء يسبب إشارة إجهاض تفتح الذراعين مبكراً، وليس ضعفاً تقنياً بحتاً.',
        'root_cause_en': 'Root is usually psychological — a mental abort signal mid-air, not a pure technical failure.',
        'cues': [
            {'ar': '"التزم قبل أن تغادر الجليد" — القرار يُتخذ على الأرض، لا يُعاد التفكير فيه في الهواء.',
             'en': '"Commit before you leave the ice."'},
            {'ar': '"المرفقان للداخل، المرفقان للداخل، المرفقان للداخل" — تكرار يشغل المساحة الذهنية عن الإجهاض.',
             'en': '"Elbows in, elbows in, elbows in."'},
            {'ar': '"ابقَ صغيراً بقدر ما تستطيع" — لا "أكمل الدوران" بل "حافظ على الوضعية"؛ الدوران يهتم بنفسه.',
             'en': '"Stay small as long as you can."'},
        ],
        'drill_ar': 'لا تُصحَّح لفظياً فقط — ابنِ الثقة تدريجياً بمحاولات مضمونة الجودة (3-5) بدل تكرار عشوائي.',
        'drill_en': 'Build confidence gradually with 3-5 quality-controlled attempts rather than random repetition.',
    },

    'inconsistent_takeoff': {
        'title_ar': 'توقيت إقلاع غير ثابت', 'title_en': 'Inconsistent Take-Off Timing',
        'root_cause_ar': 'الجذر إيقاع تزلج غير منتظم قبل القفزة، أو عمق ثني ركبة متغير من محاولة لأخرى.',
        'root_cause_en': 'Root is irregular stroke rhythm feeding the jump, or inconsistent knee bend depth.',
        'cues': [
            {'ar': '"عدّ للدخول — واحد، اثنان، ثلاثة، انطلق" — يمنح الاقتراب مرساة إيقاعية ثابتة.',
             'en': '"Count it in — one, two, three, UP."'},
            {'ar': '"انثنِ بنفس العمق في كل محاولة" — وضعية الانطلاق يجب أن تكون قابلة للتكرار.',
             'en': '"Knee bends on every rep — make it the same bend."'},
        ],
        'drill_ar': 'استخدم عداً موسيقياً ثابتاً للإقلاع بدل انتظار "شعور الجاهزية".',
        'drill_en': 'Use a fixed musical count for takeoff instead of waiting for an internal readiness feeling.',
    },

    'loss_of_speed': {
        'title_ar': 'فقدان سرعة/تدفق قبل العنصر', 'title_en': 'Loss of Speed / Flow Into Elements',
        'root_cause_ar': 'الجذر غالباً كبح غير واعٍ أثناء خطوات الاقتراب، أو عدد عبورات (crossovers) غير كافٍ لتوليد سرعة الدخول.',
        'root_cause_en': 'Root is usually unconscious braking during approach steps, or insufficient crossover power.',
        'cues': [
            {'ar': '"هاجم العنصر — لا تقترب منه" — تحول ذهني من "الوصول بحذر" إلى "التوجه بقوة".',
             'en': '"Attack the element — don\'t approach it."'},
            {'ar': '"السرعة صديقتك — استخدمها" — يعالج القلق الذي يسبب الكبح.',
             'en': '"Speed is your friend — use it."'},
            {'ar': '"تدفق خلاله، لا توقف قبله" — لا تعليق قبل العنصر.',
             'en': '"Flow through, not into — no pause before the element."'},
        ],
        'drill_ar': 'راجع خطوات الاقتراب بمعزل عن العنصر للتأكد من عدم وجود كبح غير واعٍ.',
        'drill_en': 'Review approach steps in isolation to check for unconscious braking.',
    },

    'checking_landing_control': {
        'title_ar': 'خطأ في الإيقاف/التحكم بالهبوط', 'title_en': 'Checking & Landing-Control Errors',
        'root_cause_ar': 'فتح الذراعين بقوة مفرطة يخلق دوراناً مستمراً بعد نقطة الإيقاف، أو الساق الحرة لا تمتد بسرعة كافية لموازنة الحركة.',
        'root_cause_en': 'Arms opening too forcefully continues rotation past the check, or free leg not extending fast enough.',
        'cues': [
            {'ar': '"افتح الذراعين، أغلق الوركين" — حركتان منفصلتان تحدثان معاً.',
             'en': '"Open arms, close hips."'},
            {'ar': '"مدّ للخارج منها — لا تدر خارجاً منها" — الإيقاف مدّ، وليس رمياً بالذراعين.',
             'en': '"Reach out of it — don\'t spin out of it."'},
            {'ar': '"الساق الحرة هي دفتك — استخدمها" — تتحكم في الاتجاه وتوقف الدوران.',
             'en': '"Free leg is your rudder — use it."'},
            {'ar': '"ثبّتها وابقَ لثلاث عدات" — وضعية الهبوط يجب أن تُحفظ لا أن تُلمس وتُترك.',
             'en': '"Stick it and hold for three counts."'},
        ],
        'drill_ar': 'ثبّت وضعية الهبوط لثلاث عدات كاملة بعد كل محاولة.',
        'drill_en': 'Hold the landing position for a full three-count after every attempt.',
    },

    'axis_misalignment': {
        'title_ar': 'اختلال المحور الرأسي / انحناء للأمام',
        'title_en': 'Vertical Axis Misalignment / Forward Lean',
        'root_cause_ar': (
            'المحور الرأسي (تاج الرأس → الورك → ركبة التزلج → كرة النصل) هو المبدأ الذي يبنى عليه كل عنصر آخر. '
            'اختلاله ليس "انحناءً" سطحياً، بل غالباً ضعف تفعيل عضلات الجذع وقيادة الرأس للانحراف.'
        ),
        'root_cause_en': 'Not a surface "lean" — usually weak core engagement with the head leading the tilt.',
        'cues': [
            {'ar': '"انمُ طولاً من تاج رأسك" — يقاوم الانحناء الأمامي الذي يسحب المحور.',
             'en': '"Grow tall through the crown of your head."'},
            {'ar': '"كاحل، ركبة، ورك، كتف — خط واحد" — فحص جسدي متسلسل يمر به اللاعب قبل كل عنصر.',
             'en': '"Stack: ankle, knee, hip, shoulder — all one line."'},
            {'ar': '"لا تدع الحوض يدور — نفس التحكم الذي تستخدمه في الدوران" — تفعيل مضاد للدوران في الجذع.',
             'en': '"Don\'t let the pelvis rotate — same pelvis control as a held spin."'},
        ],
        'drill_ar': 'قبل أي محاولة، يجب أن يستطيع اللاعب الوقوف بدوران ثابت على قدمين بمحاذاة رأسية مثالية لست دورات فأكثر — إن تعذر ذلك، سيتكرر خلل المحور في كل عنصر بالجلسة.',
        'drill_en': 'Before any attempt, the skater should hold a stationary two-foot spin in perfect alignment for 6+ revolutions. If not, the axis problem will follow every element that session.',
    },
}


# ── Bonus 3: physical-prep cross-reference per symptom ─────────────────────────

PHYSICAL_PREP_MAP: Dict[str, Dict[str, str]] = {
    'under_rotation': {
        'ar': 'قوة مضادة للدوران في الجذع (Pallof Press، Dead Bug) + قوة مثنيات الورك — من بروتوكول المتانة السنوي.',
        'en': 'Core anti-rotation work (Pallof Press, Dead Bug) + hip flexor strength — Year-Round Durability Protocol.',
    },
    'two_footed_landing': {
        'ar': 'تدرّج التوازن أحادي الساق (المستوى 3-4: هبوط من صندوق، هبوط بعد قفزة) — الهبوط النشط لا السلبي.',
        'en': 'Single-Leg Balance Progressions (Level 3-4: drop-catch, jump-to-hold) — active landing absorption.',
    },
    'off_axis_spin': {
        'ar': 'تدريب التوازن أحادي الساق على سطح غير مستقر (لوح توازن/BOSU) + مرونة الورك 90/90.',
        'en': 'Unstable-surface single-leg training (balance board/BOSU) + hip 90/90 mobility.',
    },
    'shallow_entry_edge': {
        'ar': 'مرونة الكاحل وتمارين استقرار الورك الجانبية (Copenhagen Plank، Lateral Band Walk).',
        'en': 'Ankle mobility + lateral hip stability work (Copenhagen Plank, Lateral Band Walk).',
    },
    'rotation_timing': {
        'ar': 'تمارين رشاقة سلم التنسيق (Ladder Drills) لتحسين إيقاع الخطوات قبل القفزة.',
        'en': 'Coordination ladder drills to sharpen pre-jump step rhythm.',
    },
    'arm_shoulder_position': {
        'ar': 'تمارين سحب متماثلة (Band Pull-Apart، Prone Y-T-W) لتصحيح عدم تماثل قوة الجزء العلوي.',
        'en': 'Symmetric pulling work (Band Pull-Apart, Prone Y-T-W) to correct upper-body strength asymmetry.',
    },
    'free_leg_position': {
        'ar': 'تقوية مثنيات الورك والأرداف (Copenhagen Plank، Single-Leg Glute Bridge).',
        'en': 'Hip flexor/glute strengthening (Copenhagen Plank, Single-Leg Glute Bridge).',
    },
    'popped_jump': {
        'ar': 'تدريب التوازن تحت الإجهاد (Balance-Under-Fatigue) لبناء الثقة العصبية العضلية تحت الضغط.',
        'en': 'Balance-Under-Fatigue training to build neuromuscular confidence under stress.',
    },
    'inconsistent_takeoff': {
        'ar': 'تمارين رشاقة الأقماع ودائرة رد الفعل (Reaction Drill) لتثبيت إيقاع الإقلاع.',
        'en': 'Agility cone circuits + reaction drills to anchor takeoff rhythm.',
    },
    'loss_of_speed': {
        'ar': 'برنامج بناء القوة خارج الموسم (Off-Season Strength) — دفعة الفخذ الخلفي وسلسلة خلفية قوية.',
        'en': 'Off-Season strength block — posterior chain and hinge-pattern power for stroke drive.',
    },
    'checking_landing_control': {
        'ar': 'تقدم توازن أحادي الساق مستوى 4 (Jump-to-Hold) + الساق الحرة كدفة نشطة.',
        'en': 'Level 4 single-leg balance (Jump-to-Hold) + active free-leg rudder control.',
    },
    'axis_misalignment': {
        'ar': 'ثبات القلب (McGill Big 3) + مرونة صدرية (Thoracic Rotation) — من بروتوكول المتانة.',
        'en': 'Core stability (McGill Big 3) + thoracic mobility — Durability Protocol.',
    },
}


# ── 3-Step Correction Protocol (Bonus 2, p.26) ─────────────────────────────────

CORRECTION_PROTOCOL_AR = [
    ('١. تلميح لفظي', 'قدّم تلميحاً واحداً محدداً وراقب 3–5 محاولات. غيّر الصياغة مرة واحدة إن لم ينجح.'),
    ('٢. تمرين معزول', 'إن استمر الخطأ بعد صياغتين، افصل المكون المكسور عن العنصر الكامل ودرّبه بمعزل عن الضغط.'),
    ('٣. إعادة المحاولة بالسرعة الكاملة', 'عُد للعنصر الكامل بالنمط المصحح، وحدّد 3–5 محاولات عالية الجودة فقط.'),
]

CORRECTION_PROTOCOL_EN = [
    ('1. Verbal Cue', 'Deliver one specific cue, observe 3-5 attempts, change phrasing once if it doesn\'t land.'),
    ('2. Isolated Drill', 'If the error persists, isolate the broken component from the full element.'),
    ('3. Full-Speed Re-Attempt', 'Return to the full element with the corrected pattern; 3-5 quality reps only.'),
]


# ── Mapping detected-error category/title → symptom_key ────────────────────────

def resolve_symptom_key(error: Dict) -> Optional[str]:
    """Map a detected error dict (category/title_ar/title_en) to a SYMPTOM_LIBRARY key."""
    cat = (error.get('category') or '').strip()
    title = (error.get('title_ar') or '') + ' ' + (error.get('title_en') or '')

    if cat in ('دوران', 'Rotation') and ('ناقص' in title or 'Under' in title):
        return 'under_rotation'
    if 'قدمين' in title or 'Two-Foot' in title or 'Heavy Landing' in title:
        return 'two_footed_landing'
    if 'محور' in title or 'Off-Axis' in title or 'Traveling' in title:
        return 'off_axis_spin'
    if cat in ('وضعية الجسم', 'Posture') or 'انحناء' in title or 'Lean' in title:
        return 'axis_misalignment'
    if cat in ('الذراعين', 'Arms') or 'تناسق الذراعين' in title or 'Arm Asymmetry' in title:
        return 'arm_shoulder_position'
    if 'حافة' in title or 'Edge' in title:
        return 'shallow_entry_edge'
    if 'انبثاق' in title or 'Popped' in title:
        return 'popped_jump'
    if 'إقلاع' in title or 'Takeoff' in title or 'Take-Off' in title:
        return 'inconsistent_takeoff'
    if 'إيقاف' in title or 'Check' in title:
        return 'checking_landing_control'
    return None


def get_symptom_info(symptom_key: str) -> Optional[Dict]:
    return SYMPTOM_LIBRARY.get(symptom_key)


def get_physical_prep(symptom_key: str) -> Optional[Dict[str, str]]:
    return PHYSICAL_PREP_MAP.get(symptom_key)
