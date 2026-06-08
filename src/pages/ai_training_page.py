"""
AI Training Page — صفحة تدريب الذكاء الاصطناعي
Complete UI for managing training data, training the model, and testing predictions.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
DB_PATH = str(ROOT / "skating_database.db")
DATA_LABELED = ROOT / "data" / "labeled"
MODEL_PATH = ROOT / "data" / "models" / "skating_model.pkl"
REPORT_PATH = ROOT / "data" / "models" / "skating_model.training_report.json"

ALL_LABELS = [
    "Axel_1", "Axel_2", "Axel_3", "Axel_4",
    "Lutz_1", "Lutz_2", "Lutz_3", "Lutz_4",
    "Flip_1", "Flip_2", "Flip_3", "Flip_4",
    "Loop_1", "Loop_2", "Loop_3", "Loop_4",
    "Salchow_1", "Salchow_2", "Salchow_3", "Salchow_4",
    "ToeLoop_1", "ToeLoop_2", "ToeLoop_3", "ToeLoop_4",
    "Upright", "Sit", "Camel", "Layback", "Combination",
    "StepSequence", "Spiral", "None",
]


# ── Helpers ────────────────────────────────────────────────────────────────

def _t(ar: str, en: str, lang: str) -> str:
    """Return Arabic or English text based on lang."""
    return ar if lang == "ar" else en


def _load_model():
    """Load trained SkatingClassifier if available."""
    if not MODEL_PATH.exists():
        return None
    try:
        from src.ai.skating_classifier import SkatingClassifier
        return SkatingClassifier.load(str(MODEL_PATH))
    except Exception as e:
        return None


def _load_training_report() -> dict:
    """Load the training report JSON if it exists."""
    if not REPORT_PATH.exists():
        return {}
    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_labeled_videos() -> list:
    """Collect labeled videos from data/labeled/ directory."""
    videos = []
    if not DATA_LABELED.exists():
        return videos
    for video_file in sorted(DATA_LABELED.glob("**/*")):
        if video_file.suffix.lower() not in (".mp4", ".mov", ".avi"):
            continue
        sidecar = video_file.with_suffix(".json")
        label = ""
        if sidecar.exists():
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                label = meta.get("label", "")
            except Exception:
                pass
        size_mb = video_file.stat().st_size / (1024 * 1024) if video_file.exists() else 0
        videos.append({
            "name": video_file.name,
            "path": str(video_file),
            "label": label,
            "size_mb": round(size_mb, 2),
            "source": "data/labeled/",
            "has_label": bool(label),
        })
    return videos


def _get_db_videos() -> list:
    """Collect labeled videos from the database."""
    videos = []
    if not Path(DB_PATH).exists():
        return videos
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filepath, label FROM discovered_videos "
            "WHERE label IS NOT NULL AND label != '' AND label != 'None'"
        )
        rows = cursor.fetchall()
        conn.close()
        for filepath, label in rows:
            if filepath:
                p = Path(filepath)
                size_mb = p.stat().st_size / (1024 * 1024) if p.exists() else 0
                videos.append({
                    "name": p.name,
                    "path": filepath,
                    "label": label or "",
                    "size_mb": round(size_mb, 2),
                    "source": "database",
                    "has_label": bool(label),
                })
    except Exception as e:
        pass
    return videos


def _scan_db_for_labeled() -> int:
    """Count labeled videos in DB that don't yet have sidecars."""
    count = 0
    if not Path(DB_PATH).exists():
        return 0
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM discovered_videos "
            "WHERE label IS NOT NULL AND label != '' AND label != 'None'"
        )
        count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        pass
    return count


# ── Tab implementations ────────────────────────────────────────────────────

