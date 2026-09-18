"""
Training Pipeline — Figure Skating Movement Classifier
======================================================

Usage:
    # Step 1: collect & label videos using the annotation page in the app
    # Step 2: run this script to extract features and train the model

    python train_model.py --data_dir data/labeled --out data/models/lstm_model.pkl

The script:
  1. Scans data/labeled/ for annotated video segments (JSON sidecar files)
  2. Extracts pose sequences with MediaPipe (cached under data/landmarks/ so
     re-running this script after adding a few new clips doesn't re-extract
     everything from scratch)
  3. Splits train/val by athlete group (not by sample) so augmented copies
     of the same clip, or multiple clips from the same skater, never leak
     across the split
  4. Trains LSTM classifier (Keras if available, else sklearn RF), with
     class weighting so common elements don't drown out rare ones
  5. Saves model + normalization stats to data/models/lstm_model.pkl
  6. Prints accuracy report

Directory layout expected:
    data/labeled/
        axel_triple_001.mp4     ← video clip (2-4 seconds)
        axel_triple_001.json    ← sidecar: {"label": "Axel_3", "rotations": 3,
                                              "athlete_id": "athlete_7"}
        sit_spin_002.mp4
        sit_spin_002.json       ← {"label": "Sit"}
        ...

    "athlete_id" is optional and anonymous (an internal id, never a real
    name) — when present, it groups clips from the same skater so they
    can't end up split across train and validation. When absent (older
    sidecars), each clip is its own group — narrower, but still prevents
    augmented copies of one clip from leaking across the split.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.models.lstm_classifier import (
    LSTMClassifier, LABEL2IDX, ALL_LABELS,
    poses_to_sequence, augment_sequence, SEQUENCE_LEN,
)

LANDMARK_DIR = ROOT / "data/landmarks"


def extract_pose_sequence(video_path: str) -> np.ndarray:
    """Run MediaPipe on video clip and return (T, 99) array."""
    try:
        import cv2
        import mediapipe as mp

        mp_pose = mp.solutions.pose
        poses = []

        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose_model:

            cap = cv2.VideoCapture(video_path)
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = pose_model.process(rgb)
                if res.pose_landmarks:
                    kps = [
                        {
                            'x': lm.x, 'y': lm.y, 'z': lm.z,
                            'visibility': lm.visibility, 'index': i
                        }
                        for i, lm in enumerate(res.pose_landmarks.landmark)
                    ]
                    poses.append({'keypoints': kps})
            cap.release()

        if not poses:
            return np.zeros((SEQUENCE_LEN, 99), dtype=np.float32)

        return poses_to_sequence(poses)

    except ImportError as e:
        print(f"  [skip] {video_path} — {e}")
        return np.zeros((SEQUENCE_LEN, 99), dtype=np.float32)


def extract_pose_sequence_cached(video_path: Path, clip_id: str) -> np.ndarray:
    """Extract (or load a cached copy of) the pose sequence for one clip.

    MediaPipe extraction is the expensive part of this whole pipeline —
    caching it means adding a handful of new labeled clips and re-running
    this script doesn't re-process every clip collected so far. The cache
    is invalidated if the source video's mtime changes (re-labeled/re-cut).
    """
    LANDMARK_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = LANDMARK_DIR / f"{clip_id}.npz"
    video_mtime = video_path.stat().st_mtime

    if cache_path.exists():
        try:
            cached = np.load(cache_path)
            if float(cached['video_mtime']) == video_mtime:
                return cached['sequence']
        except Exception:
            pass  # corrupt cache entry — fall through and re-extract

    seq = extract_pose_sequence(str(video_path))
    np.savez_compressed(cache_path, sequence=seq, video_mtime=video_mtime)
    return seq


def load_clips(data_dir: Path) -> list:
    """Scan data_dir for (video, json) pairs. Returns one entry per RAW clip
    (no augmentation yet — that happens per-split in main(), so augmented
    copies of a clip can't end up split across train and validation)."""
    videos = sorted(data_dir.glob("*.mp4")) + sorted(data_dir.glob("*.mov"))

    items, skipped = [], 0

    for vp in videos:
        jp = vp.with_suffix(".json")
        if not jp.exists():
            print(f"  [skip] no sidecar JSON for {vp.name}")
            skipped += 1
            continue

        meta = json.loads(jp.read_text())
        label = meta.get("label", "")

        if label not in LABEL2IDX:
            print(f"  [skip] unknown label '{label}' in {jp.name}")
            skipped += 1
            continue

        clip_id = vp.stem
        # Anonymous internal id, optional. Falls back to the clip's own id
        # for sidecars written before this field existed — narrower
        # grouping, but still keeps augmented copies of one clip together.
        group_id = meta.get("athlete_id") or clip_id

        print(f"  Processing {vp.name}  →  {label}  (group={group_id})")
        # poses_to_sequence() (and the cache) preserve each clip's real
        # length, which varies per clip — pad/trim to the model's fixed
        # window here so every item is a uniform (SEQUENCE_LEN, 99) array.
        # Skipping this made np.array(X_list) crash on any real dataset
        # with more than one clip length — never caught before because
        # data/labeled/ had no real clips to trigger it until now.
        seq = LSTMClassifier._pad_or_trim(extract_pose_sequence_cached(vp, clip_id), SEQUENCE_LEN)

        items.append({
            'clip_id': clip_id, 'group_id': group_id,
            'label_idx': LABEL2IDX[label], 'sequence': seq,
        })

    print(f"\n  Total clips: {len(items)}  (skipped {skipped} files)")
    return items


def group_split(items: list, val_ratio: float = 0.2, seed: int = 42):
    """Split by group_id (athlete), not by sample — so no group has clips
    on both sides of the split. Plain random per-sample splitting would let
    augmented copies of the same clip, or a skater's other clips, leak
    between train and validation and inflate the reported accuracy."""
    groups = sorted({it['group_id'] for it in items})
    rng = np.random.RandomState(seed)
    rng.shuffle(groups)

    n_val_groups = max(1, round(len(groups) * val_ratio)) if len(groups) > 1 else 0
    val_groups = set(groups[:n_val_groups])

    train_items = [it for it in items if it['group_id'] not in val_groups]
    val_items = [it for it in items if it['group_id'] in val_groups]
    return train_items, val_items


def build_arrays(items: list, augment: bool):
    """Turn a list of clip items into (X, y) arrays. Only the training
    split should be augmented — validation must reflect real, unmodified
    clips or the reported accuracy is measuring the augmentation, not the
    model."""
    X_list, y_list = [], []
    for it in items:
        if augment:
            for aug_seq in augment_sequence(it['sequence'], n=4):
                X_list.append(aug_seq)
                y_list.append(it['label_idx'])
        else:
            X_list.append(it['sequence'])
            y_list.append(it['label_idx'])
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)


