# experiments/failure_recovery_test.py
"""Failure Recovery Experiment

This script injects various failure conditions into the synthetic event data and
verifies that the DataProcessor correctly detects and recovers from them.

Scenarios:
F1 – Duplicate Event Recovery
F2 – Delayed Event Recovery
F3 – Out‑of‑Order Event Recovery
F4 – Missing/Invalid Data Recovery
F5 – Combined Failure Scenario
"""

import os
import sys
import json
import pandas as pd

# Ensure the project root is on the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_generator import generate_synthetic_data, DATA_DIR
from src.database import load_csv_data_to_db, retrieve_users, retrieve_entitlements, retrieve_usage_events
from src.data_processor import DataProcessor

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def _base_data():
    """Load the baseline synthetic data."""
    users_csv = os.path.join(DATA_DIR, "users.csv")
    if not os.path.exists(users_csv):
        generate_synthetic_data()
        load_csv_data_to_db()
    else:
        load_csv_data_to_db()
    df_users = retrieve_users()
    df_ent = retrieve_entitlements()
    df_events = retrieve_usage_events()
    return df_users, df_ent, df_events

def _run_processor(df_users, df_ent, df_events):
    proc = DataProcessor(df_users, df_ent, df_events)
    # The DataProcessor exposes a quality_summary attribute (see src/data_processor.py)
    return getattr(proc, "quality_summary", {})

def F1_duplicate_event_recovery():
    df_users, df_ent, df_events = _base_data()
    dup = df_events.sample(n=5, random_state=42)
    df_events_dup = pd.concat([df_events, dup], ignore_index=True)
    summary = _run_processor(df_users, df_ent, df_events_dup)
    return {
        "scenario_id": "F1",
        "input_records": len(df_events_dup),
        "duplicate_records": 5,
        "quality_summary": summary,
    }

def F2_delayed_event_recovery():
    df_users, df_ent, df_events = _base_data()
    delayed = df_events.sample(n=5, random_state=43).copy()
    delayed["received_timestamp"] = (
        pd.to_datetime(delayed["event_timestamp"]) + pd.Timedelta(hours=2)
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    df_events_mod = pd.concat([df_events, delayed], ignore_index=True)
    summary = _run_processor(df_users, df_ent, df_events_mod)
    return {
        "scenario_id": "F2",
        "input_records": len(df_events_mod),
        "delayed_records": 5,
        "quality_summary": summary,
    }

def F3_out_of_order_event_recovery():
    df_users, df_ent, df_events = _base_data()
    shuffled = df_events.sample(frac=1, random_state=44).reset_index(drop=True)
    summary = _run_processor(df_users, df_ent, shuffled)
    return {
        "scenario_id": "F3",
        "input_records": len(shuffled),
        "out_of_order_records": len(shuffled) - summary.get("valid_events", 0),
        "quality_summary": summary,
    }

def F4_missing_invalid_data_recovery():
    df_users, df_ent, df_events = _base_data()
    invalid = pd.DataFrame([
        {"event_id": 999001, "user_id": None, "application": "AppX", "action": "login", "event_timestamp": "bad_date", "received_timestamp": "bad_date"},
        {"event_id": 999002, "user_id": "U123", "application": "", "action": "", "event_timestamp": None, "received_timestamp": None},
    ])
    df_events_mod = pd.concat([df_events, invalid], ignore_index=True)
    summary = _run_processor(df_users, df_ent, df_events_mod)
    return {
        "scenario_id": "F4",
        "input_records": len(df_events_mod),
        "invalid_records": 2,
        "quality_summary": summary,
    }

def F5_combined_failure_scenario():
    df_users, df_ent, df_events = _base_data()
    dup = df_events.sample(n=3, random_state=45)
    delayed = df_events.sample(n=3, random_state=46).copy()
    delayed["received_timestamp"] = (
        pd.to_datetime(delayed["event_timestamp"]) + pd.Timedelta(hours=2)
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    combined = pd.concat([df_events, dup, delayed], ignore_index=True)
    summary = _run_processor(df_users, df_ent, combined)
    return {
        "scenario_id": "F5",
        "input_records": len(combined),
        "duplicate_records": 3,
        "delayed_records": 3,
        "quality_summary": summary,
    }

def run_all():
    results = {
        "F1": F1_duplicate_event_recovery(),
        "F2": F2_delayed_event_recovery(),
        "F3": F3_out_of_order_event_recovery(),
        "F4": F4_missing_invalid_data_recovery(),
        "F5": F5_combined_failure_scenario(),
    }
    # Write JSON
    json_path = os.path.join(RESULTS_DIR, "failure_recovery_results.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2)
    # Write CSV (flattened)
    rows = []
    for sid, data in results.items():
        q = data["quality_summary"]
        rows.append({
            "scenario_id": sid,
            "total_events": q.get("total_events"),
            "duplicate_events": q.get("duplicate_events"),
            "invalid_events": q.get("invalid_events"),
            "delayed_events": q.get("delayed_events"),
            "out_of_order_events": q.get("out_of_order_events"),
            "valid_events": q.get("valid_events"),
        })
    df = pd.DataFrame(rows)
    csv_path = os.path.join(RESULTS_DIR, "failure_recovery_results.csv")
    df.to_csv(csv_path, index=False)
    return results

if __name__ == "__main__":
    run_all()
    print("Failure recovery experiment completed. Results written to:", RESULTS_DIR)
