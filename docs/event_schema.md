# Event Schema Specification

## 1. Overview
The **Intelligent Decoy File System** uses a shared JSON Lines (`.jsonl`) schema between the C monitoring component and the Python preprocessing pipeline. Each line represents a discrete file-system change notification observed via Windows `ReadDirectoryChangesW`.

## 2. JSON Record Structure

```json
{
  "event_id": "EVT-00000001",
  "timestamp": "2026-10-20T01:30:00.123456",
  "event_type": "MODIFY",
  "relative_path": "decoys/Financial_Records.txt",
  "file_id": "DECOY-002",
  "is_decoy": true,
  "source": "windows_monitor_c",
  "details": "Action=MODIFIED"
}
```

## 3. Field Definitions and Types

| Field Name | Type | Required | Description | Allowed Values / Format |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | String | Yes | Monotonically increasing unique identifier | `EVT-%08lu` (e.g., `EVT-00000001`) |
| `timestamp` | String | Yes | ISO-8601 formatted local timestamp | `YYYY-MM-DDTHH:MM:SS.ffffff` |
| `event_type` | String | Yes | Normalized file-system action | `CREATE`, `DELETE`, `MODIFY`, `RENAME_OLD`, `RENAME_NEW` |
| `relative_path` | String | Yes | Normalized path relative to monitored root | Forward-slash path, e.g. `decoys/Passwords.txt` |
| `file_id` | String / Null| No | Decoy identifier from manifest if matched | e.g. `DECOY-001`, or `null` if not a decoy |
| `is_decoy` | Boolean | Yes | Indicator if the affected file is a decoy | `true` or `false` |
| `source` | String | Yes | Telemetry collector component | `windows_monitor_c` or `synthetic_generator` |
| `details` | String | No | Supplementary telemetry or raw action code | Free-form diagnostic string |

## 4. Telemetry Realities & Constraints
- **ReadDirectoryChangesW Scope**: Captures changes (Creations, Deletions, Modifications, Renames) inside the monitored directory subtree.
- **File Read Notification Limitation**: Standard `ReadDirectoryChangesW` without kernel minifilter drivers or ETW access telemetry does *not* report clean metadata read-only actions (such as viewing a file without changing its last write time or attributes). Any modifications or touch events altering file contents, metadata, or timestamps *are* captured. The application strictly distinguishes changes from read-access telemetry and does not invent fake reads.
- **Log Handling**: Log consumers parse lines defensively. Malformed or partial lines (e.g. from an abrupt process termination) are logged as parser warnings and skipped without crashing the pipeline.
