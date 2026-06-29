"""
الكتالوج الكامل لعناصر الاتحاد الدولي للتزلج (ISU) — قفزات، دورانات،
متتاليات خطوات، متتالية كوريوغرافيا — مع القيم الأساسية (Base Value).

Full ISU element catalog — jumps, spins, step sequences, choreo sequence —
with their Base Values, built from the existing `ISUStandards` reference
table (src/config/isu_standards.py) so the whole app shares one source
of truth for element values.
"""

from typing import Dict, List

from src.config.isu_standards import ISUStandards

_LEVEL_NAME_AR = {0: '', 1: 'مستوى 1', 2: 'مستوى 2', 3: 'مستوى 3', 4: 'مستوى 4'}
_LEVEL_NAME_EN = {0: '', 1: 'Level 1', 2: 'Level 2', 3: 'Level 3', 4: 'Level 4'}

# Choreographic Sequence's official base value (ISUStandards stores 0.0 as a
# legacy placeholder; current ISU Scale of Values uses a fixed 3.00).
CHOREO_SEQUENCE_BASE_VALUE = 3.00


def build_catalog() -> List[Dict]:
    """يبني قائمة مسطّحة بجميع عناصر ISU (قفزات/دورانات/متتاليات)."""
    rows: List[Dict] = []

    # ── Jumps ─────────────────────────────────────────────────────────────
    for code, info in ISUStandards.JUMPS.items():
        rows.append({
            'category': 'قفزات', 'category_en': 'Jumps',
            'code': code,
            'name_ar': info['name_ar'],
            'name_en': info['name'],
            'level': int(code[0]),
            'base_value': info['base_value'],
            'edge': info.get('edge', ''),
            'toe_pick': info.get('toe_pick', False),
        })

    # ── Spins ─────────────────────────────────────────────────────────────
    for code, info in ISUStandards.SPINS.items():
        for lvl, bv in enumerate(info['base_values']):
            if lvl == 0:
                continue
            rows.append({
                'category': 'دورانات', 'category_en': 'Spins',
                'code': f"{code}{lvl}",
                'name_ar': f"{info['name_ar']} — {_LEVEL_NAME_AR[lvl]}",
                'name_en': f"{info['name']} — {_LEVEL_NAME_EN[lvl]}",
                'level': lvl,
                'base_value': bv,
                'edge': '', 'toe_pick': False,
            })

    # ── Step sequences ────────────────────────────────────────────────────
    stsq = ISUStandards.STEP_SEQUENCES['StSq']
    for lvl, bv in enumerate(stsq['base_values']):
        if lvl == 0:
            continue
        rows.append({
            'category': 'متتاليات خطوات', 'category_en': 'Step Sequences',
            'code': f"StSq{lvl}",
            'name_ar': f"{stsq['name_ar']} — {_LEVEL_NAME_AR[lvl]}",
            'name_en': f"{stsq['name']} — {_LEVEL_NAME_EN[lvl]}",
            'level': lvl,
            'base_value': bv,
            'edge': '', 'toe_pick': False,
        })

    # ── Choreo sequence (single, non-leveled) ───────────────────────────────
    chsq = ISUStandards.STEP_SEQUENCES['ChSq']
    rows.append({
        'category': 'متتالية كوريوغرافيا', 'category_en': 'Choreo Sequence',
        'code': 'ChSq1',
        'name_ar': chsq['name_ar'],
        'name_en': chsq['name'],
        'level': 1,
        'base_value': CHOREO_SEQUENCE_BASE_VALUE,
        'edge': '', 'toe_pick': False,
    })

    return rows


ISU_ELEMENTS_CATALOG: List[Dict] = build_catalog()


def find_by_code(code: str) -> Dict:
    """يبحث عن عنصر بالكود الرسمي (مثال: '3Lz', 'CCoSp4', 'StSq3')."""
    for row in ISU_ELEMENTS_CATALOG:
        if row['code'] == code:
            return row
    return {}
