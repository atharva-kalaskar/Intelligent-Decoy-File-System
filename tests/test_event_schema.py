"""
Unit tests for event schema validation and defensive parsing.
"""

import pytest
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "ml"))

from preprocess import validate_event_record, read_event_log


def test_valid_event():
    valid = {
        "event_id": "EVT-00000001",
        "timestamp": "2026-10-20T10:15:30.123",
        "event_type": "MODIFY",
        "relative_path": "decoys/Financial_Records.txt",
        "file_id": "DECOY-002",
        "is_decoy": True,
        "source": "windows_monitor_c",
        "details": "Action=MODIFIED"
    }
    assert validate_event_record(valid) is True


def test_missing_required_field():
    invalid = {
        "event_id": "EVT-00000001",
        "timestamp": "2026-10-20T10:15:30.123",
        # missing event_type
        "relative_path": "decoys/Financial_Records.txt",
        "is_decoy": True,
        "source": "windows_monitor_c"
    }
    assert validate_event_record(invalid) is False


def test_invalid_event_type():
    invalid = {
        "event_id": "EVT-00000001",
        "timestamp": "2026-10-20T10:15:30.123",
        "event_type": "UNKNOWN_ACTION",
        "relative_path": "decoys/Financial_Records.txt",
        "is_decoy": True,
        "source": "windows_monitor_c"
    }
    assert validate_event_record(invalid) is False


def test_invalid_is_decoy_type():
    invalid = {
        "event_id": "EVT-00000001",
        "timestamp": "2026-10-20T10:15:30.123",
        "event_type": "CREATE",
        "relative_path": "documents/doc.txt",
        "is_decoy": "not_a_boolean",
        "source": "windows_monitor_c"
    }
    assert validate_event_record(invalid) is False


def test_defensive_reader_with_malformed_lines(tmp_path):
    log_file = tmp_path / "test_malformed.jsonl"
    content = (
        '{"event_id":"EVT-1","timestamp":"2026-10-20T10:00:00.000","event_type":"CREATE","relative_path":"a.txt","is_decoy":false,"source":"test"}\n'
        'THIS IS NOT JSON AT ALL\n'
        '{"partial_json": true\n'
        '\n'
        '{"event_id":"EVT-2","timestamp":"2026-10-20T10:00:01.000","event_type":"MODIFY","relative_path":"b.txt","is_decoy":true,"source":"test"}\n'
    )
    log_file.write_text(content, encoding="utf-8")

    records = read_event_log(log_file)
    assert len(records) == 2
    assert records[0]["event_id"] == "EVT-1"
    assert records[1]["event_id"] == "EVT-2"
