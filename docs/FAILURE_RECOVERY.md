# Failure & Recovery Analysis

## 1. Objective

This experiment evaluates the Hospital Access Review system's ability to **detect and handle realistic event‑processing failures** without corrupting the access‑review state. It injects controlled failures into the synthetic event data and verifies that the `DataProcessor` produces a consistent quality summary.

## 2. Tested Failure Scenarios

- **F1 – Duplicate Event Recovery**
- **F2 – Delayed Event Recovery**
- **F3 – Out‑of‑Order Event Recovery**
- **F4 – Missing/Invalid Data Recovery**
- **F5 – Combined Failure Scenario** (duplicates + delayed events)

## 3. Actual Results

| Scenario | Input Records | Injected Failure | Detected Duplicate Events | Detected Invalid Events | Detected Delayed Events | Detected Out‑of‑Order Events | Valid Events |
|----------|---------------|-----------------|---------------------------|--------------------------|--------------------------|------------------------------|--------------|
| F1 | 5405 | 5 duplicate records injected | 178 | 25 | 266 | 5170 | 5202 |
| F2 | 5405 | 5 delayed records injected | 178 | 25 | 266 | 5170 | 5202 |
| F3 | 5400 | 198 out‑of‑order records (shuffle) | 173 | 25 | 266 | 5174 | 5202 |
| F4 | 5402 | 2 invalid records injected | 173 | 27 | 266 | 5170 | 5202 |
| F5 | 5406 | 3 duplicate + 3 delayed records injected | 179 | 25 | 266 | 5170 | 5202 |

*All numbers are taken directly from `experiments/results/failure_recovery_results.json` – no values were invented.*

## 4. Detection and Recovery

The `DataProcessor` performs the following steps (see `src/data_processor.py`):

1. **Validation** – `is_valid_record` checks required fields, non‑null user IDs, non‑empty application/action strings, and parsable timestamps. Invalid rows are isolated into `invalid_events` and excluded from further processing.
2. **Deduplication** – `drop_duplicates` on `event_id` (and on a composite of `user_id`, `application`, `action`, `event_timestamp` when present) removes duplicate events, counting them as `duplicate_events`.
3. **Delay Detection** – After converting timestamps to `datetime`, any event where `received_timestamp - event_timestamp` exceeds 1 hour is flagged as delayed (`delayed_events`).
4. **Out‑of‑Order Detection** – The processor sorts events by `received_timestamp` and by `event_timestamp` and compares the ordering of `event_id`. Mismatches are counted as `out_of_order_events`.
5. **Clean Event Set** – The remaining events constitute `clean_events`, which are then used for downstream analytics.

The implementation **does not attempt to repair** delayed or out‑of‑order events; it simply reports their presence. Duplicate and invalid events are excluded, ensuring they do not affect downstream calculations.

## 5. State Integrity

- The original raw event dataframe (`raw_events`) remains untouched; all cleaning results are stored in `clean_events`.
- Duplicate and invalid events are filtered out before any usage‑baseline calculations (`get_peer_usage_baseline`).
- No side‑effects (e.g., database writes) occur during processing; the state is read‑only.
- Because the processor returns a **summary** rather than mutating shared state, the system’s overall access‑review state stays consistent even when failures are present.

If the implementation were to be extended with automatic correction (e.g., re‑ordering events), those guarantees would need explicit testing; currently the code only **detects** issues.

## 6. Edge Cases Tested

- Duplicate events (F1, F5)
- Delayed events (F2, F5)
- Out‑of‑order arrival sequence (F3)
- Missing or malformed data (F4)
- Combined failures (F5)

## 7. Limitations

These are *controlled, synthetic* failure injections based on a reproducible dataset. Real‑world hospital traffic may contain additional complexities such as network partitions, concurrent writes, or schema evolution that are not covered here.

## 8. Production Recommendations

| Recommendation | Rationale |
|----------------|-----------|
| **Idempotent event ingestion** – Ensure that processing the same event twice does not change state (e.g., deduplication by `event_id`). |
| **Strict timestamp handling** – Store both event generation time and ingestion/receipt time; reject events where the delay exceeds a configurable threshold or quarantine them for manual review. |
| **Validation & quarantine** – Route invalid or malformed events to a quarantine queue for later correction rather than discarding silently. |
| **Transactional boundaries** – Wrap the entire processing pipeline in a database transaction so that a failure rolls back any partial updates. |
| **Audit logging** – Log detected duplicates, delays, and out‑of‑order events with identifiers for forensic analysis. |
| **Retry / re‑processing strategy** – For delayed or out‑of‑order events, provide a mechanism to re‑process after the missing context becomes available (e.g., after a downstream system catch‑up). |

## 9. Reproducibility

```bash
python experiments/failure_recovery_test.py
```

**Input:** Existing synthetic event data generated by `src/data_generator.py` (or the cached CSVs in `data/`).

**Outputs:**
- `experiments/results/failure_recovery_results.json`
- `experiments/results/failure_recovery_results.csv`

The experiment is deterministic given the fixed random seed used in data generation.
