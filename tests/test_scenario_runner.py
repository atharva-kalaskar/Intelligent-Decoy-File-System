"""
Unit tests for ScenarioRunner automated demonstration engine.
"""

import pytest
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "application"))

from scenario_runner import ScenarioRunner


def test_scenario_runner_normal_office():
    runner = ScenarioRunner()
    res = runner.execute_scenario("normal_office")
    assert res["scenario_type"] == "normal_office"
    assert res["prediction"]["is_suspicious"] == 0
    assert res["prediction"]["prediction"] == "normal"
    assert res["alert"] is None


def test_scenario_runner_ransomware_burst():
    runner = ScenarioRunner()
    res = runner.execute_scenario("ransomware_burst")
    assert res["scenario_type"] == "ransomware_burst"
    assert res["prediction"]["is_suspicious"] == 1
    assert res["prediction"]["risk_level"] == "CRITICAL"
    assert res["alert"] is not None
    assert "T1486" in res["meta"]["mitre_ttp"]


def test_scenario_runner_credential_recon():
    runner = ScenarioRunner()
    res = runner.execute_scenario("credential_recon")
    assert res["scenario_type"] == "credential_recon"
    assert res["prediction"]["is_suspicious"] == 1
    assert res["prediction"]["risk_level"] in ("ELEVATED", "CRITICAL")
    assert res["alert"] is not None


def test_scenario_runner_incidental_touch():
    runner = ScenarioRunner()
    res = runner.execute_scenario("incidental_touch")
    assert res["scenario_type"] == "incidental_touch"
    # Random Forest correctly filters single incidental touch at human pace
    assert res["prediction"]["is_suspicious"] == 0
    assert res["prediction"]["prediction"] == "normal"


def test_scenario_runner_reset():
    runner = ScenarioRunner()
    res = runner.reset_demo_environment()
    assert res["status"] == "success"
