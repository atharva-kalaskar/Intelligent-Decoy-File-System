# Live Viva Demonstration Checklist

Use this checklist during oral presentations or laboratory evaluations to demonstrate the system end-to-end.

---

## 1. Pre-Flight Preparation
- [ ] Open PowerShell in the project root: `d:\NS\ANti Cp`
- [ ] Verify virtual environment is active or use `.\.venv\Scripts\python.exe`
- [ ] Verify C monitor is compiled: `Test-Path .\monitor\monitor.exe`
- [ ] Ensure monitored directory is populated:
  ```powershell
  .\.venv\Scripts\python.exe application/manage_decoys.py --setup
  ```

---

## 2. Test Execution Demonstration
- [ ] Run the full automated test suite to demonstrate 100% test passing:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/ -v
  ```
  *Show that all 18 unit, schema, feature, model, and integration tests pass in ~5 seconds.*

---

## 3. Model Training & Evaluation Demonstration
- [ ] Show model training and held-out evaluation:
  ```powershell
  .\.venv\Scripts\python.exe ml/train.py
  .\.venv\Scripts\python.exe ml/evaluate.py
  ```
  *Highlight the comparative table and the generated confusion matrix image in `data/test_results/confusion_matrix.png`.*

---

## 4. Live Streamlit Dashboard Demonstration
- [ ] Launch the Streamlit dashboard:
  ```powershell
  .\.venv\Scripts\streamlit.exe run application/dashboard.py
  ```
- [ ] Open the browser at `http://localhost:8501`.
- [ ] Point out:
  - Header status and last telemetry timestamp.
  - KPI cards: Total Telemetry Events, Decoy Hits, Windows Evaluated, Alerts Raised.
  - Tab 1: Live Telemetry & Predictions table.
  - Tab 3: Model Evaluation metrics (Accuracy, Precision, Recall, Confusion Matrix).
  - Tab 4: Canary Decoy Manifest.

---

## 5. Live Scenario Demonstrations (Sidebar Triggers)
- [ ] **Step 5.1: Benign Activity Test**
  - Click **"Simulate Normal Activity"** in the sidebar.
  - Notice event count increments in `documents/assignment.txt`.
  - Point out that **no** security alerts are raised (normal behavior).
- [ ] **Step 5.2: Decoy Attack Probe Test**
  - Click **"Simulate Decoy Attack Probe"** in the sidebar.
  - Notice the immediate detection of canary tampering in `decoys/Backup_Credentials.kdbx.txt`.
  - Point to the new **CRITICAL / ELEVATED** alert under Tab 2 with full audit evidence.
