"""
Media Library for Exercises and Drills
مكتبة الوسائط للتمارين والدريلات
Uses YouTube embed search + thumbnail images
"""
import urllib.parse

def yt_search_embed(query: str) -> str:
    """Return YouTube embed URL for a search query (playlist search mode)"""
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.youtube.com/embed?listType=search&list={encoded}&autoplay=0"

def yt_search_url(query: str) -> str:
    """Return YouTube search URL to open in browser"""
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.youtube.com/results?search_query={encoded}"

def yt_thumbnail(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

# ─────────────────────────────────────────────────────────────────────
# MEDIA DATABASE per exercise type
# Each entry: name_ar, embed_query, search_query, image_url, sources
# ─────────────────────────────────────────────────────────────────────

EXERCISE_MEDIA = {

    # ── ON-ICE: JUMPS ──────────────────────────────────────────────
    "waltz_jump": {
        "name_ar": "Waltz Jump",
        "embed_query": "figure skating waltz jump tutorial beginner",
        "search_query": "figure skating waltz jump tutorial",
        "image_url": "https://img.youtube.com/vi/7Eiz-LLaLiU/hqdefault.jpg",
        "sources": [
            {"label": "▶ Waltz Jump Tutorial", "url": "https://www.youtube.com/results?search_query=waltz+jump+figure+skating+tutorial"},
            {"label": "📸 US Figure Skating", "url": "https://www.usfigureskating.org/skate/figure-skating/basic-skills"},
        ]
    },
    "axel_single": {
        "name_ar": "Axel مفرد",
        "embed_query": "figure skating single axel jump tutorial",
        "search_query": "figure skating single axel tutorial how to",
        "image_url": "https://img.youtube.com/vi/3lNGZJC5Q8I/hqdefault.jpg",
        "sources": [
            {"label": "▶ Axel Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+single+axel+tutorial"},
            {"label": "▶ Axel Slow Motion", "url": "https://www.youtube.com/results?search_query=axel+jump+figure+skating+slow+motion"},
        ]
    },
    "axel_double": {
        "name_ar": "Axel مزدوج",
        "embed_query": "figure skating double axel tutorial",
        "search_query": "double axel figure skating tutorial",
        "image_url": "https://img.youtube.com/vi/qvhNQmfvVH0/hqdefault.jpg",
        "sources": [
            {"label": "▶ Double Axel Tutorial", "url": "https://www.youtube.com/results?search_query=double+axel+figure+skating+tutorial"},
            {"label": "▶ Double Axel Drills", "url": "https://www.youtube.com/results?search_query=double+axel+off+ice+drills"},
        ]
    },
    "axel_triple": {
        "name_ar": "Axel ثلاثي",
        "embed_query": "triple axel figure skating training how to",
        "search_query": "triple axel figure skating",
        "image_url": "https://img.youtube.com/vi/L-W75CKdEFo/hqdefault.jpg",
        "sources": [
            {"label": "▶ Triple Axel Training", "url": "https://www.youtube.com/results?search_query=triple+axel+figure+skating+training"},
            {"label": "▶ Best Triple Axels", "url": "https://www.youtube.com/results?search_query=best+triple+axel+figure+skating"},
        ]
    },
    "triple_jump": {
        "name_ar": "القفزات الثلاثية",
        "embed_query": "figure skating triple jumps tutorial training drills",
        "search_query": "figure skating triple lutz flip loop tutorial",
        "image_url": "https://img.youtube.com/vi/eCsmMBT5Eag/hqdefault.jpg",
        "sources": [
            {"label": "▶ Triple Lutz Tutorial", "url": "https://www.youtube.com/results?search_query=triple+lutz+figure+skating+tutorial"},
            {"label": "▶ Triple Flip Tutorial", "url": "https://www.youtube.com/results?search_query=triple+flip+figure+skating"},
            {"label": "▶ Triple Loop Tutorial", "url": "https://www.youtube.com/results?search_query=triple+loop+figure+skating"},
        ]
    },
    "quad_jump": {
        "name_ar": "القفزات الرباعية",
        "embed_query": "quadruple jump figure skating training Nathan Chen Yuzuru",
        "search_query": "quad jump figure skating training",
        "image_url": "https://img.youtube.com/vi/JjfQZfxaJoQ/hqdefault.jpg",
        "sources": [
            {"label": "▶ Quad Training", "url": "https://www.youtube.com/results?search_query=quad+jump+figure+skating+training"},
            {"label": "▶ Nathan Chen Quads", "url": "https://www.youtube.com/results?search_query=nathan+chen+quad+jumps+training"},
            {"label": "▶ Yuzuru Hanyu Quads", "url": "https://www.youtube.com/results?search_query=yuzuru+hanyu+quad+jump"},
        ]
    },
    "jump_combination": {
        "name_ar": "تجميعات القفزات",
        "embed_query": "figure skating jump combination 3+3 training",
        "search_query": "figure skating jump combination training tutorial",
        "image_url": "https://img.youtube.com/vi/7jvTAhRRcVk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Jump Combinations", "url": "https://www.youtube.com/results?search_query=figure+skating+jump+combination+tutorial"},
            {"label": "▶ 3+3 Combination Tips", "url": "https://www.youtube.com/results?search_query=figure+skating+3+3+combination+tips"},
        ]
    },

    # ── ON-ICE: SPINS ──────────────────────────────────────────────
    "sit_spin": {
        "name_ar": "Sit Spin (سبين جلوس)",
        "embed_query": "figure skating sit spin tutorial how to improve",
        "search_query": "figure skating sit spin tutorial",
        "image_url": "https://img.youtube.com/vi/wCTj-xOSLcI/hqdefault.jpg",
        "sources": [
            {"label": "▶ Sit Spin Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+sit+spin+tutorial+improve"},
            {"label": "▶ Sit Spin Variations", "url": "https://www.youtube.com/results?search_query=figure+skating+sit+spin+variations+advanced"},
        ]
    },
    "camel_spin": {
        "name_ar": "Camel Spin (سبين جمل)",
        "embed_query": "figure skating camel spin tutorial how to",
        "search_query": "figure skating camel spin tutorial",
        "image_url": "https://img.youtube.com/vi/pzKfuQA1Hbs/hqdefault.jpg",
        "sources": [
            {"label": "▶ Camel Spin Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+camel+spin+tutorial"},
            {"label": "▶ Flying Camel Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+flying+camel+spin"},
        ]
    },
    "layback_spin": {
        "name_ar": "Layback Spin (سبين خلفي)",
        "embed_query": "figure skating layback spin tutorial Biellmann",
        "search_query": "figure skating layback spin tutorial",
        "image_url": "https://img.youtube.com/vi/TIMfXoZ-7Y0/hqdefault.jpg",
        "sources": [
            {"label": "▶ Layback Spin Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+layback+spin+tutorial"},
            {"label": "▶ Biellmann Spin", "url": "https://www.youtube.com/results?search_query=biellmann+spin+figure+skating+tutorial"},
        ]
    },
    "combo_spin": {
        "name_ar": "Combination Spin",
        "embed_query": "figure skating combination spin tutorial level 4",
        "search_query": "figure skating combination spin tutorial",
        "image_url": "https://img.youtube.com/vi/8hGQSZuV_HI/hqdefault.jpg",
        "sources": [
            {"label": "▶ Combo Spin Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+combination+spin+level+4"},
        ]
    },
    "spin_axis": {
        "name_ar": "تمرين المحور والسرعة",
        "embed_query": "figure skating spin axis training speed improvement",
        "search_query": "figure skating spin axis training",
        "image_url": "https://img.youtube.com/vi/N-LfVX7Iu0c/hqdefault.jpg",
        "sources": [
            {"label": "▶ Spin Axis Training", "url": "https://www.youtube.com/results?search_query=figure+skating+spin+axis+training+tips"},
            {"label": "▶ Spin Speed Tips", "url": "https://www.youtube.com/results?search_query=figure+skating+faster+spin+tips"},
        ]
    },

    # ── ON-ICE: STEPS & SKATING ────────────────────────────────────
    "deep_edges": {
        "name_ar": "تمرين الحافات العميقة",
        "embed_query": "figure skating deep edges training tutorial drills",
        "search_query": "figure skating deep edges tutorial",
        "image_url": "https://img.youtube.com/vi/pVuLjpAKdBk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Deep Edge Drills", "url": "https://www.youtube.com/results?search_query=figure+skating+deep+edges+training+drills"},
            {"label": "▶ Edge Quality Training", "url": "https://www.youtube.com/results?search_query=figure+skating+edge+quality+improvement"},
        ]
    },
    "step_sequence": {
        "name_ar": "Step Sequence تسلسل الخطوات",
        "embed_query": "figure skating step sequence tutorial level 4 ISU",
        "search_query": "figure skating step sequence tutorial",
        "image_url": "https://img.youtube.com/vi/jBHMGKSbCMk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Step Sequence Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+step+sequence+tutorial+ISU"},
            {"label": "▶ Advanced Footwork", "url": "https://www.youtube.com/results?search_query=figure+skating+advanced+footwork+training"},
            {"label": "▶ Brackets & Rockers", "url": "https://www.youtube.com/results?search_query=figure+skating+brackets+rockers+counters+tutorial"},
        ]
    },
    "crossovers": {
        "name_ar": "Crossovers السريعة",
        "embed_query": "figure skating crossovers power speed tutorial",
        "search_query": "figure skating crossovers tutorial",
        "image_url": "https://img.youtube.com/vi/c78yBnhB2Yk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Crossovers Tutorial", "url": "https://www.youtube.com/results?search_query=figure+skating+crossovers+tutorial+power"},
            {"label": "▶ Speed on Ice", "url": "https://www.youtube.com/results?search_query=figure+skating+speed+training+crossovers"},
        ]
    },
    "choreography": {
        "name_ar": "كوريغرافيا وتعبير",
        "embed_query": "figure skating choreography expression artistic training",
        "search_query": "figure skating artistic expression training choreography",
        "image_url": "https://img.youtube.com/vi/Qz3OroJeGTY/hqdefault.jpg",
        "sources": [
            {"label": "▶ Artistic Expression", "url": "https://www.youtube.com/results?search_query=figure+skating+artistic+expression+training"},
            {"label": "▶ Choreography Tips", "url": "https://www.youtube.com/results?search_query=figure+skating+choreography+tips+musical+interpretation"},
            {"label": "📸 ISU Guidelines", "url": "https://www.isu.org/figure-skating"},
        ]
    },

    # ── OFF-ICE: STRENGTH ──────────────────────────────────────────
    "squat": {
        "name_ar": "القرفصاء (Squat)",
        "embed_query": "squat proper form tutorial for figure skaters athletes",
        "search_query": "squat for figure skaters tutorial",
        "image_url": "https://img.youtube.com/vi/ultWZbUMPL8/hqdefault.jpg",
        "sources": [
            {"label": "▶ Squat Tutorial", "url": "https://www.youtube.com/results?search_query=squat+proper+form+athletes"},
            {"label": "▶ Squats for Skaters", "url": "https://www.youtube.com/results?search_query=off+ice+training+squats+figure+skaters"},
        ]
    },
    "single_leg_squat": {
        "name_ar": "القرفصاء على ساق (Single-Leg Squat)",
        "embed_query": "single leg squat pistol squat tutorial for skaters balance",
        "search_query": "single leg squat tutorial skaters",
        "image_url": "https://img.youtube.com/vi/vq5-vdgJc0I/hqdefault.jpg",
        "sources": [
            {"label": "▶ Single Leg Squat", "url": "https://www.youtube.com/results?search_query=single+leg+squat+tutorial+balance"},
            {"label": "▶ Pistol Squat", "url": "https://www.youtube.com/results?search_query=pistol+squat+progression+tutorial"},
        ]
    },
    "box_jump": {
        "name_ar": "القفز على صندوق (Box Jump)",
        "embed_query": "box jump technique tutorial explosive power athletes",
        "search_query": "box jump tutorial explosive power",
        "image_url": "https://img.youtube.com/vi/52jRTBBTMqE/hqdefault.jpg",
        "sources": [
            {"label": "▶ Box Jump Tutorial", "url": "https://www.youtube.com/results?search_query=box+jump+technique+tutorial"},
            {"label": "▶ Plyometrics for Skaters", "url": "https://www.youtube.com/results?search_query=plyometric+training+figure+skaters"},
        ]
    },
    "glute_bridge": {
        "name_ar": "Glute Bridge رفع الأرداف",
        "embed_query": "glute bridge hip thrust tutorial form athletes",
        "search_query": "glute bridge tutorial athletes",
        "image_url": "https://img.youtube.com/vi/OUgsJ8-Vi0E/hqdefault.jpg",
        "sources": [
            {"label": "▶ Glute Bridge Tutorial", "url": "https://www.youtube.com/results?search_query=glute+bridge+tutorial+form"},
            {"label": "▶ Hip Thrust Progression", "url": "https://www.youtube.com/results?search_query=hip+thrust+barbell+tutorial"},
        ]
    },
    "bulgarian_squat": {
        "name_ar": "التمرين البلغاري (Bulgarian Split Squat)",
        "embed_query": "bulgarian split squat tutorial form athletes skaters",
        "search_query": "bulgarian split squat tutorial",
        "image_url": "https://img.youtube.com/vi/2C-uNgKwPLE/hqdefault.jpg",
        "sources": [
            {"label": "▶ Bulgarian Split Squat", "url": "https://www.youtube.com/results?search_query=bulgarian+split+squat+tutorial"},
        ]
    },
    "plank": {
        "name_ar": "بلانك جانبي (Side Plank)",
        "embed_query": "side plank tutorial core stability athletes",
        "search_query": "side plank tutorial core",
        "image_url": "https://img.youtube.com/vi/K2KScXLki6I/hqdefault.jpg",
        "sources": [
            {"label": "▶ Side Plank Tutorial", "url": "https://www.youtube.com/results?search_query=side+plank+tutorial+core+stability"},
        ]
    },

    # ── OFF-ICE: FLEXIBILITY ───────────────────────────────────────
    "split": {
        "name_ar": "الإشبيغات (Split)",
        "embed_query": "how to do splits flexibility training for skaters beginners",
        "search_query": "split flexibility training figure skaters",
        "image_url": "https://img.youtube.com/vi/ooJDsD3bblk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Split Tutorial", "url": "https://www.youtube.com/results?search_query=how+to+do+splits+flexibility+training"},
            {"label": "▶ Splits for Skaters", "url": "https://www.youtube.com/results?search_query=flexibility+figure+skating+splits+training"},
        ]
    },
    "hip_flexor": {
        "name_ar": "تمدد الورك (Hip Flexor Stretch)",
        "embed_query": "hip flexor stretch tutorial for skaters athletes",
        "search_query": "hip flexor stretch skaters",
        "image_url": "https://img.youtube.com/vi/YqF_-RKpiEk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Hip Flexor Stretch", "url": "https://www.youtube.com/results?search_query=hip+flexor+stretch+tutorial+athletes"},
        ]
    },
    "back_stretch": {
        "name_ar": "تمدد الظهر وتمرين العقرب",
        "embed_query": "figure skating back flexibility training layback Biellmann stretch",
        "search_query": "figure skating back flexibility training",
        "image_url": "https://img.youtube.com/vi/kBcgKRAv1Xk/hqdefault.jpg",
        "sources": [
            {"label": "▶ Back Flexibility", "url": "https://www.youtube.com/results?search_query=figure+skating+back+flexibility+training"},
            {"label": "▶ Biellmann Preparation", "url": "https://www.youtube.com/results?search_query=biellmann+flexibility+training+tutorial"},
        ]
    },
    "hamstring_stretch": {
        "name_ar": "تمدد الفخذ الخلفي (Hamstring)",
        "embed_query": "hamstring stretch flexibility training athletes tutorial",
        "search_query": "hamstring stretch athletes",
        "image_url": "https://img.youtube.com/vi/QiS8AFdlgfw/hqdefault.jpg",
        "sources": [
            {"label": "▶ Hamstring Stretch", "url": "https://www.youtube.com/results?search_query=hamstring+stretch+flexibility+training"},
        ]
    },

    # ── OFF-ICE: CARDIO ────────────────────────────────────────────
    "hiit": {
        "name_ar": "HIIT تدريب متقطع",
        "embed_query": "HIIT training for figure skaters athletes endurance",
        "search_query": "HIIT training for figure skaters",
        "image_url": "https://img.youtube.com/vi/ml6cT4AZdqI/hqdefault.jpg",
        "sources": [
            {"label": "▶ HIIT for Skaters", "url": "https://www.youtube.com/results?search_query=HIIT+training+figure+skaters+endurance"},
            {"label": "▶ Skating Cardio", "url": "https://www.youtube.com/results?search_query=cardio+training+figure+skating+athletes"},
        ]
    },
    "jump_rope": {
        "name_ar": "الحبل والـ Plyometrics",
        "embed_query": "jump rope plyometrics figure skaters training coordination",
        "search_query": "jump rope training figure skaters",
        "image_url": "https://img.youtube.com/vi/1BZM2Vre5oc/hqdefault.jpg",
        "sources": [
            {"label": "▶ Jump Rope Training", "url": "https://www.youtube.com/results?search_query=jump+rope+plyometrics+athletes+training"},
            {"label": "▶ Plyometrics", "url": "https://www.youtube.com/results?search_query=plyometric+exercises+figure+skating"},
        ]
    },

    # ── BALANCE & COORDINATION ─────────────────────────────────────
    "balance_board": {
        "name_ar": "ألواح التوازن (Balance Board)",
        "embed_query": "balance board training figure skaters ankle stability",
        "search_query": "balance board training skaters",
        "image_url": "https://img.youtube.com/vi/KD4OBqIBfDw/hqdefault.jpg",
        "sources": [
            {"label": "▶ Balance Board", "url": "https://www.youtube.com/results?search_query=balance+board+training+figure+skating"},
            {"label": "▶ Ankle Stability", "url": "https://www.youtube.com/results?search_query=ankle+stability+training+skaters"},
        ]
    },
    "off_ice_rotation": {
        "name_ar": "تمارين الدوران خارج الجليد",
        "embed_query": "off ice rotation training figure skating jumps spinner board",
        "search_query": "off ice rotation training figure skating",
        "image_url": "https://img.youtube.com/vi/rY3g2vV_gfM/hqdefault.jpg",
        "sources": [
            {"label": "▶ Off-Ice Rotation", "url": "https://www.youtube.com/results?search_query=off+ice+rotation+training+figure+skating"},
            {"label": "▶ Spinner Board Training", "url": "https://www.youtube.com/results?search_query=spinner+board+figure+skating+off+ice"},
        ]
    },

    # ── MENTAL ────────────────────────────────────────────────────
    "visualization": {
        "name_ar": "التخيل الذهني (Visualization)",
        "embed_query": "mental training visualization sports athletes figure skating",
        "search_query": "sports visualization technique athletes",
        "image_url": "https://img.youtube.com/vi/8-vCelMDkRc/hqdefault.jpg",
        "sources": [
            {"label": "▶ Visualization Training", "url": "https://www.youtube.com/results?search_query=visualization+mental+training+sports+athletes"},
            {"label": "▶ Sports Psychology", "url": "https://www.youtube.com/results?search_query=sports+psychology+figure+skating+mental+training"},
        ]
    },
    "breathing": {
        "name_ar": "التنفس والتأمل",
        "embed_query": "breathing technique sports athletes calm nervous competition",
        "search_query": "breathing technique athletes competition",
        "image_url": "https://img.youtube.com/vi/tybOi4hjZFQ/hqdefault.jpg",
        "sources": [
            {"label": "▶ Breathing Technique", "url": "https://www.youtube.com/results?search_query=breathing+technique+athletes+competition+calm"},
        ]
    },

    # ── COMPLETE OFF-ICE TRAINING PROGRAMS ─────────────────────────
    "full_off_ice": {
        "name_ar": "برنامج كامل خارج الجليد",
        "embed_query": "figure skating off ice training full workout program",
        "search_query": "figure skating off ice training program full",
        "image_url": "https://img.youtube.com/vi/T-T4_SvMX_E/hqdefault.jpg",
        "sources": [
            {"label": "▶ Full Off-Ice Workout", "url": "https://www.youtube.com/results?search_query=figure+skating+off+ice+full+training+program"},
            {"label": "▶ Elite Skater Training", "url": "https://www.youtube.com/results?search_query=figure+skating+elite+training+off+ice+program"},
            {"label": "📋 USFSA Training Resources", "url": "https://www.usfigureskating.org/skate/figure-skating/basic-skills"},
        ]
    },
}