def _tab_dashboard(lang: str):
    """Tab 1: Model Dashboard."""
    ar = lang == "ar"

    st.subheader(_t("لوحة تحكم النموذج", "Model Dashboard", lang))

    model = _load_model()
    report = _load_training_report()

    model_exists = model is not None
    accuracy = report.get("val_accuracy", 0.0)
    n_samples = report.get("n_samples_augmented", 0)
    n_classes = report.get("n_classes", 0)
    trained_at = report.get("trained_at", "")
    trained_at_str = trained_at[:10] if trained_at else (_t("غير متوفر", "N/A", lang))

    # Status banner
    if model_exists:
        st.success(_t(
            "النموذج جاهز للاستخدام",
            "Model is ready for use",
            lang
        ))
    else:
        st.warning(_t(
            "النموذج غير موجود — يرجى التدريب أولاً",
            "Model needs training — go to the Training tab",
            lang
        ))

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            _t("دقة النموذج", "Model Accuracy", lang),
            f"{accuracy:.1%}" if model_exists else "—"
        )
    with col2:
        st.metric(
            _t("عينات التدريب", "Training Samples", lang),
            f"{n_samples:,}" if model_exists else "—"
        )
    with col3:
        st.metric(
            _t("الفئات المتعلمة", "Classes Learned", lang),
            str(n_classes) if model_exists else "—"
        )
    with col4:
        st.metric(
            _t("آخر تدريب", "Last Training", lang),
            trained_at_str
        )

    if not model_exists:
        st.info(_t(
            "لا توجد بيانات نموذج. اذهب إلى تبويب 'تدريب النموذج' للبدء.",
            "No model data found. Go to the 'Train Model' tab to get started.",
            lang
        ))
        return

    # Per-class accuracy chart
    per_class = report.get("per_class_accuracy", {})
    if per_class and PANDAS_AVAILABLE:
        st.subheader(_t("دقة كل فئة", "Per-Class Accuracy", lang))
        df_cls = pd.DataFrame(
            [{"label": k, "accuracy": v} for k, v in sorted(per_class.items())]
        )
        st.bar_chart(df_cls.set_index("label")["accuracy"])

    # Feature importance chart
    if model_exists:
        try:
            feat_imp = model.get_feature_importance(top_n=10)
            if feat_imp and PANDAS_AVAILABLE:
                st.subheader(_t("أهمية الميزات", "Feature Importances", lang))
                df_fi = pd.DataFrame(feat_imp)
                st.bar_chart(df_fi.set_index("feature")["importance"])
        except Exception:
            pass

    # Labels info
    labels_trained = report.get("labels", [])
    if labels_trained:
        with st.expander(_t("الفئات المدربة", "Trained Classes", lang)):
            st.write(", ".join(labels_trained))


