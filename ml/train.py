"""
Random Forest Model Training Pipeline
Performs session-grouped leakage-free train/val/test splitting, hyperparameter tuning,
model evaluation, and serialization with metadata.
"""

import json
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from preprocess import FEATURE_COLUMNS

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "feature_windows.csv"
MODEL_SAVE_PATH = BASE_DIR / "models" / "random_forest_model.joblib"
METADATA_SAVE_PATH = BASE_DIR / "models" / "model_metadata.json"
TEST_DATA_PATH = BASE_DIR / "data" / "processed" / "test_set.csv"


def train_model(random_seed: int = 42):
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(f"Processed dataset not found: {PROCESSED_DATA_PATH}")

    df = pd.read_csv(PROCESSED_DATA_PATH)
    print(f"[INFO] Loaded dataset with {len(df)} rows.")

    # 1. Verify schema & separate features from target
    X = df[FEATURE_COLUMNS]
    y = df["is_suspicious"]
    groups = df["session_id"]

    # 2. Session-grouped splitting to prevent window data leakage
    # 70% Train, 15% Validation, 15% Held-out Test
    gss_test = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=random_seed)
    train_val_idx, test_idx = next(gss_test.split(X, y, groups))

    X_train_val = X.iloc[train_val_idx]
    y_train_val = y.iloc[train_val_idx]
    groups_train_val = groups.iloc[train_val_idx]

    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]
    df_test = df.iloc[test_idx]

    # Save held-out test set for evaluation script
    TEST_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_test.to_csv(TEST_DATA_PATH, index=False)

    gss_val = GroupShuffleSplit(n_splits=1, test_size=0.176, random_state=random_seed) # 0.176 of 0.85 ≈ 0.15
    train_idx, val_idx = next(gss_val.split(X_train_val, y_train_val, groups_train_val))

    X_train = X_train_val.iloc[train_idx]
    y_train = y_train_val.iloc[train_idx]
    X_val = X_train_val.iloc[val_idx]
    y_val = y_train_val.iloc[val_idx]

    print(f"[INFO] Data split - Train: {len(X_train)} | Validation: {len(X_val)} | Test: {len(X_test)}")
    print(f"[INFO] Unique sessions - Train: {groups.iloc[train_val_idx].iloc[train_idx].nunique()} | Val: {groups.iloc[train_val_idx].iloc[val_idx].nunique()} | Test: {groups.iloc[test_idx].nunique()}")

    # 3. Model Hyperparameter Tuning on Validation Set
    best_f1 = -1.0
    best_params = {}
    best_clf = None

    param_grid = [
        {"n_estimators": 100, "max_depth": 8, "min_samples_split": 2, "class_weight": "balanced"},
        {"n_estimators": 150, "max_depth": 10, "min_samples_split": 2, "class_weight": "balanced"},
        {"n_estimators": 200, "max_depth": 12, "min_samples_split": 4, "class_weight": "balanced"},
        {"n_estimators": 200, "max_depth": None, "min_samples_split": 2, "class_weight": None}
    ]

    print("[INFO] Tuning hyperparameters over validation set...")
    for params in param_grid:
        clf = RandomForestClassifier(**params, random_state=random_seed, n_jobs=-1)
        clf.fit(X_train, y_train)
        val_preds = clf.predict(X_val)
        val_f1 = f1_score(y_val, val_preds, zero_division=0)
        val_acc = accuracy_score(y_val, val_preds)
        print(f"  Params: {params} -> Val F1: {val_f1:.4f}, Val Acc: {val_acc:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            best_params = params
            best_clf = clf

    print(f"[OK] Selected best parameters: {best_params} (Val F1: {best_f1:.4f})")

    # 4. Refit selected configuration on combined Train + Validation
    print("[INFO] Retraining best model on combined Train+Validation sets...")
    final_clf = RandomForestClassifier(**best_params, random_state=random_seed, n_jobs=-1)
    final_clf.fit(X_train_val, y_train_val)

    # 5. Serialize model and metadata
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_clf, MODEL_SAVE_PATH)
    print(f"[OK] Saved trained model to: {MODEL_SAVE_PATH}")

    # Feature importance
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(FEATURE_COLUMNS, final_clf.feature_importances_)
    }

    metadata = {
        "model_name": "RandomForestClassifier",
        "model_version": "1.0.0",
        "feature_schema_version": "1.0.0",
        "trained_at": datetime.now().isoformat(),
        "random_seed": random_seed,
        "hyperparameters": best_params,
        "feature_columns": FEATURE_COLUMNS,
        "feature_importances": feature_importances,
        "dataset_summary": {
            "total_windows": len(df),
            "train_val_samples": len(X_train_val),
            "test_samples": len(X_test),
            "class_distribution": df["is_suspicious"].value_counts().to_dict()
        },
        "dependencies": {
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__
        }
    }

    with open(METADATA_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Saved model metadata to: {METADATA_SAVE_PATH}")
    print("[INFO] Feature importances:")
    for f_name, f_imp in sorted(feature_importances.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {f_name:20s}: {f_imp:.4f}")

    return final_clf, metadata


if __name__ == "__main__":
    train_model()
