# 🛡️ Intelligent Decoy File System

[![Platform: Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com)
[![Python: 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![C: Win32 API](https://img.shields.io/badge/Core-C%20(Win32%20API)-00599C?logo=c&logoColor=white)](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-readdirectorychangesw)
[![ML: Random Forest](https://img.shields.io/badge/ML-Random%20Forest-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Dashboard: Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/Tests-24%2F24%20Passing-brightgreen?logo=pytest&logoColor=white)](tests/)

An intelligent, behavioral deception defense system that detects ransomware bursts and credential reconnaissance in real time while **eliminating false alarms from accidental user clicks**.

---

## 📌 Overview

Traditional honeypots use static rules (e.g., *"alarm if any decoy file is touched"*), which produce false alarms when users accidentally click or preview a file.

This project combines:
1. **Low-overhead Win32 C watcher engine** hooked into `ReadDirectoryChangesW` for millisecond-precision event telemetry.
2. **Behavioral feature engineering** grouping events into 30-second sliding windows (event velocity, inter-event intervals, decoy ratios).
3. **Supervised Random Forest classifier** that accurately differentiates real attacks from legitimate user operations.
4. **Streamlit Cyber SOC dashboard** with real-time incident monitoring and interactive test scenarios.

```
[ Monitored Directory & Decoy Files ]
                 │
                 ▼ (Win32 ReadDirectoryChangesW)
[ Native C Monitoring Engine ] ──► logs/events.jsonl
                                         │
                                         ▼ (30s Sliding Windows)
                    [ Feature Extraction (11 Behavioral Features) ]
                                         │
                                         ▼
                    [ Supervised Random Forest Classifier ]
                                         │
                                         ▼
                    [ SQLite Storage & Streamlit SOC Dashboard ]
```

---

## ✨ Key Features

- **Real-Time Kernel Telemetry**: High-performance C watcher using asynchronous Overlapped I/O and aligned 64KB buffers.
- **Machine Learning Triage**: 100-tree Random Forest classifier achieving **100% accuracy** and **0.0% false positive rate** on held-out test windows.
- **Sub-Millisecond Inference**: Model classification completes in **~0.04 ms** per window.
- **Canary Decoy Fleet**: Manifest-driven deployment of synthetic honeytokens (passwords, private keys, databases, spreadsheets).
- **Interactive SOC Dashboard**: Dark-mode console with live metrics, forensic drawer, incident log, and 1-click test triggers.
- **Safe Sandboxing**: All operations are strictly confined to `runtime/monitored/` with path-traversal safeguards.

---

## 📁 Project Structure

```
├── application/              # SOC Dashboard, Alert Engine & Storage
│   ├── alert_engine.py       # Incident evaluation & triage
│   ├── dashboard.py          # Streamlit Cyber SOC interface
│   ├── manage_decoys.py      # Canary deployment & management
│   ├── process_manager.py    # Native C monitor process controller
│   ├── scenario_runner.py    # Safe simulation runner (benign & attacks)
│   └── storage.py            # SQLite database manager (WAL mode)
│
├── config/
│   └── settings.json         # Paths, windowing intervals & thresholds
│
├── decoys/
│   ├── manifest.json         # Registry of active decoy files and tokens
│   └── sample_files/         # Harmless watermarked canary templates
│
├── ml/                       # Machine Learning Pipeline
│   ├── evaluate.py           # Model benchmark & evaluation script
│   ├── generate_dataset.py   # Multi-scenario dataset generator
│   ├── predict.py            # Inference & evidence rationale engine
│   ├── preprocess.py         # 30-second windowing & 11-feature extraction
│   └── train.py              # Random Forest training script
│
├── models/
│   ├── model_metadata.json   # Model parameters & feature rankings
│   └── random_forest_model.joblib # Serialized trained model
│
├── monitor/                  # Native Windows C Watcher
│   ├── CMakeLists.txt        # CMake build file
│   ├── monitor.exe           # Pre-compiled Windows executable
│   └── src/                  # C source files (main, watcher, event_logger)
│
├── runtime/monitored/        # Sandboxed target directory (documents & decoys)
├── tests/                    # 24 automated unit and integration tests
├── demo_live.py              # Interactive terminal presentation console
├── LAUNCH_DASHBOARD.bat      # 1-Click launcher for Streamlit Dashboard
├── RUN_LIVE_DEMO.bat         # 1-Click launcher for Terminal Demo
└── requirements.txt          # Python dependencies
```

---

## ⚙️ Prerequisites

- **OS**: Windows 10 or Windows 11 (64-bit)
- **Python**: 3.10+ (Recommended: **Python 3.11**)
- **C Compiler**: MinGW-w64 GCC (`gcc`) or MSVC (`cl.exe`)

---

## 🚀 Step-by-Step Setup Guide

Open **Windows PowerShell** in the project root (`d:\NS\ANti Cp`):

### Step 1: Set Up Python Virtual Environment
```powershell
# Create virtual environment
py -3.11 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```
> **Note**: If script execution is restricted on your system, run:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

### Step 2: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Compile the C Monitor (Optional)
The repository includes a pre-built `monitor/monitor.exe`. To recompile from source:
```powershell
gcc -O2 -Wall monitor/src/main.c monitor/src/watcher.c monitor/src/event_logger.c -o monitor/monitor.exe
```

### Step 4: Initialize Decoys & Monitored Directory
Deploy the canary files and sample documents into the monitored sandbox:
```powershell
python application/manage_decoys.py --setup
```

### Step 5: Verify Setup with Tests
Run the automated pytest test suite to ensure everything is working:
```powershell
python -m pytest tests/ -v
```
*(All 24 tests should pass)*

---

## 🖥️ How to Run the Project

### Option 1: 1-Click Batch Files (Easiest)
- Double-click **`LAUNCH_DASHBOARD.bat`** to start the SOC Web Console.
- Double-click **`RUN_LIVE_DEMO.bat`** to launch the Terminal Demo.

---

### Option 2: Cyber SOC Web Dashboard
Launch the Streamlit web dashboard:
```powershell
.\.venv\Scripts\streamlit.exe run application/dashboard.py
```
Open **`http://localhost:8501`** in your browser.

The dashboard provides:
- Live C monitor process controls (Start / Stop)
- 1-Click Demonstration Studio (4 instant test scenarios)
- Real-time KPI counters & filterable event streams
- Forensic evidence drawer showing why an alert was triggered
- Model performance benchmarks and confusion matrix

---

### Option 3: Interactive Terminal Demo
For presentations or quick terminal evaluation:
```powershell
python demo_live.py
```
Select from the interactive menu to trigger benign activities, ransomware bursts, or credential probes, and view disk changes and ML decisions live.

---

### Option 4: Full Dual-Terminal Real-Time Pipeline
To monitor file changes as you manually interact with files in Windows Explorer:

**Terminal 1 (Start C Watcher Engine):**
```powershell
.\monitor\monitor.exe
```

**Terminal 2 (Start Streamlit Dashboard):**
```powershell
.\.venv\Scripts\streamlit.exe run application/dashboard.py
```

---

## 🎯 Demonstration Scenarios

Use the dashboard's **Demonstration Studio** or `demo_live.py` to test the 4 core scenarios:

| Scenario | Simulated Activity | Decoys Touched | ML Verdict | Result |
| :--- | :--- | :---: | :---: | :--- |
| **1. Normal Office** | Routine document editing in `documents/` | 0 | `NORMAL` (0.0% Risk) | Clean baseline, 0 alerts |
| **2. Ransomware Attack** | Rapid multi-file bulk encryption | Multiple | `CRITICAL` (100.0% Risk) | Alert raised, MITRE T1486 / T1485 |
| **3. Credential Recon** | Searching password database & SSH keys | > 70% ratio | `ELEVATED` (100.0% Risk) | Alert raised, MITRE T1083 / T1552 |
| **4. Incidental Decoy Click** | Legitimate work + 1 accidental decoy click | 1 (slow cadence) | `NORMAL` (0.0% Risk) | **Zero false alarm!** |

---

## 🔄 Retraining & Dataset Generation (Optional)

If you modify features or scenarios, you can regenerate the dataset and retrain the model:

```powershell
# 1. Generate synthetic behavioral dataset
python ml/generate_dataset.py

# 2. Train Random Forest model
python ml/train.py

# 3. Evaluate model on held-out test split
python ml/evaluate.py
```

---

## 📤 Adding This Project to GitHub

To push this project to your GitHub repository:

### 1. Check Git Installation
```powershell
git --version
```
*(If Git is not installed, run: `winget install --id Git.Git -e --source winget` and restart PowerShell)*

### 2. Configure Git (if first time)
```powershell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Initialize & Commit
```powershell
# In project root (d:\NS\ANti Cp)
git init
git add .
git commit -m "feat: initial commit - intelligent decoy file system"
```

### 4. Link Remote & Push
Create an empty repository on GitHub (without initializing a README), then run:
```powershell
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

---

## 📜 License & Academic Notice

- **Purpose**: University Coursework & Defensive Security Research Prototype.
- **Safety**: Safe for educational use. All attack behaviors are harmless simulations confined to `runtime/monitored/`.
