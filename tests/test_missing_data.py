import pytest
import pandas as pd
from src.data_processor import DataProcessor

def test_missing_and_invalid_data_handling():
    """
    Test 4 — Missing/invalid data:
    Provide missing user/application/timestamp fields.
    Expected: invalid records are flagged and the application continues without crashing.
    """
    users = [
        {"user_id": "USR-1004", "name": "Dave Technician", "role": "Lab Technician", "staff_type": "Permanent Staff", "department": "Laboratory", "status": "ACTIVE"}
    ]
    entitlements = [
        {"entitlement_id": "ENT-1004", "user_id": "USR-1004", "application": "Billing", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"}
    ]

    events = [
        # Valid event
        {"event_id": "EVT-OK", "user_id": "USR-1004", "application": "Billing", "action": "EXPORT", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:02"},
        # Corrupt 1: Missing user_id
        {"event_id": "EVT-BAD1", "user_id": None, "application": "Billing", "action": "EXPORT", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:02"},
        # Corrupt 2: Missing application
        {"event_id": "EVT-BAD2", "user_id": "USR-1004", "application": None, "action": "EXPORT", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:02"},
        # Corrupt 3: Invalid timestamp format
        {"event_id": "EVT-BAD3", "user_id": "USR-1004", "application": "Billing", "action": "EXPORT", "event_timestamp": "NOT_A_TIMESTAMP", "received_timestamp": "2026-09-01 10:00:02"}
    ]

    df_events = pd.DataFrame(events)

    # Verification: Processor executes without throwing an unhandled exception or crashing
    processor = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=df_events)

    # Verification: Invalid records flagged in quality summary and invalid_events DataFrame
    assert processor.quality_summary["invalid_events"] == 3
    assert len(processor.invalid_events) == 3
    assert len(processor.clean_events) == 1
    assert processor.clean_events.iloc[0]["event_id"] == "EVT-OK"

    # Verification: Application continues cleanly and computes baseline metrics for valid records
    baseline_df = processor.get_peer_usage_baseline()
    assert not baseline_df.empty
    assert baseline_df.iloc[0]["user_usage"] == 1
