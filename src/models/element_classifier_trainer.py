"""
ML Training Pipeline for Element Classification
نظام تدريب نماذج تصنيف العناصر (قفزات، دورانات، خطوات)
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib


@dataclass
class TrainingConfig:
    """Training configuration"""
    model_type: str = "random_forest"  # random_forest, gradient_boost, svm, neural_net
    test_size: float = 0.2
    random_seed: int = 42
    n_estimators: int = 100  # for tree-based models
    max_depth: Optional[int] = None
    learning_rate: float = 0.1
    verbose: bool = True


@dataclass
class TrainingResults:
    """Training results"""
    model_name: str
    accuracy_train: float
    accuracy_test: float
    classification_report: str
    confusion_matrix: np.ndarray
    feature_importance: Optional[Dict[str, float]] = None
    cross_val_scores: Optional[List[float]] = None


class ElementClassifierTrainer:
    """
    ML Trainer for Element Classification
    مدرب نماذج تصنيف العناصر
    """

    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.label_encoder = {}  # map labels to integers

    def prepare_dataset(
        self,
        dataset_df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare dataset for training

        Args:
            dataset_df: DataFrame with elements

        Returns:
            (X, y, feature_names)
        """
        print("📊 Preparing dataset...")

        # Feature engineering
        features_list = []
        labels = []

        for _, row in dataset_df.iterrows():
            # Extract features from row
            features = self._extract_features(row)

            if features:
                features_list.append(features)
                labels.append(row['isu_code'])

        if not features_list:
            raise ValueError("No features extracted!")

        X = np.array(features_list)
        y = np.array(labels)

        # Get feature names
        self.feature_names = list(features_list[0].keys())

        # Convert to numpy arrays
        X = np.array([list(f.values()) for f in features_list])

        print(f"   Features shape: {X.shape}")
        print(f"   Labels shape: {y.shape}")
        print(f"   Unique labels: {len(np.unique(y))}")

        return X, y, self.feature_names

    def _extract_features(self, row: pd.Series) -> Optional[Dict]:
        """
        Extract features from a single data point

        Features include:
        - Duration
        - Frame count
        - Type of element
        - Rotations (for jumps)
        - Level (for spins/steps)
        - Base value
        - etc.
        """
        try:
            features = {}

            # Basic features
            features['duration'] = (row['end_frame'] - row['start_frame']) / 30.0  # assume 30 fps
            features['frame_count'] = row['end_frame'] - row['start_frame']

            # Element type encoding
            element_type = row['element_type']
            features['is_jump'] = 1 if element_type == 'jump' else 0
            features['is_spin'] = 1 if element_type == 'spin' else 0
            features['is_step'] = 1 if element_type == 'step_sequence' else 0

            # Jump features
            if pd.notna(row.get('rotations')):
                features['rotations'] = float(row['rotations'])
            else:
                features['rotations'] = 0.0

            # Spin/step features
            if pd.notna(row.get('level')):
                features['level'] = float(row['level'])
            else:
                features['level'] = 0.0

            # Scoring features
            features['base_value'] = float(row['base_value'])
            features['goe'] = float(row['goe'])

            return features

        except Exception as e:
            print(f"Error extracting features: {e}")
            return None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> TrainingResults:
        """
        Train the model

        Args:
            X_train, y_train: training data
            X_test, y_test: test data

        Returns:
            TrainingResults
        """
        print(f"\n🚀 Training {self.config.model_type} model...")

        # Encode labels
        unique_labels = np.unique(np.concatenate([y_train, y_test]))
        self.label_encoder = {label: i for i, label in enumerate(unique_labels)}
        inverse_encoder = {i: label for label, i in self.label_encoder.items()}

        y_train_encoded = np.array([self.label_encoder[label] for label in y_train])
        y_test_encoded = np.array([self.label_encoder[label] for label in y_test])

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Create model
        self.model = self._create_model()

        # Train
        self.model.fit(X_train_scaled, y_train_encoded)

        # Predictions
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)

        # Decode predictions
        y_train_pred_labels = [inverse_encoder[i] for i in y_train_pred]
        y_test_pred_labels = [inverse_encoder[i] for i in y_test_pred]

        # Metrics
        acc_train = accuracy_score(y_train, y_train_pred_labels)
        acc_test = accuracy_score(y_test, y_test_pred_labels)

        print(f"\n📈 Results:")
        print(f"   Train accuracy: {acc_train:.3f}")
        print(f"   Test accuracy: {acc_test:.3f}")

        # Classification report
        report = classification_report(y_test, y_test_pred_labels)
        print(f"\n{report}")

        # Confusion matrix
        cm = confusion_matrix(y_test, y_test_pred_labels)

        # Feature importance
        feature_importance = None
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            feature_importance = {
                name: float(imp)
                for name, imp in zip(self.feature_names, importances)
            }

            print("\n📊 Feature Importance:")
            for name, imp in sorted(feature_importance.items(),
                                   key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {name}: {imp:.4f}")

        # Cross-validation
        cv_scores = None
        if self.config.verbose:
            print("\n🔄 Running cross-validation...")
            cv_scores = cross_val_score(
                self.model,
                X_train_scaled,
                y_train_encoded,
                cv=5
            )
            print(f"   CV scores: {cv_scores}")
            print(f"   CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        return TrainingResults(
            model_name=self.config.model_type,
            accuracy_train=acc_train,
            accuracy_test=acc_test,
            classification_report=report,
            confusion_matrix=cm,
            feature_importance=feature_importance,
            cross_val_scores=cv_scores.tolist() if cv_scores is not None else None
        )

    def _create_model(self):
        """Create model based on config"""
        if self.config.model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth,
                random_state=self.config.random_seed,
                n_jobs=-1
            )

        elif self.config.model_type == "gradient_boost":
            return GradientBoostingClassifier(
                n_estimators=self.config.n_estimators,
                max_depth=self.config.max_depth or 3,
                learning_rate=self.config.learning_rate,
                random_state=self.config.random_seed
            )

        elif self.config.model_type == "svm":
            return SVC(
                kernel='rbf',
                random_state=self.config.random_seed
            )

        elif self.config.model_type == "neural_net":
            return MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                max_iter=500,
                random_state=self.config.random_seed
            )

        else:
            raise ValueError(f"Unknown model type: {self.config.model_type}")

    def predict(self, features: Dict) -> Tuple[str, float]:
        """
        Predict element type from features

        Args:
            features: feature dictionary

        Returns:
            (predicted_label, confidence)
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")

        # Convert features to array
        feature_vector = [features.get(name, 0.0) for name in self.feature_names]
        X = np.array([feature_vector])

        # Scale
        X_scaled = self.scaler.transform(X)

        # Predict
        pred_encoded = self.model.predict(X_scaled)[0]
        pred_proba = self.model.predict_proba(X_scaled)[0]

        # Decode
        inverse_encoder = {i: label for label, i in self.label_encoder.items()}
        predicted_label = inverse_encoder[pred_encoded]
        confidence = pred_proba[pred_encoded]

        return predicted_label, confidence

    def save_model(self, output_dir: str):
        """Save trained model"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save model
        model_file = output_path / "model.pkl"
        joblib.dump(self.model, model_file)

        # Save scaler
        scaler_file = output_path / "scaler.pkl"
        joblib.dump(self.scaler, scaler_file)

        # Save metadata
        metadata = {
            'model_type': self.config.model_type,
            'feature_names': self.feature_names,
            'label_encoder': self.label_encoder,
            'training_config': {
                'n_estimators': self.config.n_estimators,
                'max_depth': self.config.max_depth,
                'learning_rate': self.config.learning_rate
            }
        }

        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n✅ Model saved to: {output_path}")

    def load_model(self, model_dir: str):
        """Load trained model"""
        model_path = Path(model_dir)

        # Load model
        model_file = model_path / "model.pkl"
        self.model = joblib.load(model_file)

        # Load scaler
        scaler_file = model_path / "scaler.pkl"
        self.scaler = joblib.load(scaler_file)

        # Load metadata
        metadata_file = model_path / "metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        self.feature_names = metadata['feature_names']
        self.label_encoder = metadata['label_encoder']

        print(f"✅ Model loaded from: {model_path}")


