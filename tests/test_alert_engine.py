"""
Unit and integration tests for Alert Engine and Storage.
"""

import pytest
import time
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "application"))
sys.path.insert(0, str(BASE_DIR / "ml"))

from storage import StorageManager
from alert_engine import AlertEngine


@pytest.fixture
def test_db_and_engine(tmp_path):
    db_file = tmp_path / "test_decoy.db"
    log_file = tmp_path / "test_events.jsonl"
    storage = StorageManager(db_file)
    engine = AlertEngine(log_path=log_file, db_path=db_file)
    return storage, engine, log_file


def test_storage_initialization(test_db_and_engine):
    storage, _, _ = test_db_and_engine
    stats = storage.get_system_stats()
    assert stats["total_events"] == 0
    assert stats["total_alerts"] == 0


def test_alert_engine_suspicious_scenario(test_db_and_engine):
    storage, engine, log_file = test_db_and_engine

    # Write synthetic suspicious events (attacker probing credential & key decoys)
    base_ts = "2026-10-20T10:00:"
    suspicious_events = [
        f'{{"event_id":"TEST-EVT-01","timestamp":"{base_ts}01.100","event_type":"MODIFY","relative_path":"decoys/Backup_Credentials.kdbx.txt","file_id":"DECOY-002","is_decoy":true,"source":"test"}}',
        f'{{"event_id":"TEST-EVT-02","timestamp":"{base_ts}02.200","event_type":"MODIFY","relative_path":"decoys/private_key.pem.txt","file_id":"DECOY-005","is_decoy":true,"source":"test"}}',
        f'{{"event_id":"TEST-EVT-03","timestamp":"{base_ts}03.300","event_type":"DELETE","relative_path":"decoys/database_dump.sql","file_id":"DECOY-004","is_decoy":true,"source":"test"}}',
        f'{{"event_id":"TEST-EVT-04","timestamp":"{base_ts}04.400","event_type":"MODIFY","relative_path":"documents/assignment.txt","file_id":null,"is_decoy":false,"source":"test"}}'
    ]
    log_file.write_text("\n".join(suspicious_events) + "\n", encoding="utf-8")

    # Ingest and evaluate
    new_evts = engine.process_new_events()
    assert new_evts == 4

    pred_record = engine.evaluate_recent_window()
    assert pred_record is not None
    assert pred_record["is_suspicious"] == 1
    assert pred_record["prediction"] == "suspicious"
    assert pred_record["suspicious_probability"] >= 0.50

    # Verify alert was created in SQLite
    alerts = storage.get_recent_alerts(limit=5)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["prediction_id"] == pred_record["prediction_id"]
    assert alert["severity"] in ("ELEVATED", "CRITICAL")
    assert "decoy" in alert["description"].lower()


def test_alert_engine_normal_scenario(test_db_and_engine):
    storage, engine, log_file = test_db_and_engine

    # Write benign document editing events
    base_ts = "2026-10-20T10:05:"
    benign_events = [
        f'{{"event_id":"BENIGN-01","timestamp":"{base_ts}01.000","event_type":"MODIFY","relative_path":"documents/project_notes.txt","file_id":null,"is_decoy":false,"source":"test"}}',
        f'{{"event_id":"BENIGN-02","timestamp":"{base_ts}06.000","event_type":"MODIFY","relative_path":"documents/assignment.txt","file_id":null,"is_decoy":false,"source":"test"}}'
    ]
    log_file.write_text("\n".join(benign_events) + "\n", encoding="utf-8")

    engine.process_new_events()
    pred_record = engine.evaluate_recent_window()
    assert pred_record is not None
    assert pred_record["is_suspicious"] == 0

    # No alert should be generated for benign activity
    alerts = storage.get_recent_alerts(limit=5)
    assert len(alerts) == 0
