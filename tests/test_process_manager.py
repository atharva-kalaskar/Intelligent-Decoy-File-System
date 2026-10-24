"""
Unit tests for Windows process manager controlling monitor.exe.
"""

import time
import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "application"))

import process_manager


def test_process_manager_lifecycle():
    # 1. Ensure clean initial state
    process_manager.stop_monitor()
    running, pid = process_manager.is_monitor_running()
    assert running is False
    assert pid is None

    # 2. Start monitor process
    ok, msg = process_manager.start_monitor()
    assert ok is True
    assert "started" in msg.lower()

    time.sleep(1.0)

    # 3. Verify running state
    running, pid = process_manager.is_monitor_running()
    assert running is True
    assert isinstance(pid, int)
    assert pid > 0

    # 4. Stop monitor process
    ok, msg = process_manager.stop_monitor()
    assert ok is True

    time.sleep(0.5)

    # 5. Verify stopped state
    running, pid = process_manager.is_monitor_running()
    assert running is False
    assert pid is None
