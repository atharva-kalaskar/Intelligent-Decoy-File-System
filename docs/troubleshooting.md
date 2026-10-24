# Troubleshooting & Windows Compatibility Guide

## 1. Common Windows Environment Issues

### 1.1 PowerShell Execution Policy Restriction
- **Symptom:** Running `.\.venv\Scripts\Activate.ps1` gives error: `File ... cannot be loaded because running scripts is disabled on this system`.
- **Resolution:** Either bypass the policy for the current process:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
  Or run commands directly via the virtual environment binary without activating:
  ```powershell
  .\.venv\Scripts\python.exe -m pytest tests/
  ```

### 1.2 Windows Defender SmartScreen / Antivirus Heuristic Flagging
- **Symptom:** Windows Defender flags `monitor.exe` or PowerShell scripts attempting to launch it with: `Operation did not complete successfully because the file contains a virus or potentially unwanted software`.
- **Cause:** Freshly compiled, unsigned MinGW executables calling `ReadDirectoryChangesW` and manipulating files named `Backup_Credentials` or `private_key` can trigger cloud heuristic detectors.
- **Resolution:**
  - Launch `monitor.exe` directly via standard console or Python subprocess rather than detached `Start-Process`.
  - Add an exclusion for the project test folder if prompted:
    ```powershell
    # Only if permitted by your lab administrator:
    Add-MpPreference -ExclusionPath "D:\NS\ANti Cp"
    ```

### 1.3 Missing C Compiler
- **Symptom:** `gcc` or `cl` is not recognized.
- **Resolution:**
  - Install MinGW-w64 via MSYS2 or standalone MinGW, and append its `bin` directory to your Windows `PATH` environment variable.
  - Test compiler availability:
    ```powershell
    gcc --version
    ```

### 1.4 SQLite Database Locked Errors (`sqlite3.OperationalError: database is locked`)
- **Symptom:** Multiple components trying to access `application/decoy_system.db` concurrently.
- **Resolution:** The storage layer enables Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) with a 10.0-second busy timeout. If a lock error persists, ensure no external SQLite GUI browser holds an exclusive transaction.

### 1.5 Port 8501 Already in Use by Streamlit
- **Symptom:** `Network error: Port 8501 is already in use.`
- **Resolution:** Specify an alternate port when starting Streamlit:
  ```powershell
  .\.venv\Scripts\streamlit.exe run application/dashboard.py --server.port 8502
  ```