def print_class_distribution(y: np.ndarray, title: str = "Class distribution"):
    unique, counts = np.unique(y, return_counts=True)
    print(f"\n{title}:")
    for idx, cnt in zip(unique, counts):
        print(f"  {ALL_LABELS[idx]:<20} {cnt:>4} samples")


def compute_class_weights(y: np.ndarray) -> dict:
    """Inverse-frequency class weights so rare elements (e.g. a triple jump
    with only a handful of clips) aren't drowned out by common ones (e.g.
    'None') in the loss."""
    classes, counts = np.unique(y, return_counts=True)
    total = len(y)
    n_classes = len(classes)
    return {
        int(c): float(total / (n_classes * count))
        for c, count in zip(classes, counts)
    }


def evaluate(model: LSTMClassifier, X_val: np.ndarray, y_val: np.ndarray):
    correct = 0
    per_class_correct = {}
    per_class_total   = {}

    for seq, true_idx in zip(X_val, y_val):
        if hasattr(model, '_use_keras') and model._use_keras:
            pred_label, conf = model.predict_keras(seq)
        elif hasattr(model, '_use_rf') and model._use_rf:
            emb   = model._embed(seq)[np.newaxis]
            emb   = model._rf_scaler.transform(emb)
            pred_idx = model._rf_fallback.predict(emb)[0]
            pred_label = model.idx2label[pred_idx]
        else:
            pred_label, conf = model.predict(seq)

        true_label = ALL_LABELS[true_idx]
        hit = pred_label == true_label
        correct += hit

        per_class_correct[true_label] = per_class_correct.get(true_label, 0) + hit
        per_class_total[true_label]   = per_class_total.get(true_label, 0) + 1

    overall = correct / len(y_val) if y_val.size else 0
    print(f"\nValidation accuracy: {overall:.1%}  ({correct}/{len(y_val)})")

    print("\nPer-class accuracy:")
    for lbl in sorted(per_class_total):
        acc = per_class_correct.get(lbl, 0) / per_class_total[lbl]
        bar = "█" * int(acc * 20)
        print(f"  {lbl:<22} {acc:.0%}  {bar}")


