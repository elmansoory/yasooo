"""
My Videos Page — عرض وتحليل الفيديوهات المكتشفة تلقائياً
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict

import streamlit as st
import pandas as pd


DB_PATH   = "skating_database.db"
JSON_PATH = "data/scanned_videos/all_videos.json"
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.m4v', '.flv', '.webm', '.mts', '.3gp'}


# ── Data loading ────────────────────────────────────────────────────────────

def _load_from_db() -> List[Dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT filepath, filename, size_mb, duration, width, height, fps, "
            "label, analyzed, scan_date FROM discovered_videos ORDER BY filename"
        ).fetchall()
        conn.close()
        cols = ['filepath', 'filename', 'size_mb', 'duration',
                'width', 'height', 'fps', 'label', 'analyzed', 'scan_date']
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def _load_from_json() -> List[Dict]:
    try:
        with open(JSON_PATH, encoding='utf-8') as f:
            data = json.load(f)
        return data.get('videos', [])
    except Exception:
        return []


def _load_videos() -> List[Dict]:
    videos = _load_from_db()
    if not videos:
        videos = _load_from_json()
    return videos


def _update_label(filepath: str, label: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE discovered_videos SET label=? WHERE filepath=?",
            (label, filepath)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _mark_analyzed(filepath: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "UPDATE discovered_videos SET analyzed=1 WHERE filepath=?",
            (filepath,)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Page ────────────────────────────────────────────────────────────────────

def show_my_videos(lang: str = 'ar'):
    ar = lang == 'ar'

    title  = "🎬 فيديوهاتي" if ar else "🎬 My Videos"
    st.title(title)

    videos = _load_videos()

    if not videos:
        st.info(
            "لم يُعثر على فيديوهات. شغّل YASOOO.bat مرة أخرى ليبدأ المسح التلقائي."
            if ar else
            "No videos found. Run YASOOO.bat again to trigger automatic scan."
        )
        if st.button("🔍 مسح الآن" if ar else "🔍 Scan Now"):
            _run_scan()
        return

    # ── Stats bar ──────────────────────────────────────────────────────────
    total      = len(videos)
    labeled    = sum(1 for v in videos if v.get('label'))
    analyzed   = sum(1 for v in videos if v.get('analyzed'))
    total_gb   = sum(v.get('size_mb') or 0 for v in videos) / 1024

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("إجمالي الفيديوهات" if ar else "Total Videos", total)
    c2.metric("مُصنَّف"            if ar else "Labeled",       labeled)
    c3.metric("محلَّل"             if ar else "Analyzed",      analyzed)
    c4.metric("الحجم الكلي"       if ar else "Total Size",    f"{total_gb:.1f} GB")

    st.divider()

    # ── Filters ────────────────────────────────────────────────────────────
    col_search, col_ext, col_status = st.columns([3, 1, 1])

    with col_search:
        search = st.text_input(
            "🔍 بحث باسم الملف" if ar else "🔍 Search by filename",
            placeholder="axel, lutz, spin ..."
        )

    with col_ext:
        all_exts = sorted({Path(v['filepath']).suffix.lower()
                           for v in videos if v.get('filepath')})
        ext_filter = st.selectbox(
            "الصيغة" if ar else "Format",
            ["الكل" if ar else "All"] + all_exts
        )

    with col_status:
        status_filter = st.selectbox(
            "الحالة" if ar else "Status",
            ["الكل" if ar else "All",
             "غير مُصنَّف" if ar else "Unlabeled",
             "محلَّل" if ar else "Analyzed"]
        )

    # Apply filters
    filtered = videos
    if search:
        filtered = [v for v in filtered
                    if search.lower() in (v.get('filename') or '').lower()]
    if ext_filter not in ('الكل', 'All'):
        filtered = [v for v in filtered
                    if Path(v.get('filepath', '')).suffix.lower() == ext_filter]
    if status_filter in ('غير مُصنَّف', 'Unlabeled'):
        filtered = [v for v in filtered if not v.get('label')]
    elif status_filter in ('محلَّل', 'Analyzed'):
        filtered = [v for v in filtered if v.get('analyzed')]

    st.caption(f"{'عرض' if ar else 'Showing'} {len(filtered)} {'من' if ar else 'of'} {total}")

    # ── Table ──────────────────────────────────────────────────────────────
    if not filtered:
        st.info("لا توجد نتائج" if ar else "No results")
        return

    LABELS = [
        "", "Axel_1", "Axel_2", "Axel_3", "Axel_4",
        "Lutz_1", "Lutz_2", "Lutz_3", "Lutz_4",
        "Flip_1", "Flip_2", "Flip_3", "Flip_4",
        "Loop_1", "Loop_2", "Loop_3", "Loop_4",
        "Salchow_1", "Salchow_2", "Salchow_3", "Salchow_4",
        "ToeLoop_1", "ToeLoop_2", "ToeLoop_3", "ToeLoop_4",
        "Upright", "Sit", "Camel", "Layback", "Combination",
        "StepSequence", "Spiral", "None",
    ]

    # Show 20 per page
    PAGE_SIZE = 20
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.number_input(
        "الصفحة" if ar else "Page",
        min_value=1, max_value=total_pages, value=1, step=1
    )
    page_videos = filtered[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    for v in page_videos:
        fp   = v.get('filepath', '')
        name = v.get('filename', fp)
        dur  = v.get('duration')
        size = v.get('size_mb', 0)
        lbl  = v.get('label') or ''
        done = v.get('analyzed', 0)

        with st.expander(
            f"{'✅' if done else ('🏷️' if lbl else '📹')}  {name}"
            f"  |  {f'{dur:.0f}s' if dur else '?s'}"
            f"  |  {size:.1f} MB"
        ):
            col_info, col_action = st.columns([2, 1])

            with col_info:
                st.caption(fp)
                w, h, fps = v.get('width'), v.get('height'), v.get('fps')
                if w and h:
                    st.caption(f"{w}×{h}  @{fps:.0f}fps" if fps else f"{w}×{h}")

                # Preview if file exists
                if Path(fp).exists():
                    if st.checkbox(
                        "معاينة" if ar else "Preview",
                        key=f"prev_{fp}"
                    ):
                        st.video(fp)

            with col_action:
                # Label selector
                cur_idx = LABELS.index(lbl) if lbl in LABELS else 0
                new_lbl = st.selectbox(
                    "التسمية" if ar else "Label",
                    LABELS, index=cur_idx,
                    key=f"lbl_{fp}"
                )
                if new_lbl != lbl:
                    _update_label(fp, new_lbl)
                    st.success("✓")

                # Analyze button
                if Path(fp).exists():
                    if st.button(
                        "🤖 تحليل" if ar else "🤖 Analyze",
                        key=f"analyze_{fp}"
                    ):
                        _analyze_video(fp, ar)
                        _mark_analyzed(fp)
                        st.rerun()
                else:
                    st.error("الملف غير موجود" if ar else "File not found")

    # ── Bulk train button ──────────────────────────────────────────────────
    st.divider()
    labeled_count = sum(1 for v in videos if v.get('label'))
    if labeled_count >= 10:
        st.success(
            f"✅ لديك {labeled_count} فيديو مُصنَّف — يمكنك تدريب النموذج!"
            if ar else
            f"✅ You have {labeled_count} labeled videos — ready to train!"
        )
        if st.button("🧠 ابدأ تدريب النموذج" if ar else "🧠 Train Model"):
            _train_model(videos, ar)
    else:
        st.info(
            f"صنِّف {10 - labeled_count} فيديو إضافية لبدء تدريب النموذج"
            if ar else
            f"Label {10 - labeled_count} more videos to enable model training"
        )

    # ── Rescan button ──────────────────────────────────────────────────────
    if st.button("🔍 إعادة مسح الجهاز" if ar else "🔍 Rescan Device"):
        with st.spinner("جارٍ المسح..." if ar else "Scanning..."):
            _run_scan()
        st.rerun()


# ── Actions ─────────────────────────────────────────────────────────────────

def _run_scan():
    import subprocess, sys
    subprocess.run(
        [sys.executable, "setup_auto.py", "--scan-videos"],
        capture_output=True
    )


def _analyze_video(filepath: str, ar: bool):
    try:
        from src.pages.video_analysis_page import SkatingVideoAnalyzer
        with st.spinner("جارٍ التحليل..." if ar else "Analyzing..."):
            analyzer = SkatingVideoAnalyzer()
            results = analyzer.analyze(filepath)

        if 'error' in results:
            st.error(results['error'])
            return

        jumps = results.get('jumps', [])
        spins = results.get('spins', [])
        score = results.get('total_score', 0)
        tes   = results.get('tes', 0)
        pcs   = results.get('pcs', 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("🏆 النقاط", f"{score:.2f}")
        c2.metric("⚡ TES", f"{tes:.2f}")
        c3.metric("🎭 PCS", f"{pcs:.2f}")

        if jumps:
            st.markdown("**🦘 القفزات المكتشفة:**" if ar else "**🦘 Detected Jumps:**")
            for j in jumps:
                clean = "✅" if j.get('is_clean', True) else "⚠️"
                st.write(
                    f"{clean} {j.get('type', '')} | "
                    f"{j.get('rotations', 0):.1f} دوران | "
                    f"{j.get('height_cm', 0)} cm | "
                    f"GOE: {j.get('goe', 0):+d} | "
                    f"{j.get('final_score', 0):.2f} pts"
                )

        if spins:
            st.markdown("**🌀 الدورانات المكتشفة:**" if ar else "**🌀 Detected Spins:**")
            for s in spins:
                st.write(
                    f"• {s.get('type', '')} | "
                    f"{s.get('rotations', 0):.1f} دوران | "
                    f"{s.get('rpm', 0):.0f} RPM | "
                    f"{s.get('final_score', 0):.2f} pts"
                )

        if not jumps and not spins:
            st.info("لم يُكتشف أي عنصر" if ar else "No elements detected")

        # Save to DB
        try:
            import json, sqlite3
            conn = sqlite3.connect(DB_PATH)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT, session_note TEXT, analyzed_at TEXT,
                    duration REAL, total_score REAL, tes REAL, pcs REAL,
                    jumps_count INTEGER, spins_count INTEGER, errors_count INTEGER,
                    jump_details TEXT, spin_details TEXT
                )
            """)
            from datetime import datetime
            conn.execute(
                "INSERT INTO analysis_results (player_name,session_note,analyzed_at,"
                "duration,total_score,tes,pcs,jumps_count,spins_count,errors_count,"
                "jump_details,spin_details) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (Path(filepath).stem, filepath,
                 datetime.now().strftime('%Y-%m-%d %H:%M'),
                 results.get('video_info', {}).get('duration', 0),
                 score, tes, pcs, len(jumps), len(spins),
                 len(results.get('errors', [])),
                 json.dumps(jumps, ensure_ascii=False),
                 json.dumps(spins, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
            st.caption("✅ " + ("تم الحفظ في السجل" if ar else "Saved to history"))
        except Exception:
            pass

    except Exception as e:
        st.error(f"خطأ في التحليل: {e}" if ar else f"Analysis error: {e}")


def _train_model(videos: List[Dict], ar: bool):
    import subprocess, sys

    labeled = [v for v in videos if v.get('label') and Path(v['filepath']).exists()]
    if len(labeled) < 10:
        st.warning("عدد الفيديوهات المُصنَّفة غير كافٍ (10 على الأقل)")
        return

    # Copy labeled videos to data/labeled with JSON sidecars
    import shutil
    labeled_dir = Path("data/labeled")
    labeled_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for v in labeled:
        src  = Path(v['filepath'])
        dest = labeled_dir / src.name
        if not dest.exists():
            try:
                shutil.copy2(src, dest)
            except Exception:
                continue
        # Write sidecar JSON
        sidecar = dest.with_suffix('.json')
        if not sidecar.exists():
            sidecar.write_text(
                json.dumps({'label': v['label']}, ensure_ascii=False),
                encoding='utf-8'
            )
        copied += 1

    st.info(
        f"تم نسخ {copied} فيديو إلى data/labeled — جارٍ التدريب..."
        if ar else
        f"Copied {copied} videos to data/labeled — training..."
    )

    with st.spinner("التدريب قد يستغرق عدة دقائق..." if ar else "Training may take a few minutes..."):
        result = subprocess.run(
            [sys.executable, "train_model.py",
             "--data_dir", "data/labeled",
             "--out", "data/models/lstm_model.pkl",
             "--epochs", "30"],
            capture_output=True, text=True
        )

    if result.returncode == 0:
        st.success("✅ تم تدريب النموذج بنجاح! أعد تشغيل التطبيق لتفعيله."
                   if ar else
                   "✅ Model trained successfully! Restart the app to activate it.")
        st.code(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    else:
        st.error("فشل التدريب" if ar else "Training failed")
        st.code(result.stderr[-1000:])
