"""
auto_suggest_labels.py — اقتراح تصنيف تلقائي للفيديوهات المكتشفة (غير مؤكَّد)

يشغّل نفس محرك الكشف المستخدم في "🤖 تحليل" (SkatingVideoAnalyzer) على كل فيديو
لم يُصنَّف بعد في discovered_videos، ويكتب أفضل تخمين كـ"اقتراح تلقائي"
(label_source='auto') — وليس تصنيفاً نهائياً. الاقتراحات **لا تُحتسب في تدريب
النموذج** حتى يراجعها المدرب ويؤكّدها من صفحة "🎬 فيديوهاتي" (لتفادي تلويث
بيانات التدريب باقتراحات غير مُتحقَّق منها — انظر PROJECT_LOG.md §5 قاعدة #1).

ملاحظة صادقة عن دقة الكاشف الحالي: يميّز Axel/Lutz/Flip/ToeLoop تقريبياً من
زمن الطيران فقط، ولا يميّز Salchow/Loop إطلاقاً بعد (راجع _classify_jump في
video_analysis_page.py) — الاقتراحات مفيدة كنقطة بداية سريعة للمراجعة، وليست
بديلاً عن نظر المدرب.

الاستخدام:
    python auto_suggest_labels.py                 # يعالج أول 30 فيديو غير مُصنَّف
    python auto_suggest_labels.py --limit 100
    python auto_suggest_labels.py --dry-run        # يطبع الاقتراحات بدون كتابتها
"""

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

DB_PATH = str(ROOT / "skating_database.db")

# Filename keywords that strongly indicate off-ice footage (gym/conditioning/
# stretching) rather than on-ice skating with jumps/spins. The jump/spin
# detector has no concept of "off ice" — on real off-ice clips it was
# observed to misread ordinary body motion as a low-confidence jump and
# guess "Axel_1" almost every time, which is worse than no suggestion at
# all. These clips are filtered out BEFORE running the (slow, and on this
# content meaningless) pose analyzer — cheap and avoids the false guesses.
_OFF_ICE_KEYWORDS = [
    'workout', 'stretch', 'flexib', 'gym', 'fitness', 'cardio',
    'warm up', 'warmup', 'warm-up', 'conditioning', 'home workout',
    'ballet', 'yoga', 'pilates', 'abs', 'core workout', 'strength',
    'off-ice', 'off ice', 'dryland', 'dry land', 'plyometric',
    'تمارين', 'لياقة', 'إحماء', 'اطالة', 'إطالة', 'خارج الجليد',
]


def _looks_off_ice(filename: str) -> bool:
    name = filename.lower()
    return any(kw in name for kw in _OFF_ICE_KEYWORDS)


# code prefix -> LABELS family name (matches my_videos_page.py's LABELS list)
_JUMP_FAMILY = {
    'A': 'Axel', 'Lz': 'Lutz', 'F': 'Flip',
    'Lo': 'Loop', 'S': 'Salchow', 'T': 'ToeLoop',
}
_SPIN_FAMILY = {
    'USp': 'Upright', 'SSp': 'Sit', 'CSp': 'Camel', 'LSp': 'Layback',
    'CoSp': 'Combination', 'CCoSp': 'Combination',
}


def _map_jump_code(code: str) -> str:
    """'3Lz' -> 'Lutz_3', '4T' -> 'ToeLoop_4', '1A' -> 'Axel_1'."""
    digits = ''.join(c for c in code if c.isdigit())
    suffix = ''.join(c for c in code if not c.isdigit())
    rotations = max(1, min(4, int(digits))) if digits else 1
    family = _JUMP_FAMILY.get(suffix)
    if not family:
        return ''
    return f"{family}_{rotations}"


def _map_spin_code(code: str) -> str:
    return _SPIN_FAMILY.get(code, '')


def _ensure_columns(conn: sqlite3.Connection):
    for stmt in (
        "ALTER TABLE discovered_videos ADD COLUMN label_source TEXT",
        "ALTER TABLE discovered_videos ADD COLUMN athlete_id TEXT",
    ):
        try:
            conn.execute(stmt)
            conn.commit()
        except sqlite3.OperationalError:
            pass


