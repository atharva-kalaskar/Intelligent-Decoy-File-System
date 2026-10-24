"""
Dataset Generation Pipeline for Controlled Educational Scenarios
Produces labeled behavioral event streams and feature windows adhering to:
- Scenario A: Normal routine document activity (label 0)
- Scenario B: Isolated / incidental decoy touch (label 0)
- Scenario C: Decoy reconnaissance & credential hunting (label 1)
- Scenario D: Bulk tampering & ransomware-like bursts (label 1)

Includes session tracking to guarantee leakage-free train/test splits.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

from preprocess import calculate_window_features, FEATURE_COLUMNS

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "synthetic_scenarios.jsonl"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "feature_windows.csv"
MANIFEST_PATH = BASE_DIR / "decoys" / "manifest.json"

NORMAL_FILES = [
    "documents/assignment.txt",
    "documents/project_notes.txt",
    "documents/research_paper.txt",
    "documents/meeting_minutes.txt",
    "documents/src/code_draft.c",
    "documents/src/helper.h",
    "documents/exports/report_v1.pdf.txt",
    "documents/notes_daily.txt"
]

DECOY_ENTRIES = [
    ("DECOY-001", "decoys/Confidential_Report.docx.txt"),
    ("DECOY-002", "decoys/Backup_Credentials.kdbx.txt"),
    ("DECOY-003", "decoys/Financial_Records_2025.xlsx.txt"),
    ("DECOY-004", "decoys/database_dump.sql"),
    ("DECOY-005", "decoys/private_key.pem.txt")
]


def generate_scenario_session(
    session_id: str,
    scenario_type: str,
    base_time: datetime,
    duration_seconds: float = 60.0
) -> list:
    """
    Generates a realistic stream of timestamped file-system events for one session.
    """
    events = []
    current_time = base_time
    end_time = base_time + timedelta(seconds=duration_seconds)
    evt_num = 0

    if scenario_type == "normal_routine":
        # Realistic student/worker editing documents at modest pace
        while current_time < end_time:
            evt_num += 1
            path = random.choice(NORMAL_FILES)
            action = random.choices(["MODIFY", "CREATE", "DELETE"], weights=[0.80, 0.15, 0.05])[0]
            delta = random.uniform(2.0, 8.0)
            current_time += timedelta(seconds=delta)
            if current_time >= end_time:
                break
            events.append({
                "session_id": session_id,
                "event_id": f"GEN-{session_id}-{evt_num:05d}",
                "timestamp": current_time.isoformat(),
                "event_type": action,
                "relative_path": path,
                "file_id": None,
                "is_decoy": False,
                "source": "synthetic_generator",
                "details": f"scenario={scenario_type}",
                "is_suspicious": 0
            })

    elif scenario_type == "incidental_decoy":
        # Normal user browsing, with at most 1 accidental decoy touch
        decoy_touched = False
        while current_time < end_time:
            evt_num += 1
            if not decoy_touched and random.random() < 0.25:
                decoy_id, decoy_path = random.choice(DECOY_ENTRIES)
                path = decoy_path
                file_id = decoy_id
                is_decoy = True
                decoy_touched = True
                action = "MODIFY"
            else:
                path = random.choice(NORMAL_FILES)
                file_id = None
                is_decoy = False
                action = random.choices(["MODIFY", "CREATE"], weights=[0.85, 0.15])[0]

            delta = random.uniform(1.5, 6.0)
            current_time += timedelta(seconds=delta)
            if current_time >= end_time:
                break
            events.append({
                "session_id": session_id,
                "event_id": f"GEN-{session_id}-{evt_num:05d}",
                "timestamp": current_time.isoformat(),
                "event_type": action,
                "relative_path": path,
                "file_id": file_id,
                "is_decoy": is_decoy,
                "source": "synthetic_generator",
                "details": f"scenario={scenario_type}",
                "is_suspicious": 0
            })

    elif scenario_type == "decoy_reconnaissance":
        # Attacker systematically inspecting multiple decoy canary tokens
        while current_time < end_time:
            evt_num += 1
            if random.random() < 0.70:
                decoy_id, decoy_path = random.choice(DECOY_ENTRIES)
                path = decoy_path
                file_id = decoy_id
                is_decoy = True
                action = random.choices(["MODIFY", "DELETE", "RENAME_OLD", "RENAME_NEW"], weights=[0.6, 0.2, 0.1, 0.1])[0]
            else:
                path = random.choice(NORMAL_FILES)
                file_id = None
                is_decoy = False
                action = "MODIFY"

            delta = random.uniform(0.5, 2.5)
            current_time += timedelta(seconds=delta)
            if current_time >= end_time:
                break
            events.append({
                "session_id": session_id,
                "event_id": f"GEN-{session_id}-{evt_num:05d}",
                "timestamp": current_time.isoformat(),
                "event_type": action,
                "relative_path": path,
                "file_id": file_id,
                "is_decoy": is_decoy,
                "source": "synthetic_generator",
                "details": f"scenario={scenario_type}",
                "is_suspicious": 1
            })

    elif scenario_type == "bulk_tampering_ransomware":
        # Fast bulk modification/deletion/renaming across files including decoys
        while current_time < end_time:
            evt_num += 1
            if random.random() < 0.45:
                decoy_id, decoy_path = random.choice(DECOY_ENTRIES)
                path = decoy_path
                file_id = decoy_id
                is_decoy = True
            else:
                path = random.choice(NORMAL_FILES)
                file_id = None
                is_decoy = False

            action = random.choices(["MODIFY", "DELETE", "RENAME_OLD", "RENAME_NEW"], weights=[0.50, 0.30, 0.10, 0.10])[0]
            delta = random.uniform(0.05, 0.40)  # Very high event frequency
            current_time += timedelta(seconds=delta)
            if current_time >= end_time:
                break
            events.append({
                "session_id": session_id,
                "event_id": f"GEN-{session_id}-{evt_num:05d}",
                "timestamp": current_time.isoformat(),
                "event_type": action,
                "relative_path": path,
                "file_id": file_id,
                "is_decoy": is_decoy,
                "source": "synthetic_generator",
                "details": f"scenario={scenario_type}",
                "is_suspicious": 1
            })

    return events


def generate_full_dataset(
    num_sessions_per_scenario: int = 120,
    window_size_sec: float = 30.0,
    slide_sec: float = 10.0,
    random_seed: int = 42
):
    """
    Constructs multi-session scenarios, aggregates them into sliding windows,
    and produces both raw JSONL and processed feature CSV datasets.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    scenarios = [
        ("normal_routine", 0, num_sessions_per_scenario),
        ("incidental_decoy", 0, num_sessions_per_scenario),
        ("decoy_reconnaissance", 1, num_sessions_per_scenario),
        ("bulk_tampering_ransomware", 1, num_sessions_per_scenario)
    ]

    all_raw_events = []
    window_records = []
    base_time = datetime(2026, 10, 20, 8, 0, 0)

    print("[INFO] Generating synthetic educational scenario sessions...")
    session_count = 0

    for sc_name, label, count in scenarios:
        for idx in range(count):
            session_count += 1
            session_id = f"SES-{session_count:04d}-{sc_name[:3]}"
            session_start = base_time + timedelta(minutes=session_count * 2)
            duration = random.uniform(45.0, 120.0)

            evts = generate_scenario_session(session_id, sc_name, session_start, duration)
            all_raw_events.extend(evts)

            # Slide windows within session
            if not evts:
                continue

            sess_start_ts = datetime.fromisoformat(evts[0]["timestamp"]).timestamp()
            sess_end_ts = datetime.fromisoformat(evts[-1]["timestamp"]).timestamp()

            cur_start = sess_start_ts
            while cur_start + window_size_sec <= sess_end_ts + slide_sec:
                cur_end = cur_start + window_size_sec
                win_evts = [
                    e for e in evts
                    if cur_start <= datetime.fromisoformat(e["timestamp"]).timestamp() < cur_end
                ]

                if win_evts:
                    features = calculate_window_features(win_evts, window_size_sec)
                    features["session_id"] = session_id
                    features["scenario_type"] = sc_name
                    features["is_suspicious"] = label
                    features["window_start"] = datetime.fromtimestamp(cur_start).isoformat()
                    features["window_end"] = datetime.fromtimestamp(cur_end).isoformat()
                    window_records.append(features)

                cur_start += slide_sec

    # Save raw events to JSON Lines
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_DATA_PATH, "w", encoding="utf-8") as f:
        for evt in all_raw_events:
            f.write(json.dumps(evt) + "\n")

    # Convert to DataFrame
    df = pd.DataFrame(window_records)

    # Validate schema
    for col in FEATURE_COLUMNS:
        assert col in df.columns, f"Missing feature column: {col}"
        assert not df[col].isnull().any(), f"NaN values detected in feature: {col}"

    # Save processed CSV
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DATA_PATH, index=False)

    print(f"[OK] Generated {len(all_raw_events)} raw events across {session_count} sessions.")
    print(f"[OK] Produced {len(df)} feature windows.")
    print(f"[OK] Class distribution:\n{df['is_suspicious'].value_counts().to_dict()}")
    print(f"[OK] Scenario distribution:\n{df['scenario_type'].value_counts().to_dict()}")
    print(f"[OK] Saved raw data to: {RAW_DATA_PATH}")
    print(f"[OK] Saved processed dataset to: {PROCESSED_DATA_PATH}")

    return df


if __name__ == "__main__":
    generate_full_dataset()
