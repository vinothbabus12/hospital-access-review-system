# Expanded Experiments Results (E1 – E10)

## 1. Overview and Objectives

This document presents the methodology, configuration, and experimental results for the **Expanded Experiments (E1–E10)** conducted on the Hospital Access Review System.

The primary objective of the expanded experiment suite is to evaluate how the evidence engine, peer-usage baseline engine, and risk scoring engine behave under realistic operational conditions and deliberate data anomalies encountered in enterprise healthcare environments.

All experiments are conducted using **in-memory copies** of the synthetic hospital dataset generated with a fixed random seed (`42`), ensuring:
- Absolute reproducibility of results.
- Zero mutation of the underlying persistent storage (`data/` CSV files and SQLite database).
- Rigorous validation of system robustness against common data pipeline failures (duplicates, latency, out-of-order logs, corrupted payloads).

---

## 2. Experimental Scenarios (E1 – E10)

| Scenario ID | Name | Operational Description & Injected Condition | Expected System Behavior |
|:---|:---|:---|:---|
| **E1** | **Normal Baseline Access** | Base synthetic hospital dataset with standard access patterns and peer usage. | Serves as reference control; normal distribution of LOW/MEDIUM/HIGH risk. |
| **E2** | **Unused Privileges** | Injects 5 extra entitlements across staff users with zero recorded usage events. | Detects `UNUSED_PRIVILEGE` evidence code, raises case count to 712, increases `REVIEW` recommendation. |
| **E3** | **High Privilege Escalation** | Injects 3 high-privilege `ADMIN` entitlements on core clinical applications (`CoreEMR`). | Triggers `HIGH_PRIVILEGE` evidence code; increases `HIGH` risk cases (+3) and `REVOKE` recommendations (+3). |
| **E4** | **Inactive Users** | Marks 4 active staff accounts as `INACTIVE` while retaining granted entitlements. | Triggers `INACTIVE_USER` evidence code (+16 detections across entitlements); escalates risk to `HIGH` (+4). |
| **E5** | **Low Usage vs. Peers** | Removes usage events for the most active user to drop usage far below departmental peers. | Highlights peer deviation anomaly, triggers `UNUSED_PRIVILEGE` flags, adjusts peer median/average. |
| **E6** | **High Usage vs. Peers** | Inflates access log events tenfold for a low-activity user. | Validates peer baseline adaptation and deduplication mechanisms without crashing. |
| **E7** | **Duplicate Event Ingestion** | Injects duplicate usage events with identical `event_id` and timestamps. | DataProcessor detects duplicate events (+5), eliminates duplicates, preventing inflated peer statistics. |
| **E8** | **Delayed Log Delivery** | Injects delayed logs where `received_timestamp` exceeds `event_timestamp` by > 2 hours. | DataProcessor flags delayed events (+5); chronological sorting guarantees correct timeline analysis. |
| **E9** | **Out-of-Order Delivery** | Shuffles event arrival sequence randomly to simulate network jitter or batch log lag. | DataProcessor reconstructs chronological order by `event_timestamp` without distorting usage metrics. |
| **E10** | **Missing & Corrupt Payloads** | Injects malformed event rows (missing `user_id`, null timestamps, empty `action`). | Pipeline discards invalid records gracefully (+2 errors), isolates clean records, and executes review. |

---

## 3. Results Matrix

The table below reflects **exact measured output** generated from running `experiments/expanded_experiments.py` on the hospital dataset.

