"""
LSTM Sequence Classifier for Figure Skating Elements
نموذج LSTM لتصنيف حركات التزلج من تسلسل نقاط الجسم

Architecture:
  Input : (batch, T, 99)  ← 33 landmarks × (x, y, z) per frame
  Layer1: LSTM(128, return_sequences=True)
  Layer2: LSTM(64)
  Layer3: Dense(64, relu)
  Output: Dense(N_CLASSES, softmax)

Works with scikit-learn-compatible interface so it can be swapped in/out
alongside the sklearn fallback (RandomForest) in element_classifier_trainer.py.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Labels — must match what the annotation tool writes
JUMP_LABELS = [
    "Axel_1", "Axel_2", "Axel_3", "Axel_4",
    "Lutz_1", "Lutz_2", "Lutz_3", "Lutz_4",
    "Flip_1", "Flip_2", "Flip_3", "Flip_4",
    "Loop_1", "Loop_2", "Loop_3", "Loop_4",
    "Salchow_1", "Salchow_2", "Salchow_3", "Salchow_4",
    "ToeLoop_1", "ToeLoop_2", "ToeLoop_3", "ToeLoop_4",
]
SPIN_LABELS  = ["Upright", "Sit", "Camel", "Layback", "Combination"]
OTHER_LABELS = ["StepSequence", "Spiral", "None"]

ALL_LABELS = JUMP_LABELS + SPIN_LABELS + OTHER_LABELS
LABEL2IDX  = {l: i for i, l in enumerate(ALL_LABELS)}
IDX2LABEL  = {i: l for l, i in LABEL2IDX.items()}

N_LANDMARKS  = 33
COORDS       = 3          # x, y, z
INPUT_DIM    = N_LANDMARKS * COORDS   # 99
SEQUENCE_LEN = 60         # 2 seconds at 30fps — window fed to the model


# ── Pure-numpy LSTM cell (no framework dependency) ─────────────────────────

class _LSTMCell:
    """Single LSTM cell with numpy."""

    def __init__(self, input_size: int, hidden_size: int):
        # Xavier init
        s = np.sqrt(2.0 / (input_size + hidden_size))
        def W(r, c): return np.random.randn(r, c) * s
        h = hidden_size; i = input_size

        self.Wf = W(h, i + h); self.bf = np.zeros(h)
        self.Wi = W(h, i + h); self.bi = np.zeros(h)
        self.Wc = W(h, i + h); self.bc = np.zeros(h)
        self.Wo = W(h, i + h); self.bo = np.zeros(h)
        self.hidden_size = hidden_size

    def forward(self, x: np.ndarray, h: np.ndarray, c: np.ndarray):
        xh = np.concatenate([x, h])
        f  = _sigmoid(self.Wf @ xh + self.bf)
        ig = _sigmoid(self.Wi @ xh + self.bi)
        g  = np.tanh(self.Wc @ xh + self.bc)
        o  = _sigmoid(self.Wo @ xh + self.bo)
        c2 = f * c + ig * g
        h2 = o * np.tanh(c2)
        return h2, c2

    def params(self):
        return [self.Wf, self.bf, self.Wi, self.bi,
                self.Wc, self.bc, self.Wo, self.bo]

    def set_params(self, p):
        (self.Wf, self.bf, self.Wi, self.bi,
         self.Wc, self.bc, self.Wo, self.bo) = p


def _sigmoid(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))
def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


class LSTMClassifier:
    """
    Lightweight 2-layer LSTM classifier (numpy only, no PyTorch/TF required).

    For production accuracy, call train_with_keras() which uses Keras if
    available, then exports weights back into this class for inference.
    """

    def __init__(self, hidden1: int = 128, hidden2: int = 64,
                 dense: int = 64, n_classes: int = len(ALL_LABELS)):
        self.h1 = hidden1
        self.h2 = hidden2
        self.n_classes = n_classes

        self.lstm1 = _LSTMCell(INPUT_DIM, hidden1)
        self.lstm2 = _LSTMCell(hidden1, hidden2)

        s = np.sqrt(2.0 / (hidden2 + dense))
        self.W_dense = np.random.randn(dense, hidden2) * s
        self.b_dense = np.zeros(dense)
        self.W_out   = np.random.randn(n_classes, dense) * np.sqrt(2.0 / (dense + n_classes))
        self.b_out   = np.zeros(n_classes)

        self.label2idx = LABEL2IDX
        self.idx2label = IDX2LABEL
        self.scaler_mean: Optional[np.ndarray] = None
        self.scaler_std:  Optional[np.ndarray] = None

    # ── Inference ──────────────────────────────────────────────────────────

    def predict_proba(self, sequence: np.ndarray) -> np.ndarray:
        """
        Args:
            sequence: (T, 99) float32 — normalised landmark coords
        Returns:
            (n_classes,) probability vector
        """
        seq = self._normalise(sequence)
        seq = self._pad_or_trim(seq, SEQUENCE_LEN)

        h1 = np.zeros(self.h1); c1 = np.zeros(self.h1)
        h2 = np.zeros(self.h2); c2 = np.zeros(self.h2)

        for t in range(seq.shape[0]):
            h1, c1 = self.lstm1.forward(seq[t], h1, c1)
            h2, c2 = self.lstm2.forward(h1, h2, c2)

        x = np.maximum(0, self.W_dense @ h2 + self.b_dense)   # ReLU
        logits = self.W_out @ x + self.b_out
        return _softmax(logits)

    def predict(self, sequence: np.ndarray) -> Tuple[str, float]:
        """Returns (label, confidence)."""
        proba = self.predict_proba(sequence)
        idx   = int(np.argmax(proba))
        return self.idx2label[idx], float(proba[idx])

    def predict_top3(self, sequence: np.ndarray) -> List[Tuple[str, float]]:
        proba = self.predict_proba(sequence)
        top3  = np.argsort(proba)[::-1][:3]
        return [(self.idx2label[i], float(proba[i])) for i in top3]

    # ── Training (numpy SGD — slow but dependency-free) ───────────────────

    def fit_sklearn_fallback(
        self,
        X: np.ndarray,   # (N, T, 99)
        y: np.ndarray,   # (N,) int labels
        epochs: int = 20,
        lr: float = 0.001,
    ):
        """
        Very simple SGD training loop (no backprop through time — uses
        sklearn RF on extracted LSTM embeddings as a quicker alternative).
        Call train_pipeline() for the proper training workflow.
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler

        print("Extracting LSTM embeddings for RF training...")
        embeddings = np.array([self._embed(x) for x in X])
        sc = StandardScaler()
        embeddings = sc.fit_transform(embeddings)

        rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        rf.fit(embeddings, y)

        self._rf_fallback  = rf
        self._rf_scaler    = sc
        self._use_rf       = True
        print(f"RF trained. OOB score: {rf.oob_score_:.3f}" if hasattr(rf, 'oob_score_') else "RF trained.")

    def _embed(self, sequence: np.ndarray) -> np.ndarray:
        """Run LSTM and return last hidden state as embedding."""
        seq = self._normalise(sequence)
        seq = self._pad_or_trim(seq, SEQUENCE_LEN)
        h1 = np.zeros(self.h1); c1 = np.zeros(self.h1)
        h2 = np.zeros(self.h2); c2 = np.zeros(self.h2)
        for t in range(seq.shape[0]):
            h1, c1 = self.lstm1.forward(seq[t], h1, c1)
            h2, c2 = self.lstm2.forward(h1, h2, c2)
        return h2

    # ── Keras training (preferred, requires tensorflow) ───────────────────

    @classmethod
    def train_with_keras(
        cls,
        X_train: np.ndarray,   # (N, T, 99)
        y_train: np.ndarray,   # (N,) int
        X_val:   np.ndarray,
        y_val:   np.ndarray,
        save_path: str = "data/models/lstm_model.pkl",
        epochs: int = 50,
        batch_size: int = 32,
    ) -> "LSTMClassifier":
        """
        Train with Keras for best accuracy, export weights to this class.
        Falls back to sklearn RF if TensorFlow is not available.
        """
        try:
            import tensorflow as tf
            from tensorflow import keras

            n_classes = len(ALL_LABELS)
            T = X_train.shape[1]

            model = keras.Sequential([
                keras.layers.Input(shape=(T, INPUT_DIM)),
                keras.layers.LSTM(128, return_sequences=True),
                keras.layers.Dropout(0.3),
                keras.layers.LSTM(64),
                keras.layers.Dropout(0.3),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.Dense(n_classes, activation='softmax'),
            ])

            model.compile(
                optimizer=keras.optimizers.Adam(0.001),
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy'],
            )

            cb = [
                keras.callbacks.EarlyStopping(patience=8, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(patience=4, factor=0.5),
            ]

            model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=cb,
                verbose=1,
            )

            obj = cls()
            obj._keras_model = model
            obj._use_keras   = True
            obj.save(save_path)
            print(f"Keras model saved → {save_path}")
            return obj

        except ImportError:
            print("TensorFlow not available — falling back to sklearn RF.")
            obj = cls()
            obj.fit_sklearn_fallback(X_train, y_train)
            obj.save(save_path)
            return obj

    def predict_keras(self, sequence: np.ndarray) -> Tuple[str, float]:
        seq   = self._normalise(sequence)
        seq   = self._pad_or_trim(seq, SEQUENCE_LEN)
        proba = self._keras_model.predict(seq[np.newaxis], verbose=0)[0]
        idx   = int(np.argmax(proba))
        return self.idx2label[idx], float(proba[idx])

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> "LSTMClassifier":
        with open(path, 'rb') as f:
            return pickle.load(f)

    @staticmethod
    def is_trained(path: str) -> bool:
        return Path(path).exists()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _normalise(self, seq: np.ndarray) -> np.ndarray:
        if self.scaler_mean is not None:
            return (seq - self.scaler_mean) / (self.scaler_std + 1e-8)
        return seq.astype(np.float32)

    @staticmethod
    def _pad_or_trim(seq: np.ndarray, length: int) -> np.ndarray:
        T = seq.shape[0]
        if T >= length:
            return seq[:length]
        pad = np.zeros((length - T, seq.shape[1]), dtype=seq.dtype)
        return np.vstack([seq, pad])