def _tab_training_clips(lang: str):
    """Tab 2: Manage training clips."""
    ar = lang == "ar"

    st.subheader(_t("إدارة مقاطع التدريب", "Manage Training Clips", lang))

    # Collect videos from both sources
    dir_videos = _get_labeled_videos()
    db_vids = _get_db_videos()

    # Deduplicate by path
    seen = set()
    all_vids = []
    for v in dir_videos + db_vids:
        if v["path"] not in seen:
            seen.add(v["path"])
            all_vids.append(v)

    # Stats
    total = len(all_vids)
    from collections import Counter
    label_counts = Counter(v["label"] for v in all_vids if v["label"])

    col1, col2, col3 = st.columns(3)
    col1.metric(_t("إجمالي المقاطع", "Total Clips", lang), total)
    col2.metric(_t("المسميات الفريدة", "Unique Labels", lang), len(label_counts))
    col3.metric(_t("بدون تسمية", "Unlabeled", lang), sum(1 for v in all_vids if not v["label"]))

    # Warning for sparse labels
    sparse = [lbl for lbl, cnt in label_counts.items() if cnt < 3]
    if sparse:
        st.warning(
            _t(
                f"هذه التسميات تحتاج مقاطع أكثر (< 3): {', '.join(sparse)}",
                f"These labels need more clips (< 3): {', '.join(sparse)}",
                lang,
            )
        )

    # Label distribution chart
    if label_counts and PANDAS_AVAILABLE:
        st.subheader(_t("توزيع التسميات", "Label Distribution", lang))
        df_lbl = pd.DataFrame(
            [{"label": k, "count": v} for k, v in sorted(label_counts.items())]
        )
        st.bar_chart(df_lbl.set_index("label")["count"])

    # Scan button
    if st.button(_t("مسح عن مقاطع جديدة", "Scan for New Videos", lang)):
        db_count = _scan_db_for_labeled()
        st.info(
            _t(
                f"تم العثور على {db_count} مقطع مسمى في قاعدة البيانات",
                f"Found {db_count} labeled videos in database",
                lang,
            )
        )
        st.rerun()

    # Filterable table
    if all_vids and PANDAS_AVAILABLE:
        st.subheader(_t("قائمة المقاطع", "Video List", lang))

        filter_label = st.selectbox(
            _t("تصفية حسب التسمية", "Filter by Label", lang),
            options=[""] + sorted(label_counts.keys()),
            format_func=lambda x: _t("الكل", "All", lang) if x == "" else x,
        )

        filtered = all_vids if not filter_label else [v for v in all_vids if v["label"] == filter_label]

        df = pd.DataFrame([{
            _t("الاسم", "Name", lang): v["name"],
            _t("التسمية", "Label", lang): v["label"] or _t("بدون تسمية", "Unlabeled", lang),
            _t("الحجم (MB)", "Size (MB)", lang): v["size_mb"],
            _t("المصدر", "Source", lang): v["source"],
            _t("حالة التسمية", "Label Status", lang): _t("موجودة", "Labeled", lang) if v["has_label"] else _t("مفقودة", "Missing", lang),
        } for v in filtered])

        st.dataframe(df, use_container_width=True)

    st.divider()

    # Upload new labeled clip
    st.subheader(_t("رفع مقطع جديد مع تسمية", "Upload New Labeled Clip", lang))

    uploaded_file = st.file_uploader(
        _t("اختر ملف فيديو (.mp4)", "Choose a video file (.mp4)", lang),
        type=["mp4", "mov", "avi"],
    )
    selected_label = st.selectbox(
        _t("اختر التسمية", "Select Label", lang),
        options=ALL_LABELS,
    )

    if uploaded_file and st.button(_t("حفظ المقطع", "Save Clip", lang)):
        try:
            DATA_LABELED.mkdir(parents=True, exist_ok=True)
            # Sanitize filename
            safe_name = uploaded_file.name.replace(" ", "_")
            video_dest = DATA_LABELED / safe_name
            sidecar_dest = video_dest.with_suffix(".json")

            # Save video
            with open(video_dest, "wb") as f:
                f.write(uploaded_file.read())

            # Save sidecar
            with open(sidecar_dest, "w", encoding="utf-8") as f:
                json.dump({"label": selected_label}, f, ensure_ascii=False)

            st.success(
                _t(
                    f"تم حفظ المقطع: {safe_name} بتسمية {selected_label}",
                    f"Clip saved: {safe_name} with label {selected_label}",
                    lang,
                )
            )
            st.rerun()
        except Exception as e:
            st.error(_t(f"فشل الحفظ: {e}", f"Save failed: {e}", lang))


