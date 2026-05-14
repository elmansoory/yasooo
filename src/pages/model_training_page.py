"""
Model Training Page — تدريب نموذج اكتشاف الأخطاء
يدعم:
  - تحميل فيديوهات من YouTube (yt-dlp)
  - استخدام فيديوهات الجهاز المكتشفة
  - تصنيف العناصر وتدريب النموذج
  - عرض دقة النموذج ومتابعة التحسن
"""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

import streamlit as st
import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = str(ROOT / "skating_database.db")

LABELS = [
    "Axel_1","Axel_2","Axel_3","Axel_4",
    "Lutz_1","Lutz_2","Lutz_3","Lutz_4",
    "Flip_1","Flip_2","Flip_3","Flip_4",
    "Loop_1","Loop_2","Loop_3","Loop_4",
    "Salchow_1","Salchow_2","Salchow_3","Salchow_4",
    "ToeLoop_1","ToeLoop_2","ToeLoop_3","ToeLoop_4",
    "Upright","Sit","Camel","Layback","Combination",
    "StepSequence","Spiral","None",
]

YOUTUBE_SEARCH_TERMS = {
    "Axel_1":    "single axel figure skating tutorial",
    "Axel_2":    "double axel figure skating",
    "Axel_3":    "triple axel figure skating",
    "Lutz_3":    "triple lutz figure skating",
    "Flip_3":    "triple flip figure skating",
    "Loop_3":    "triple loop figure skating",
    "Salchow_3": "triple salchow figure skating",
    "ToeLoop_3": "triple toe loop figure skating",
    "Sit":       "sit spin figure skating tutorial",
    "Camel":     "camel spin figure skating tutorial",
    "Upright":   "upright spin figure skating",
    "Layback":   "layback spin figure skating",
    "StepSequence": "step sequence figure skating",
}


# ── DB helpers ──────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_elements_with_youtube() -> List[Dict]:
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, name_ar, name_en, isu_code, element_type, level,
                   youtube_url, base_value
            FROM skating_elements
            WHERE youtube_url IS NOT NULL AND youtube_url != ''
            ORDER BY element_type, level
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_training_videos() -> List[Dict]:
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT id, filepath, filename, source, label, youtube_url,
                   duration, width, height, fps, size_mb, used_in_training
            FROM training_videos
            ORDER BY created_at DESC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_discovered_videos_labeled() -> List[Dict]:
    try:
        conn = get_db()
        rows = conn.execute("""
            SELECT filepath, filename, label, duration, size_mb
            FROM discovered_videos
            WHERE label IS NOT NULL AND label != ''
            ORDER BY filename
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def add_training_video(filepath: str, label: str, source: str = 'local',
                       youtube_url: str = None, duration: float = None,
                       width: int = None, height: int = None,
                       fps: float = None, size_mb: float = None):
    try:
        conn = get_db()
        conn.execute("""
            INSERT OR IGNORE INTO training_videos
              (filepath, filename, source, label, youtube_url,
               duration, width, height, fps, size_mb)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (filepath, Path(filepath).name, source, label, youtube_url,
              duration, width, height, fps, size_mb))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"DB error: {e}")


def get_model_stats() -> Dict:
    model_path = ROOT / "data/models/lstm_model.pkl"
    stats = {
        'exists': model_path.exists(),
        'size_mb': round(model_path.stat().st_size / 1024 / 1024, 2) if model_path.exists() else 0,
        'modified': model_path.stat().st_mtime if model_path.exists() else None,
        'training_count': 0,
        'label_distribution': {},
    }
    videos = get_training_videos() + get_discovered_videos_labeled()
    stats['training_count'] = len(videos)
    for v in videos:
        lbl = v.get('label', 'Unknown') or 'Unknown'
        stats['label_distribution'][lbl] = stats['label_distribution'].get(lbl, 0) + 1
    return stats


# ── YouTube downloader ─────────────────────────────────────────────────────

def is_ytdlp_available() -> bool:
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--version"],
                       capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def install_ytdlp():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "yt-dlp", "-q"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def download_youtube_video(url: str, label: str, out_dir: Path) -> Optional[str]:
    """Download a YouTube video, return local filepath or None on failure."""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_label = label.replace(" ", "_").replace("/", "_")
    out_template = str(out_dir / f"{safe_label}_%(id)s.%(ext)s")

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--format", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
        "--merge-output-format", "mp4",
        "--output", out_template,
        "--no-playlist",
        "--max-filesize", "200m",
        "--quiet",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        return None

    # Find downloaded file
    matches = list(out_dir.glob(f"{safe_label}_*.mp4"))
    return str(matches[0]) if matches else None


