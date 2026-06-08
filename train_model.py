"""
Train Figure Skating AI Model
Usage: python train_model.py [--data_dir data/labeled] [--out data/models/skating_model.pkl]
                             [--epochs 100] [--augment 5]

Also scans discovered_videos table in DB for labeled videos.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DB_PATH = ROOT / "skating_database.db"
DEFAULT_DATA_DIR = ROOT / "data" / "labeled"
DEFAULT_OUT = ROOT / "data" / "models" / "skating_model.pkl"


def parse_args():
    parser = argparse.ArgumentParser(description="Train Figure Skating AI Model")
    parser.add_argument("--data_dir", default=str(DEFAULT_DATA_DIR),
                        help="Directory with labeled .mp4/.mov + .json sidecars")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output path for trained model (.pkl)")
    parser.add_argument("--epochs", type=int, default=100,
                        help="(Kept for API compat -- ignored for sklearn)")
    parser.add_argument("--augment", type=int, default=5,
                        help="Data augmentation multiplier (default: 5x)")
    return parser.parse_args()


# ── Data collection ────────────────────────────────────────────────────────

def scan_labeled_directory(data_dir: str) -> list:
    """Scan data_dir for .mp4/.mov files with matching .json sidecars."""
    results = []
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"[WARN] data_dir does not exist: {data_dir}")
        return results

    for video_file in sorted(data_path.glob("**/*")):
        if video_file.suffix.lower() not in (".mp4", ".mov", ".avi"):
            continue
        sidecar = video_file.with_suffix(".json")
        if sidecar.exists():
            try:
                with open(sidecar, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                label = meta.get("label", "").strip()
                if label:
                    results.append((str(video_file), label))
            except Exception as e:
                print(f"[WARN] Failed to read sidecar {sidecar}: {e}")

    return results


def scan_database_videos() -> list:
    """Scan discovered_videos table for videos with non-empty labels."""
    results = []
    if not DB_PATH.exists():
        print(f"[INFO] Database not found at {DB_PATH} -- skipping DB scan")
        return results

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filepath, label FROM discovered_videos "
            "WHERE label IS NOT NULL AND label != '' AND label != 'None'"
        )
        rows = cursor.fetchall()
        conn.close()

        for filepath, label in rows:
            if filepath and os.path.exists(filepath):
                results.append((filepath, label.strip()))
            else:
                print(f"[WARN] DB video not found on disk: {filepath}")

    except sqlite3.OperationalError as e:
        print(f"[INFO] Could not query discovered_videos: {e}")
    except Exception as e:
        print(f"[WARN] Database scan error: {e}")

    return results


# ── Data augmentation ──────────────────────────────────────────────────────

def augment_features(
    X: np.ndarray,
    y: np.ndarray,
    multiplier: int,
) -> tuple:
    """
    Generate augmented versions of feature vectors:
      - Add Gaussian noise (scale 0.01)
      - Randomly flip x-coordinates (features 9,10 = x_std, x_range)
      - Slightly scale feature values (+-10%)

    Returns augmented X, y (includes originals).
    """
    if multiplier <= 1:
        return X, y

    X_aug_list = [X]
    y_aug_list = [y]

    rng = np.random.default_rng(42)

    for _ in range(multiplier - 1):
        X_noisy = X.copy()

        # 1. Gaussian noise
        noise = rng.normal(0, 0.01, X_noisy.shape).astype(np.float32)
        X_noisy = X_noisy + noise

        # 2. Random flip of x-coordinate features (indices 9=x_std, 10=x_range)
        flip_mask = rng.random(len(X_noisy)) > 0.5
        if flip_mask.any() and X_noisy.shape[1] > 10:
            X_noisy[flip_mask, 9] = np.abs(X_noisy[flip_mask, 9])

        # 3. Scale features by +-10%
        scale = rng.uniform(0.9, 1.1, X_noisy.shape).astype(np.float32)
        X_noisy = X_noisy * scale

        X_aug_list.append(X_noisy)
        y_aug_list.append(y.copy())

    X_out = np.vstack(X_aug_list)
    y_out = np.concatenate(y_aug_list)
    return X_out, y_out


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    print("=" * 60)
    print("  Figure Skating AI Training Pipeline")
    print("=" * 60)
    print(f"  Data directory : {args.data_dir}")
    print(f"  Output model   : {args.out}")
    print(f"  Augmentation   : {args.augment}x")
    print("=" * 60)

    # ── Import modules ────────────────────────────────────────────────
    try:
        from src.ai.feature_extractor import VideoFeatureExtractor
        from src.ai.skating_classifier import SkatingClassifier
    except ImportError as e:
        print(f"[ERROR] Cannot import AI modules: {e}")
        sys.exit(1)

    # ── Collect videos ────────────────────────────────────────────────
    print("\n[1/5] Scanning for labeled videos...")

    labeled_dir_videos = scan_labeled_directory(args.data_dir)
    db_videos = scan_database_videos()

    # Merge, deduplicate by filepath
    seen_paths = set()
    all_videos = []
    for filepath, label in labeled_dir_videos + db_videos:
        if filepath not in seen_paths:
            seen_paths.add(filepath)
            all_videos.append((filepath, label))

    print(f"  Found {len(labeled_dir_videos)} videos in data_dir")
    print(f"  Found {len(db_videos)} videos in database")
    print(f"  Total unique: {len(all_videos)}")

    if not all_videos:
        print("\n[ERROR] No labeled videos found. Cannot train.")
        print("  Add .mp4 files with .json sidecars to data/labeled/")
        print('  JSON format: {"label": "Axel_3"}')
        sys.exit(1)

    # Show distribution
    from collections import Counter
    label_counts = Counter(label for _, label in all_videos)
    print("\n  Label distribution:")
    for label, count in sorted(label_counts.items()):
        print(f"    {label:20s}: {count} clips")

    unique_labels = sorted(label_counts.keys())
    label2idx_dynamic = {l: i for i, l in enumerate(unique_labels)}

    # ── Feature extraction ────────────────────────────────────────────
    print("\n[2/5] Extracting features from videos...")
    extractor = VideoFeatureExtractor()

    X_list = []
    y_list = []
    failed = []

    for i, (vpath, label) in enumerate(all_videos):
        print(f"  [{i+1}/{len(all_videos)}] {os.path.basename(vpath)} ({label})", end="")
        feats = extractor.extract_clip_features(vpath)
        if feats is None:
            print(" FAILED")
            failed.append(vpath)
            continue
        X_list.append(extractor.to_vector(feats))
        y_list.append(label2idx_dynamic[label])
        print(" OK")

    if not X_list:
        print("\n[ERROR] All feature extractions failed.")
        sys.exit(1)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    print(f"\n  Extracted: {len(X)} / {len(all_videos)} ({len(failed)} failed)")

    if failed:
        print("  Failed files:")
        for f in failed:
            print(f"    {f}")

    # ── Data augmentation ─────────────────────────────────────────────
    if args.augment > 1:
        print(f"\n[3/5] Augmenting data ({args.augment}x)...")
        X_aug, y_aug = augment_features(X, y, multiplier=args.augment)
        print(f"  Samples: {len(X)} -> {len(X_aug)}")
        X, y = X_aug, y_aug
    else:
        print("\n[3/5] Skipping augmentation (--augment 1)")

    # ── Train model ───────────────────────────────────────────────────
    print("\n[4/5] Training ensemble classifier...")
    classifier = SkatingClassifier()
    classifier.set_dynamic_labels(unique_labels)

    try:
        metrics = classifier.train(X, y, val_ratio=0.2, verbose=True)
    except Exception as e:
        print(f"\n[ERROR] Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    val_acc = metrics["val_accuracy"]
    print(f"\n  Validation accuracy: {val_acc:.3f} ({val_acc*100:.1f}%)")

    if val_acc < 0.60:
        print("  WARNING: Accuracy < 60% -- consider collecting more clips per label")
    elif val_acc < 0.80:
        print("  OK: Good accuracy (60-80%) -- acceptable for initial training")
    else:
        print("  EXCELLENT: Accuracy >80%")

    print("\n  Per-class accuracy:")
    for label, acc in sorted(metrics["per_class_accuracy"].items()):
        bar = "#" * int(acc * 20)
        print(f"    {label:20s}: {acc:.2f} {bar}")

    print("\n  Top feature importances:")
    feat_imp = metrics.get("feature_importances", {})
    top_feats = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)[:5]
    for fname, fimp in top_feats:
        print(f"    {fname:20s}: {fimp:.4f}")

    # ── Save model ────────────────────────────────────────────────────
    print(f"\n[5/5] Saving model to {args.out}...")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        classifier.save(str(out_path))
        print(f"  Model saved: {out_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save model: {e}")
        sys.exit(1)

    # ── Save training report ──────────────────────────────────────────
    report_path = out_path.with_suffix(".training_report.json")
    report = {
        "trained_at": datetime.now().isoformat(),
        "model_path": str(out_path),
        "n_samples_raw": int(len(X_list)),
        "n_samples_augmented": int(len(X)),
        "n_classes": len(unique_labels),
        "labels": unique_labels,
        "val_accuracy": float(val_acc),
        "per_class_accuracy": metrics["per_class_accuracy"],
        "failed_extractions": failed,
        "augment_multiplier": args.augment,
        "label_distribution": {l: int(c) for l, c in label_counts.items()},
    }
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  Training report saved: {report_path}")
    except Exception as e:
        print(f"[WARN] Could not save training report: {e}")

    # ── Summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Samples trained : {len(X_list)} raw x {args.augment}x augment")
    print(f"  Classes         : {len(unique_labels)}")
    print(f"  Validation acc  : {val_acc:.1%}")
    print(f"  Model saved to  : {out_path}")
    print("=" * 60)
    print("\n  Restart the app to activate the new model.")
    print()


if __name__ == "__main__":
    main()