def _run_training(augment_mult: int, lang: str) -> None:
    """Run the training pipeline inline within Streamlit."""
    import subprocess

    log_lines = []

    def log(msg: str):
        log_lines.append(msg)

    log(_t("بدء عملية التدريب...", "Starting training...", lang))

    try:
        from src.ai.feature_extractor import VideoFeatureExtractor
        from src.ai.skating_classifier import SkatingClassifier

        extractor = VideoFeatureExtractor()

        # Collect videos
        dir_vids = _get_labeled_videos()
        db_vids = _get_db_videos()
        seen = set()
        all_vids = []
        for v in dir_vids + db_vids:
            if v["path"] not in seen and v["has_label"]:
                seen.add(v["path"])
                all_vids.append(v)

        if not all_vids:
            st.error(_t("لا توجد مقاطع مسماة!", "No labeled clips found!", lang))
            return

        log(f"{_t('عدد المقاطع', 'Total clips', lang)}: {len(all_vids)}")

        # Feature extraction with progress
        progress = st.progress(0, _t("استخراج الميزات...", "Extracting features...", lang))
        status_placeholder = st.empty()

        X_list = []
        y_list = []
        from collections import Counter
        label_counts = Counter(v["label"] for v in all_vids)
        unique_labels = sorted(label_counts.keys())
        label2idx = {l: i for i, l in enumerate(unique_labels)}

        failed = 0
        for i, v in enumerate(all_vids):
            status_placeholder.text(
                f"{_t('معالجة', 'Processing', lang)}: {v['name']} ({v['label']})"
            )
            feats = extractor.extract_clip_features(v["path"])
            if feats is None:
                log(f"SKIP: {v['name']} — extraction failed")
                failed += 1
            else:
                X_list.append(extractor.to_vector(feats))
                y_list.append(label2idx[v["label"]])
                log(f"OK: {v['name']}")
            progress.progress((i + 1) / len(all_vids))

        status_placeholder.empty()

        if not X_list:
            st.error(_t("فشل استخراج جميع الميزات!", "All feature extractions failed!", lang))
            return

        import numpy as np
        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.int32)
        log(f"{_t('استخرجت', 'Extracted', lang)}: {len(X)} {_t('عينة', 'samples', lang)}, {failed} {_t('فشل', 'failed', lang)}")

        # Augmentation
        if augment_mult > 1:
            log(f"{_t('تعزيز البيانات', 'Augmenting data', lang)}: {augment_mult}x")
            from train_model import augment_features
            X, y = augment_features(X, y, augment_mult)
            log(f"{_t('بعد التعزيز', 'After augmentation', lang)}: {len(X)} {_t('عينة', 'samples', lang)}")

        # Train
        log(_t("تدريب النموذج...", "Training model...", lang))
        progress.progress(0.0, _t("تدريب النموذج...", "Training model...", lang))

        clf = SkatingClassifier()
        clf.set_dynamic_labels(unique_labels)
        metrics = clf.train(X, y, val_ratio=0.2, verbose=False)
        val_acc = metrics["val_accuracy"]

        log(f"{_t('دقة التحقق', 'Validation accuracy', lang)}: {val_acc:.1%}")

        # Save
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        clf.save(str(MODEL_PATH))
        log(f"{_t('تم الحفظ في', 'Saved to', lang)}: {MODEL_PATH}")

        # Save report
        report = {
            "trained_at": datetime.now().isoformat(),
            "model_path": str(MODEL_PATH),
            "n_samples_raw": len(X_list),
            "n_samples_augmented": int(len(X)),
            "n_classes": len(unique_labels),
            "labels": unique_labels,
            "val_accuracy": float(val_acc),
            "per_class_accuracy": metrics["per_class_accuracy"],
            "augment_multiplier": augment_mult,
            "label_distribution": {l: int(c) for l, c in label_counts.items()},
        }
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        progress.progress(1.0, _t("اكتمل التدريب!", "Training complete!", lang))
        st.session_state["last_train_accuracy"] = val_acc
        st.session_state["last_train_labels"] = unique_labels

        # Success display
        st.success(
            _t(
                f"تم التدريب بنجاح! الدقة: {val_acc:.1%}",
                f"Training successful! Accuracy: {val_acc:.1%}",
                lang,
            )
        )

        col1, col2 = st.columns(2)
        col1.metric(_t("دقة التحقق", "Validation Accuracy", lang), f"{val_acc:.1%}")
        col2.metric(_t("الفئات", "Classes", lang), len(unique_labels))

        if val_acc < 0.60:
            st.warning(_t(
                "الدقة أقل من 60% — يُنصح بجمع مقاطع أكثر لكل فئة",
                "Accuracy < 60% — consider collecting more clips per label",
                lang,
            ))
        elif val_acc >= 0.80:
            st.success(_t("ممتاز! دقة > 80%", "Excellent! Accuracy > 80%", lang))

        per_class = metrics.get("per_class_accuracy", {})
        if per_class and PANDAS_AVAILABLE:
            st.subheader(_t("دقة كل فئة", "Per-Class Accuracy", lang))
            df_cls = pd.DataFrame(
                [{"label": k, "accuracy": v} for k, v in sorted(per_class.items())]
            )
            st.bar_chart(df_cls.set_index("label")["accuracy"])

        st.info(_t(
            "أعد تشغيل التطبيق لتفعيل النموذج الجديد",
            "Restart the app to activate the new model",
            lang,
        ))

    except Exception as e:
        import traceback
        log(f"ERROR: {e}")
        st.error(_t(f"فشل التدريب: {e}", f"Training failed: {e}", lang))
        st.exception(e)

    # Show log
    st.subheader(_t("سجل التدريب", "Training Log", lang))
    st.code("\n".join(log_lines))


