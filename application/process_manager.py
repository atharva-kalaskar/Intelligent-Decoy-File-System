"""
Process Manager for Windows C Monitoring Engine
Controls the lifecycle of monitor/monitor.exe using standard library and native Windows APIs.
Provides status detection, asynchronous process start, and graceful or forced termination.
"""

import os
import subprocess
from pathlib import Path
from typing import Tuple, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
MONITOR_EXE = BASE_DIR / "monitor" / "monitor.exe"
PID_FILE = BASE_DIR / "logs" / "monitor.pid"


def is_monitor_running() -> Tuple[bool, Optional[int]]:
    """
    Checks if monitor.exe is actively running on Windows using native tasklist.
    Returns (True, PID) if running, else (False, None).
    """
    try:
        cmd = ['tasklist', '/FI', 'IMAGENAME eq monitor.exe', '/FO', 'CSV', '/NH']
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
        output = res.stdout.strip()
        if output and "monitor.exe" in output.lower():
            # CSV format: "monitor.exe","1234","Console","0","1,234 K"
            parts = output.split(",")
            if len(parts) >= 2:
                pid_str = parts[1].replace('"', '').strip()
                try:
                    return True, int(pid_str)
                except ValueError:
                    return True, None
            return True, None
    except Exception:
        pass

    # Check pid file as fallback
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if pid exists
            check_res = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], capture_output=True, text=True)
            if str(pid) in check_res.stdout:
                return True, pid
            else:
                PID_FILE.unlink(missing_ok=True)
        except Exception:
            PID_FILE.unlink(missing_ok=True)

    return False, None


def start_monitor(
    monitored_dir: Optional[Path] = None,
    log_file: Optional[Path] = None,
    manifest_file: Optional[Path] = None
) -> Tuple[bool, str]:
    """
    Launches monitor.exe in the background as a detached process.
    """
    if not MONITOR_EXE.exists():
        return False, f"Monitor executable not found at: {MONITOR_EXE}. Please compile it first."

    running, pid = is_monitor_running()
    if running:
        return False, f"Monitor engine is already running with PID {pid}."

    target_dir = str(monitored_dir or (BASE_DIR / "runtime" / "monitored"))
    target_log = str(log_file or (BASE_DIR / "logs" / "events.jsonl"))
    target_manifest = str(manifest_file or (BASE_DIR / "decoys" / "manifest.json"))

    args = [
        str(MONITOR_EXE),
        "--dir", target_dir,
        "--log", target_log,
        "--manifest", target_manifest
    ]

    try:
        # Direct stdout and stderr to log files so printf does not fail on Windows
        stdout_log = BASE_DIR / "logs" / "c_monitor_stdout.log"
        stderr_log = BASE_DIR / "logs" / "c_monitor_stderr.log"
        stdout_log.parent.mkdir(parents=True, exist_ok=True)
        
        stdout_f = open(stdout_log, "a", encoding="utf-8")
        stderr_f = open(stderr_log, "a", encoding="utf-8")

        DETACHED_PROCESS = 0x00000008
        CREATE_NO_WINDOW = 0x08000000
        flags = DETACHED_PROCESS | CREATE_NO_WINDOW

        proc = subprocess.Popen(
            args,
            cwd=str(BASE_DIR),
            creationflags=flags,
            stdout=stdout_f,
            stderr=stderr_f
        )

        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(proc.pid))

        return True, f"Monitor engine started successfully (PID: {proc.pid})."
    except Exception as e:
        return False, f"Failed to start monitor engine: {e}"


def stop_monitor() -> Tuple[bool, str]:
    """
    Terminates all running instances of monitor.exe safely.
    """
    running, pid = is_monitor_running()
    if not running:
        PID_FILE.unlink(missing_ok=True)
        return True, "Monitor engine is not running."

    try:
        res = subprocess.run(['taskkill', '/F', '/IM', 'monitor.exe'], capture_output=True, text=True, timeout=5.0)
        PID_FILE.unlink(missing_ok=True)
        if res.returncode == 0:
            return True, "Monitor engine stopped cleanly."
        else:
            return False, f"taskkill returned code {res.returncode}: {res.stderr.strip()}"
    except Exception as e:
        return False, f"Error stopping monitor: {e}"
