import pytest
import pandas as pd
from src.baseline import run_baseline_experiment

def test_baseline_experiment_metrics():
    # Sample entitlement evaluation data
    sample_data = [
        # Case 1: Active user, unused privilege, ADMIN permission -> High risk
        {"user_id": "USR-1", "status": "ACTIVE", "user_usage": 0, "permission": "ADMIN", "peer_average": 5.0, "risk_score": 70, "recommendation": "REVOKE"},
        # Case 2: Active user, normal usage, READ permission -> Low risk
        {"user_id": "USR-2", "status": "ACTIVE", "user_usage": 10, "permission": "READ", "peer_average": 10.0, "risk_score": 0, "recommendation": "APPROVE"},
        # Case 3: Inactive user -> High risk
        {"user_id": "USR-3", "status": "INACTIVE", "user_usage": 0, "permission": "WRITE", "peer_average": 2.0, "risk_score": 60, "recommendation": "REVOKE"},
        # Case 4: Active user, unused privilege -> High risk
        {"user_id": "USR-4", "status": "ACTIVE", "user_usage": 0, "permission": "WRITE", "peer_average": 8.0, "risk_score": 40, "recommendation": "REVIEW"},
    ]
    df = pd.DataFrame(sample_data)

    results = run_baseline_experiment(df)

    assert results["total_cases"] == 4
    assert "baseline_approval_rate" in results
    assert "prototype_approval_rate" in results
    assert "baseline_blanket_approval_rate" in results
    assert "prototype_blanket_approval_rate" in results
    assert "reduction_percentage_points" in results
    assert "relative_reduction" in results

    # In Baseline, 3 active users are approved (75.0% blanket approval rate)
    assert results["baseline_blanket_approval_rate"] == 75.0
    # In Prototype, only USR-2 is approved (25.0% approval rate, 0% high-risk blanket approval rate)
    assert results["prototype_blanket_approval_rate"] == 0.0
    # Reduction in percentage points = 75.0 - 0.0 = 75.0 pp
    assert results["reduction_percentage_points"] == 75.0
    assert results["relative_reduction"] == 100.0