def train_element_classifier():
    """
    Train element classifier
    """
    from src.utils.dataset_manager import DatasetManager

    # Load dataset
    dm = DatasetManager("data/skating_dataset")
    df = dm.export_to_dataframe()

    if len(df) == 0:
        print("❌ No data found! Please annotate some videos first.")
        return

    print(f"📊 Dataset loaded: {len(df)} elements")

    # Get train/test split
    try:
        train_ids = dm.get_split('train')
        test_ids = dm.get_split('test')
    except ValueError:
        # Create split if not exists
        dm.create_train_test_split(test_ratio=0.2)
        train_ids = dm.get_split('train')
        test_ids = dm.get_split('test')

    # Split data
    train_df = df[df['video_id'].isin(train_ids)]
    test_df = df[df['video_id'].isin(test_ids)]

    print(f"   Train: {len(train_df)} elements")
    print(f"   Test: {len(test_df)} elements")

    # Create trainer
    config = TrainingConfig(
        model_type="random_forest",
        n_estimators=100,
        verbose=True
    )

    trainer = ElementClassifierTrainer(config)

    # Prepare data
    X_train, y_train, feature_names = trainer.prepare_dataset(train_df)
    X_test, y_test, _ = trainer.prepare_dataset(test_df)

    # Train
    results = trainer.train(X_train, y_train, X_test, y_test)

    # Save model
    trainer.save_model("models/element_classifier")

    print("\n✅ Training complete!")

    return trainer, results


if __name__ == "__main__":
    train_element_classifier()
