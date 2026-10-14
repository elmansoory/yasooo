"""
readiness_rubric.py — Physical Readiness Tracker: original rubric definition

Original content for YASOOO. Informed by the general, widely-known concept
that off-ice physical readiness for skaters is commonly assessed across a
handful of categories (strength, mobility, balance, explosive power,
rotational control) with one reusable scoring rubric whose per-exercise
targets simply scale up by competitive level — NOT a reproduction of any
specific paid program's exercise list, wording, or numeric targets.

See PROJECT_LOG.md §5 rule #9 for the no-copyrighted-text policy this
follows.
"""
from __future__ import annotations
from typing import Dict, List

LEVELS: List[str] = [
    "Pre-Preliminary", "Preliminary", "Pre-Juvenile", "Juvenile",
    "Intermediate", "Novice", "Junior", "Senior",
]

SCORE_LABELS: Dict[int, Dict[str, str]] = {
    1: {"ar": "غير مكتمل", "en": "Incomplete"},
    2: {"ar": "مقبول", "en": "Fair"},
    3: {"ar": "جيد", "en": "Good"},
    4: {"ar": "ممتاز", "en": "Excellent"},
}

LEVEL_UP_MIN_SCORE = 3  # every exercise must reach at least "Good"

# Each exercise has a base_target at Pre-Preliminary (level index 0) and a
# per-level increment — the target scales automatically with level instead
# of hardcoding 8 separate numbers per exercise.
PILLARS: Dict[str, List[Dict]] = {
    "Strength": [
        {"name_ar": "ثبات القرفصاء على قدم واحدة", "name_en": "Single-Leg Squat Hold",
         "unit_ar": "ثانية", "unit_en": "sec", "base_target": 10, "increment": 4},
        {"name_ar": "ثبات اللوح الأمامي", "name_en": "Front Plank Hold",
         "unit_ar": "ثانية", "unit_en": "sec", "base_target": 20, "increment": 10},
        {"name_ar": "اندفاع الورك (Hip Thrust)", "name_en": "Hip Thrust",
         "unit_ar": "تكرار", "unit_en": "reps", "base_target": 8, "increment": 2},
    ],
    "Mobility": [
        {"name_ar": "انحناء أمامي (مسافة الأصابع-الأرض)", "name_en": "Forward Fold Reach",
         "unit_ar": "سم من الأرض", "unit_en": "cm from floor", "base_target": 15, "increment": -2},
        {"name_ar": "مرونة الورك الدورانية", "name_en": "Hip Rotational Mobility",
         "unit_ar": "درجة", "unit_en": "degrees", "base_target": 30, "increment": 8},
        {"name_ar": "مرونة الكتف العلوية", "name_en": "Overhead Shoulder Mobility",
         "unit_ar": "تقييم وصفي", "unit_en": "qualitative demo", "base_target": 0, "increment": 0},
    ],
    "Balance": [
        {"name_ar": "ثبات التوازن على قدم واحدة (عينان مغلقتان)", "name_en": "Single-Leg Balance (eyes closed)",
         "unit_ar": "ثانية", "unit_en": "sec", "base_target": 8, "increment": 4},
        {"name_ar": "مشي خط مستقيم على كعب-أصابع", "name_en": "Heel-to-Toe Line Walk",
         "unit_ar": "خطوة بلا خطأ", "unit_en": "steps no error", "base_target": 6, "increment": 2},
    ],
    "Plyometrics": [
        {"name_ar": "قفزة طبل عمودية متتالية", "name_en": "Consecutive Tuck Jumps",
         "unit_ar": "تكرار نظيف", "unit_en": "clean reps", "base_target": 5, "increment": 3},
        {"name_ar": "قفزة أحادية القدم للمسافة", "name_en": "Single-Leg Bound for Distance",
         "unit_ar": "تقييم وصفي", "unit_en": "qualitative demo", "base_target": 0, "increment": 0},
    ],
    "Rotations": [
        {"name_ar": "دوران محوري ثابت خارج الجليد", "name_en": "Off-Ice Axis Spin Hold",
         "unit_ar": "دورة متزنة", "unit_en": "stable rotations", "base_target": 3, "increment": 2},
        {"name_ar": "دوران مطوي خارج الجليد (كرسي/قرص)", "name_en": "Off-Ice Tuck Rotation Drill",
         "unit_ar": "تقييم وصفي", "unit_en": "qualitative demo", "base_target": 0, "increment": 0},
    ],
}


def target_for_level(exercise: Dict, level: str) -> str:
    """Human-readable target for this exercise at this level."""
    if level not in LEVELS:
        return "—"
    idx = LEVELS.index(level)
    base = exercise.get("base_target", 0)
    inc = exercise.get("increment", 0)
    if base == 0 and inc == 0:
        return "—"
    value = base + inc * idx
    return str(max(value, 0))


def all_exercises_flat() -> List[Dict]:
    """Flat list of (pillar, exercise) pairs, for iterating in the UI."""
    out = []
    for pillar, exercises in PILLARS.items():
        for ex in exercises:
            out.append({"pillar": pillar, **ex})
    return out