def suggest_label(analyzer, filepath: str) -> str:
    """Returns a best-guess LABELS entry, or 'None' if nothing detected, or
    '' if analysis failed outright (caller should skip writing anything)."""
    try:
        results = analyzer.analyze(filepath)
    except Exception as e:
        print(f"    ⚠️  فشل التحليل: {e}")
        return ''

    if 'error' in results and results['error']:
        print(f"    ⚠️  {results['error']}")
        return ''

    jumps = results.get('jumps', [])
    spins = results.get('spins', [])
    steps = results.get('step_sequences', [])

    # Confidence gate on JUMPS only: discovered live on the user's real
    # library that a seated/standing person talking to camera (coach-
    # explainer videos — nutrition tips, scoring explainers, etc.) can
    # trip the jump detector's "airborne/tucked" pose heuristic, producing
    # a confident-looking jump guess. A height_cm >= 30 floor alone turned
    # out NOT to be enough — re-tested live against the user's real
    # library and it still fired. Every single false positive observed
    # across ~10 real talking-head clips mapped to the exact same bucket:
    # _classify_jump's code '1A' (Single Axel), which is ALSO what any
    # weak/short/noisy "airborne" detection falls into regardless of its
    # height_cm reading (rotations < 1.3 -> always '1A', and height_cm is
    # computed independently from a different signal, so it doesn't
    # reliably gate this bucket). Excluding '1A' entirely from
    # auto-suggestion removes the exact bucket every observed false
    # positive came from — a real Single Axel clip now gets 'None'
    # suggested instead of a wrong-but-confident-looking guess, which is
    # the safer trade-off (still flagged for manual review either way).
    #
    # No spin gate: unlike jumps, no false-positive evidence was observed
    # for spins on the same real talking-head clips, and an early attempt
    # at a rotations>=5 spin gate caused a regression — a real, previously
    # correctly-suggested camel spin clip (confirmed by filename/manual
    # ground truth) only registers 3.0 rotations from a short clip, so a
    # strict floor loses real signal without evidence it filters any noise.
    MIN_JUMP_HEIGHT_CM = 30   # matches _classify_jump's own goe>=0 floor
    EXCLUDED_JUMP_CODES = {'1A'}  # the detector's noise-floor fallback bucket

    if jumps:
        best = max(jumps, key=lambda j: j.get('final_score', 0))
        code = best.get('code', '')
        if code not in EXCLUDED_JUMP_CODES and best.get('height_cm', 0) >= MIN_JUMP_HEIGHT_CM:
            label = _map_jump_code(code)
            if label:
                return label
    if spins:
        best = max(spins, key=lambda s: s.get('final_score', 0))
        label = _map_spin_code(best.get('code', ''))
        if label:
            return label
    if steps:
        return 'StepSequence'
    return 'None'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=30,
                        help='عدد الفيديوهات غير المُصنَّفة لمعالجتها في هذه الدفعة (افتراضي 30)')
    parser.add_argument('--dry-run', action='store_true',
                        help='اطبع الاقتراحات فقط دون كتابتها في قاعدة البيانات')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    _ensure_columns(conn)

    rows = conn.execute(
        "SELECT filepath FROM discovered_videos "
        "WHERE (label IS NULL OR label = '') "
        "ORDER BY filename LIMIT ?",
        (args.limit,)
    ).fetchall()

    if not rows:
        print("لا توجد فيديوهات بدون تصنيف حالياً (أو كلها عولجت في دفعات سابقة).")
        conn.close()
        return

    from src.pages.video_analysis_page import SkatingVideoAnalyzer
    analyzer = SkatingVideoAnalyzer()

    print(f"معالجة {len(rows)} فيديو (دفعة بحد أقصى --limit={args.limit})...")
    suggested, skipped = 0, 0
    off_ice = 0
    for i, (filepath,) in enumerate(rows, 1):
        name = Path(filepath).name
        print(f"  [{i}/{len(rows)}] {name}")
        if not Path(filepath).exists():
            print("    ⚠️  الملف غير موجود، تخطّي")
            skipped += 1
            continue

        if _looks_off_ice(name):
            print("    → خارج الجليد على الأرجح (اسم الملف) — تخصيص Not_Skating بدون تحليل")
            if not args.dry_run:
                conn.execute(
                    "UPDATE discovered_videos SET label='Not_Skating', label_source='auto' "
                    "WHERE filepath=?",
                    (filepath,)
                )
                conn.commit()
            off_ice += 1
            continue

        label = suggest_label(analyzer, filepath)
        if not label:
            skipped += 1
            continue

        print(f"    → اقتراح: {label}")
        if not args.dry_run:
            conn.execute(
                "UPDATE discovered_videos SET label=?, label_source='auto' WHERE filepath=?",
                (label, filepath)
            )
            conn.commit()
        suggested += 1

    conn.close()
    print(f"\n✓ اكتمل: {suggested} اقتراح تزلج، {off_ice} صُنِّف Not_Skating تلقائياً (اسم الملف)، "
          f"{skipped} تخطٍّ. {'(dry-run، لم يُكتب شيء)' if args.dry_run else ''}")
    print(
        "⚠️  فلترة \"خارج الجليد\" تعتمد على اسم الملف فقط — راجع صفحة \"🎬 فيديوهاتي\" "
        "للتأكد من عدم تصنيف أي فيديو تزلج فعلي بالخطأ كـ Not_Skating (اسم ملف مضلِّل مثلاً)."
    )
    print('افتح "🎬 فيديوهاتي" لمراجعة الاقتراحات (🤖) وتأكيدها أو تصحيحها.')
    print(f"شغّل السكربت مجدداً (--limit أعلى) لمعالجة الدفعة التالية من الفيديوهات غير المُصنَّفة.")


if __name__ == '__main__':
    main()
