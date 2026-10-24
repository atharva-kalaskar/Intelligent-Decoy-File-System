# Quality Assurance & Test Plan

## 1. Scope & Strategy
The testing regime combines C-level compiler checks, unit testing of event schemas and mathematical feature calculations, model loading and inference validation, component integration, and automated end-to-end pipeline execution on Windows.

---

## 2. Test Cases Matrix

| Test Suite | Test Identifier | Target Component | Description / Expected Behavior | Automated Status |
| :--- | :--- | :--- | :--- | :--- |
| **C Compiler** | `TC-C-01` | `monitor/monitor.exe` | Clean compilation under MinGW GCC with `-Wall -Werror` | **PASS** |
| **C Monitor** | `TC-C-02` | `watcher.c` | Live capture of CREATE, MODIFY, DELETE events via Win32 API | **PASS** |
| **C Monitor** | `TC-C-03` | `watcher.c` | Manifest matching: decoy path correctly tagged `is_decoy=True` | **PASS** |
| **C Monitor** | `TC-C-04` | `main.c` | Timeout and `--max-events` clean shutdown without handle leak | **PASS** |
| **Event Schema**| `TC-SCH-01` | `preprocess.py` | Valid schema record passes validation | **PASS** |
| **Event Schema**| `TC-SCH-02` | `preprocess.py` | Missing required fields return `False` | **PASS** |
| **Event Schema**| `TC-SCH-03` | `preprocess.py` | Invalid event types (not in allowlist) rejected | **PASS** |
| **Event Schema**| `TC-SCH-04` | `preprocess.py` | Defensive reader skips non-JSON / corrupted lines without crash | **PASS** |
| **Features** | `TC-FT-01` | `preprocess.py` | Empty window returns deterministic zero vector without division error | **PASS** |
| **Features** | `TC-FT-02` | `preprocess.py` | Single event computes zero inter-event mean and std | **PASS** |
| **Features** | `TC-FT-03` | `preprocess.py` | Multi-event window computes exact mathematical mean & sample std | **PASS** |
| **Features** | `TC-FT-04` | `preprocess.py` | Temporal windowing correctly slices events into 30s intervals | **PASS** |
| **Model** | `TC-MD-01` | `predict.py` | Model artifact loads correctly and validates metadata version | **PASS** |
| **Model** | `TC-MD-02` | `predict.py` | Benign document edits yield $P(\text{suspicious}) < 0.50$ | **PASS** |
| **Model** | `TC-MD-03` | `predict.py` | Multi-decoy tampering yields $P(\text{suspicious}) \ge 0.50$ | **PASS** |
| **Model** | `TC-MD-04` | `predict.py` | Missing feature dictionary keys fall back to defaults gracefully | **PASS** |
| **Model** | `TC-MD-05` | `predict.py` | Non-existent model path raises `FileNotFoundError` | **PASS** |
| **Storage** | `TC-DB-01` | `storage.py` | SQLite schema tables & indexes initialize properly | **PASS** |
| **Alert Engine**| `TC-ALT-01` | `alert_engine.py` | Suspicious activity triggers an alert with concrete evidence | **PASS** |
| **Alert Engine**| `TC-ALT-02` | `alert_engine.py` | Benign document editing generates no spurious alerts | **PASS** |
| **Integration** | `TC-INT-01` | Full Pipeline | End-to-end: C watcher -> JSONL -> Python features -> RF -> DB -> Alert | **PASS** |

---

## 3. Automated Test Execution Commands
```powershell
# Run all automated tests:
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Run individual test modules:
.\.venv\Scripts\python.exe -m pytest tests/test_event_schema.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_features.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_model.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_alert_engine.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_integration.py -v -s
```
All 18 automated unit and integration tests execute and pass in under 6 seconds.
