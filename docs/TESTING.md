# Testing Documentation & Failure / Edge-Case Report

This document details the automated test suite implemented using `pytest`, covering failure modes, edge cases, expected outcomes, and actual execution results.

---

## 🧪 Test Suite Summary

- **Testing Framework:** Pytest (`9.1.1`)
- **Total Test Files:** 8 test modules
- **Total Test Cases:** 13 unit tests
- **Overall Execution Result:** **13 Passed, 0 Failed, 0 Skipped (1.91s execution time)**

---

## 📋 Failure & Edge-Case Test Documentation

### 1. Duplicate Event Test (`tests/test_duplicates.py`)
- **Test Objective:** Verify that inserting duplicate event logs (`event_id` or identical payload) does not cause double-counting of user usage statistics.
- **Test Setup:** Ingest 2 identical usage events (`EVT-1`) for user `USR-1001` on application `Pharmacy`.
- **Expected Result:**
  - Duplicate event detected (`duplicate_events == 1`).
  - `clean_events` contains exactly 1 clean event.
  - User usage count in peer baseline is calculated as `1` (not 2).
- **Actual Result:** **PASSED** (`test_duplicate_event_counted_only_once`)
  - Duplicate event was successfully flagged and dropped. `user_usage` calculated accurately as `1`.

---

### 2. Delayed Event Test (`tests/test_delayed_events.py`)
- **Test Objective:** Verify that events arriving with a significant delay (`received_timestamp` > 1 hour after `event_timestamp`) are processed according to `event_timestamp`.
- **Test Setup:** Ingest an event (`EVT-100`) occurring on `2026-09-01 08:00:00` but received on `2026-09-03 14:00:00` (54 hours delayed).
- **Expected Result:**
  - Delayed event detected (`delayed_events == 1`).
  - Event retained in `clean_events` with `event_timestamp` (`2026-09-01 08:00:00`).
  - `last_usage_date` calculation reflects event occurrence date, not arrival date.
- **Actual Result:** **PASSED** (`test_delayed_event_calculated_by_event_timestamp`)
  - Delayed event flagged; timestamp correctly preserved for chronological usage calculation.

---

### 3. Out-of-Order Event Test (`tests/test_out_of_order.py`)
- **Test Objective:** Verify that events arriving out of chronological order are sorted by `event_timestamp` such that usage statistics remain identical to in-order arrival streams.
- **Test Setup:** Ingest events in arrival order `EVT-3` (Sep 2), `EVT-1` (Sep 1 09:00), `EVT-2` (Sep 1 10:00). Compare against in-order stream `EVT-1`, `EVT-2`, `EVT-3`.
- **Expected Result:**
  - Events re-ordered chronologically in `clean_events` (`["EVT-1", "EVT-2", "EVT-3"]`).
  - Final usage statistics and peer baseline metrics are 100% identical between in-order and out-of-order streams.
- **Actual Result:** **PASSED** (`test_out_of_order_events_identical_statistics`)
  - Chronological re-ordering succeeded; computed usage baselines matched perfectly.

---

### 4. Missing / Invalid Data Test (`tests/test_missing_data.py` & `tests/test_data_validation.py`)
- **Test Objective:** Verify that corrupt log entries (missing `user_id`, missing `application`, unparseable timestamp strings) are flagged into `invalid_events` without throwing unhandled exceptions or crashing the pipeline.
- **Test Setup:** Ingest 1 valid event (`EVT-OK`) alongside 3 corrupt events (`EVT-BAD1` with `user_id=None`, `EVT-BAD2` with `application=None`, `EVT-BAD3` with `event_timestamp="NOT_A_TIMESTAMP"`).
- **Expected Result:**
  - Corrupt records flagged (`invalid_events == 3`).
  - Valid records processed into `clean_events` (`clean_events` length == 1).
  - Pipeline completes cleanly without throwing exceptions.
- **Actual Result:** **PASSED** (`test_missing_and_invalid_data_handling`)
  - All corrupt records safely isolated; valid records processed cleanly.

---

## 📊 Complete Pytest Execution Output

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Vinothbabu\OneDrive\Documents\New folder\hospital-access-review
collected 13 items

tests/test_baseline.py::test_baseline_experiment_metrics PASSED          [  7%]
tests/test_data_validation.py::test_invalid_event_flagging PASSED        [ 15%]
tests/test_database.py::test_database_creation_and_tables PASSED         [ 23%]
tests/test_database.py::test_data_loading_and_retrieval PASSED           [ 30%]
tests/test_database.py::test_save_review_decision PASSED                 [ 38%]
tests/test_delayed_events.py::test_delayed_event_calculated_by_event_timestamp PASSED [ 46%]
tests/test_duplicates.py::test_duplicate_event_counted_only_once PASSED  [ 53%]
tests/test_evidence_engine.py::test_peer_role_baseline_calculations PASSED [ 61%]
tests/test_evidence_engine.py::test_evidence_flags_and_transparency PASSED [ 69%]
tests/test_missing_data.py::test_missing_and_invalid_data_handling PASSED [ 76%]
tests/test_out_of_order.py::test_out_of_order_events_identical_statistics PASSED [ 84%]
tests/test_risk_engine.py::test_risk_scoring_rules_and_levels PASSED     [ 92%]
tests/test_risk_engine.py::test_evaluate_risk_dataframe PASSED           [100%]

============================= 13 passed in 1.91s ==============================
```
