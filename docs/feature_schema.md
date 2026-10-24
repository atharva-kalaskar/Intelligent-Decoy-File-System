# Feature Schema Specification

## 1. Overview
The **Intelligent Decoy File System** groups raw file-system events into configurable time windows (e.g. 30 seconds with a 10-second slide) and computes numerical behavioral metrics. These features serve as the input vector $\mathbf{x} \in \mathbb{R}^{11}$ for the Random Forest classifier and the rule-based baseline detector.

## 2. Feature Table

| Feature Name | Type | Unit / Range | Description | Handling of Edge Cases (e.g. Empty / Single Event) |
| :--- | :--- | :--- | :--- | :--- |
| `event_count` | Integer | $[0, \infty)$ | Total count of valid file events in window | 0 if no events occur |
| `unique_files` | Integer | $[0, \infty)$ | Count of distinct file paths observed | 0 if no events occur |
| `decoy_events` | Integer | $[0, \infty)$ | Number of events targeting decoy files | 0 if no decoy events |
| `decoy_ratio` | Float | $[0.0, 1.0]$ | Proportion $\frac{\text{decoy\_events}}{\text{event\_count}}$ | Explicitly $0.0$ when $\text{event\_count} = 0$ |
| `create_count` | Integer | $[0, \infty)$ | Total `CREATE` events | 0 if none |
| `modify_count` | Integer | $[0, \infty)$ | Total `MODIFY` events | 0 if none |
| `delete_count` | Integer | $[0, \infty)$ | Total `DELETE` events | 0 if none |
| `rename_count` | Integer | $[0, \infty)$ | Total `RENAME_OLD` + `RENAME_NEW` events | 0 if none |
| `events_per_second`| Float | $[0.0, \infty)$ | $\frac{\text{event\_count}}{\text{window\_duration\_seconds}}$ | $0.0$ if $\text{event\_count} = 0$ |
| `inter_event_mean` | Float | $[0.0, \infty)$ seconds | Mean time delta between consecutive events | $0.0$ if fewer than 2 events in window |
| `inter_event_std` | Float | $[0.0, \infty)$ seconds | Sample std dev of inter-event time deltas | $0.0$ if fewer than 2 events in window |

## 3. Label Definition
- Target Column: `is_suspicious`
- Allowed Values:
  - `0`: Normal / benign activity (routine document editing, reading, single incidental touches)
  - `1`: Suspicious activity (bulk decoy manipulation, high-frequency alterations, ransomware-like behavior, unauthorized credential decoy tampering)

## 4. Invariant Rules
- Features are strictly numerical.
- The order, types, column names, and scaling must match exactly between offline training and live inference.
- Schema versioning (`1.0.0`) is validated by the model metadata upon loading.
