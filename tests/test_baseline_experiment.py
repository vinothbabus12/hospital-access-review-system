import os
import sys
import json
import pandas as pd
import pytest

# Ensure the project root is on sys.path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.baseline_experiment import run_experiment
from src.baseline import run_baseline_experiment


def test_experiment_returns_expected_keys():
    results = run_experiment()
    expected_keys = {
        "total_cases",
        "baseline_approvals",
        "baseline_approval_rate",
        "prototype_approvals",
        "prototype_approval_rate",
        "baseline_blanket_approvals",
        "baseline_blanket_approval_rate",
        "prototype_blanket_approvals",
        "prototype_blanket_approval_rate",
        "reduction_percentage_points",
        "relative_reduction",
        "summary_df",
        "case_details_df",
    }
    assert expected_keys.issubset(set(results.keys()))


def test_metric_consistency_and_calculations():
    res = run_experiment()
    total = res["total_cases"]
    assert total > 0

    # Consistency checks for approval rates and reductions
    if total > 0:
        # Overall approval rates
        expected_baseline_rate = round(res["baseline_approvals"] / total * 100, 1)
        assert res["baseline_approval_rate"] == expected_baseline_rate

        expected_prototype_rate = round(res["prototype_approvals"] / total * 100, 1)
        assert res["prototype_approval_rate"] == expected_prototype_rate

        # Blanket approval rates
        expected_blanket_rate = round(res["baseline_blanket_approvals"] / total * 100, 1)
        assert res["baseline_blanket_approval_rate"] == expected_blanket_rate

        expected_proto_blanket_rate = round(res["prototype_blanket_approvals"] / total * 100, 1)
        assert res["prototype_blanket_approval_rate"] == expected_proto_blanket_rate

        # Reduction calculations based on overall approval rates
        expected_reduction_pp = round(res["baseline_approval_rate"] - res["prototype_approval_rate"], 1)
        assert res["reduction_percentage_points"] == expected_reduction_pp

        if res["baseline_approval_rate"] > 0:
            expected_relative = round((expected_reduction_pp / res["baseline_approval_rate"]) * 100, 1)
        else:
            expected_relative = 0.0
        assert res["relative_reduction"] == expected_relative





def test_experiment_reproducibility():
    first = run_experiment()
    second = run_experiment()
    # Compare a subset of deterministic numeric fields
    numeric_keys = [
        "total_cases",
        "baseline_approvals",
        "baseline_approval_rate",
        "prototype_approvals",
        "prototype_approval_rate",
        "baseline_blanket_approvals",
        "baseline_blanket_approval_rate",
        "prototype_blanket_approvals",
        "prototype_blanket_approval_rate",
        "reduction_percentage_points",
        "relative_reduction",
    ]
    for k in numeric_keys:
        assert first[k] == second[k]


def test_run_baseline_experiment_empty_dataframe():
    empty_df = pd.DataFrame()
    result = run_baseline_experiment(empty_df)
    # All metrics should be zero or empty DataFrames
    zero_keys = [
        "total_cases",
        "baseline_approvals",
        "baseline_approval_rate",
        "prototype_approvals",
        "prototype_approval_rate",
        "baseline_blanket_approvals",
        "baseline_blanket_approval_rate",
        "prototype_blanket_approvals",
        "prototype_blanket_approval_rate",
        "reduction_percentage_points",
        "relative_reduction",
    ]
    for k in zero_keys:
        assert result[k] == 0 or result[k] == 0.0
    # DataFrames should be empty
    assert isinstance(result["summary_df"], pd.DataFrame)
    assert result["summary_df"].empty
    assert isinstance(result["case_details_df"], pd.DataFrame)
    assert result["case_details_df"].empty