| Scenario | Total Cases | Affected Cases | Risk Low | Risk Med | Risk High | Avg Risk | Max Risk | UNUSED PRIV | HIGH PRIV | INACTIVE USER | Invalid Events | Duplicates | Delayed | Out-of-Order | System Success |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **E1** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 25 | 173 | 266 | 5,170 | Yes |
| **E2** | 712 | 278 | 434 | 229 | 49 | 20.83 | 90 | 208 | 230 | 117 | 25 | 173 | 266 | 5,170 | Yes |
| **E3** | 710 | 276 | 434 | 224 | 52 | 20.90 | 90 | 206 | 233 | 117 | 25 | 173 | 266 | 5,170 | Yes |
| **E4** | 707 | 274 | 433 | 221 | 53 | 21.15 | 90 | 203 | 230 | 133 | 25 | 173 | 266 | 5,170 | Yes |
| **E5** | 707 | 278 | 429 | 229 | 49 | 20.98 | 90 | 208 | 230 | 117 | 25 | 171 | 260 | 5,103 | Yes |
| **E6** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 25 | 203 | 266 | 5,170 | Yes |
| **E7** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 25 | 178 | 266 | 5,170 | Yes |
| **E8** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 25 | 173 | 271 | 5,170 | Yes |
| **E9** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 25 | 173 | 266 | 5,171 | Yes |
| **E10** | 707 | 273 | 434 | 224 | 49 | 20.69 | 90 | 203 | 230 | 117 | 27 | 173 | 266 | 5,170 | Yes |

---

## 4. Detailed Scenario Analysis

### 4.1 E1: Normal Access Baseline Control
- **Total Entitlement Reviews**: 707
- **Baseline Approvals Recommended**: 434 (61.4%)
- **Reviews / Revocations Recommended**: 273 (38.6%)
- Serves as the control benchmark against which all delta comparisons are evaluated.

### 4.2 E2: Unused Privileges
- **Delta vs E1**: Total cases expanded by +5 (712 total).
- **Evidence Detection**: `UNUSED_PRIVILEGE` detections increased exactly by 5 (203 → 208).
- **Reviewer Impact**: System recommended `REVIEW` for all 5 unused accounts with zero historical usage.

### 4.3 E3: High Privilege Ingestion
- **Delta vs E1**: Total cases expanded by +3 (710 total).
- **Evidence Detection**: `HIGH_PRIVILEGE` detections increased by 3 (230 → 233).
- **Risk Impact**: High risk cases increased by exactly 3 (49 → 52).
- **Action Impact**: System recommended immediate `REVOKE` for unverified administrative grants.

### 4.4 E4: Inactive Accounts
- **Delta vs E1**: 4 users marked inactive across multiple assigned entitlements.
- **Evidence Detection**: `INACTIVE_USER` detections increased from 117 to 133 (+16 entitlement cases).
- **Risk Impact**: High-risk cases elevated by 4 (49 → 53).

### 4.5 E5 & E6: Peer Usage Deviations
- **E5 (Suppressed Usage)**: Dropping activity below peer baselines increased affected cases to 278, triggering dormant entitlement warnings.
- **E6 (Inflated Usage)**: Replicated events were automatically captured by the deduplication filter (duplicates detected rose from 173 to 203, +30), preventing synthetic distortion of peer averages.

### 4.6 E7 – E10: Data Pipeline Quality & Fault Tolerance
- **E7 (Duplicates)**: Detected duplicate events increased by 5 (173 → 178).
- **E8 (Delayed Delivery)**: Detected delayed arrivals increased by 5 (266 → 271).
- **E9 (Out-of-Order Streams)**: Handled out-of-order sequence with chronological re-sorting (5,171 events).
- **E10 (Corrupt Payloads)**: Validation errors caught corrupt payloads (25 → 27), protecting downstream risk engines from runtime crashes.

---

## 5. Artifacts and Outputs

The execution outputs are stored in `experiments/results/`:
- `experiments/results/expanded_results.json`: Machine-readable structured metric tree for all scenarios.
- `experiments/results/expanded_results.csv`: Tabular matrix formatted for automated reporting and BI dashboards.

---

## 6. Reproducibility Instructions

To reproduce these experiments from the project root:

```bash
# 1. Execute the expanded experiments pipeline
python experiments/expanded_experiments.py

# 2. Run the automated test suite
pytest -q
```

All scenarios will execute deterministically, regenerate the artifacts under `experiments/results/`, and complete without modifying the source dataset.
