"""
Figure Skating Element Classifier
Uses scikit-learn ensemble methods — no deep learning framework required.
"""

from __future__ import annotations

import warnings
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import joblib
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    warnings.warn("joblib not available — model persistence will not work")

try:
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not available — SkatingClassifier will not work")

try:
    from src.models.lstm_classifier import LABEL2IDX, IDX2LABEL, ALL_LABELS
except ImportError:
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
    LABEL2IDX = {l: i for i, l in enumerate(ALL_LABELS)}
    IDX2LABEL = {i: l for l, i in LABEL2IDX.items()}

from src.ai.feature_extractor import FEATURE_NAMES


class SkatingClassifier:
    """
    Ensemble figure skating element classifier.
    Combines RandomForest + GradientBoosting for robust predictions.
    """

    def __init__(self):
        self.label2idx = LABEL2IDX
        self.idx2label = IDX2LABEL
        self.feature_names = FEATURE_NAMES
        self.training_history: dict = {}
        self._dynamic_idx2label: Optional[dict] = None

        if SKLEARN_AVAILABLE:
            self.model = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                )),
            ])
            self.gradient_boost_model = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=4,
                    random_state=42,
                )),
            ])
        else:
            self.model = None
            self.gradient_boost_model = None

        self._rf_trained = False
        self._gb_trained = False
        self._train_labels: list = []

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        val_ratio: float = 0.2,
        verbose: bool = True,
    ) -> dict:
        """
        Train the ensemble classifier.

        Returns metrics dict with val_accuracy, per_class_accuracy,
        confusion_matrix, n_samples, feature_importances.
        """
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn is required for training")

        if len(X) < 4:
            raise ValueError(f"Need at least 4 samples, got {len(X)}")

        n_classes = len(np.unique(y))
        actual_val_ratio = val_ratio if len(X) >= 10 else 0.0

        if actual_val_ratio > 0:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y,
                test_size=actual_val_ratio,
                random_state=42,
                stratify=y if n_classes > 1 else None,
            )
        else:
            X_train, X_val = X, X
            y_train, y_val = y, y

        if verbose:
            print(f"Training RF on {len(X_train)} samples, validating on {len(X_val)}...")

        # Train RandomForest pipeline
        self.model.fit(X_train, y_train)
        self._rf_trained = True

        # Train GradientBoosting pipeline
        if verbose:
            print("Training GradientBoosting...")
        try:
            self.gradient_boost_model.fit(X_train, y_train)
            self._gb_trained = True
        except Exception as e:
            warnings.warn(f"GradientBoosting training failed: {e}")
            self._gb_trained = False

        # Validation accuracy
        rf_proba = self.model.predict_proba(X_val)
        if self._gb_trained:
            gb_proba = self.gradient_boost_model.predict_proba(X_val)
            # Align probability arrays (may differ in n_classes if train/val split differs)
            try:
                ensemble_proba = (rf_proba + gb_proba) / 2.0
            except Exception:
                ensemble_proba = rf_proba
        else:
            ensemble_proba = rf_proba

        y_pred = np.argmax(ensemble_proba, axis=1)
        val_acc = float(accuracy_score(y_val, y_pred))

        # Per-class accuracy
        unique_classes = np.unique(y_val)
        per_class_acc = {}
        for cls in unique_classes:
            mask = y_val == cls
            if mask.sum() > 0:
                cls_acc = float(accuracy_score(y_val[mask], y_pred[mask]))
                label = self._get_label(cls)
                per_class_acc[label] = cls_acc

        # Confusion matrix
        cm = confusion_matrix(y_val, y_pred, labels=unique_classes)
        cm_dict = {
            "matrix": cm.tolist(),
            "labels": [self._get_label(c) for c in unique_classes],
        }

        # Feature importances from RF
        rf_clf = self.model.named_steps["clf"]
        feat_imp = {
            name: float(imp)
            for name, imp in zip(self.feature_names, rf_clf.feature_importances_)
        }

        # Store training history
        self._train_labels = [self._get_label(c) for c in np.unique(y)]
        self.training_history = {
            "val_accuracy": val_acc,
            "n_samples": int(len(X)),
            "n_classes": int(n_classes),
            "trained_at": datetime.now().isoformat(),
            "model_version": "1.0.0",
        }

        metrics = {
            "val_accuracy": val_acc,
            "per_class_accuracy": per_class_acc,
            "confusion_matrix": cm_dict,
            "n_samples": int(len(X)),
            "feature_importances": feat_imp,
        }

        if verbose:
            print(f"Validation accuracy: {val_acc:.3f} ({val_acc*100:.1f}%)")
            print(f"Classes: {self._train_labels}")

        return metrics

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict(self, features: np.ndarray) -> tuple:
        """Return (label, confidence) using ensemble of RF + GB."""
        proba_dict = self.predict_proba(features)
        if not proba_dict:
            return ("None", 0.0)
        best_label = max(proba_dict, key=proba_dict.get)
        return (best_label, proba_dict[best_label])

    def predict_proba(self, features: np.ndarray) -> dict:
        """Return dict of label -> probability for top 5 predictions."""
        if not self._rf_trained or self.model is None:
            return {}

        x = features.reshape(1, -1)

        try:
            rf_proba = self.model.predict_proba(x)[0]
            rf_classes = self.model.classes_

            if self._gb_trained:
                gb_proba = self.gradient_boost_model.predict_proba(x)[0]
                gb_classes = self.gradient_boost_model.classes_

                # Build unified probability array
                all_cls = sorted(set(rf_classes) | set(gb_classes))
                rf_map = {c: p for c, p in zip(rf_classes, rf_proba)}
                gb_map = {c: p for c, p in zip(gb_classes, gb_proba)}
                ensemble = {
                    c: (rf_map.get(c, 0.0) + gb_map.get(c, 0.0)) / 2.0
                    for c in all_cls
                }
            else:
                ensemble = {
                    c: float(p) for c, p in zip(rf_classes, rf_proba)
                }

            # Sort by probability and take top 5
            sorted_items = sorted(ensemble.items(), key=lambda kv: kv[1], reverse=True)[:5]
            return {
                self._get_label(cls_idx): float(prob)
                for cls_idx, prob in sorted_items
            }

        except Exception as e:
            warnings.warn(f"Prediction failed: {e}")
            return {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str):
        """Save model with joblib."""
        if not JOBLIB_AVAILABLE:
            raise RuntimeError("joblib is required for saving")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "SkatingClassifier":
        """Load model with joblib."""
        if not JOBLIB_AVAILABLE:
            raise RuntimeError("joblib is required for loading")
        return joblib.load(path)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_feature_importance(self, top_n: int = 10) -> list:
        """Return list of {feature, importance} sorted by importance descending."""
        if not self._rf_trained or self.model is None:
            return []

        try:
            rf_clf = self.model.named_steps["clf"]
            importances = rf_clf.feature_importances_
            items = [
                {"feature": name, "importance": float(imp)}
                for name, imp in zip(self.feature_names, importances)
            ]
            items.sort(key=lambda x: x["importance"], reverse=True)
            return items[:top_n]
        except Exception as e:
            warnings.warn(f"Could not compute feature importance: {e}")
            return []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_label(self, idx) -> str:
        """Convert class index to label string."""
        idx = int(idx)
        # Check dynamic label mapping first
        if self._dynamic_idx2label and idx in self._dynamic_idx2label:
            return self._dynamic_idx2label[idx]
        return self.idx2label.get(idx, f"class_{idx}")

    def set_dynamic_labels(self, label_list: list):
        """Set a dynamic label mapping for classes not in ALL_LABELS."""
        self._dynamic_idx2label = {i: l for i, l in enumerate(label_list)}
