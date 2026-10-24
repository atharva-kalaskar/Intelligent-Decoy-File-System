# University Course Project Technical Report
## Course: Network Security & Defensive Cyber Systems
### Project Title: Intelligent Decoy File System for Suspicious Activity Detection Using Random Forest

---

### Abstract
Modern endpoint security environments face continuous threats from ransomware, unauthorized data exfiltration, and internal privilege misuse. Traditional signature-based defenses often struggle against zero-day exploits and polymorphic malware. This project implements and evaluates an **Intelligent Decoy File System**, a hybrid cyber defense system that integrates deception technology with machine learning behavioral triage. Deployed on Windows 10/11, the system monitors a designated directory using a custom native C engine leveraging the Win32 `ReadDirectoryChangesW` API. Interactions with known canary decoy files and legitimate documents are serialized into structured JSON Lines records, processed into 30-second sliding behavioral time windows, and transformed into 11 numerical behavioral features. A supervised Random Forest classifier is trained, tuned, and evaluated against a transparent rule-based security heuristic. Experimental results on 474 held-out test windows demonstrate that the Random Forest model achieves 100% accuracy and F1-score with 0.0% false positive rate in controlled scenario evaluation, compared to 99.79% accuracy and 0.50% false positive rate for the rule baseline, while operating with sub-millisecond inference latency. All incidents and telemetry are persisted in an ACID-compliant SQLite store and visualized via a Streamlit web interface.

---

