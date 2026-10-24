"""
Unit tests for model loading, inference consistency, and error handling.
"""

import pytest
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "ml"))

from predict import predict_window, load_model_and_metadata
from preprocess import FEATURE_COLUMNS


def test_model_loading():
    model, metadata = load_model_and_metadata()
    assert model is not None
    assert metadata["model_version"] == "1.0.0"
    assert metadata["feature_columns"] == FEATURE_COLUMNS


def test_normal_activity_prediction():
    # Routine editing with 0 decoy events and modest rate
    normal_window = {
        "event_count": 3,
        "unique_files": 2,
        "decoy_events": 0,
        "decoy_ratio": 0.0,
        "create_count": 0,
        "modify_count": 3,
        "delete_count": 0,
        "rename_count": 0,
        "events_per_second": 0.1,
        "inter_event_mean": 5.0,
        "inter_event_std": 1.2
    }
    result = predict_window(normal_window)
    assert result["is_suspicious"] == 0
    assert result["prediction"] == "normal"
    assert result["suspicious_probability"] < 0.50
    assert result["risk_level"] in ("LOW", "ELEVATED")


def test_suspicious_recon_prediction():
    # Multiple decoy hits with high decoy ratio
    recon_window = {
        "event_count": 6,
        "unique_files": 4,
        "decoy_events": 4,
        "decoy_ratio": 0.67,
        "create_count": 0,
        "modify_count": 4,
        "delete_count": 0,
        "rename_count": 0,
        "events_per_second": 0.5,
        "inter_event_mean": 1.5,
        "inter_event_std": 0.4
    }
    result = predict_window(recon_window)
    assert result["is_suspicious"] == 1
    assert result["prediction"] == "suspicious"
    assert result["suspicious_probability"] >= 0.50
    assert result["risk_level"] in ("ELEVATED", "CRITICAL")
    assert "decoy" in result["reason_summary"].lower()


def test_missing_features_defaults():
    # Window missing several columns should gracefully default to 0.0
    sparse_window = {
        "event_count": 1,
        "decoy_events": 0
    }
    result = predict_window(sparse_window)
    assert "prediction" in result
    assert "suspicious_probability" in result


def test_missing_model_file_handling():
    with pytest.raises(FileNotFoundError):
        load_model_and_metadata(model_path=Path("non_existent_model.joblib"))
