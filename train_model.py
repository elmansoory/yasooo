"""
Training Pipeline — Figure Skating Movement Classifier
======================================================

Usage:
    # Step 1: collect & label videos using the annotation page in the app
    # Step 2: run this script to extract features and train the model

    python train_model.py --data_dir data/labeled --out data/models/lstm_model.pkl

The script:
  1. Scans data/labeled/ for annotated video segments (JSON sidecar files)
  2. Extracts pose sequences with MediaPipe
  3. Trains LSTM classifier (Keras if available, else sklearn RF)
  4. Saves model to data/models/lstm_model.pkl
  5. Prints accuracy report

Directory layout expected:
    data/labeled/
        axel_triple_001.mp4     ← video clip (2-4 seconds)
        axel_triple_001.json    ← sidecar: {"label": "Axel_3", "rotations": 3}
        sit_spin_002.mp4
        sit_spin_002.json       ← {"label": "Sit"}
        ...
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


def load_dataset(data_dir: Path):
    """Scan data_dir for (video, json) pairs and build X, y arrays."""
    videos = sorted(data_dir.glob("*.mp4")) + sorted(data_dir.glob("*.mov"))

    X_list, y_list, skipped = [], [], 0

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

        print(f"  Processing {vp.name}  →  {label}")
        seq = extract_pose_sequence(str(vp))

        # Augment: generate 4× more samples from each video
        for aug_seq in augment_sequence(seq, n=4):
            X_list.append(aug_seq)
            y_list.append(LABEL2IDX[label])

    print(f"\n  Total samples: {len(X_list)}  (skipped {skipped} files)")
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)


def print_class_distribution(y: np.ndarray):
    unique, counts = np.unique(y, return_counts=True)
    print("\nClass distribution:")
    for idx, cnt in zip(unique, counts):
        print(f"  {ALL_LABELS[idx]:<20} {cnt:>4} samples")


def split_dataset(X, y, val_ratio=0.2, seed=42):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(len(X))
    n_val = int(len(X) * val_ratio)
    return (X[idx[n_val:]], y[idx[n_val:]],
            X[idx[:n_val]],  y[idx[:n_val]])


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
    X, y = load_dataset(data_dir)

    if len(X) == 0:
        print("No valid samples found. Add .mp4 videos with .json sidecar files.")
        sys.exit(1)

    print_class_distribution(y)
    X_tr, y_tr, X_val, y_val = split_dataset(X, y, args.val_ratio)
    print(f"\nTrain: {len(X_tr)}  Val: {len(X_val)}")

    print("\nTraining model ...")
    model = LSTMClassifier.train_with_keras(
        X_tr, y_tr, X_val, y_val,
        save_path=args.out,
        epochs=args.epochs,
        batch_size=args.batch,
    )

    evaluate(model, X_val, y_val)
    print(f"\nModel saved → {args.out}")


if __name__ == "__main__":
    main()
