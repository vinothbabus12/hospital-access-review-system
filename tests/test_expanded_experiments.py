import os
import sys
import json
import hashlib
import pandas as pd
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.expanded_experiments import run_all_scenarios, _write_json, _write_csv, RESULTS_DIR
from src.database import DATA_DIR


@pytest.fixture(scope="module")
def all_results():
    """Run all expanded experiment scenarios once for the module."""
    return run_all_scenarios()


def test_all_scenarios_executed(all_results):
    """Verify that all ten expected scenarios (E1-E10) are executed and returned."""
    expected_scenarios = [f"E{i}" for i in range(1, 11)]
    for sid in expected_scenarios:
        assert sid in all_results, f"Missing scenario: {sid}"
        assert all_results[sid]["processing_success"] is True


def test_metric_structure_and_types(all_results):
    """Verify each scenario produces valid numeric metrics and expected schema."""
    required_keys = [
        "scenario_id",
        "total_cases",
        "affected_cases",
        "risk_score_stats",
        "risk_counts",
        "UNUSED_PRIVILEGE",
        "HIGH_PRIVILEGE",
        "LOW_USAGE_VS_PEERS",
        "HIGH_USAGE_VS_PEERS",
        "INACTIVE_USER",
        "recommendation_counts",
        "validation_errors",
        "duplicate_events_detected",
        "delayed_events_detected",
        "out_of_order_events_handled",
        "processing_success",
    ]
    for sid, data in all_results.items():
        for key in required_keys:
            assert key in data, f"Key '{key}' missing from scenario {sid}"

        # Total and affected cases should be non-negative integers
        assert isinstance(data["total_cases"], int) and data["total_cases"] > 0
        assert isinstance(data["affected_cases"], int) and data["affected_cases"] >= 0

        # Risk score stats
        stats = data["risk_score_stats"]
        assert "avg" in stats and "min" in stats and "max" in stats
        assert 0 <= stats["min"] <= stats["max"] <= 100
        assert 0 <= stats["avg"] <= 100


def test_risk_levels_and_recommendations(all_results):
    """Verify risk categories and system recommendations are strictly within domain values."""
    allowed_risk_levels = {"LOW", "MEDIUM", "HIGH"}
    allowed_recommendations = {"APPROVE", "REVIEW", "REVOKE", "MODIFY"}

    for sid, data in all_results.items():
        risk_counts = data["risk_counts"]
        assert set(risk_counts.keys()).issubset(allowed_risk_levels)
        assert sum(risk_counts.values()) == data["total_cases"]

        rec_counts = data["recommendation_counts"]
        assert set(rec_counts.keys()).issubset(allowed_recommendations)
        assert sum(rec_counts.values()) == data["total_cases"]


def test_anomaly_injection_and_detection(all_results):
    """Verify that injected anomalies are properly detected in their respective scenarios."""
    base = all_results["E1"]

    # E2: injected unused privileges should increase UNUSED_PRIVILEGE
    assert all_results["E2"]["UNUSED_PRIVILEGE"] > base["UNUSED_PRIVILEGE"]

    # E3: injected high privilege should increase HIGH_PRIVILEGE
    assert all_results["E3"]["HIGH_PRIVILEGE"] > base["HIGH_PRIVILEGE"]

    # E4: marked inactive users should increase INACTIVE_USER count
    assert all_results["E4"]["INACTIVE_USER"] > base["INACTIVE_USER"]

    # E7: injected duplicate events should increase duplicate_events_detected
    assert all_results["E7"]["duplicate_events_detected"] > base["duplicate_events_detected"]

    # E8: injected delayed events should increase delayed_events_detected
    assert all_results["E8"]["delayed_events_detected"] > base["delayed_events_detected"]

    # E10: injected malformed rows should increase validation_errors
    assert all_results["E10"]["validation_errors"] > base["validation_errors"]


def test_original_dataset_integrity(all_results):
    """Ensure running experiments does not modify original CSV datasets on disk."""
    for csv_file in ["users.csv", "entitlements.csv", "usage_events.csv"]:
        path = os.path.join(DATA_DIR, csv_file)
        assert os.path.exists(path), f"Base dataset file {csv_file} missing!"
        df = pd.read_csv(path)
        assert not df.empty, f"Base dataset file {csv_file} is unexpectedly empty!"


def test_file_output_generation(all_results):
    """Verify JSON and CSV writer functions produce valid, readable files."""
    json_path = _write_json(all_results)
    csv_path = _write_csv(all_results)

    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)

    with open(json_path, "r", encoding="utf-8") as jf:
        loaded_json = json.load(jf)
    assert len(loaded_json) == 10

    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == 10
    assert "scenario_id" in df_csv.columns