### Table of Contents
1. [Chapter 1: Introduction & Problem Statement](#chapter-1-introduction--problem-statement)
2. [Chapter 2: Background & Literature Review](#chapter-2-background--literature-review)
3. [Chapter 3: Objectives, Scope & Requirements](#chapter-3-objectives-scope--requirements)
4. [Chapter 4: Architecture & Design](#chapter-4-architecture--design)
5. [Chapter 5: Implementation Details](#chapter-5-implementation-details)
6. [Chapter 6: Dataset Construction & Evaluation Protocol](#chapter-6-dataset-construction--evaluation-protocol)
7. [Chapter 7: Experimental Results & Analysis](#chapter-7-experimental-results--analysis)
8. [Chapter 8: Security, Limitations & Future Work](#chapter-8-security-limitations--future-work)
9. [Chapter 9: Conclusion & Academic References](#chapter-9-conclusion--academic-references)

---

### Chapter 1: Introduction & Problem Statement
File systems remain the primary target for hostile intrusions, whether the objective is data encryption (ransomware) or reconnaissance for high-value intellectual property and credentials. Signature-based antivirus tools only alert when a binary or known file hash matches a vendor database. Conversely, Deception Technology places harmless "honey-files" or decoy assets in environments where legitimate users have little reason to interact with them. 

However, simple tripwire alerts often suffer from false alarms caused by accidental user clicks, indexer software (e.g. Windows Search), or backup agents. The primary research question investigated in this work is:
> *Can a supervised Random Forest classifier, trained on multi-dimensional temporal and behavioral interaction features, reliably distinguish suspicious attack patterns from normal or incidental document activity in a decoy-augmented Windows file system more effectively than a static rule-based baseline?*

---

### Chapter 2: Background & Literature Review
1. **Deception Technology & Honeypots:** Foundational research by Spitzner (2003) and Rowe (2007) establishes that high-interaction and low-interaction decoys create asymmetric advantages for defenders. Canary files deployed in user directories act as high-fidelity tripwires.
2. **Windows File System Monitoring:** Under the Windows operating system, file system notifications are handled via several mechanisms:
   - *User-mode APIs:* `ReadDirectoryChangesW` allows an application to register for change notifications (file addition, deletion, modification, and rename) within an NTFS directory tree.
   - *Kernel-mode Minifilters:* Microsoft's Filter Manager architecture allows kernel drivers (`FltRegisterFilter`) to intercept pre- and post-I/O packets, enabling read-access telemetry at the cost of kernel privileges and system stability risks.
3. **Random Forest for Behavioral Intrusion Detection:** Introduced by Breiman (2001), Random Forest is an ensemble learning algorithm that constructs an array of decorrelated decision trees using bootstrap aggregating (bagging) and random feature selection. It is exceptionally resilient to overfitting, captures complex non-linear feature interactions, and outputs calibrated class probabilities suitable for risk scoring.

---

### Chapter 3: Objectives, Scope & Requirements
- **Primary Objective:** Build an end-to-end working defensive prototype combining a C watcher, Python feature extraction, Random Forest classification, persistent SQLite storage, and a Streamlit dashboard.
- **Operating Scope:** Restricted strictly to an authorized local test directory (`runtime/monitored/`). Operates in standard user mode without administrative elevation or kernel modifications.
- **Functional Requirements:**
  - FR1: Monitor file-system events (`CREATE`, `MODIFY`, `DELETE`, `RENAME`) in real time.
  - FR2: Tag known decoy files according to a validated JSON manifest.
  - FR3: Aggregate events into sliding 30-second observation windows.
  - FR4: Extract 11 numerical behavioral features per window.
  - FR5: Supervised classification with Random Forest, outputting risk ratings.
  - FR6: ACID persistence in SQLite with full evidence linkage.
  - FR7: Interactive live dashboard with manual and automated test triggers.

---

### Chapter 4: Architecture & Design
The system follows a modular six-stage pipeline:
1. **File System Layer:** Divided into `documents/` (routine user documents) and `decoys/` (canary honey-files).
2. **C Watcher Engine:** Single-process Win32 multi-threaded watcher using overlapped I/O and a 64KB aligned buffer. Outputs JSON Lines to `logs/events.jsonl`.
3. **Preprocessing Pipeline:** Ingests JSON Lines defensively, slices events into 30-second windows with a 10-second slide, and extracts statistical features.
4. **Machine Learning Classifier:** Evaluates feature vectors using a trained 100-tree Random Forest model versus a static rule-based detector.
5. **Alert Engine:** Dispatches alerts with structured evidence when suspicious probability exceeds 0.50.
6. **SQLite Storage & Streamlit UI:** Maintains long-term audit logs and visualizes telemetry.

---

### Chapter 5: Implementation Details
- **C Engine (`monitor/src/`):**
  - Compiled cleanly under GCC with `-Wall -Werror`.
  - Configured with `FILE_NOTIFY_CHANGE_FILE_NAME | FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_CREATION`.
  - Synchronous console signal handling (`SetConsoleCtrlHandler`) ensures handles are closed and logs are flushed upon SIGINT.
- **Feature Extraction (`ml/preprocess.py`):**
  - Features include: `event_count`, `unique_files`, `decoy_events`, `decoy_ratio`, `create_count`, `modify_count`, `delete_count`, `rename_count`, `events_per_second`, `inter_event_mean`, `inter_event_std`.
  - Edge cases (such as zero-event or single-event windows) are mathematically handled with deterministic defaults.
- **Persistence (`application/storage.py`):**
  - Uses SQLite in Write-Ahead Logging (`WAL`) mode to prevent reader-writer lock contention between the alert engine and Streamlit.

---

### Chapter 6: Dataset Construction & Evaluation Protocol
- **Scenarios Generated:**
  - *Scenario A (Normal Routine):* 695 windows of regular student/worker document drafting, low event rates.
  - *Scenario B (Incidental Decoy):* 737 windows containing accidental single touches to decoy files without malicious patterns.
  - *Scenario C (Decoy Reconnaissance):* 777 windows simulating attackers enumerating credential and key decoys.
  - *Scenario D (Bulk Tampering / Ransomware):* 798 windows simulating high-frequency modification, renaming, and deletion bursts.
- **Leakage Prevention:** Dataset partitioning utilizes `GroupShuffleSplit` grouped strictly by `session_id`. No overlapping sliding windows from the same session can exist across train, validation, or test sets.

---

### Chapter 7: Experimental Results & Analysis
The model was evaluated against 474 completely held-out test windows (202 Normal, 272 Suspicious).

| Metric | Random Forest Model | Rule-Based Baseline |
| :--- | :--- | :--- |
| **Accuracy** | **100.00%** | 99.79% |
| **Precision** | **100.00%** | 99.63% |
| **Recall** | **100.00%** | 100.00% |
| **F1-Score** | **100.00%** | 99.82% |
| **False Positive Rate (FPR)** | **0.00%** | 0.50% |
| **Inference Latency** | 0.0410 ms | **0.0150 ms** |

**Observations:**
The Random Forest model effectively eliminated the false positive observed in the rule-based baseline. By evaluating the combination of inter-event arrival times, burst rate, and decoy ratio simultaneously, the ensemble correctly distinguished legitimate high-frequency user actions from automated attack sequences.

---

### Chapter 8: Security, Limitations & Future Work
- **Telemetry Boundaries:** `ReadDirectoryChangesW` reports modifications and creations, but does not capture non-modifying read accesses. Future enhancements could incorporate Windows ETW tracing for user-space process and thread attribution.
- **Adversarial Hardening:** Deploying dynamic honey-tokens and randomized decoy generation would mitigate an adversary's ability to fingerprint static manifest files.

---

### Chapter 9: Conclusion & Academic References
The project successfully designed, implemented, and validated a complete Windows decoy monitoring and behavioral detection pipeline. Automated testing confirms 100% test pass rates across C monitoring, feature extraction, model inference, and database persistence.

#### Academic References
1. Breiman, L. (2001). *Random Forests*. Machine Learning, 45(1), 5-32.
2. Spitzner, L. (2003). *Honeypots: Tracking Hackers*. Addison-Wesley Professional.
3. Rowe, N. C. (2007). *Designing Good Deceptions in Defense of Information Systems*. Information Security Journal, 16(2), 65-74.
4. Microsoft Corporation. (2023). *ReadDirectoryChangesW function (winbase.h)*. Windows Developer Documentation.
5. Pedregosa, F., et al. (2011). *Scikit-learn: Machine Learning in Python*. Journal of Machine Learning Research, 12, 2825-2830.
