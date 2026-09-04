# experiments/scenarios.py
"""Scenario definitions for expanded experiments.
Each function receives fresh copies of the synthetic data, injects a specific
condition, runs the evidence/evaluation pipeline, and returns a dictionary of
metrics.
"""

import os
import sys
import random
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_processor import DataProcessor
from src.evidence_engine import evaluate_all_entitlements

# Fixed random seed for reproducibility
_RANDOM_SEED = 42
random.seed(_RANDOM_SEED)


def _load_base_data():
    """Load the original synthetic data using the baseline helpers.
    Returns a tuple of (users_df, entitlements_df, events_df).
    """
    from experiments.baseline_experiment import load_and_process_data
    users_df, entitlements_df, events_df, _, _ = load_and_process_data()
    return users_df.copy(), entitlements_df.copy(), events_df.copy()


def _run_pipeline(df_users: pd.DataFrame, df_ent: pd.DataFrame, df_events: pd.DataFrame):
    """Run DataProcessor and evidence evaluation, returning the processor and
    the evaluated DataFrame.
    """
    processor = DataProcessor(df_users, df_ent, df_events)
    df_baseline = processor.get_peer_usage_baseline()
    df_evaluated = evaluate_all_entitlements(df_baseline)
    return processor, df_evaluated


def _compute_metrics(scenario_id: str, processor: DataProcessor, df_evaluated: pd.DataFrame) -> dict:
    """Calculate the required numeric metrics for a scenario.
    The returned dict is JSON‑serialisable.
    """
    total_cases = len(df_evaluated)
    affected_cases = int((df_evaluated["recommendation"] != "APPROVE").sum())

    # Risk score statistics
    risk_scores = df_evaluated["risk_score"].astype(float)
    risk_score_stats = {
        "avg": round(risk_scores.mean(), 2) if total_cases else 0,
        "min": int(risk_scores.min()) if total_cases else 0,
        "max": int(risk_scores.max()) if total_cases else 0,
    }

    # Risk level counts
    risk_counts = df_evaluated["risk_level"].value_counts().to_dict()
    for level in ["LOW", "MEDIUM", "HIGH"]:
        risk_counts.setdefault(level, 0)

    # Evidence code counts helper
    def _code_count(code: str) -> int:
        return int(df_evaluated["evidence_codes"].apply(lambda lst: code in lst).sum())

    evidence_counts = {
        "UNUSED_PRIVILEGE": _code_count("UNUSED_PRIVILEGE"),
        "HIGH_PRIVILEGE": _code_count("HIGH_PRIVILEGE"),
        "LOW_USAGE_VS_PEERS": _code_count("LOW_USAGE_VS_PEERS"),
        "HIGH_USAGE_VS_PEERS": _code_count("HIGH_USAGE_VS_PEERS"),
        "INACTIVE_USER": _code_count("INACTIVE_USER"),
    }

    # Recommendation counts
    rec_counts = df_evaluated["recommendation"].value_counts().to_dict()
    for rec in ["APPROVE", "REVIEW", "REVOKE", "MODIFY"]:
        rec_counts.setdefault(rec, 0)

    # Data quality summary from processor
    quality = processor.get_quality_report()
    validation_errors = quality.get("invalid_events", 0)
    duplicate_events = quality.get("duplicate_events", 0)
    delayed_events = quality.get("delayed_events", 0)
    out_of_order = quality.get("out_of_order_events", 0)

    return {
        "scenario_id": scenario_id,
        "total_cases": total_cases,
        "affected_cases": affected_cases,
        "risk_score_stats": risk_score_stats,
        "risk_counts": risk_counts,
        **evidence_counts,
        "recommendation_counts": rec_counts,
        "validation_errors": validation_errors,
        "duplicate_events_detected": duplicate_events,
        "delayed_events_detected": delayed_events,
        "out_of_order_events_handled": out_of_order,
        "processing_success": True,
    }

# -----------------------------------------------------------------------------
# Scenario implementations
# -----------------------------------------------------------------------------

def E1_normal_access_pattern():
    """E1 – Normal access pattern (baseline data unchanged)."""
    users, ent, events = _load_base_data()
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E1", processor, evaluated)


