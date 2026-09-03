import pytest
import pandas as pd
from src.data_processor import DataProcessor

def test_invalid_event_flagging():
    events = [
        {"event_id": "EVT-OK", "user_id": "USR-1004", "application": "Billing", "action": "EXPORT", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:02"},
        {"event_id": "EVT-BAD1", "user_id": None, "application": "Billing", "action": "EXPORT", "event_timestamp": "2026-09-01 10:00:00", "received_timestamp": "2026-09-01 10:00:02"}, # Missing user_id
        {"event_id": "EVT-BAD2", "user_id": "USR-1005", "application": "Billing", "action": "EXPORT", "event_timestamp": "NOT_A_TIMESTAMP", "received_timestamp": "2026-09-01 10:00:02"} # Corrupt timestamp
    ]
    df_events = pd.DataFrame(events)

    processor = DataProcessor(df_users=pd.DataFrame(), df_entitlements=pd.DataFrame(), df_events=df_events)

    # Verification: invalid records flagged without throwing unhandled exceptions
    assert processor.quality_summary["invalid_events"] == 2
    assert len(processor.clean_events) == 1
    assert processor.clean_events.iloc[0]["event_id"] == "EVT-OK"