def main():
    parser = argparse.ArgumentParser(description="Train figure skating movement classifier")
    parser.add_argument("--data_dir", default="data/labeled",
                        help="Directory with labeled .mp4 + .json pairs")
    parser.add_argument("--out", default="data/models/lstm_model.pkl",
                        help="Output model path")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch",  type=int, default=32)
    parser.add_argument("--val_ratio", type=float, default=0.2)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}")
        print("Create it and add labeled video clips (see script docstring).")
        sys.exit(1)

    print(f"Loading dataset from {data_dir} ...")
    items = load_clips(data_dir)

    if len(items) == 0:
        print("No valid samples found. Add .mp4 videos with .json sidecar files.")
        sys.exit(1)

    n_groups = len({it['group_id'] for it in items})
    print(f"  {len(items)} clips across {n_groups} athlete group(s)")

    train_items, val_items = group_split(items, args.val_ratio)
    X_tr, y_tr = build_arrays(train_items, augment=True)
    X_val, y_val = build_arrays(val_items, augment=False)

    if len(X_val) == 0:
        print("\nWARNING: only one athlete group in the dataset — validation set "
              "is empty. Add clips from at least 2 different athlete_id groups "
              "(or leave athlete_id unset to group per-clip) to get a real "
              "held-out accuracy number.")

    print_class_distribution(y_tr, "Train class distribution (post-augmentation)")
    if len(y_val):
        print_class_distribution(y_val, "Validation class distribution")
    print(f"\nTrain: {len(X_tr)}  Val: {len(X_val)}")

    class_weight = compute_class_weights(y_tr) if len(y_tr) else None

    # Normalize using train-set statistics only, and store them on the model
    # so inference (predict_keras / predict) applies the exact same
    # normalization — training on raw coordinates while normalizing only at
    # inference time is a silent train/serve mismatch. Shape (99,), not
    # keepdims — must broadcast against both a training batch (N, T, 99)
    # and a single inference sequence (T, 99).
    scaler_mean = X_tr.mean(axis=(0, 1)) if len(X_tr) else None
    scaler_std = X_tr.std(axis=(0, 1)) + 1e-6 if len(X_tr) else None
    if scaler_mean is not None:
        X_tr = (X_tr - scaler_mean) / scaler_std
        if len(X_val):
            X_val = (X_val - scaler_mean) / scaler_std

    print("\nTraining model ...")
    model = LSTMClassifier.train_with_keras(
        X_tr, y_tr, X_val, y_val,
        save_path=args.out,
        epochs=args.epochs,
        batch_size=args.batch,
        class_weight=class_weight,
        scaler_mean=scaler_mean,
        scaler_std=scaler_std,
    )

    if len(X_val):
        evaluate(model, X_val, y_val)
    print(f"\nModel saved → {args.out}")


if __name__ == "__main__":
    main()
