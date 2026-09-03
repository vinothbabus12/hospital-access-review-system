import pytest
import pandas as pd
from src.risk_engine import calculate_risk_score, evaluate_risk, get_risk_summary

def test_risk_scoring_rules_and_levels():
    # Test case 1: Score 70 (Unused +40, ADMIN +30) -> HIGH risk
    row_high = {
        "user_id": "USR-1001",
        "user_usage": 0,
        "permission": "ADMIN",
        "peer_average": 5.0,
        "status": "ACTIVE",
        "granted_date": "2020-01-01"
    }

    res_high = calculate_risk_score(row_high)
    assert res_high["risk_score"] == 70
    assert res_high["risk_level"] == "HIGH"
    assert "* Privilege unused (+40)" in res_high["evidence"]
    assert "* ADMIN permission (+30)" in res_high["evidence"]
    assert res_high["recommendation"] == "REVOKE"
    assert "High risk entitlement with zero actual usage" in res_high["recommendation_reason"]

    # Test case 2: Score 30 (ADMIN +30, active user, usage normal) -> MEDIUM risk
    row_med = {
        "user_id": "USR-1002",
        "user_usage": 10,
        "permission": "ADMIN",
        "peer_average": 10.0,
        "status": "ACTIVE",
        "granted_date": "2020-01-01"
    }

    res_med = calculate_risk_score(row_med)
    assert res_med["risk_score"] == 30
    assert res_med["risk_level"] == "MEDIUM"
    assert res_med["recommendation"] == "REVIEW"

    # Test case 3: Score 0 (READ, normal usage) -> LOW risk
    row_low = {
        "user_id": "USR-1003",
        "user_usage": 15,
        "permission": "READ",
        "peer_average": 15.0,
        "status": "ACTIVE",
        "granted_date": "2020-01-01"
    }

    res_low = calculate_risk_score(row_low)
    assert res_low["risk_score"] == 0
    assert res_low["risk_level"] == "LOW"
    assert res_low["recommendation"] == "APPROVE"

def test_evaluate_risk_dataframe():
    data = [
        {"user_id": "USR-1", "user_usage": 0, "permission": "ADMIN", "peer_average": 10.0, "status": "ACTIVE", "granted_date": "2020-01-01"},
        {"user_id": "USR-2", "user_usage": 20, "permission": "READ", "peer_average": 20.0, "status": "ACTIVE", "granted_date": "2020-01-01"}
    ]
    df = pd.DataFrame(data)
    evaluated_df = evaluate_risk(df)

    assert "risk_score" in evaluated_df.columns
    assert "risk_level" in evaluated_df.columns
    assert "recommendation" in evaluated_df.columns
    assert evaluated_df.iloc[0]["risk_level"] == "HIGH"
    assert evaluated_df.iloc[1]["risk_level"] == "LOW"

    summary = get_risk_summary(evaluated_df)
    assert summary["total_users"] == 2
    assert summary["high_risk_count"] == 1
    assert summary["unused_count"] == 1