def _tab_train_model(lang: str):
    """Tab 3: Train the model."""
    ar = lang == "ar"

    st.subheader(_t("تدريب النموذج", "Train Model", lang))

    # Pre-training checklist
    st.subheader(_t("قائمة التحقق قبل التدريب", "Pre-Training Checklist", lang))

    labeled_exists = DATA_LABELED.exists()
    dir_vids = _get_labeled_videos() if labeled_exists else []
    db_vids = _get_db_videos()

    seen = set()
    all_labeled = []
    for v in dir_vids + db_vids:
        if v["path"] not in seen and v["has_label"]:
            seen.add(v["path"])
            all_labeled.append(v)

    from collections import Counter
    label_counts = Counter(v["label"] for v in all_labeled)
    n_clips = len(all_labeled)
    n_labels = len(label_counts)

    # Check sklearn
    try:
        import sklearn
        sklearn_ok = True
    except ImportError:
        sklearn_ok = False

    checks = [
        (labeled_exists,
         _t("مجلد data/labeled/ موجود", "data/labeled/ directory exists", lang)),
        (n_clips >= 10,
         _t(f"على الأقل 10 مقاطع ({n_clips} موجود)", f"At least 10 clips ({n_clips} found)", lang)),
        (n_labels >= 3,
         _t(f"على الأقل 3 تسميات مختلفة ({n_labels} موجود)", f"At least 3 different labels ({n_labels} found)", lang)),
        (sklearn_ok,
         _t("scikit-learn مثبت", "scikit-learn installed", lang)),
    ]

    all_ok = all(ok for ok, _ in checks)
    for ok, msg in checks:
        icon = "✅" if ok else "❌"
        st.write(f"{icon} {msg}")

    if not all_ok:
        st.warning(_t(
            "يرجى استيفاء جميع متطلبات التدريب أولاً.",
            "Please fulfill all training requirements first.",
            lang,
        ))

    st.divider()

    # Augmentation slider
    augment_mult = st.slider(
        _t("مضاعف تعزيز البيانات", "Data Augmentation Multiplier", lang),
        min_value=1, max_value=10, value=5,
        help=_t(
            "كل مقطع سيتم توليد نسخ معدلة منه بهذا العدد",
            "Each clip will generate this many augmented versions",
            lang,
        ),
    )

    st.info(
        _t(
            f"التدريب على {n_clips} مقطع × {augment_mult}x = {n_clips * augment_mult} عينة",
            f"Training on {n_clips} clips × {augment_mult}x = {n_clips * augment_mult} samples",
            lang,
        )
    )

    # Training button
    train_key = "training_in_progress"
    if train_key not in st.session_state:
        st.session_state[train_key] = False

    if st.button(
        _t("ابدأ التدريب", "Start Training", lang),
        disabled=not all_ok or st.session_state.get(train_key, False),
        type="primary",
    ):
        st.session_state[train_key] = True
        _run_training(augment_mult, lang)
        st.session_state[train_key] = False


