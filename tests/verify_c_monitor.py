"""
Verification script for C monitoring engine and Windows ReadDirectoryChangesW capture.
"""
import subprocess
import time
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MONITOR_EXE = BASE_DIR / "monitor" / "monitor.exe"
LOG_FILE = BASE_DIR / "logs" / "events.jsonl"
MONITORED_DIR = BASE_DIR / "runtime" / "monitored"


def test_c_monitor_live_capture():
    assert MONITOR_EXE.exists(), f"Monitor executable not found at {MONITOR_EXE}"

    # Clear log file
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    print("[INFO] Launching C monitor with 3500ms timeout...")
    proc = subprocess.Popen(
        [str(MONITOR_EXE), "--timeout", "3500", "--dir", str(MONITORED_DIR), "--log", str(LOG_FILE)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Allow monitor to initialize and hook directory changes
    time.sleep(0.5)

    test_doc = MONITORED_DIR / "documents" / "test_doc_verify.txt"
    decoy_doc = MONITORED_DIR / "decoys" / "Confidential_Report.docx.txt"

    # Action 1: Create a normal file
    print("[ACTION] Creating normal file...")
    test_doc.write_text("Verification normal content\n", encoding="utf-8")
    time.sleep(0.3)

    # Action 2: Modify a known decoy file
    print("[ACTION] Modifying decoy file...")
    with open(decoy_doc, "a", encoding="utf-8") as f:
        f.write("\nUnauthorized append probe testing telemetry.\n")
    time.sleep(0.3)

    # Action 3: Delete normal file
    print("[ACTION] Deleting normal file...")
    if test_doc.exists():
        test_doc.unlink()
    time.sleep(0.3)

    # Wait for monitor to exit via timeout
    stdout, stderr = proc.communicate(timeout=6.0)
    print(f"[C MONITOR STDOUT]:\n{stdout}")
    if stderr:
        print(f"[C MONITOR STDERR]:\n{stderr}")

    assert LOG_FILE.exists(), "Event log was not created!"
    lines = [line.strip() for line in LOG_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"[INFO] Total events captured in log: {len(lines)}")
    assert len(lines) > 0, "No events were recorded by the C monitor!"

    events = [json.loads(line) for line in lines]

    decoy_events = [e for e in events if e.get("is_decoy")]
    normal_events = [e for e in events if not e.get("is_decoy")]

    print(f"[INFO] Decoy events captured: {len(decoy_events)}")
    print(f"[INFO] Normal events captured: {len(normal_events)}")

    # Verify decoy event details
    assert len(decoy_events) >= 1, "Expected at least 1 decoy event"
    first_decoy = decoy_events[0]
    assert first_decoy["file_id"] == "DECOY-001" or "Confidential_Report" in first_decoy["relative_path"]
    assert first_decoy["is_decoy"] is True
    assert first_decoy["source"] == "windows_monitor_c"

    print("[SUCCESS] C Monitor live event capture verified successfully!")


if __name__ == "__main__":
    test_c_monitor_live_capture()
