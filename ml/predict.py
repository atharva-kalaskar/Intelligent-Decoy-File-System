"""
Inference Module for Window Activity Classification
Validates feature inputs against schema, loads model artifacts, computes class probabilities,
and constructs evidence-based risk explanations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd

from preprocess import FEATURE_COLUMNS

logger = logging.getLogger("predict_engine")
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "random_forest_model.joblib"
DEFAULT_METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

_CACHED_MODEL = None
_CACHED_METADATA = None
_CACHED_PATH = None


def load_model_and_metadata(
    model_path: Path = DEFAULT_MODEL_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH,
    force_reload: bool = False
) -> Tuple[Any, Dict[str, Any]]:
    """Loads and caches the trained Random Forest model and associated metadata."""
    global _CACHED_MODEL, _CACHED_METADATA, _CACHED_PATH

    model_path = Path(model_path)
    metadata_path = Path(metadata_path)

    if not force_reload and _CACHED_MODEL is not None and _CACHED_PATH == model_path:
        return _CACHED_MODEL, _CACHED_METADATA

    if not model_path.exists():
        raise FileNotFoundError(f"Trained model artifact not found at: {model_path}")

    _CACHED_MODEL = joblib.load(model_path)
    _CACHED_PATH = model_path

    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            _CACHED_METADATA = json.load(f)
    else:
        _CACHED_METADATA = {"model_version": "1.0.0", "feature_schema_version": "1.0.0"}

    return _CACHED_MODEL, _CACHED_METADATA


def generate_reason_summary(features: Dict[str, Any], proba: float, prediction: int) -> str:
    """
    Constructs an evidence-backed factual rationale based on observed metrics.
    Avoids asserting unconfirmed intent.
    """
    reasons = []
    decoy_evts = features.get("decoy_events", 0)
    decoy_rat = features.get("decoy_ratio", 0.0)
    eps = features.get("events_per_second", 0.0)
    inter_mean = features.get("inter_event_mean", 0.0)
    del_count = features.get("delete_count", 0)
    mod_count = features.get("modify_count", 0)

    if decoy_evts > 0:
        reasons.append(f"{decoy_evts} decoy event(s) observed ({decoy_rat*100:.1f}% of window activity)")

    if eps >= 5.0:
        reasons.append(f"High event frequency ({eps:.1f} events/sec)")

    if del_count > 0:
        reasons.append(f"{del_count} file deletion(s)")

    if mod_count >= 5:
        reasons.append(f"Elevated modification burst ({mod_count} files)")

    if inter_mean > 0 and inter_mean < 0.3:
        reasons.append(f"Rapid automated burst timing (mean interval {inter_mean:.3f}s)")

    if not reasons:
        if prediction == 0:
            return "Standard file modification cadence within expected parameters; no honey-file triggers."
        return "Behavioral window feature combination matched suspicious classification boundaries."

    summary = "; ".join(reasons)
    if prediction == 1:
        return f"Suspicious indicator(s): {summary}"
    else:
        return f"Incidental / non-threatening indicator(s): {summary}"


def predict_window(
    features: Dict[str, Any],
    threshold: float = 0.50,
    model_path: Path = DEFAULT_MODEL_PATH,
    metadata_path: Path = DEFAULT_METADATA_PATH
) -> Dict[str, Any]:
    """
    Performs inference for an extracted window feature dictionary.
    Returns prediction dictionary with probability, label, and evidence summary.
    """
    model, metadata = load_model_and_metadata(model_path, metadata_path)

    # 1. Align feature vector to exact training column order
    row_values = []
    for col in FEATURE_COLUMNS:
        val = features.get(col, 0.0)
        row_values.append(float(val) if val is not None else 0.0)

    X_sample = pd.DataFrame([row_values], columns=FEATURE_COLUMNS)

    # 2. Compute probabilities
    probabilities = model.predict_proba(X_sample)[0]
    suspicious_proba = float(probabilities[1]) if len(probabilities) > 1 else float(probabilities[0])

    is_suspicious = 1 if suspicious_proba >= threshold else 0

    if suspicious_proba >= 0.75:
        risk_level = "CRITICAL"
    elif suspicious_proba >= 0.40:
        risk_level = "ELEVATED"
    else:
        risk_level = "LOW"

    reason_summary = generate_reason_summary(features, suspicious_proba, is_suspicious)

    return {
        "prediction": "suspicious" if is_suspicious == 1 else "normal",
        "is_suspicious": is_suspicious,
        "suspicious_probability": round(suspicious_proba, 4),
        "normal_probability": round(1.0 - suspicious_proba, 4),
        "risk_level": risk_level,
        "model_version": metadata.get("model_version", "1.0.0"),
        "reason_summary": reason_summary,
        "input_features": {k: features.get(k) for k in FEATURE_COLUMNS}
    }


if __name__ == "__main__":
    # Test sample with decoy activity
    test_sample = {
        "event_count": 5,
        "unique_files": 3,
        "decoy_events": 2,
        "decoy_ratio": 0.40,
        "create_count": 1,
        "modify_count": 4,
        "delete_count": 0,
        "rename_count": 0,
        "events_per_second": 1.2,
        "inter_event_mean": 0.8,
        "inter_event_std": 0.2
    }
    pred = predict_window(test_sample)
    print(json.dumps(pred, indent=2))
