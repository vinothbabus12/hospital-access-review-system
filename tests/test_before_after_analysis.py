# tests/test_before_after_analysis.py
"""Unit and integration tests for the Before vs After Analysis module."""

import os
import sys
import json
import hashlib
import pandas as pd
import pytest
import plotly.graph_objects as go

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.before_after_analysis import (
    load_experiment_inputs,
    calculate_before_after_metrics,
    create_approval_rate_chart,
    create_decision_distribution_chart,
    create_risk_distribution_chart,
    create_scenario_comparison_chart,
    save_before_after_results,
    RESULTS_DIR
)


def _file_hash(filepath):
    """Utility to compute SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_json_results_are_read_correctly():
    """Verify that source JSON experiment result files are read accurately."""
    inputs = load_experiment_inputs()
    assert "baseline" in inputs
    assert "expanded" in inputs
    assert isinstance(inputs["baseline"], dict)
    assert isinstance(inputs["expanded"], dict)
    assert len(inputs["baseline"]) > 0
    assert "E1" in inputs["expanded"]


def test_calculate_before_after_metrics_presence_and_types():
    """Verify that all 17 required metrics are present, correctly typed, and mathematically sound."""
    inputs = load_experiment_inputs()
    metrics = calculate_before_after_metrics(inputs)

    expected_keys = [
        "total_cases",
        "baseline_approvals",
        "prototype_approvals",
        "prototype_revocations",
        "prototype_modifications",
        "prototype_review_override_decisions",
        "baseline_approval_rate",
        "prototype_approval_rate",
        "approval_rate_reduction_percentage_points",
        "relative_approval_rate_reduction",
        "high_risk_cases",
        "medium_risk_cases",
        "low_risk_cases",
        "unused_privilege_cases",
        "high_privilege_cases",
        "low_usage_vs_peer_cases",
        "inactive_user_cases",
    ]

    for key in expected_keys:
        assert key in metrics, f"Missing required metric: {key}"

    # Value sanity
    assert metrics["total_cases"] > 0
    assert metrics["baseline_approvals"] > 0
    assert metrics["prototype_approvals"] > 0
    assert 0 <= metrics["baseline_approval_rate"] <= 100
    assert 0 <= metrics["prototype_approval_rate"] <= 100

    # Test exact formula implementations
    expected_pp = round(metrics["baseline_approval_rate"] - metrics["prototype_approval_rate"], 1)
    assert metrics["approval_rate_reduction_percentage_points"] == expected_pp

    expected_rel = round(
        ((metrics["baseline_approval_rate"] - metrics["prototype_approval_rate"]) / metrics["baseline_approval_rate"]) * 100.0,
        1
    )
    assert metrics["relative_approval_rate_reduction"] == expected_rel


def test_percentage_calculations_handle_zero_safely():
    """Verify that zero division does not crash when baseline approval rate is 0."""
    empty_inputs = {
        "baseline": {"total_cases": 0, "baseline_approvals": 0, "baseline_approval_rate": 0.0, "prototype_approval_rate": 0.0},
        "expanded": {},
        "case_details": pd.DataFrame(),
        "review_decisions": pd.DataFrame()
    }
    metrics = calculate_before_after_metrics(empty_inputs)
    assert metrics["relative_approval_rate_reduction"] == 0.0
    assert metrics["approval_rate_reduction_percentage_points"] == 0.0


def test_source_experiment_results_are_not_modified():
    """Verify that analyzing results leaves the source JSON files completely unchanged."""
    baseline_path = os.path.join(RESULTS_DIR, "baseline_results.json")
    expanded_path = os.path.join(RESULTS_DIR, "expanded_results.json")

    hash_baseline_before = _file_hash(baseline_path)
    hash_expanded_before = _file_hash(expanded_path)

    # Run full analysis
    inputs = load_experiment_inputs()
    _ = calculate_before_after_metrics(inputs)

    hash_baseline_after = _file_hash(baseline_path)
    hash_expanded_after = _file_hash(expanded_path)

    assert hash_baseline_before == hash_baseline_after, "baseline_results.json was modified!"
    assert hash_expanded_before == hash_expanded_after, "expanded_results.json was modified!"


def test_charts_can_be_generated_without_crashing():
    """Verify that all 4 required Plotly figures are generated cleanly without runtime errors."""
    inputs = load_experiment_inputs()
    metrics = calculate_before_after_metrics(inputs)

    # 1. Baseline vs Prototype Approval Rate
    fig1 = create_approval_rate_chart(metrics)
    assert isinstance(fig1, go.Figure)

    # 2. Prototype Decision Distribution
    fig2 = create_decision_distribution_chart(metrics)
    assert isinstance(fig2, go.Figure)

    # 3. Risk Distribution
    fig3 = create_risk_distribution_chart(metrics)
    assert isinstance(fig3, go.Figure)

    # 4. Expanded Experiment Scenario Comparison
    fig4 = create_scenario_comparison_chart(inputs.get("expanded", {}))
    assert isinstance(fig4, go.Figure)


def test_results_reproducibility(tmp_path):
    """Verify that metrics calculation is deterministic and files persist cleanly."""
    inputs = load_experiment_inputs()
    metrics_1 = calculate_before_after_metrics(inputs)
    metrics_2 = calculate_before_after_metrics(inputs)
    assert metrics_1 == metrics_2

    # Save to temp path and ensure valid file structure
    temp_dir = str(tmp_path)
    json_path, csv_path = save_before_after_results(metrics_1, output_dir=temp_dir)

    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)

    with open(json_path, "r", encoding="utf-8") as f:
        loaded_json = json.load(f)
    assert loaded_json["total_cases"] == metrics_1["total_cases"]

    df = pd.read_csv(csv_path)
    assert not df.empty
    assert "Metric" in df.columns
    assert "Value" in df.columns
