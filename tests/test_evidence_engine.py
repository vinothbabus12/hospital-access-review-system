import pytest
import pandas as pd
from src.data_processor import DataProcessor
from src.evidence_engine import generate_evidence_record, evaluate_all_entitlements

def test_peer_role_baseline_calculations():
    # Setup users with different roles (Nurse vs Consultant vs Intern vs Lab Technician)
    users = [
        {"user_id": "USR-1", "name": "Nurse Alice", "role": "Nurse", "staff_type": "FULL_TIME", "department": "Emergency", "status": "ACTIVE"},
        {"user_id": "USR-2", "name": "Nurse Bob", "role": "Nurse", "staff_type": "FULL_TIME", "department": "Emergency", "status": "ACTIVE"},
        {"user_id": "USR-3", "name": "Nurse Charlie", "role": "Nurse", "staff_type": "FULL_TIME", "department": "Emergency", "status": "ACTIVE"},
        {"user_id": "USR-4", "name": "Dr. Dave", "role": "Consultant", "staff_type": "FULL_TIME", "department": "Cardiology", "status": "ACTIVE"},
    ]

    entitlements = [
        {"entitlement_id": "ENT-1", "user_id": "USR-1", "application": "EHR", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"},
        {"entitlement_id": "ENT-2", "user_id": "USR-2", "application": "EHR", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"},
        {"entitlement_id": "ENT-3", "user_id": "USR-3", "application": "EHR", "permission": "READ", "granted_date": "2024-01-01", "status": "ACTIVE"},
        {"entitlement_id": "ENT-4", "user_id": "USR-4", "application": "EHR", "permission": "ADMIN", "granted_date": "2024-01-01", "status": "ACTIVE"},
    ]

    # Events: Nurse Alice has 10 usages, Nurse Bob has 20 usages, Nurse Charlie has 0 usages
    # Nurse Peer avg = (10+20+0)/3 = 10.0, median = 10.0
    events = [
        {"event_id": f"E-1-{i}", "user_id": "USR-1", "application": "EHR", "action": "VIEW", "event_timestamp": f"2026-09-01 10:{i:02d}:00", "received_timestamp": f"2026-09-01 10:{i:02d}:01"} for i in range(10)
    ] + [
        {"event_id": f"E-2-{i}", "user_id": "USR-2", "application": "EHR", "action": "VIEW", "event_timestamp": f"2026-09-02 12:{i:02d}:00", "received_timestamp": f"2026-09-02 12:{i:02d}:01"} for i in range(20)
    ]

    processor = DataProcessor(df_users=users, df_entitlements=entitlements, df_events=events)
    baseline_df = processor.get_peer_usage_baseline()
    evaluated_df = evaluate_all_entitlements(baseline_df)

    # Check Nurse Charlie (0 usages)
    charlie_row = evaluated_df[evaluated_df["user_id"] == "USR-3"].iloc[0]
    assert charlie_row["user_usage"] == 0
    assert charlie_row["last_usage_date"] == "Never"
    assert charlie_row["peer_average"] == 10.0
    assert charlie_row["peer_median"] == 10.0
    assert charlie_row["difference_from_peer"] == -10.0
    assert "UNUSED_PRIVILEGE" in charlie_row["evidence_codes"]

    # Check Dr. Dave (Consultant, 0 usages, ADMIN permission)
    dave_row = evaluated_df[evaluated_df["user_id"] == "USR-4"].iloc[0]
    assert dave_row["role"] == "Consultant"
    assert "HIGH_PRIVILEGE" in dave_row["evidence_codes"]
    assert "UNUSED_PRIVILEGE" in dave_row["evidence_codes"]

def test_evidence_flags_and_transparency():
    sample_row = {
        "user_id": "USR-999",
        "name": "Inactive Staff",
        "role": "Lab Technician",
        "permission": "ADMIN",
        "status": "INACTIVE",
        "user_usage": 0,
        "peer_average": 15.0,
        "peer_median": 15.0,
        "last_usage_date": "Never",
        "granted_date": "2025-01-01"
    }

    record = generate_evidence_record(sample_row)

    assert "UNUSED_PRIVILEGE" in record["evidence_codes"]
    assert "HIGH_PRIVILEGE" in record["evidence_codes"]
    assert "INACTIVE_USER" in record["evidence_codes"]
    assert record["recommendation"] == "REVOKE"
    assert "Role: Lab Technician" in record["explanation"]
    assert "Peer Avg: 15.0" in record["explanation"]

    # Test LOW_USAGE_VS_PEERS when user_usage > 0 but < 20% of peer avg
    sample_low_usage = sample_row.copy()
    sample_low_usage["user_usage"] = 1
    record_low = generate_evidence_record(sample_low_usage)
    assert "LOW_USAGE_VS_PEERS" in record_low["evidence_codes"]
