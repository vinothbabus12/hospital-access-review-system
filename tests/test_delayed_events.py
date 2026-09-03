import pytest
import pandas as pd
from src.data_processor import DataProcessor

def test_delayed_event_calculated_by_event_timestamp():
    """
    Test 2 — Delayed event:
    Create an event where received_timestamp is later than event_timestamp.
    Expected: usage is calculated according to event_timestamp.
    """
    users = [
        {"user_id": "USR-1002", "name": "Bob Nurse", "role": "Nurse", "staff_type": "Permanent Staff", "department": "Emergency", "status": "ACTIVE"}
    ]
    entitlements = [
        {"entitlement_id": "ENT-1002", "user_id": "USR-1002", "application": "Patient Records", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"}
    ]
    events = [
        {
            "event_id": "EVT-100",
            "user_id": "USR-1002",
            "application": "Patient Records",
            "action": "VIEW_RECORD",
            "event_timestamp": "2026-09-01 08:00:00",
            "received_timestamp": "2026-09-03 14:00:00" # 54 hours delayed
        }
    ]

    processor = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=events)
    baseline_df = processor.get_peer_usage_baseline()

    # Verification: delayed event identified correctly
    assert processor.quality_summary["delayed_events"] == 1
    assert len(processor.clean_events) == 1

    # Verification: event_dt is preserved based on event_timestamp (2026-09-01 08:00:00)
    processed_evt = processor.clean_events.iloc[0]
    assert str(processed_evt["event_dt"]) == "2026-09-01 08:00:00"

    # Verification: last_usage_date calculation uses event_timestamp
    assert not baseline_df.empty
    last_used = baseline_df.iloc[0]["last_usage_date"]
    assert str(last_used) == "2026-09-01 08:00:00"
