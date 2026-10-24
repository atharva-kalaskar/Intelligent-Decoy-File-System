"""
Comprehensive End-to-End Integration Test for the Entire Pipeline:
File system event -> C monitor -> JSONL log -> Python feature extraction -> Random Forest -> Alert Engine -> SQLite
"""

import subprocess
import time
import json
from pathlib import Path
import pytest
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "application"))
sys.path.insert(0, str(BASE_DIR / "ml"))

from storage import StorageManager
from alert_engine import AlertEngine
import manage_decoys

MONITOR_EXE = BASE_DIR / "monitor" / "monitor.exe"
LOG_FILE = BASE_DIR / "logs" / "events.jsonl"
MONITORED_DIR = BASE_DIR / "runtime" / "monitored"


def test_full_pipeline_end_to_end(tmp_path):
    assert MONITOR_EXE.exists(), "C monitor executable does not exist. Run compile step first."

    # 1. Setup clean monitored environment with decoys
    manage_decoys.setup_monitored_environment(BASE_DIR)

    test_db = tmp_path / "integration_test.db"
    test_log = tmp_path / "integration_events.jsonl"

    # 3. Launch C monitor with a 4000ms timeout
    proc = subprocess.Popen(
        [str(MONITOR_EXE), "--timeout", "4000", "--dir", str(MONITORED_DIR), "--log", str(test_log)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    time.sleep(0.6)  # Allow watcher to hook ReadDirectoryChangesW

    # 4. Perform controlled activities:
    # A) Benign document creation & modification
    normal_doc = MONITORED_DIR / "documents" / "integration_doc.txt"
    normal_doc.write_text("Legitimate project work notes.\n", encoding="utf-8")
    time.sleep(0.2)

    # B) Multi-decoy tampering (simulating suspicious reconnaissance)
    decoy1 = MONITORED_DIR / "decoys" / "Backup_Credentials.kdbx.txt"
    decoy2 = MONITORED_DIR / "decoys" / "private_key.pem.txt"

    with open(decoy1, "a", encoding="utf-8") as f:
        f.write("\nExploit tamper probe 1\n")
    time.sleep(0.2)

    with open(decoy2, "a", encoding="utf-8") as f:
        f.write("\nExploit tamper probe 2\n")
    time.sleep(0.2)

    # 5. Wait for C monitor to exit
    stdout, stderr = proc.communicate(timeout=7.0)
    assert proc.returncode == 0, f"Monitor exited with error code {proc.returncode}"

    # 6. Verify log contents
    assert test_log.exists(), "Log file was not generated"
    lines = [l.strip() for l in test_log.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 3, f"Expected at least 3 events, got {len(lines)}"

    # 7. Run Alert Engine & SQLite Persistence
    engine = AlertEngine(log_path=test_log, db_path=test_db)
    inserted_count = engine.process_new_events()
    assert inserted_count >= 3, f"Expected >= 3 newly inserted events into database, got {inserted_count}"

    pred_res = engine.evaluate_recent_window()
    assert pred_res is not None, "Evaluation returned None"
    assert pred_res["is_suspicious"] == 1, f"Expected suspicious classification for multi-decoy tampering, got {pred_res}"
    assert pred_res["suspicious_probability"] >= 0.50

    # 8. Verify SQLite Storage State
    stats = engine.storage.get_system_stats()
    assert stats["total_events"] >= 3
    assert stats["decoy_events"] >= 2
    assert stats["total_predictions"] >= 1
    assert stats["total_alerts"] >= 1

    alerts = engine.storage.get_recent_alerts(limit=5)
    assert len(alerts) >= 1
    latest_alert = alerts[0]
    assert latest_alert["severity"] in ("ELEVATED", "CRITICAL")
    assert "decoy" in latest_alert["description"].lower()

    print("\n[SUCCESS] Full End-to-End Integration Test Completed Perfectly!")
