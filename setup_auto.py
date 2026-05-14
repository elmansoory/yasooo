"""
setup_auto.py — Automatic setup and video discovery
يعمل تلقائياً عند تشغيل YASOOO.bat

يقوم بـ:
1. مسح جميع محركات الأقراص عن الفيديوهات
2. حفظ قائمة الفيديوهات في قاعدة البيانات
3. إعداد المجلدات اللازمة
"""

import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Video extensions ────────────────────────────────────────────────────────
VIDEO_EXTS = {
    '.mp4', '.mov', '.avi', '.mkv', '.wmv',
    '.m4v', '.flv', '.webm', '.mts', '.m2ts',
    '.3gp', '.ts', '.mpg', '.mpeg',
}

# Folders to skip (system, temp, etc.)
SKIP_DIRS = {
    'windows', 'system32', 'syswow64', 'program files', 'programdata',
    'appdata', '$recycle.bin', 'system volume information',
    'recovery', 'boot', 'perflogs', 'msocache', 'intel',
    'node_modules', '__pycache__', '.git',
}


def get_windows_drives():
    """Return all available drive letters on Windows."""
    import string
    import os
    drives = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if Path(drive).exists():
            try:
                os.listdir(drive)
                drives.append(drive)
            except PermissionError:
                pass
    return drives


def scan_for_videos(roots=None, max_per_drive=5000):
    """
    Scan all drives (or specified roots) for video files.
    Returns list of Path objects.
    """
    if roots is None:
        try:
            roots = get_windows_drives()
        except Exception:
            roots = [str(Path.home()), "C:\\"]

    found = []
    print(f"  مسح المحركات: {roots}")

    for root in roots:
        root_path = Path(root)
        if not root_path.exists():
            continue

        count = 0
        try:
            for p in root_path.rglob("*"):
                try:
                    # Skip system/hidden dirs
                    parts_lower = {part.lower() for part in p.parts}
                    if parts_lower & SKIP_DIRS:
                        continue

                    if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
                        found.append(p)
                        count += 1
                        if count % 100 == 0:
                            print(f"    {root}: وُجد {count} فيديو...")
                        if count >= max_per_drive:
                            print(f"    {root}: وصل الحد الأقصى ({max_per_drive})")
                            break
                except (PermissionError, OSError):
                    continue
        except (PermissionError, OSError):
            print(f"    {root}: لا يمكن الوصول")
            continue

        print(f"    {root}: ✓ {count} فيديو")

    return found


def get_video_info(path: Path):
    """Get basic video info using opencv if available."""
    info = {
        'filepath': str(path),
        'filename': path.name,
        'size_mb': round(path.stat().st_size / (1024 * 1024), 2),
        'duration': None,
        'width': None,
        'height': None,
        'fps': None,
    }
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            fc  = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            info['fps']      = round(fps, 2) if fps > 0 else None
            info['duration'] = round(fc / fps, 1) if fps > 0 else None
            info['width']    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            info['height']   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
    except Exception:
        pass
    return info


def save_to_db(videos_info: list, db_path: str):
    """Save discovered videos into the skating database."""
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS discovered_videos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath    TEXT UNIQUE,
            filename    TEXT,
            size_mb     REAL,
            duration    REAL,
            width       INTEGER,
            height      INTEGER,
            fps         REAL,
            label       TEXT DEFAULT NULL,
            analyzed    INTEGER DEFAULT 0,
            scan_date   TEXT
        )
    """)

    now = datetime.now().isoformat()
    inserted = 0
    for v in videos_info:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO discovered_videos
                  (filepath, filename, size_mb, duration, width, height, fps, scan_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                v['filepath'], v['filename'], v['size_mb'],
                v['duration'], v['width'], v['height'], v['fps'], now,
            ))
            inserted += cur.rowcount
        except Exception:
            continue

    conn.commit()

    total = cur.execute("SELECT COUNT(*) FROM discovered_videos").fetchone()[0]
    conn.close()
    return inserted, total


def save_to_json(videos_info: list, json_path: str):
    """Also save as JSON for the app to read without DB."""
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'scan_date': datetime.now().isoformat(),
            'total': len(videos_info),
            'videos': videos_info,
        }, f, ensure_ascii=False, indent=2)


def setup_directories():
    """Create required app directories."""
    for d in ['data/labeled', 'data/models', 'data/exports',
              'data/scanned_videos', 'cache']:
        Path(ROOT / d).mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan-videos', action='store_true',
                        help='Scan all drives for video files')
    parser.add_argument('--drives', nargs='+',
                        help='Specific drives to scan e.g. C:\\ D:\\')
    parser.add_argument('--max', type=int, default=5000,
                        help='Max videos per drive (default 5000)')
    args = parser.parse_args()

    # ── Always: create directories ────────────────────────────────────────
    setup_directories()
    print("  ✓ المجلدات جاهزة")

    if not args.scan_videos:
        return

    # ── Scan for videos ───────────────────────────────────────────────────
    print("\n  ابدأ مسح الفيديوهات على الجهاز...")
    print("  (قد يستغرق دقيقة أو أكثر حسب حجم القرص)")

    roots = args.drives if args.drives else None
    video_paths = scan_for_videos(roots=roots, max_per_drive=args.max)

    if not video_paths:
        print("  لم يُعثر على فيديوهات.")
        return

    print(f"\n  جمع المعلومات عن {len(video_paths)} فيديو...")
    videos_info = []
    for i, p in enumerate(video_paths):
        if i % 200 == 0 and i > 0:
            print(f"    {i}/{len(video_paths)}...")
        try:
            videos_info.append(get_video_info(p))
        except Exception:
            videos_info.append({'filepath': str(p), 'filename': p.name,
                                'size_mb': 0, 'duration': None,
                                'width': None, 'height': None, 'fps': None})

    # ── Save results ──────────────────────────────────────────────────────
    db_path   = str(ROOT / 'skating_database.db')
    json_path = str(ROOT / 'data/scanned_videos/all_videos.json')

    inserted, total = save_to_db(videos_info, db_path)
    save_to_json(videos_info, json_path)

    print(f"\n  ✓ اكتمل المسح:")
    print(f"    • فيديوهات جديدة أُضيفت: {inserted}")
    print(f"    • إجمالي الفيديوهات في قاعدة البيانات: {total}")
    print(f"    • ملف JSON: {json_path}")

    # Print breakdown by extension
    from collections import Counter
    ext_count = Counter(Path(v['filepath']).suffix.lower() for v in videos_info)
    print("\n  توزيع الصيغ:")
    for ext, cnt in ext_count.most_common():
        print(f"    {ext:<8} {cnt} ملف")


if __name__ == '__main__':
    main()
