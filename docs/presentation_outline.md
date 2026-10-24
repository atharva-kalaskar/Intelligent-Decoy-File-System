# Viva & Course Presentation Outline

## Slide 1: Title & Team
- **Title:** Intelligent Decoy File System for Suspicious Activity Detection Using Random Forest
- **Course:** Network Security & Defensive Systems
- **Core Premise:** Combining Win32 file-system change telemetry with Machine Learning behavioral triage to defeat ransomware and unauthorized data reconnaissance.

---

## Slide 2: The Problem with Traditional Defenses
- Signature AV fails against zero-day malware and custom scripts.
- Pure honey-files often suffer from high false-alarm rates when users make accidental clicks or search indexers scan directories.
- Need: An automated, low-latency behavioral classifier to separate genuine attacks from benign noise.

---

## Slide 3: Architecture & Technology Stack
- **Telemetry Layer (C):** Windows `ReadDirectoryChangesW` with overlapped I/O and aligned 64KB buffers.
- **Data Exchange:** Standard JSON Lines (`logs/events.jsonl`).
- **Feature Extraction (Python):** 30-second sliding windows, extracting 11 behavioral metrics.
- **Machine Learning (scikit-learn):** Supervised Random Forest Classifier vs. Rule-Based Baseline.
- **Storage & Dashboard:** SQLite WAL mode & Streamlit web interface.

---

## Slide 4: Behavioral Feature Engineering
- Event Counts & Unique Files.
- Decoy Events & Decoy Ratio.
- Action Distribution (`CREATE`, `MODIFY`, `DELETE`, `RENAME`).
- Temporal Dynamics: Events-per-second, Inter-event arrival time mean, Inter-event standard deviation.

---

## Slide 5: Experimental Methodology & Data Integrity
- 4 Realistic Scenarios: Benign routine, Incidental decoy touch, Credential reconnaissance, Bulk tampering.
- 480 Sessions -> 3,007 Feature Windows (52% suspicious / 48% normal).
- **Zero Leakage:** Train/Test partitioning via `GroupShuffleSplit` on `session_id`.

---

## Slide 6: Results & Comparative Analysis
- Evaluated on 474 held-out test windows:
  - Random Forest: **100% Accuracy, 100% F1-score, 0.0% False Positive Rate**.
  - Rule-Based Baseline: **99.79% Accuracy, 99.82% F1-score, 0.50% False Positive Rate**.
- Inference latency: Sub-millisecond (0.041 ms/window).

---

## Slide 7: Live Demonstration Walkthrough
- Terminal 1: C Monitor active on `runtime/monitored/`.
- Terminal 2: Streamlit Dashboard displaying live status.
- Demonstration of benign editing (no alert).
- Demonstration of decoy tripwire tampering (immediate `CRITICAL` alert + evidence).

---

## Slide 8: Technical Defense / Viva Anticipated Questions
1. **Q:** *Why not use Python watchdog instead of C?*
   - **A:** C interacts directly with the Win32 kernel API, provides deterministic memory management, avoids GIL overhead, and allows fine-grained control over buffer alignment and `ERROR_NOTIFY_ENUM_DIR` handling.
2. **Q:** *Does this capture read-only file access?*
   - **A:** No; `ReadDirectoryChangesW` captures directory modifications and metadata alterations. Pure in-memory reads without file updates require kernel minifilters or ETW, which would require administrative elevation.
3. **Q:** *Why Random Forest over Deep Learning?*
   - **A:** Random Forest is computationally lightweight, operates under 0.05 ms latency on standard CPU, does not require GPU infrastructure, is resistant to overfitting on tabular features, and provides clear feature importance metrics.
