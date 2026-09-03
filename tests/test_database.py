import os
import pytest
import pandas as pd
from src.database import (
    DB_PATH,
    create_database,
    create_tables,
    load_csv_data,
    retrieve_users,
    retrieve_entitlements,
    retrieve_usage_events,
    save_review_decision,
    save_review_decisions,
    retrieve_review_decisions,
    retrieve_audit_decisions
)

def test_database_creation_and_tables():
    conn = create_database()
    assert conn is not None
    conn.close()
    assert os.path.exists(DB_PATH)

    create_tables()
    conn = create_database()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "users" in tables
    assert "entitlements" in tables
    assert "usage_events" in tables
    assert "review_decisions" in tables

def test_data_loading_and_retrieval():
    load_csv_data()
    
    users_df = retrieve_users()
    assert isinstance(users_df, pd.DataFrame)
    assert not users_df.empty
    assert "user_id" in users_df.columns

    entitlements_df = retrieve_entitlements()
    assert isinstance(entitlements_df, pd.DataFrame)
    assert not entitlements_df.empty
    assert "entitlement_id" in entitlements_df.columns

    events_df = retrieve_usage_events()
    assert isinstance(events_df, pd.DataFrame)
    assert not events_df.empty
    assert "event_id" in events_df.columns

    decisions_df = retrieve_review_decisions()
    assert isinstance(decisions_df, pd.DataFrame)

def test_save_review_decision():
    sample_decision = {
        "decision_id": "TEST-DEC-001",
        "user_id": "USR-1001",
        "entitlement_id": "ENT-1001",
        "risk_score": 75,
        "recommendation": "REVOKE",
        "reviewer_decision": "REVOKE",
        "override": 0,
        "reason": "Unused high privilege",
        "reviewer": "Security Admin",
        "decision_timestamp": "2026-09-03 10:00:00"
    }

    save_review_decision(sample_decision)

    decisions = retrieve_audit_decisions()
    assert not decisions.empty
    match = decisions[decisions["decision_id"] == "TEST-DEC-001"]
    assert len(match) == 1
    assert match.iloc[0]["reviewer"] == "Security Admin"
