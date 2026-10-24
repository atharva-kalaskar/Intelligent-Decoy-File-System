"""
Event log ingestion, schema validation, behavioral windowing, and feature extraction.
Strictly adheres to docs/event_schema.md and docs/feature_schema.md.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger("event_preprocessor")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

REQUIRED_EVENT_FIELDS = {"event_id", "timestamp", "event_type", "relative_path", "is_decoy", "source"}
VALID_EVENT_TYPES = {"CREATE", "DELETE", "MODIFY", "RENAME_OLD", "RENAME_NEW"}

FEATURE_COLUMNS = [
    "event_count",
    "unique_files",
    "decoy_events",
    "decoy_ratio",
    "create_count",
    "modify_count",
    "delete_count",
    "rename_count",
    "events_per_second",
    "inter_event_mean",
    "inter_event_std"
]


def parse_iso_timestamp(ts_str: str) -> Optional[datetime]:
    """Parses ISO-8601 timestamps supporting standard formats with milliseconds."""
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts_str, fmt)
        except ValueError:
            continue
    return None


def validate_event_record(record: Dict[str, Any]) -> bool:
    """Validates that a dictionary conforms to the required raw event schema."""
    if not isinstance(record, dict):
        return False
    if not REQUIRED_EVENT_FIELDS.issubset(record.keys()):
        return False
    if record["event_type"] not in VALID_EVENT_TYPES:
        return False
    if not isinstance(record["is_decoy"], bool):
        return False
    if not isinstance(record["relative_path"], str) or not record["relative_path"].strip():
        return False
    if parse_iso_timestamp(record["timestamp"]) is None:
        return False
    return True


def read_event_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Defensively reads a JSON Lines event log. Skips empty lines and malformed records
    without crashing.
    """
    events = []
    if not log_path.exists():
        logger.warning(f"Log file does not exist: {log_path}")
        return events

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                record = json.loads(line_str)
                if validate_event_record(record):
                    events.append(record)
                else:
                    logger.debug(f"Skipping invalid schema record at line {line_num}: {line_str[:80]}")
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON at line {line_num}: {e}. Skipping.")
    return events


def calculate_window_features(window_events: List[Dict[str, Any]], window_duration_sec: float = 30.0) -> Dict[str, Any]:
    """
    Computes the 11 numerical behavioral features from an ordered list of events.
    Handles empty and single-event edge cases deterministically.
    """
    if window_duration_sec <= 0:
        window_duration_sec = 30.0

    if not window_events:
        return {
            "event_count": 0,
            "unique_files": 0,
            "decoy_events": 0,
            "decoy_ratio": 0.0,
            "create_count": 0,
            "modify_count": 0,
            "delete_count": 0,
            "rename_count": 0,
            "events_per_second": 0.0,
            "inter_event_mean": 0.0,
            "inter_event_std": 0.0
        }

    event_count = len(window_events)
    unique_files = len({e["relative_path"] for e in window_events})
    decoy_events = sum(1 for e in window_events if e.get("is_decoy", False))
    decoy_ratio = float(decoy_events / event_count) if event_count > 0 else 0.0

    create_count = sum(1 for e in window_events if e["event_type"] == "CREATE")
    modify_count = sum(1 for e in window_events if e["event_type"] == "MODIFY")
    delete_count = sum(1 for e in window_events if e["event_type"] == "DELETE")
    rename_count = sum(1 for e in window_events if e["event_type"] in ("RENAME_OLD", "RENAME_NEW"))

    events_per_second = float(event_count / window_duration_sec)

    # Inter-event time deltas calculation
    timestamps = [parse_iso_timestamp(e["timestamp"]) for e in window_events]
    valid_ts = [t.timestamp() for t in timestamps if t is not None]

    if len(valid_ts) >= 2:
        deltas = np.diff(np.sort(valid_ts))
        inter_event_mean = float(np.mean(deltas))
        inter_event_std = float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0
    else:
        inter_event_mean = 0.0
        inter_event_std = 0.0

    return {
        "event_count": int(event_count),
        "unique_files": int(unique_files),
        "decoy_events": int(decoy_events),
        "decoy_ratio": round(decoy_ratio, 4),
        "create_count": int(create_count),
        "modify_count": int(modify_count),
        "delete_count": int(delete_count),
        "rename_count": int(rename_count),
        "events_per_second": round(events_per_second, 4),
        "inter_event_mean": round(inter_event_mean, 4),
        "inter_event_std": round(inter_event_std, 4)
    }


def aggregate_events_into_windows(
    events: List[Dict[str, Any]],
    window_size_sec: float = 30.0,
    slide_sec: float = 10.0,
    min_events: int = 1
) -> List[Dict[str, Any]]:
    """
    Aggregates timestamped events into sliding temporal windows and extracts features.
    """
    if not events:
        return []

    # Sort events by parsed timestamp
    parsed_events = []
    for e in events:
        ts = parse_iso_timestamp(e["timestamp"])
        if ts is not None:
            parsed_events.append((ts.timestamp(), e))

    parsed_events.sort(key=lambda x: x[0])
    if not parsed_events:
        return []

    start_time = parsed_events[0][0]
    end_time = parsed_events[-1][0]

    windows = []
    current_start = start_time

    # If all events occurred in a narrow window, ensure at least one window
    if end_time - start_time < window_size_sec:
        win_evts = [e for _, e in parsed_events]
        if len(win_evts) >= min_events:
            feats = calculate_window_features(win_evts, window_size_sec)
            feats["window_start"] = datetime.fromtimestamp(start_time).isoformat()
            feats["window_end"] = datetime.fromtimestamp(start_time + window_size_sec).isoformat()
            windows.append(feats)
        return windows

    while current_start <= end_time:
        current_end = current_start + window_size_sec
        win_evts = [e for t, e in parsed_events if current_start <= t < current_end]

        if len(win_evts) >= min_events:
            feats = calculate_window_features(win_evts, window_size_sec)
            feats["window_start"] = datetime.fromtimestamp(current_start).isoformat()
            feats["window_end"] = datetime.fromtimestamp(current_end).isoformat()
            windows.append(feats)

        current_start += slide_sec

    return windows
