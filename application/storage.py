"""
SQLite Storage Layer for Telemetry, Model Predictions, and Alerts.
Provides schema management, parameterized queries, and ACID-safe operations.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "application" / "decoy_system.db"


class StorageManager:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")  # Write-Ahead Logging for high concurrency
        return conn

    def init_database(self):
        """Initializes tables and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Events Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                file_id TEXT,
                is_decoy INTEGER NOT NULL,
                source TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL
            );
            """)

            # 2. Predictions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                window_start TEXT,
                window_end TEXT,
                prediction TEXT NOT NULL,
                is_suspicious INTEGER NOT NULL,
                suspicious_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                model_version TEXT NOT NULL,
                reason_summary TEXT NOT NULL,
                feature_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            # 3. Alerts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                prediction_id TEXT,
                evidence_json TEXT NOT NULL,
                is_acknowledged INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
            );
            """)

            # 4. Ingestion Checkpoint Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_state (
                key TEXT PRIMARY KEY,
                last_val TEXT,
                updated_at TEXT
            );
            """)

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_decoy ON events(is_decoy);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_preds_created ON predictions(created_at);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at);")
            conn.commit()

    def insert_events(self, events: List[Dict[str, Any]]) -> int:
        """Inserts multiple events, ignoring duplicates."""
        if not events:
            return 0

        now_str = datetime.now().isoformat()
        inserted_count = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for evt in events:
                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO events 
                    (event_id, timestamp, event_type, relative_path, file_id, is_decoy, source, details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        evt["event_id"],
                        evt["timestamp"],
                        evt["event_type"],
                        evt["relative_path"],
                        evt.get("file_id"),
                        1 if evt.get("is_decoy") else 0,
                        evt.get("source", "windows_monitor_c"),
                        evt.get("details", ""),
                        now_str
                    ))
                    if cursor.rowcount > 0:
                        inserted_count += 1
                except sqlite3.Error as e:
                    pass
            conn.commit()
        return inserted_count

    def insert_prediction(self, pred_record: Dict[str, Any]):
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO predictions
            (prediction_id, window_start, window_end, prediction, is_suspicious, suspicious_probability,
             risk_level, model_version, reason_summary, feature_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred_record["prediction_id"],
                pred_record.get("window_start"),
                pred_record.get("window_end"),
                pred_record["prediction"],
                pred_record["is_suspicious"],
                pred_record["suspicious_probability"],
                pred_record["risk_level"],
                pred_record["model_version"],
                pred_record["reason_summary"],
                json.dumps(pred_record.get("input_features", {})),
                now_str
            ))
            conn.commit()

    def insert_alert(self, alert_record: Dict[str, Any]):
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO alerts
            (alert_id, timestamp, severity, title, description, prediction_id, evidence_json, is_acknowledged, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_record["alert_id"],
                alert_record["timestamp"],
                alert_record["severity"],
                alert_record["title"],
                alert_record["description"],
                alert_record.get("prediction_id"),
                json.dumps(alert_record.get("evidence", {})),
                0,
                now_str
            ))
            conn.commit()

    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_predictions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_system_stats(self) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events;")
            total_events = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM events WHERE is_decoy = 1;")
            decoy_events = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM predictions;")
            total_predictions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM predictions WHERE is_suspicious = 1;")
            suspicious_predictions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alerts;")
            total_alerts = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(timestamp) FROM events;")
            last_event_time = cursor.fetchone()[0]

            return {
                "total_events": total_events,
                "decoy_events": decoy_events,
                "total_predictions": total_predictions,
                "suspicious_predictions": suspicious_predictions,
                "total_alerts": total_alerts,
                "last_event_time": last_event_time
            }

    def clear_all_telemetry(self):
        """Purges all event, prediction, and alert records for a clean demonstration session."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts;")
            cursor.execute("DELETE FROM predictions;")
            cursor.execute("DELETE FROM events;")
            conn.commit()
