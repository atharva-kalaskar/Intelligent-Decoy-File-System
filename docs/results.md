# Experimental Results & Model Performance Benchmarks

## 1. Overview
This document records the empirical results obtained from executing the training and evaluation pipeline on the held-out test dataset generated for the **Intelligent Decoy File System**.

---

## 2. Dataset Partitioning & Leakage Prevention
- **Total Windows Generated:** 3,007 across 480 unique behavioral sessions.
- **Class Balance:**
  - Normal (0): 1,432 windows (47.6%)
  - Suspicious (1): 1,575 windows (52.4%)
- **Data Splitting Strategy:** `GroupShuffleSplit` on `session_id`.
  - Training Set: 2,080 windows (336 sessions)
  - Validation Set: 453 windows (72 sessions)
  - Held-out Test Set: 474 windows (72 sessions)
- **Data Leakage Guarantee:** Because time-sliding windows from the same session share temporal proximity, splitting by session ID guarantees that no window in the test set shares events or context with any window in the training set.

---

## 3. Comparative Metric Summary (Held-Out Test Set)

| Metric | Supervised Random Forest Classifier | Rule-Based Baseline Detector | Performance Delta |
| :--- | :--- | :--- | :--- |
| **Accuracy** | **100.00%** (474/474) | 99.79% (473/474) | **+0.21%** |
| **Precision** | **100.00%** | 99.63% | **+0.37%** |
| **Recall** | **100.00%** (272/272) | 100.00% (272/272) | 0.00% |
| **F1-Score** | **100.00%** | 99.82% | **+0.18%** |
| **False Positive Rate (FPR)** | **0.00%** (0/202) | 0.50% (1/202) | **-0.50% (Zero FP)** |
| **Inference Latency** | 0.0410 ms/window | **0.0150 ms/window** | +0.0260 ms |

---

## 4. Confusion Matrix Details

### Random Forest
- True Negatives: 202
- False Positives: 0
- False Negatives: 0
- True Positives: 272

### Rule-Based Baseline
- True Negatives: 201
- False Positives: 1 (caused by high burst rate during normal editing)
- False Negatives: 0
- True Positives: 272

---

## 5. Random Forest Feature Importances

Ranked contributions of the 11 engineered features:
1. `decoy_events`: **0.2410**
2. `decoy_ratio`: **0.2324**
3. `inter_event_mean`: **0.2113**
4. `events_per_second`: **0.1495**
5. `event_count`: **0.0909**
6. `modify_count`: **0.0289**
7. `rename_count`: **0.0279**
8. `inter_event_std`: **0.0095**
9. `unique_files`: **0.0085**
10. `create_count`: 0.0000
11. `delete_count`: 0.0000