def E2_unused_privileges():
    """E2 – Add entitlements that have no corresponding usage events."""
    users, ent, events = _load_base_data()
    sample_users = users.sample(n=5, random_state=_RANDOM_SEED)
    extra = []
    for i, (_, row) in enumerate(sample_users.iterrows()):
        extra.append({
            "entitlement_id": f"ENT_EXTRA_UNUSED_{i+1}",
            "user_id": row["user_id"],
            "application": "DummyApp",
            "permission": "READ_ONLY",
            "granted_date": "2023-01-01",
            "status": row.get("status", "ACTIVE"),
        })
    ent_extra = pd.DataFrame(extra)
    ent = pd.concat([ent, ent_extra], ignore_index=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E2", processor, evaluated)


def E3_high_privilege():
    """E3 – Introduce high‑privilege (ADMIN) entitlements."""
    users, ent, events = _load_base_data()
    sample_users = users.sample(n=3, random_state=_RANDOM_SEED)
    extra = []
    for i, (_, row) in enumerate(sample_users.iterrows()):
        extra.append({
            "entitlement_id": f"ENT_EXTRA_ADMIN_{i+1}",
            "user_id": row["user_id"],
            "application": "CoreEMR",
            "permission": "ADMIN",
            "granted_date": "2023-06-15",
            "status": row.get("status", "ACTIVE"),
        })
    ent_extra = pd.DataFrame(extra)
    ent = pd.concat([ent, ent_extra], ignore_index=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E3", processor, evaluated)


def E4_inactive_users():
    """E4 – Mark some active users as INACTIVE while keeping entitlements."""
    users, ent, events = _load_base_data()
    inactive_ids = users.sample(n=4, random_state=_RANDOM_SEED)["user_id"]
    users.loc[users["user_id"].isin(inactive_ids), "status"] = "INACTIVE"
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E4", processor, evaluated)


def E5_low_usage_vs_peers():
    """E5 – Reduce usage for a user far below its peers."""
    users, ent, events = _load_base_data()
    if events.empty:
        return _compute_metrics("E5", DataProcessor(users, ent, events), pd.DataFrame())
    usage_counts = events["user_id"].value_counts()
    target_user = usage_counts.idxmax()
    events = events[events["user_id"] != target_user]
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E5", processor, evaluated)


def E6_high_usage_vs_peers():
    """E6 – Inflate usage for a user far above its peers."""
    users, ent, events = _load_base_data()
    if events.empty:
        return _compute_metrics("E6", DataProcessor(users, ent, events), pd.DataFrame())
    usage_counts = events["user_id"].value_counts()
    low_user = usage_counts.idxmin()
    low_user_events = events[events["user_id"] == low_user]
    duplicated = pd.concat([low_user_events] * 10, ignore_index=True)
    events = pd.concat([events, duplicated], ignore_index=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E6", processor, evaluated)


def E7_duplicate_events():
    """E7 – Inject exact duplicate usage events and verify detection."""
    users, ent, events = _load_base_data()
    dup_subset = events.sample(n=5, random_state=_RANDOM_SEED)
    events = pd.concat([events, dup_subset], ignore_index=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E7", processor, evaluated)


def E8_delayed_events():
    """E8 – Make some events delayed (>1 hour between event and received timestamps)."""
    users, ent, events = _load_base_data()
    if events.empty:
        return _compute_metrics("E8", DataProcessor(users, ent, events), pd.DataFrame())
    events = events.copy()
    events["event_timestamp"] = pd.to_datetime(events["event_timestamp"], errors="coerce")
    events["received_timestamp"] = pd.to_datetime(events["received_timestamp"], errors="coerce")
    delay_idx = events.sample(n=5, random_state=_RANDOM_SEED).index
    events.loc[delay_idx, "received_timestamp"] = events.loc[delay_idx, "event_timestamp"] + pd.Timedelta(hours=2)
    events["event_timestamp"] = events["event_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    events["received_timestamp"] = events["received_timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E8", processor, evaluated)


def E9_out_of_order_events():
    """E9 – Shuffle event order to create out‑of‑order arrivals."""
    users, ent, events = _load_base_data()
    events = events.sample(frac=1, random_state=_RANDOM_SEED).reset_index(drop=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E9", processor, evaluated)


def E10_missing_invalid_data():
    """E10 – Insert rows with missing fields or malformed timestamps."""
    users, ent, events = _load_base_data()
    malformed = pd.DataFrame([
        {"event_id": None, "user_id": None, "application": "AppX", "action": "login", "event_timestamp": "baddate", "received_timestamp": "alsobad"},
        {"event_id": 999999, "user_id": "U123", "application": "", "action": "", "event_timestamp": None, "received_timestamp": None},
    ])
    events = pd.concat([events, malformed], ignore_index=True)
    processor, evaluated = _run_pipeline(users, ent, events)
    return _compute_metrics("E10", processor, evaluated)

# Export a list of scenario callables for the runner.
SCENARIOS = [
    E1_normal_access_pattern,
    E2_unused_privileges,
    E3_high_privilege,
    E4_inactive_users,
    E5_low_usage_vs_peers,
    E6_high_usage_vs_peers,
    E7_duplicate_events,
    E8_delayed_events,
    E9_out_of_order_events,
    E10_missing_invalid_data,
]