def get_video_meta(filepath: str) -> Dict:
    try:
        import cv2
        cap = cv2.VideoCapture(filepath)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        fc  = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return {'duration': round(fc/fps, 1), 'width': w, 'height': h,
                'fps': round(fps, 1), 'size_mb': round(Path(filepath).stat().st_size/1e6, 2)}
    except Exception:
        return {'duration': None, 'width': None, 'height': None,
                'fps': None, 'size_mb': round(Path(filepath).stat().st_size/1e6, 2)}


# ── Training runner ────────────────────────────────────────────────────────

def prepare_labeled_dir(videos: List[Dict]) -> int:
    """Copy/link labeled videos to data/labeled with JSON sidecars."""
    import shutil
    labeled_dir = ROOT / "data/labeled"
    labeled_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for v in videos:
        src = Path(v['filepath'])
        if not src.exists():
            continue
        dest = labeled_dir / src.name
        if not dest.exists():
            try:
                shutil.copy2(src, dest)
            except Exception:
                continue
        sidecar = dest.with_suffix('.json')
        if not sidecar.exists():
            sidecar.write_text(
                json.dumps({'label': v['label']}, ensure_ascii=False),
                encoding='utf-8'
            )
        copied += 1
    return copied


def run_training(epochs: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "train_model.py"),
         "--data_dir", str(ROOT / "data/labeled"),
         "--out",      str(ROOT / "data/models/lstm_model.pkl"),
         "--epochs",   str(epochs)],
        capture_output=True, text=True, cwd=str(ROOT)
    )


# ── Page ───────────────────────────────────────────────────────────────────

