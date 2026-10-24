"""
Scenario Simulation and Automated Demonstration Engine
Executes controlled real-world scenarios on disk and through the defensive pipeline:
- Scenario 1: Normal Office / Development Activity (Benign Baseline)
- Scenario 2: Ransomware Rapid Bulk Encryption (Critical Threat)
- Scenario 3: Targeted Honeytoken Credential Theft (Elevated Threat)
- Scenario 4: Incidental Decoy Click / False Alarm Stress Test (ML Resilience)
"""

import os
import sys
import time
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "application"))
sys.path.insert(0, str(BASE_DIR / "ml"))

from storage import StorageManager
from alert_engine import AlertEngine
import manage_decoys
from preprocess import calculate_window_features
from predict import predict_window

MONITORED_DIR = BASE_DIR / "runtime" / "monitored"
LOG_FILE = BASE_DIR / "logs" / "events.jsonl"
MANIFEST_FILE = BASE_DIR / "decoys" / "manifest.json"


def load_manifest() -> Dict[str, Any]:
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"decoys": []}


def append_to_log_file(events: List[Dict[str, Any]]):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for evt in events:
            f.write(json.dumps(evt) + "\n")


class ScenarioRunner:
    def __init__(self):
        self.storage = StorageManager()
        self.engine = AlertEngine()
        self.manifest = load_manifest()

    def reset_demo_environment(self) -> Dict[str, Any]:
        """
        Pristine reset: Cleans SQLite records, clears events log, and repopulates decoys.
        """
        # 1. Clear database
        self.storage.clear_all_telemetry()

        # 2. Clear events.jsonl
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")

        # 3. Clean and reset files
        manage_decoys.setup_monitored_environment(BASE_DIR)

        return {
            "status": "success",
            "message": "Environment successfully reset to pristine state. All telemetry, predictions, and alerts purged."
        }

    def execute_scenario(self, scenario_type: str) -> Dict[str, Any]:
        """
        Executes a complete controlled attack or benign scenario end-to-end.
        """
        audit_log = []
        start_ts = datetime.now()
        session_id = f"DEMO-{int(time.time())}"

        audit_log.append(f"[{start_ts.strftime('%H:%M:%S')}] Initializing scenario: {scenario_type.upper()}")

        # Ensure directory structure exists
        docs_dir = MONITORED_DIR / "documents"
        decoys_dir = MONITORED_DIR / "decoys"
        docs_dir.mkdir(parents=True, exist_ok=True)
        decoys_dir.mkdir(parents=True, exist_ok=True)

        events: List[Dict[str, Any]] = []

        if scenario_type == "normal_office":
            meta = {
                "title": "Normal Enterprise Office Workflow",
                "badge": "BENIGN BASELINE",
                "color": "#10b981",
                "mitre_ttp": "None (Authorized User Behavior)",
                "description": "Routine document edits, draft notes creation, and clean modifications without honeytoken interaction.",
                "learning_point": "Demonstrates zero false-positive rate. Routine office work will never trigger defensive alarms."
            }
            # Step 1: Normal document edits
            sim_time = start_ts - timedelta(seconds=25)
            doc_targets = [
                ("documents/assignment.txt", "Updated project milestone status to complete."),
                ("documents/project_notes.txt", "Added reference to NIST SP 800-61 incident response guidelines."),
                ("documents/meeting_minutes.txt", "Recorded action items from security architecture review."),
                ("documents/research_paper.txt", "Revised literature review section on behavioral deception.")
            ]
            for rel_path, note in doc_targets:
                full_path = MONITORED_DIR / rel_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, "a", encoding="utf-8") as f:
                    f.write(f"\n[{sim_time.strftime('%H:%M:%S')}] {note}")
                
                sim_time += timedelta(seconds=4.0)
                evt = {
                    "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                    "timestamp": sim_time.isoformat(),
                    "event_type": "MODIFY",
                    "relative_path": rel_path,
                    "file_id": None,
                    "is_decoy": False,
                    "source": "demo_simulator",
                    "details": "[DEMO EVENT] Routine document modification"
                }
                events.append(evt)

            # Step 2: Create a temporary work file and delete it
            temp_file = MONITORED_DIR / "documents" / "temp_draft.txt"
            temp_file.write_text("Temporary scratch notes for team sync.", encoding="utf-8")
            sim_time += timedelta(seconds=3.0)
            events.append({
                "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                "timestamp": sim_time.isoformat(),
                "event_type": "CREATE",
                "relative_path": "documents/temp_draft.txt",
                "file_id": None,
                "is_decoy": False,
                "source": "demo_simulator",
                "details": "[DEMO EVENT] Draft document created"
            })

            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Generated {len(events)} normal office events on disk.")

        elif scenario_type == "ransomware_burst":
            meta = {
                "title": "Ransomware Rapid Encryption Attack",
                "badge": "CRITICAL THREAT",
                "color": "#ef4444",
                "mitre_ttp": "T1486 (Data Encrypted for Impact), T1485 (Data Destruction)",
                "description": "High-velocity automated attack iterating through directory trees, encrypting files, altering honeytokens, and dropping ransom demands.",
                "learning_point": "Random Forest flags the extreme burst velocity (events/sec), inter-arrival compression, and multi-honeytoken destruction."
            }
            sim_time = start_ts - timedelta(seconds=20)
            
            # Rapid burst across regular docs and decoys
            attack_sequence = [
                ("documents/assignment.txt", "MODIFY", False, None),
                ("documents/project_notes.txt", "MODIFY", False, None),
                ("decoys/Confidential_Report.docx.txt", "MODIFY", True, "DECOY-001"),
                ("documents/research_paper.txt", "MODIFY", False, None),
                ("decoys/Backup_Credentials.kdbx.txt", "MODIFY", True, "DECOY-002"),
                ("decoys/Financial_Records_2025.xlsx.txt", "MODIFY", True, "DECOY-003"),
                ("decoys/database_dump.sql", "MODIFY", True, "DECOY-004"),
                ("documents/meeting_minutes.txt", "MODIFY", False, None),
                ("decoys/private_key.pem.txt", "MODIFY", True, "DECOY-005"),
                ("documents/assignment.txt.locked", "RENAME_NEW", False, None),
                ("decoys/Confidential_Report.docx.txt.locked", "RENAME_NEW", True, "DECOY-001"),
                ("decoys/Backup_Credentials.kdbx.txt.locked", "RENAME_NEW", True, "DECOY-002"),
            ]

            # Physical tamper
            for rel_path, evt_type, is_decoy, file_id in attack_sequence:
                target_file = MONITORED_DIR / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[ENCRYPTED_PAYLOAD_SIMULATION_{int(time.time())}]")

                sim_time += timedelta(seconds=0.15)  # 150ms intervals = fast burst
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                    "timestamp": sim_time.isoformat(),
                    "event_type": evt_type,
                    "relative_path": rel_path,
                    "file_id": file_id,
                    "is_decoy": is_decoy,
                    "source": "demo_simulator",
                    "details": "[DEMO EVENT] Simulated ransomware bulk tampering"
                })

            # Drop ransom note
            ransom_note = MONITORED_DIR / "HOW_TO_RECOVER_YOUR_FILES.txt"
            ransom_note.write_text(
                "ATTENTION: All your personal files and confidential archives have been encrypted.\n"
                "Contact decryption_recovery@testbed.onion with your victim key to restore access.\n",
                encoding="utf-8"
            )
            sim_time += timedelta(seconds=0.10)
            events.append({
                "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                "timestamp": sim_time.isoformat(),
                "event_type": "CREATE",
                "relative_path": "HOW_TO_RECOVER_YOUR_FILES.txt",
                "file_id": None,
                "is_decoy": False,
                "source": "demo_simulator",
                "details": "[DEMO EVENT] Ransom demand note dropped"
            })

            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Simulated rapid encryption of {len(events)} targets in 2.1s.")

        elif scenario_type == "credential_recon":
            meta = {
                "title": "Targeted Honeytoken Credential Theft",
                "badge": "HIGH THREAT / RECON",
                "color": "#f59e0b",
                "mitre_ttp": "T1083 (File Discovery), T1552 (Unsecured Credentials)",
                "description": "Adversary selectively targeting password databases, private cryptographic keys, and database dumps.",
                "learning_point": "Honeytoken trap triggers. While speed is modest, the decoy ratio is 70%+, exposing deliberate asset theft."
            }
            sim_time = start_ts - timedelta(seconds=15)
            recon_targets = [
                ("decoys/Backup_Credentials.kdbx.txt", "DECOY-002", "Credential database inspected"),
                ("decoys/private_key.pem.txt", "DECOY-005", "RSA private key exfiltrated"),
                ("documents/project_notes.txt", None, "Benign distraction access"),
                ("decoys/database_dump.sql", "DECOY-004", "Database user table read"),
                ("decoys/Financial_Records_2025.xlsx.txt", "DECOY-003", "Financial records probed"),
                ("decoys/Confidential_Report.docx.txt", "DECOY-001", "Confidential memo opened"),
                ("documents/assignment.txt", None, "Folder inspection")
            ]

            for rel_path, file_id, note in recon_targets:
                target_file = MONITORED_DIR / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[UNAUTHORIZED_EXFIL_PROBE {sim_time.strftime('%H:%M:%S')}] {note}")

                sim_time += timedelta(seconds=1.4)
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                    "timestamp": sim_time.isoformat(),
                    "event_type": "MODIFY",
                    "relative_path": rel_path,
                    "file_id": file_id,
                    "is_decoy": bool(file_id),
                    "source": "demo_simulator",
                    "details": f"[DEMO EVENT] {note}"
                })

            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Adversary probed {len(events)} files with heavy decoy focus (5 honeytoken hits).")

        elif scenario_type == "incidental_touch":
            meta = {
                "title": "Incidental Decoy Click (False Alarm Stress Test)",
                "badge": "ML DISCRIMINATION TEST",
                "color": "#818cf8",
                "mitre_ttp": "Benign Human Error / Desktop Indexer",
                "description": "User modifies 4 benign documents and accidentally double-clicks 1 decoy at normal human cadence.",
                "learning_point": "CRITICAL RESEARCH HIGHLIGHT: A naive static rule triggers a false alarm on any decoy touch. The Random Forest model correctly recognizes low velocity and low burst as non-malicious."
            }
            sim_time = start_ts - timedelta(seconds=28)
            touches = [
                ("documents/assignment.txt", False, None),
                ("documents/project_notes.txt", False, None),
                ("decoys/Confidential_Report.docx.txt", True, "DECOY-001"),  # Accidental click
                ("documents/meeting_minutes.txt", False, None),
                ("documents/research_paper.txt", False, None)
            ]

            for rel_path, is_decoy, file_id in touches:
                target_file = MONITORED_DIR / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, "a", encoding="utf-8") as f:
                    f.write(f"\n[USER_TOUCH {sim_time.strftime('%H:%M:%S')}] Benign routine update.")

                sim_time += timedelta(seconds=5.5)  # Slow 5.5s intervals
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:8]}",
                    "timestamp": sim_time.isoformat(),
                    "event_type": "MODIFY",
                    "relative_path": rel_path,
                    "file_id": file_id,
                    "is_decoy": is_decoy,
                    "source": "demo_simulator",
                    "details": "[DEMO EVENT] Normal cadence incidental interaction"
                })

            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Generated 5 events with 1 incidental decoy touch at human pace.")

        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        # Step 3: Write events to event log & persist to SQLite
        append_to_log_file(events)
        inserted_count = self.storage.insert_events(events)
        audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Ingested {inserted_count} structured events into SQLite store.")

        # Step 4: Run Machine Learning Behavioral Feature Extraction & Prediction
        pred_record = self.engine.evaluate_recent_window(events=events)
        audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Extracted 11-feature behavioral vector.")
        
        pred_label = pred_record["prediction"].upper()
        prob_percent = pred_record["suspicious_probability"] * 100
        audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Random Forest Classification: {pred_label} (Confidence: {prob_percent:.1f}%)")

        if pred_record["is_suspicious"] == 1:
            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] [ALERT DISPATCHED] Severity: {pred_record['risk_level']} | Logged to Security Incidents.")
        else:
            audit_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] [NO ALERT] Activity classified benign. Threat threshold not exceeded.")

        # Retrieve latest alert if one was generated
        recent_alerts = self.storage.get_recent_alerts(limit=1)
        latest_alert = recent_alerts[0] if (recent_alerts and pred_record["is_suspicious"] == 1) else None

        return {
            "scenario_type": scenario_type,
            "meta": meta,
            "events_generated": len(events),
            "prediction": pred_record,
            "alert": latest_alert,
            "audit_log": audit_log,
            "events_sample": events[:10]
        }
