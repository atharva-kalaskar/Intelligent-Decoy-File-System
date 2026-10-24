"""
Unit tests for behavioral feature extraction and edge case handling.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "ml"))

from preprocess import calculate_window_features, aggregate_events_into_windows, FEATURE_COLUMNS


def test_empty_window_features():
    feats = calculate_window_features([], window_duration_sec=30.0)
    for col in FEATURE_COLUMNS:
        assert col in feats
    assert feats["event_count"] == 0
    assert feats["decoy_ratio"] == 0.0
    assert feats["events_per_second"] == 0.0
    assert feats["inter_event_mean"] == 0.0
    assert feats["inter_event_std"] == 0.0


def test_single_event_features():
    evts = [{
        "event_id": "EVT-01",
        "timestamp": "2026-10-20T10:00:00.000",
        "event_type": "MODIFY",
        "relative_path": "decoys/canary.txt",
        "is_decoy": True,
        "source": "test"
    }]
    feats = calculate_window_features(evts, window_duration_sec=30.0)
    assert feats["event_count"] == 1
    assert feats["unique_files"] == 1
    assert feats["decoy_events"] == 1
    assert feats["decoy_ratio"] == 1.0
    assert feats["modify_count"] == 1
    assert feats["inter_event_mean"] == 0.0
    assert feats["inter_event_std"] == 0.0


def test_multiple_events_features():
    evts = [
        {
            "event_id": "EVT-01",
            "timestamp": "2026-10-20T10:00:00.000",
            "event_type": "CREATE",
            "relative_path": "documents/doc1.txt",
            "is_decoy": False,
            "source": "test"
        },
        {
            "event_id": "EVT-02",
            "timestamp": "2026-10-20T10:00:02.000",
            "event_type": "MODIFY",
            "relative_path": "decoys/decoy1.txt",
            "is_decoy": True,
            "source": "test"
        },
        {
            "event_id": "EVT-03",
            "timestamp": "2026-10-20T10:00:06.000",
            "event_type": "DELETE",
            "relative_path": "documents/doc1.txt",
            "is_decoy": False,
            "source": "test"
        }
    ]
    feats = calculate_window_features(evts, window_duration_sec=30.0)
    assert feats["event_count"] == 3
    assert feats["unique_files"] == 2
    assert feats["decoy_events"] == 1
    assert abs(feats["decoy_ratio"] - 1.0 / 3.0) < 0.001
    assert feats["create_count"] == 1
    assert feats["modify_count"] == 1
    assert feats["delete_count"] == 1
    # deltas: 2.0s, 4.0s -> mean = 3.0s, std = sqrt((1^2 + 1^2)/(2-1)) = sqrt(2) ≈ 1.4142
    assert abs(feats["inter_event_mean"] - 3.0) < 0.001
    assert abs(feats["inter_event_std"] - np.std([2.0, 4.0], ddof=1)) < 0.001


def test_sliding_window_aggregation():
    base = "2026-10-20T10:00:"
    evts = [
        {"event_id": f"E-{i}", "timestamp": f"{base}{i:02d}.000", "event_type": "MODIFY", "relative_path": f"f_{i}.txt", "is_decoy": False, "source": "test"}
        for i in range(45)  # 45 seconds of events
    ]
    windows = aggregate_events_into_windows(evts, window_size_sec=30.0, slide_sec=10.0)
    assert len(windows) >= 2
    # Check that windows contain valid features
    for w in windows:
        for col in FEATURE_COLUMNS:
            assert col in w
