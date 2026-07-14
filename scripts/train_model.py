#!/usr/bin/env python3
"""
Model Training Script
سكريبت تدريب النموذج

Trains ML models on extracted video features
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import json
from datetime import datetime

from src.utils.feature_extractor import FeatureExtractor


def train_model(
    features_file: str = 'data/features/extracted_features.pkl',
    target: str = 'category',
    model_type: str = 'random_forest',
    test_size: float = 0.2,
    output_dir: str = 'data/models'
):
    """
    Train ML model on extracted features

    Args:
        features_file: Path to extracted features file
        target: What to predict ('category', 'subcategory', 'skill_level')
        model_type: Type of model ('random_forest', 'gradient_boosting', 'svm')
        test_size: Fraction of data for testing
        output_dir: Directory to save trained model
    """
    print("=" * 60)
    print("🤖 MODEL TRAINING")
    print("=" * 60)
    print(f"Features file: {features_file}")
    print(f"Target: {target}")
    print(f"Model type: {model_type}")
    print()

    # Load features
    print("📂 Loading features...")
    extractor = FeatureExtractor()
    extractor.load_features(features_file)

    if not extractor.extracted_features:
        print("❌ No features found!")
        return

    # Get training data
    print(f"📊 Preparing training data for target: {target}")
    X, y, labels = extractor.get_training_data(
        target=target,
        include_landmarks=True
    )

    if len(X) == 0:
        print("❌ No valid training data!")
        return

    print(f"✅ Dataset: {len(X)} samples, {X.shape[1]} features, {len(labels)} classes")
    print(f"Classes: {labels}")
    print()

    # Check class distribution
    print("📊 Class Distribution:")
    unique, counts = np.unique(y, return_counts=True)
    for idx, count in zip(unique, counts):
        print(f"  {labels[idx]}: {count} samples")
    print()

    # Normalize features
    print("🔧 Normalizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split data
    print(f"✂️ Splitting data (test size: {test_size})...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=test_size, random_state=42, stratify=y
    )

    print(f"  Training set: {len(X_train)} samples")
    print(f"  Test set: {len(X_test)} samples")
    print()

    # Create model
    print(f"🏗️ Creating {model_type} model...")

    if model_type == 'random_forest':
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
    elif model_type == 'gradient_boosting':
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
    elif model_type == 'svm':
        model = SVC(
            kernel='rbf',
            C=1.0,
            gamma='scale',
            random_state=42
        )
    else:
        print(f"❌ Unknown model type: {model_type}")
        return

    # Train model
    print("🚀 Training model...")
    model.fit(X_train, y_train)
    print("✅ Training complete!")
    print()

    # Evaluate on test set
    print("📊 Evaluating on test set...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"🎯 Test Accuracy: {accuracy:.2%}")
    print()

    # Classification report
    print("📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=labels, zero_division=0))

    # Confusion matrix
    print("🔢 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    print()

    # Cross-validation
    print("🔄 Cross-validation (5-fold)...")
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, n_jobs=-1)
    print(f"  CV Scores: {cv_scores}")
    print(f"  Mean CV Accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
    print()

    # Feature importance (if available)
    if hasattr(model, 'feature_importances_'):
        print("⭐ Top 10 Most Important Features:")
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]

        feature_names = [
            'duration', 'num_frames', 'fps',
            'avg_body_angle', 'std_body_angle',
            'avg_com_height', 'std_com_height',
            'avg_motion', 'max_motion', 'total_distance',
            'total_rotation', 'max_angular_vel', 'avg_angular_vel',
            'num_airborne', 'max_jump_height', 'avg_jump_height'
        ]

        for i in indices:
            if i < len(feature_names):
                print(f"  {i+1}. {feature_names[i]}: {importances[i]:.4f}")
            else:
                print(f"  {i+1}. Landmark feature {i-15}: {importances[i]:.4f}")
        print()

    # Save model
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f"{model_type}_{target}_{timestamp}.pkl"
    model_path = output_path / model_filename

    print(f"💾 Saving model to: {model_path}")

    model_data = {
        'model': model,
        'scaler': scaler,
        'labels': labels,
        'target': target,
        'model_type': model_type,
        'accuracy': float(accuracy),
        'cv_mean': float(cv_scores.mean()),
        'cv_std': float(cv_scores.std()),
        'num_features': X.shape[1],
        'num_classes': len(labels),
        'training_date': datetime.now().isoformat(),
        'num_training_samples': len(X_train),
        'num_test_samples': len(X_test)
    }

    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)

    print("✅ Model saved successfully!")

    # Save metadata as JSON
    metadata_path = output_path / model_filename.replace('.pkl', '_metadata.json')
    metadata = {k: v for k, v in model_data.items() if k not in ['model', 'scaler']}

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"💾 Metadata saved to: {metadata_path}")
    print()

    # Summary
    print("=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"Model: {model_type}")
    print(f"Target: {target}")
    print(f"Test Accuracy: {accuracy:.2%}")
    print(f"CV Accuracy: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
    print(f"Saved to: {model_path}")
    print("=" * 60)

    return model_data


def train_all_targets(
    features_file: str = 'data/features/extracted_features.pkl',
    model_type: str = 'random_forest'
):
    """Train models for all targets"""
    targets = ['category', 'subcategory', 'skill_level']

    for target in targets:
        print(f"\n{'=' * 60}")
        print(f"Training for target: {target}")
        print(f"{'=' * 60}\n")

        try:
            train_model(
                features_file=features_file,
                target=target,
                model_type=model_type
            )
        except Exception as e:
            print(f"❌ Error training {target}: {e}")
            continue


def compare_models(
    features_file: str = 'data/features/extracted_features.pkl',
    target: str = 'category'
):
    """Compare different model types"""
    model_types = ['random_forest', 'gradient_boosting', 'svm']
    results = []

    for model_type in model_types:
        print(f"\n{'=' * 60}")
        print(f"Training: {model_type}")
        print(f"{'=' * 60}\n")

        try:
            model_data = train_model(
                features_file=features_file,
                target=target,
                model_type=model_type
            )

            results.append({
                'model_type': model_type,
                'accuracy': model_data['accuracy'],
                'cv_mean': model_data['cv_mean'],
                'cv_std': model_data['cv_std']
            })
        except Exception as e:
            print(f"❌ Error with {model_type}: {e}")
            continue

    # Print comparison
    print("\n" + "=" * 60)
    print("📊 MODEL COMPARISON")
    print("=" * 60)
    print(f"{'Model':<20} {'Test Acc':>12} {'CV Mean':>12} {'CV Std':>10}")
    print("-" * 60)

    for result in sorted(results, key=lambda x: x['cv_mean'], reverse=True):
        print(f"{result['model_type']:<20} {result['accuracy']:>11.2%} "
              f"{result['cv_mean']:>11.2%} {result['cv_std']:>9.4f}")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train ML model on video features')
    parser.add_argument('--features', type=str,
                       default='data/features/extracted_features.pkl',
                       help='Path to extracted features file')
    parser.add_argument('--target', type=str, default='category',
                       choices=['category', 'subcategory', 'skill_level'],
                       help='What to predict')
    parser.add_argument('--model', type=str, default='random_forest',
                       choices=['random_forest', 'gradient_boosting', 'svm'],
                       help='Model type')
    parser.add_argument('--test-size', type=float, default=0.2,
                       help='Fraction of data for testing')
    parser.add_argument('--output', type=str, default='data/models',
                       help='Output directory for trained model')
    parser.add_argument('--all-targets', action='store_true',
                       help='Train models for all targets')
    parser.add_argument('--compare', action='store_true',
                       help='Compare all model types')

    args = parser.parse_args()

    if args.compare:
        compare_models(args.features, args.target)
    elif args.all_targets:
        train_all_targets(args.features, args.model)
    else:
        train_model(
            features_file=args.features,
            target=args.target,
            model_type=args.model,
            test_size=args.test_size,
            output_dir=args.output
        )