def _tab_test_model(lang: str):
    """Tab 4: Test the model on a new video."""
    ar = lang == "ar"

    st.subheader(_t("اختبار النموذج", "Test Model", lang))

    model = _load_model()
    if model is None:
        st.warning(_t(
            "لا يوجد نموذج مدرب. يرجى التدريب أولاً.",
            "No trained model found. Please train first.",
            lang,
        ))
        return

    uploaded = st.file_uploader(
        _t("ارفع فيديو للاختبار (.mp4)", "Upload a test video (.mp4)", lang),
        type=["mp4", "mov", "avi"],
        key="test_video_uploader",
    )

    manual_label = st.selectbox(
        _t("التسمية الصحيحة (اختياري للمقارنة)", "Correct label (optional for comparison)", lang),
        options=[""] + ALL_LABELS,
        format_func=lambda x: _t("لا شيء", "None", lang) if x == "" else x,
    )

    if uploaded and st.button(_t("تحليل الفيديو", "Analyze Video", lang)):
        try:
            from src.ai.feature_extractor import VideoFeatureExtractor

            # Save to temp file
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            with st.spinner(_t("استخراج الميزات...", "Extracting features...", lang)):
                extractor = VideoFeatureExtractor()
                feats = extractor.extract_clip_features(tmp_path)

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            if feats is None:
                st.error(_t(
                    "فشل استخراج الميزات من الفيديو.",
                    "Failed to extract features from video.",
                    lang,
                ))
                return

            import numpy as np
            vec = extractor.to_vector(feats)

            # Predict
            pred_label, confidence = model.predict(vec)
            proba_dict = model.predict_proba(vec)

            # Results
            st.subheader(_t("نتيجة التصنيف", "Classification Result", lang))

            col1, col2 = st.columns(2)
            col1.metric(_t("التصنيف المتوقع", "Predicted Label", lang), pred_label)
            col2.metric(_t("مستوى الثقة", "Confidence", lang), f"{confidence:.1%}")

            # Comparison with manual label
            if manual_label:
                if pred_label == manual_label:
                    st.success(_t("صحيح!", "Correct!", lang) + " ✅")
                else:
                    st.error(
                        _t(
                            f"خطأ! التسمية الصحيحة: {manual_label}",
                            f"Wrong! Correct label: {manual_label}",
                            lang,
                        ) + " ❌"
                    )

            # Top-5 probabilities chart
            if proba_dict and PANDAS_AVAILABLE:
                st.subheader(_t("أفضل 5 احتمالات", "Top 5 Probabilities", lang))
                df_prob = pd.DataFrame(
                    [{"label": k, "probability": v} for k, v in proba_dict.items()]
                ).sort_values("probability", ascending=False)
                st.bar_chart(df_prob.set_index("label")["probability"])

            # Extracted features table
            with st.expander(_t("الميزات المستخرجة", "Extracted Features", lang)):
                if PANDAS_AVAILABLE:
                    df_feats = pd.DataFrame(
                        [{"feature": k, "value": round(v, 6)} for k, v in feats.items()]
                    )
                    st.dataframe(df_feats, use_container_width=True)
                else:
                    for k, v in feats.items():
                        st.write(f"{k}: {v:.6f}")

        except Exception as e:
            st.error(_t(f"خطأ أثناء التحليل: {e}", f"Analysis error: {e}", lang))
            st.exception(e)


