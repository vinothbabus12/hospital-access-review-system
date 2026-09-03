import pytest
import pandas as pd
from src.data_processor import DataProcessor

def test_out_of_order_events_identical_statistics():
    """
    Test 3 — Out-of-order events:
    Provide events in an incorrect arrival order.
    Expected: final usage state/statistics are identical to correctly ordered events.
    """
    users = [
        {"user_id": "USR-1003", "name": "Charlie Doctor", "role": "Doctor", "staff_type": "Permanent Staff", "department": "Radiology", "status": "ACTIVE"}
    ]
    entitlements = [
        {"entitlement_id": "ENT-1003", "user_id": "USR-1003", "application": "Radiology", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"}
    ]

    # Correct chronological event list
    correct_events = [
        {"event_id": "EVT-1", "user_id": "USR-1003", "application": "Radiology", "action": "LOGIN", "event_timestamp": "2026-09-01 09:00:00", "received_timestamp": "2026-09-01 09:00:05"},
        {"event_id": "EVT-2", "user_id": "USR-1003", "application": "Radiology", "action": "VIEW_RECORD", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:05"},
        {"event_id": "EVT-3", "user_id": "USR-1003", "application": "Radiology", "action": "RUN_TEST", "event_timestamp": "2026-09-02 12:00:00", "received_timestamp": "2026-09-02 12:00:05"}
    ]

    # Out-of-order arrival events (arriving in order EVT-3, EVT-1, EVT-2)
    out_of_order_events = [
        {"event_id": "EVT-3", "user_id": "USR-1003", "application": "Radiology", "action": "RUN_TEST", "event_timestamp": "2026-09-02 12:00:00", "received_timestamp": "2026-09-02 12:00:05"},
        {"event_id": "EVT-1", "user_id": "USR-1003", "application": "Radiology", "action": "LOGIN", "event_timestamp": "2026-09-01 09:00:00", "received_timestamp": "2026-09-02 12:05:00"},
        {"event_id": "EVT-2", "user_id": "USR-1003", "application": "Radiology", "action": "VIEW_RECORD", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-02 12:10:00"}
    ]

    p_correct = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=correct_events)
    p_out_of_order = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=out_of_order_events)

    # Verification: Event sequence in clean_events is sorted identically chronologically
    sorted_ids_correct = list(p_correct.clean_events["event_id"])
    sorted_ids_out = list(p_out_of_order.clean_events["event_id"])
    assert sorted_ids_correct == ["EVT-1", "EVT-2", "EVT-3"]
    assert sorted_ids_out == ["EVT-1", "EVT-2", "EVT-3"]

    # Verification: Baseline statistics are 100% identical between in-order and out-of-order log streams
    baseline_correct = p_correct.get_peer_usage_baseline()
    baseline_out = p_out_of_order.get_peer_usage_baseline()

    assert baseline_correct.iloc[0]["user_usage"] == baseline_out.iloc[0]["user_usage"]
    assert baseline_correct.iloc[0]["peer_average"] == baseline_out.iloc[0]["peer_average"]
    assert baseline_correct.iloc[0]["last_usage_date"] == baseline_out.iloc[0]["last_usage_date"]
