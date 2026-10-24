"""
Alert Engine and Real-time Stream Processor
Consumes event records from logs/events.jsonl, maintains window state, runs Random Forest
inference, persists predictions, and raises evidence-backed alerts.
"""

import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "ml"))
sys.path.insert(0, str(BASE_DIR / "application"))

from storage import StorageManager
from preprocess import read_event_log, calculate_window_features, aggregate_events_into_windows, parse_iso_timestamp
from predict import predict_window

logger = logging.getLogger("alert_engine")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class AlertEngine:
    def __init__(
        self,
        log_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
        window_size_sec: float = 30.0,
        slide_sec: float = 10.0
    ):
        self.log_path = Path(log_path) if log_path else BASE_DIR / "logs" / "events.jsonl"
        self.storage = StorageManager(db_path) if db_path else StorageManager()
        self.window_size_sec = window_size_sec
        self.slide_sec = slide_sec
        self.last_processed_line = 0

    def process_new_events(self) -> int:
        """
        Reads newly appended lines from events.jsonl, ingests them into SQLite,
        and returns count of newly ingested events.
        """
        events = read_event_log(self.log_path)
        if not events:
            return 0

        inserted = self.storage.insert_events(events)
        return inserted

    def evaluate_recent_window(self, events: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        Evaluates the most recent observation window from persisted events or provided event batch.
        """
        if events is not None:
            chronological_events = events
        else:
            all_events = self.storage.get_recent_events(limit=200)
            if not all_events:
                logger.info("No events in storage to evaluate.")
                return None
            # Storage returns newest first; reverse for temporal ordering
            chronological_events = list(reversed(all_events))

        features = calculate_window_features(chronological_events, self.window_size_sec)

        # Run model inference
        prediction_res = predict_window(features)

        window_start = chronological_events[0]["timestamp"]
        window_end = chronological_events[-1]["timestamp"]
        pred_id = f"PRED-{int(time.time()*1000):012d}"

        pred_record = {
            "prediction_id": pred_id,
            "window_start": window_start,
            "window_end": window_end,
            "prediction": prediction_res["prediction"],
            "is_suspicious": prediction_res["is_suspicious"],
            "suspicious_probability": prediction_res["suspicious_probability"],
            "risk_level": prediction_res["risk_level"],
            "model_version": prediction_res["model_version"],
            "reason_summary": prediction_res["reason_summary"],
            "input_features": features
        }

        self.storage.insert_prediction(pred_record)

        # Generate alert if classified suspicious or high risk
        if prediction_res["is_suspicious"] == 1:
            decoy_evts = [e for e in chronological_events if e.get("is_decoy")]
            evidence = {
                "features": features,
                "triggered_decoys": list({e["relative_path"] for e in decoy_evts}),
                "decoy_event_ids": [e["event_id"] for e in decoy_evts[:10]],
                "model_confidence": prediction_res["suspicious_probability"]
            }

            alert_id = f"ALT-{int(time.time()*1000):012d}"
            severity = prediction_res["risk_level"]

            alert_record = {
                "alert_id": alert_id,
                "timestamp": datetime.now().isoformat(),
                "severity": severity,
                "title": f"Decoy File Interaction Alert ({severity})",
                "description": prediction_res["reason_summary"],
                "prediction_id": pred_id,
                "evidence": evidence
            }

            self.storage.insert_alert(alert_record)

            print("\n=======================================================")
            print(f" [!] SECURITY ALERT GENERATED: {alert_id} ({severity})")
            print(f" Reason: {prediction_res['reason_summary']}")
            print(f" Probability: {prediction_res['suspicious_probability']*100:.1f}%")
            print(f" Decoys Compromised: {evidence['triggered_decoys']}")
            print("=======================================================\n")

        return pred_record

    def run_once(self) -> Optional[Dict[str, Any]]:
        self.process_new_events()
        return self.evaluate_recent_window()

    def run_daemon(self, poll_interval_sec: float = 2.0):
        print(f"[INFO] Alert Engine running in daemon mode (polling every {poll_interval_sec}s)...")
        try:
            while True:
                new_evts = self.process_new_events()
                if new_evts > 0:
                    self.evaluate_recent_window()
                time.sleep(poll_interval_sec)
        except KeyboardInterrupt:
            print("[INFO] Alert engine terminated by user.")


if __name__ == "__main__":
    engine = AlertEngine()
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        engine.run_daemon()
    else:
        res = engine.run_once()
        print(f"[OK] Alert engine evaluated window: {res}")