def _tab_guide(lang: str):
    """Tab 5: Training guide in Arabic/English."""
    ar = lang == "ar"

    st.subheader(_t("دليل التدريب", "Training Guide", lang))

    if ar:
        st.markdown("""
### الخطوة 1 — جمع الفيديوهات
- سجّل مقاطع قصيرة مدتها **2-5 ثوانٍ** لكل عنصر تزلج
- كل مقطع يجب أن يحتوي على **عنصر واحد فقط**
- تأكد أن المتزلج يظهر بوضوح في الإطار
- الإضاءة الجيدة تُحسّن دقة الاستخراج

### الخطوة 2 — وضع التسميات
- استخدم صفحة **"مقاطعي"** لإضافة تسميات على الفيديوهات المكتشفة
- أو ارفع مقاطع مباشرة من تبويب **"إدارة مقاطع التدريب"** مع اختيار التسمية
- التسمية تُحفظ تلقائيًا في ملف JSON جانب الفيديو

### الخطوة 3 — عدد التسجيلات المطلوبة
- الحد الأدنى: **10 مقاطع** لكل تسمية للحصول على دقة معقولة
- الموصى به: **30+ مقطع** لكل تسمية للحصول على دقة عالية
- تنوع الزوايا والمزلقين يُحسّن الدقة

### الخطوة 4 — تشغيل التدريب
- انتقل إلى تبويب **"تدريب النموذج"**
- اختر مضاعف التعزيز (5x موصى به)
- اضغط "ابدأ التدريب" وانتظر اكتمال العملية
- يمكن أيضًا تشغيل: `python train_model.py` من سطر الأوامر

### الخطوة 5 — تقييم النتائج
- الدقة أُحسب على 20% من البيانات لم تُستخدم في التدريب
- راجع **دقة كل فئة** لمعرفة الفئات الضعيفة
        """)

        st.divider()
        st.subheader("عتبات الجودة")
        data = {
            "الدقة": ["< 60%", "60% - 80%", "> 80%"],
            "التقييم": ["يحتاج مزيدًا من البيانات", "جيد — مقبول للاستخدام", "ممتاز"],
            "التوصية": [
                "أضف أكثر من 10 مقاطع لكل فئة",
                "يمكن الاستخدام، واصل جمع المزيد",
                "النموذج جاهز للإنتاج",
            ],
        }
    else:
        st.markdown("""
### Step 1 — Collect Videos
- Record short clips **2-5 seconds** long, one skating element per clip
- Make sure the skater is clearly visible in the frame
- Good lighting improves feature extraction accuracy
- Variety of angles and skaters improves generalization

### Step 2 — Label Clips
- Use the **My Videos** page to label already-discovered videos
- Or upload clips directly from the **Training Clips** tab with a label selected
- Labels are automatically saved as a JSON sidecar file

### Step 3 — Minimum Recordings Required
- Minimum: **10 clips per label** for reasonable accuracy
- Recommended: **30+ clips per label** for high accuracy
- More diversity = better model

### Step 4 — Run Training
- Go to the **Train Model** tab
- Choose augmentation multiplier (5x recommended)
- Click "Start Training" and wait
- Or run: `python train_model.py` from command line

### Step 5 — Evaluate Results
- Accuracy is computed on 20% of data held out from training
- Review **per-class accuracy** to identify weak labels
        """)

        st.divider()
        st.subheader("Quality Thresholds")
        data = {
            "Accuracy": ["< 60%", "60% - 80%", "> 80%"],
            "Rating": ["Needs more data", "Good — acceptable for use", "Excellent"],
            "Recommendation": [
                "Add 10+ clips per label",
                "Usable, keep collecting data",
                "Model is production-ready",
            ],
        }

    if PANDAS_AVAILABLE:
        st.table(pd.DataFrame(data))

    # Recommended clip counts
    st.divider()
    st.subheader(_t("عدد المقاطع الموصى به لكل نوع", "Recommended Clips per Element Type", lang))

    if PANDAS_AVAILABLE:
        rec_data = {
            _t("نوع العنصر", "Element Type", lang): [
                _t("القفزات (Axel, Lutz, إلخ)", "Jumps (Axel, Lutz, etc.)", lang),
                _t("الدورانات (Spin)", "Spins", lang),
                _t("التسلسلات (Step/Spiral)", "Steps/Spirals", lang),
            ],
            _t("الحد الأدنى", "Minimum", lang): [10, 8, 8],
            _t("الموصى به", "Recommended", lang): [30, 20, 20],
            _t("ممتاز", "Excellent", lang): [50, 40, 40],
        }
        st.table(pd.DataFrame(rec_data))


# ── Main entrypoint ────────────────────────────────────────────────────────

def show_ai_training_page(lang: str = "ar"):
    """Main entry point for the AI Training page."""
    ar = lang == "ar"

    st.title(_t("تدريب الذكاء الاصطناعي", "AI Training System", lang))
    st.caption(
        _t(
            "نظام تدريب متكامل لتحليل حركات التزلج الفني باستخدام OpenCV و scikit-learn",
            "Complete AI training for figure skating element analysis using OpenCV & scikit-learn",
            lang,
        )
    )

    tab_labels = [
        _t("لوحة التحكم", "Dashboard", lang),
        _t("إدارة المقاطع", "Training Clips", lang),
        _t("تدريب النموذج", "Train Model", lang),
        _t("اختبار النموذج", "Test Model", lang),
        _t("دليل التدريب", "Training Guide", lang),
    ]

    # Use emojis in tab headers
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        f"📊 {tab_labels[0]}",
        f"🎬 {tab_labels[1]}",
        f"🏋️ {tab_labels[2]}",
        f"🧪 {tab_labels[3]}",
        f"📖 {tab_labels[4]}",
    ])

    with tab1:
        try:
            _tab_dashboard(lang)
        except Exception as e:
            st.error(f"Dashboard error: {e}")
            st.exception(e)

    with tab2:
        try:
            _tab_training_clips(lang)
        except Exception as e:
            st.error(f"Training clips error: {e}")
            st.exception(e)

    with tab3:
        try:
            _tab_train_model(lang)
        except Exception as e:
            st.error(f"Train model error: {e}")
            st.exception(e)

    with tab4:
        try:
            _tab_test_model(lang)
        except Exception as e:
            st.error(f"Test model error: {e}")
            st.exception(e)

    with tab5:
        try:
            _tab_guide(lang)
        except Exception as e:
            st.error(f"Guide error: {e}")
            st.exception(e)