# ─── Map exercises in training_generator to media keys ────────────────
EXERCISE_TO_MEDIA_KEY = {
    "القرفصاء (Squat)": "squat",
    "القرفصاء على ساق واحدة (Single-leg Squat)": "single_leg_squat",
    "التمرين البلغاري (Bulgarian Split Squat)": "bulgarian_squat",
    "رفع الساق الخلفية (Glute Bridge)": "glute_bridge",
    "الرفع الأمامي للساق (Leg Raise)": "plank",
    "بلانك جانبي (Side Plank)": "plank",
    "القفز على صندوق (Box Jump)": "box_jump",
    "القفز الرأسي (Vertical Jump)": "box_jump",
    "تمدد الإشبيغات (Split)": "split",
    "تمدد الورك الأمامي (Hip Flexor Stretch)": "hip_flexor",
    "تمدد الساق الخلفية (Hamstring Stretch)": "hamstring_stretch",
    "تمدد العقرب (Scorpion Stretch)": "back_stretch",
    "تمدد الظهر (Back Arch)": "back_stretch",
    "تمدد الكتف والذراع": "back_stretch",
    "الركض المتقطع (HIIT)": "hiit",
    "الدراجة الثابتة": "hiit",
    "تمارين plyometric": "jump_rope",
    "السباحة": "hiit",
    "الجمباز والحبل": "jump_rope",
    "الوقوف على ألواح التوازن (Balance Board)": "balance_board",
    "تمارين الدوران خارج الجليد": "off_ice_rotation",
    "التوازن على ساق واحدة مع الحركة": "balance_board",
    "تمارين حبال الاتزان (TRX)": "balance_board",
    "التخيل الذهني (Visualization)": "visualization",
    "التنفس العميق والتأمل": "breathing",
    "تمرين التركيز الواحد": "visualization",
    # ON-ICE DRILLS
    "تمرين الإقلاع من الوقوف": "waltz_jump",
    "Waltz Jump بالحائط": "waltz_jump",
    "Half jump drills": "waltz_jump",
    "تمرين تجميعة 3+2": "jump_combination",
    "تمرين Axel مزدوج من الخطوات": "axel_double",
    "تمرين القفز في منتصف Step sequence": "step_sequence",
    "تمرين القفزة الرباعية من توقف": "quad_jump",
    "تمرين الإطالة في الهواء": "triple_jump",
    "تمرين في النصف الثاني من البرنامج": "jump_combination",
    "تمرين المحور (Axis training)": "spin_axis",
    "تمرين سرعة الدوران": "spin_axis",
    "تمرين الانتقال بين المواضع": "combo_spin",
    "تمرين الدخول المتنوع للسبين": "combo_spin",
    "تمرين الحافات العميقة": "deep_edges",
    "Brackets, Rockers, Counters": "step_sequence",
    "تمرين سرعة الـ Crossovers": "crossovers",
    "تمرين Step sequence إيقاعي": "step_sequence",
    "تمرين التزلج الكامل للحلبة": "crossovers",
    "تمرين ربط العناصر بالموسيقى": "choreography",
    "تمرين التعبير عن المشاعر": "choreography",
    "تمرين Transitions مبتكرة": "choreography",
}


def get_media(exercise_name_ar: str) -> dict:
    """Get media data for an exercise by its Arabic name"""
    key = EXERCISE_TO_MEDIA_KEY.get(exercise_name_ar)
    if key and key in EXERCISE_MEDIA:
        return EXERCISE_MEDIA[key]
    return None


def render_media_html(media: dict, compact: bool = False) -> str:
    """Render media sources as HTML link buttons"""
    if not media:
        return ""
    links_html = ""
    for src in media.get("sources", []):
        links_html += f'<a href="{src["url"]}" target="_blank" style="display:inline-block; margin:3px; padding:6px 12px; background:#1f77b4; color:white; border-radius:20px; text-decoration:none; font-size:0.85em;">{src["label"]}</a>'
    return links_html
