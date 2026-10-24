# System Architecture & Technical Design Document

## 1. Executive Summary
The **Intelligent Decoy File System** is a Windows-based deception and threat detection prototype developed for Network Security coursework. It couples low-level Win32 file-system change telemetry with supervised machine learning (Random Forest) to detect reconnaissance and tampering on high-value canary decoy documents.

---

## 2. Pipeline Architecture & Data Flow

```
+-------------------------------------------------------------------------+
|                  1. MONITORED FILE SYSTEM (Win32)                      |
|                                                                         |
|   runtime/monitored/                                                    |
|     ├── documents/ (benign: assignment.txt, project_notes.txt)          |
|     └── decoys/    (canaries: Backup_Credentials, private_key.pem, ...) |
+-------------------------------------------------------------------------+
                                    │
                       File System Activity Events
                       (CREATE, MODIFY, DELETE, RENAME)
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|              2. C MONITORING ENGINE (Win32 API)                        |
|                                                                         |
|   monitor/src/watcher.c                                                 |
|     - ReadDirectoryChangesW (Overlapped I/O, 64KB buffer)               |
|     - Manifest lookup & decoy tagging                                   |
|   monitor/src/event_logger.c                                            |
|     - ISO-8601 millisecond timestamps                                   |
|     - Sequential event IDs: EVT-<run_id>-<seq>                          |
|     - Thread-safe serialization & auto-flush                            |
+-------------------------------------------------------------------------+
                                    │
                               Raw Stream
                            logs/events.jsonl
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|              3. PYTHON EVENT PROCESSOR & WINDOW AGGREGATOR              |
|                                                                         |
|   ml/preprocess.py                                                      |
|     - Defensive JSON Lines parsing & schema validation                  |
|     - 30-second sliding temporal window aggregation                     |
|     - 11-dimensional behavioral feature extraction                      |
+-------------------------------------------------------------------------+
                                    │
                         Numerical Feature Vector
                           x ∈ ℝ¹¹, y ∈ {0, 1}
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|              4. SUPERVISED RANDOM FOREST CLASSIFIER                     |
|                                                                         |
|   ml/predict.py                                                         |
|     - 100 Estimator ensemble with max_depth=8, balanced weights        |
|     - Outputs P(Suspicious) probability & Risk Level                     |
|     - Transparent factual evidence reason generation                    |
+-------------------------------------------------------------------------+
                                    │
                      Prediction & Risk Indicators
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                   5. ALERT ENGINE & PERSISTENCE                         |
|                                                                         |
|   application/alert_engine.py                                           |
|     - Triage filter (P >= 0.50 triggers incident generation)            |
|   application/storage.py                                                |
|     - SQLite ACID storage with WAL mode                                 |
|     - Tables: events, predictions, alerts, ingestion_state              |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|              6. VISUALIZATION & INTERACTIVE DASHBOARD                   |
|                                                                         |
|   application/dashboard.py (Streamlit)                                  |
|     - Real-time KPI monitors, incident logs, filterable telemetry       |
|     - Model benchmarks, confusion matrices, feature importances         |
|     - Interactive test triggers for benign & attack simulations         |
+-------------------------------------------------------------------------+
```

---

## 3. Component Deep Dive

### 3.1 Component A: Decoy File Manager (`application/manage_decoys.py`)
- **Manifest-Driven:** Driven by `decoys/manifest.json`. Defines unique IDs (`DECOY-001` through `DECOY-005`), relative paths, categories, and canary tokens.
- **Path Traversal Security:** The helper `is_safe_path()` checks that resolved paths stay strictly within `runtime/monitored/`, preventing directory traversal attacks.
- **Harmless Dummy Payloads:** All contents are explicitly synthetic, clearly watermarked as educational honeypots, and contain zero real credentials or private keys.

### 3.2 Component B: Windows C Monitoring Engine (`monitor/`)
- **API Choice:** Uses `ReadDirectoryChangesW` with `FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED`.
- **Overlapped Asynchronous I/O:** Avoids thread blocking by pairing `OVERLAPPED.hEvent` with `WaitForSingleObject` using a 100ms polling interval. This allows prompt response to termination signals (`SetConsoleCtrlHandler`) and test timeouts.
- **Buffer Management:** Employs a 64KB DWORD-aligned buffer. Handles `ERROR_NOTIFY_ENUM_DIR` by warning about buffer overflow conditions rather than silently failing.
- **Path Normalization:** Converts Windows backslashes (`\`) to forward slashes (`/`) to match Unix-style web/JSON standards.

### 3.3 Component C: Structured Event Logging (`logs/events.jsonl`)
- Adheres to standard JSON Lines format (one valid JSON object per line).
- Captures: `event_id`, `timestamp` (ISO-8601), `event_type`, `relative_path`, `file_id`, `is_decoy`, `source`, `details`.
- Flushed synchronously after each write to ensure telemetry persistence in the event of abrupt termination.

### 3.4 Component D & E: Behavioral Feature Engineering (`ml/preprocess.py`)
Groups events into 30-second windows and calculates:
1. `event_count`
2. `unique_files`
3. `decoy_events`
4. `decoy_ratio` (explicitly 0.0 if empty)
5. `create_count`
6. `modify_count`
7. `delete_count`
8. `rename_count`
9. `events_per_second`
10. `inter_event_mean` (0.0 if < 2 events)
11. `inter_event_std` (0.0 if < 2 events)

### 3.5 Component F: Machine Learning Pipeline (`ml/`)
- Model: `RandomForestClassifier` from `scikit-learn`.
- Splitting: `GroupShuffleSplit` on `session_id` to guarantee 100% isolation of sliding windows between train, validation, and test splits.
- Baseline: Transparent rule-based security heuristic evaluated on the identical test set.
- Latency: Average inference latency under 0.05 milliseconds per window.

### 3.6 Component G: Alert Engine & Storage (`application/`)
- SQLite storage with Write-Ahead Logging (`WAL` mode) for reliable read/write concurrency.
- Evaluates recent windows, computes class probabilities, and assigns risk severity (`CRITICAL`, `ELEVATED`, `LOW`).
- Associates concrete evidence (compromised canary files, event IDs, feature parameters) with every alert.