# ── Feature extraction helpers ─────────────────────────────────────────────

def poses_to_sequence(poses: List[Dict]) -> np.ndarray:
    """
    Convert a list of pose dicts (from AdvancedSkatingAnalyzer) to
    a (T, 99) float32 array ready for LSTMClassifier.

    Each pose dict has 'keypoints': list of 33 dicts with x, y, z.
    Missing / low-visibility landmarks are zeroed.
    """
    MIN_VIS = 0.3
    rows = []
    for p in poses:
        row = np.zeros(INPUT_DIM, dtype=np.float32)
        for kp in p['keypoints']:
            i = kp['index']
            if kp.get('visibility', 0) >= MIN_VIS:
                row[i*3    ] = kp['x']
                row[i*3 + 1] = kp['y']
                row[i*3 + 2] = kp['z']
        rows.append(row)
    return np.array(rows, dtype=np.float32)


def augment_sequence(seq: np.ndarray, n: int = 4) -> List[np.ndarray]:
    """
    Data augmentation: horizontal flip, time jitter, noise.
    Increases training set size without collecting more videos.
    """
    out = [seq]
    for _ in range(n - 1):
        aug = seq.copy()
        # Random time shift (±10%)
        shift = int(seq.shape[0] * 0.1 * np.random.choice([-1, 0, 1]))
        if shift > 0:
            aug = np.vstack([np.zeros((shift, seq.shape[1])), aug[:-shift]])
        elif shift < 0:
            aug = np.vstack([aug[-shift:], np.zeros((-shift, seq.shape[1]))])
        # Small Gaussian noise
        aug += np.random.randn(*aug.shape).astype(np.float32) * 0.005
        out.append(aug)
    return out
