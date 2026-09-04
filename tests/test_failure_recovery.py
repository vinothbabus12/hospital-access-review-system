import pandas as pd
import pytest
from src.data_processor import DataProcessor

def make_events_df():
    """Create a DataFrame containing representative failure scenarios.

    The dataset includes:
    * A valid baseline event.
    * A duplicate of the baseline event (same ``event_id``).
    * A delayed event where the received timestamp is >1 hour after the event timestamp.
    * An out‑of‑order event (event timestamp later than others but received earlier).
    * An invalid event missing a required ``user_id``.
    """
    data = [
        {
            "event_id": "e1",
            "user_id": "u1",
            "application": "app1",
            "action": "login",
            "event_timestamp": "2023-01-01T10:00:00Z",
            "received_timestamp": "2023-01-01T10:00:05Z",
        },
        # Duplicate of e1
        {
            "event_id": "e1",
            "user_id": "u1",
            "application": "app1",
            "action": "login",
            "event_timestamp": "2023-01-01T10:00:00Z",
            "received_timestamp": "2023-01-01T10:00:05Z",
        },
        # Delayed event (>1 hour delay)
        {
            "event_id": "e2",
            "user_id": "u2",
            "application": "app2",
            "action": "logout",
            "event_timestamp": "2023-01-01T08:00:00Z",
            "received_timestamp": "2023-01-01T10:30:00Z",
        },
        # Out‑of‑order event (received before its event time)
        {
            "event_id": "e3",
            "user_id": "u3",
            "application": "app1",
            "action": "access",
            "event_timestamp": "2023-01-01T12:00:00Z",
            "received_timestamp": "2023-01-01T11:55:00Z",
        },
        # Invalid event (missing user_id)
        {
            "event_id": "e4",
            "user_id": None,
            "application": "app2",
            "action": "modify",
            "event_timestamp": "2023-01-01T09:00:00Z",
            "received_timestamp": "2023-01-01T09:00:10Z",
        },
    ]
    return pd.DataFrame(data)

def test_failure_recovery_counts():
    """Verify that ``DataProcessor`` correctly flags each failure type.

    The ``DataProcessor`` is instantiated with minimal user/entitlement data –
    the focus is on the event‑processing logic.
    """
    events_df = make_events_df()

    # Minimal user / entitlement tables – required by the constructor but not exercised here.
    dummy_users = pd.DataFrame([
        {
            "user_id": "u1",
            "name": "User One",
            "role": "staff",
            "staff_type": "full",
            "department": "IT",
            "status": "ACTIVE",
        }
    ])
    dummy_entitlements = pd.DataFrame([
        {"user_id": "u1", "application": "app1", "status": "ACTIVE"}
    ])

    processor = DataProcessor(df_users=dummy_users, df_entitlements=dummy_entitlements, df_events=events_df)
    report = processor.get_quality_report()

    # Total events supplied to the processor
    assert report["total_events"] == 5
    # One duplicate (second e1) should be counted
    assert report["duplicate_events"] == 1
    # One delayed event (e2) > 1 hour
    assert report["delayed_events"] == 1
    # One invalid record (e4) – missing user_id
    assert report["invalid_events"] == 1
    # Out‑of‑order detection – at least the e3 case should be flagged
    assert report["out_of_order_events"] >= 1
    # Valid events are total minus duplicates and invalid records
    expected_valid = report["total_events"] - report["duplicate_events"] - report["invalid_events"]
    assert report["valid_events"] == expected_valid

if __name__ == "__main__":
    pytest.main([__file__])
