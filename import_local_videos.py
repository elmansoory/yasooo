"""
import_local_videos.py — استيراد فيديوهات من مجلد محدد على جهازك
يُستخدم عندما تريد فحص مجلد بعينه (بدل مسح كل الأقراص كما يفعل setup_auto.py
تلقائياً عند تشغيل YASOOO.bat).

الاستخدام:
    python import_local_videos.py "I:\\Gaming Drv\\Off Ice"
    python import_local_videos.py "I:\\Gaming Drv\\Off Ice" "D:\\Another Folder"

بعد التشغيل، افتح صفحة "🎬 فيديوهاتي" في التطبيق لتصنيف الفيديوهات المكتشفة
وبدء التدريب.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from setup_auto import scan_for_videos, get_video_info, save_to_db, save_to_json  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print('الاستخدام: python import_local_videos.py "المسار\\للمجلد" [مسار آخر ...]')
        print(r'مثال:     python import_local_videos.py "I:\Gaming Drv\Off Ice"')
        sys.exit(1)

    roots = sys.argv[1:]
    for r in roots:
        if not Path(r).exists():
            print(f"⚠️  تحذير: المسار غير موجود أو غير قابل للوصول: {r}")

    print(f"جارٍ مسح {len(roots)} مجلد(ات)...")
    video_paths = scan_for_videos(roots=roots, max_per_drive=20000)

    if not video_paths:
        print("لم يُعثر على أي فيديوهات في المسار(ات) المحددة.")
        sys.exit(0)

    print(f"\nجمع المعلومات عن {len(video_paths)} فيديو...")
    videos_info = []
    for i, p in enumerate(video_paths):
        if i % 50 == 0 and i > 0:
            print(f"  {i}/{len(video_paths)}...")
        try:
            videos_info.append(get_video_info(p))
        except Exception:
            videos_info.append({'filepath': str(p), 'filename': p.name,
                                'size_mb': 0, 'duration': None,
                                'width': None, 'height': None, 'fps': None})

    db_path   = str(ROOT / 'skating_database.db')
    json_path = str(ROOT / 'data/scanned_videos/all_videos.json')

    inserted, total = save_to_db(videos_info, db_path)
    save_to_json(videos_info, json_path)

    print("\n✓ اكتمل الاستيراد:")
    print(f"  • فيديوهات جديدة أُضيفت: {inserted}")
    print(f"  • إجمالي الفيديوهات المكتشفة في قاعدة البيانات: {total}")
    print("\nافتح التطبيق ثم اذهب لصفحة \"🎬 فيديوهاتي\" لتصنيف الفيديوهات وبدء التدريب.")


if __name__ == '__main__':
    main()
