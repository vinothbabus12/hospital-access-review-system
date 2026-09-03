import pytest
import pandas as pd
from src.data_processor import DataProcessor

def test_duplicate_event_counted_only_once():
    """
    Test 1 — Duplicate event:
    Insert the same event twice.
    Expected: usage is counted only once.
    """
    users = [
        {"user_id": "USR-1001", "name": "Alice Smith", "role": "Pharmacist", "staff_type": "Permanent Staff", "department": "Pharmacy", "status": "ACTIVE"}
    ]
    entitlements = [
        {"entitlement_id": "ENT-1001", "user_id": "USR-1001", "application": "Pharmacy", "permission": "READ_WRITE", "granted_date": "2024-01-01", "status": "ACTIVE"}
    ]
    events = [
        {"event_id": "EVT-1", "user_id": "USR-1001", "application": "Pharmacy", "action": "LOGIN", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:05"},
        {"event_id": "EVT-1", "user_id": "USR-1001", "application": "Pharmacy", "action": "LOGIN", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:15"}, # Duplicate event_id
    ]

    processor = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=events)
    baseline_df = processor.get_peer_usage_baseline()

    # Verification: duplicate event is detected and removed
    assert processor.quality_summary["duplicate_events"] == 1
    assert len(processor.clean_events) == 1
    assert processor.clean_events.iloc[0]["event_id"] == "EVT-1"

    # Verification: usage count is counted only once (1, not 2)
    assert not baseline_df.empty
    user_usage = baseline_df.iloc[0]["user_usage"]
    assert user_usage == 1