def show_model_training_page(lang: str = 'ar'):
    ar = lang == 'ar'
    st.title("🧠 تدريب نموذج الذكاء الاصطناعي" if ar else "🧠 AI Model Training")
    st.caption(
        "كلما أضفت فيديوهات مُصنَّفة، كلما تحسّن النموذج في اكتشاف الأخطاء"
        if ar else
        "More labeled videos = better error detection accuracy"
    )

    stats = get_model_stats()

    # ── Status bar ─────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("حالة النموذج" if ar else "Model Status",
              "✅ مُدرَّب" if stats['exists'] else "⚠️ غير مُدرَّب")
    c2.metric("فيديوهات التدريب" if ar else "Training Videos", stats['training_count'])
    c3.metric("تصنيفات مختلفة" if ar else "Unique Labels",
              len(stats['label_distribution']))
    if stats['exists'] and stats['modified']:
        from datetime import datetime
        dt = datetime.fromtimestamp(stats['modified']).strftime('%Y-%m-%d')
        c4.metric("آخر تدريب" if ar else "Last Trained", dt)
    else:
        c4.metric("حجم النموذج" if ar else "Model Size",
                  f"{stats['size_mb']} MB" if stats['exists'] else "—")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 من YouTube",
        "📂 من الجهاز",
        "🏷️ إدارة التصنيفات",
        "🚀 تدريب النموذج",
    ])

    # ──────────────────────────────────────────────────────────────────────
    # Tab 1: YouTube
    # ──────────────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("تحميل فيديوهات من YouTube" if ar else "Download from YouTube")

        ytdlp_ok = is_ytdlp_available()
        if not ytdlp_ok:
            st.warning("yt-dlp غير مثبت" if ar else "yt-dlp not installed")
            if st.button("⬇️ تثبيت yt-dlp" if ar else "⬇️ Install yt-dlp"):
                with st.spinner("جارٍ التثبيت..." if ar else "Installing..."):
                    ok = install_ytdlp()
                st.success("✅ تم التثبيت" if ok else "❌ فشل التثبيت")
                st.rerun()

        # Elements with YouTube links from DB
        elements = get_elements_with_youtube()
        if elements:
            st.markdown(
                f"**{len(elements)} عنصر بروابط YouTube من ملفات Excel**"
                if ar else
                f"**{len(elements)} elements with YouTube links from Excel files**"
            )

            df = pd.DataFrame(elements)[['name_ar','name_en','isu_code','element_type','level','youtube_url']]
            df.columns = ['عربي','English','Code','Type','Level','YouTube']
            st.dataframe(df, use_container_width=True, height=300)

            st.markdown("---")
            st.subheader("تحميل عنصر بعينه" if ar else "Download specific element")
            col_el, col_lbl = st.columns([2, 1])
            with col_el:
                el_names = [f"{e['name_en']} ({e['isu_code'] or ''})" for e in elements]
                selected_idx = st.selectbox("اختر العنصر" if ar else "Select element",
                                            range(len(el_names)),
                                            format_func=lambda i: el_names[i])
            with col_lbl:
                dl_label = st.selectbox("التسمية" if ar else "Label", LABELS)

            selected_el = elements[selected_idx]
            dl_url = st.text_input(
                "رابط YouTube" if ar else "YouTube URL",
                value=selected_el.get('youtube_url') or ""
            )

            if ytdlp_ok and dl_url and st.button("⬇️ تحميل" if ar else "⬇️ Download"):
                out_dir = ROOT / "data/training_downloads"
                with st.spinner("جارٍ التحميل..." if ar else "Downloading..."):
                    fp = download_youtube_video(dl_url, dl_label, out_dir)
                if fp:
                    meta = get_video_meta(fp)
                    add_training_video(fp, dl_label, 'youtube', dl_url, **meta)
                    st.success(f"✅ تم الحفظ: {Path(fp).name}")
                else:
                    st.error("فشل التحميل — تأكد من الرابط" if ar else "Download failed — check the URL")

        st.divider()
        st.subheader("تحميل دفعة تلقائية" if ar else "Batch auto-download")
        st.info(
            "سيحمّل النظام فيديو واحداً لكل نوع حركة تلقائياً من YouTube"
            if ar else
            "System will auto-download one reference video per movement type from YouTube"
        )

        batch_labels = st.multiselect(
            "اختر العناصر" if ar else "Select elements",
            list(YOUTUBE_SEARCH_TERMS.keys()),
            default=list(YOUTUBE_SEARCH_TERMS.keys())[:6]
        )

        if ytdlp_ok and batch_labels and st.button(
            f"⬇️ تحميل {len(batch_labels)} فيديو" if ar else f"⬇️ Download {len(batch_labels)} videos"
        ):
            out_dir = ROOT / "data/training_downloads"
            progress = st.progress(0)
            log = st.empty()
            ok_count = 0
            for i, lbl in enumerate(batch_labels):
                query  = YOUTUBE_SEARCH_TERMS[lbl]
                yt_url = f"ytsearch1:{query}"
                log.info(f"Downloading: {lbl} …")
                fp = download_youtube_video(yt_url, lbl, out_dir)
                if fp:
                    meta = get_video_meta(fp)
                    add_training_video(fp, lbl, 'youtube', yt_url, **meta)
                    ok_count += 1
                progress.progress((i + 1) / len(batch_labels))
            log.empty()
            st.success(f"✅ تم تحميل {ok_count} من {len(batch_labels)}")

    # ──────────────────────────────────────────────────────────────────────
    # Tab 2: Local device videos
    # ──────────────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("فيديوهات الجهاز المكتشفة" if ar else "Discovered Device Videos")

        discovered = get_discovered_videos_labeled()
        training   = get_training_videos()
        training_fps = {v['filepath'] for v in training}

        if not discovered:
            st.info(
                "لا توجد فيديوهات مُصنَّفة بعد — اذهب إلى صفحة 🎬 فيديوهاتي لتصنيف فيديوهاتك"
                if ar else
                "No labeled videos yet — go to 🎬 My Videos page to label your videos"
            )
        else:
            st.success(
                f"✅ {len(discovered)} فيديو مُصنَّف جاهز للتدريب"
                if ar else
                f"✅ {len(discovered)} labeled videos ready for training"
            )

            df = pd.DataFrame(discovered)
            df['in_training'] = df['filepath'].apply(lambda p: "✅" if p in training_fps else "➕")
            df['size'] = df['size_mb'].apply(lambda s: f"{s:.1f} MB" if s else "?")
            df['dur']  = df['duration'].apply(lambda d: f"{d:.0f}s" if d else "?")
            st.dataframe(
                df[['filename','label','dur','size','in_training']].rename(columns={
                    'filename':'الملف','label':'التسمية',
                    'dur':'المدة','size':'الحجم','in_training':'في التدريب'
                }),
                use_container_width=True
            )

            new_videos = [v for v in discovered if v['filepath'] not in training_fps]
            if new_videos and st.button(
                f"➕ إضافة {len(new_videos)} فيديو للتدريب" if ar
                else f"➕ Add {len(new_videos)} videos to training set"
            ):
                for v in new_videos:
                    meta = get_video_meta(v['filepath'])
                    add_training_video(v['filepath'], v['label'], 'local', **meta)
                st.success("✅ تمت الإضافة")
                st.rerun()

        st.divider()
        st.subheader("رفع فيديو جديد" if ar else "Upload new video")
        uploaded = st.file_uploader(
            "رفع مقطع فيديو" if ar else "Upload video clip",
            type=['mp4','mov','avi','mkv']
        )
        if uploaded:
            upload_label = st.selectbox("تسمية الفيديو" if ar else "Video label",
                                        LABELS, key="upload_lbl")
            if st.button("💾 حفظ" if ar else "💾 Save"):
                save_dir = ROOT / "data/training_uploads"
                save_dir.mkdir(parents=True, exist_ok=True)
                dest = save_dir / uploaded.name
                dest.write_bytes(uploaded.read())
                meta = get_video_meta(str(dest))
                add_training_video(str(dest), upload_label, 'uploaded', **meta)
                st.success(f"✅ {uploaded.name}")

    # ──────────────────────────────────────────────────────────────────────
    # Tab 3: Label management
    # ──────────────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("توزيع البيانات" if ar else "Data Distribution")

        all_vids = get_training_videos() + [
            {'label': v['label'], 'source': 'local'}
            for v in get_discovered_videos_labeled()
        ]

        if not all_vids:
            st.info("لا توجد بيانات بعد" if ar else "No data yet")
        else:
            dist = {}
            for v in all_vids:
                lbl = v.get('label') or 'Unknown'
                dist[lbl] = dist.get(lbl, 0) + 1

            df_dist = pd.DataFrame(
                sorted(dist.items(), key=lambda x: -x[1]),
                columns=['Label', 'Count']
            )
            df_dist['Status'] = df_dist['Count'].apply(
                lambda c: "✅ كافٍ" if c >= 10 else ("⚠️ قليل" if c >= 3 else "❌ يحتاج المزيد")
            )

            st.dataframe(df_dist, use_container_width=True)

            missing = [l for l in LABELS if l not in dist]
            if missing:
                st.warning(
                    f"تحتاج فيديوهات لـ: {', '.join(missing[:8])}{'...' if len(missing)>8 else ''}"
                    if ar else
                    f"Need videos for: {', '.join(missing[:8])}{'...' if len(missing)>8 else ''}"
                )

            import plotly.express as px
            fig = px.bar(df_dist.head(20), x='Label', y='Count',
                         color='Count', color_continuous_scale='Blues')
            fig.update_layout(height=300, margin=dict(t=20, b=40))
            st.plotly_chart(fig, use_container_width=True)

    # ──────────────────────────────────────────────────────────────────────
    # Tab 4: Train model
    # ──────────────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("تدريب النموذج" if ar else "Train Model")

        all_labeled = get_training_videos() + [
            {'filepath': v['filepath'], 'label': v['label']}
            for v in get_discovered_videos_labeled()
            if Path(v['filepath']).exists()
        ]
        ready = [v for v in all_labeled if v.get('label') and v.get('filepath')
                 and Path(v['filepath']).exists()]

        c1, c2 = st.columns(2)
        with c1:
            epochs = st.slider("عدد دورات التدريب" if ar else "Training epochs",
                               10, 100, 30, 5)
        with c2:
            st.metric("فيديوهات جاهزة" if ar else "Ready videos", len(ready))

        if len(ready) < 5:
            st.error(
                f"تحتاج على الأقل 5 فيديوهات مُصنَّفة (لديك {len(ready)})"
                if ar else
                f"Need at least 5 labeled videos (you have {len(ready)})"
            )
        else:
            if len(ready) < 20:
                st.warning(
                    f"النموذج سيعمل لكن الدقة ستكون محدودة ({len(ready)} فيديو). "
                    "أضف المزيد للحصول على نتائج أفضل."
                    if ar else
                    f"Model will work but accuracy will be limited ({len(ready)} videos). "
                    "Add more for better results."
                )

            if st.button("🚀 ابدأ التدريب" if ar else "🚀 Start Training",
                         type="primary"):
                with st.spinner("جارٍ تجهيز البيانات..." if ar else "Preparing data..."):
                    copied = prepare_labeled_dir(ready)
                st.info(f"{'جُهِّز' if ar else 'Prepared'} {copied} {'فيديو' if ar else 'videos'}")

                log_box = st.empty()
                with st.spinner("جارٍ التدريب... قد يستغرق عدة دقائق" if ar else
                                "Training... this may take several minutes"):
                    result = run_training(epochs)

                if result.returncode == 0:
                    st.success(
                        "✅ اكتمل التدريب! أعد تشغيل التطبيق لتفعيل النموذج."
                        if ar else
                        "✅ Training complete! Restart the app to activate the model."
                    )
                    out = result.stdout
                    log_box.code(out[-3000:] if len(out) > 3000 else out)
                else:
                    st.error("❌ فشل التدريب" if ar else "❌ Training failed")
                    st.code(result.stderr[-2000:])

            # Show current model accuracy if exists
            if stats['exists']:
                st.divider()
                st.subheader("معلومات النموذج الحالي" if ar else "Current Model Info")
                st.metric("حجم الملف" if ar else "File size",
                          f"{stats['size_mb']} MB")
                st.info(
                    "لتحسين الدقة: أضف المزيد من الفيديوهات المتنوعة وأعد التدريب"
                    if ar else
                    "To improve accuracy: add more diverse videos and retrain"
                )
