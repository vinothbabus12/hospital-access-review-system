# tests/test_stakeholder_validation.py
"""Unit and integration tests for Simulated Stakeholder Validation."""

import os
import sys
import json
import hashlib
import pandas as pd
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.validation_cases import (
    get_curated_validation_cases,
    VALID_DECISIONS,
    VALID_DISAGREEMENT_CATEGORIES
)
from experiments.stakeholder_validation import (
    run_stakeholder_validation,
    save_stakeholder_validation_results,
    RESULTS_DIR
)
from src.database import DATA_DIR


@pytest.fixture(scope="module")
def validation_results():
    """Run stakeholder validation once for test module."""
    return run_stakeholder_validation()


def _file_hash(filepath):
    """Utility to compute SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_validation_sample_minimum_cases(validation_results):
    """Verify that validation sample contains at least 20 cases (we provide 25)."""
    cases = validation_results["cases"]
    assert len(cases) >= 20
    assert validation_results["total_validation_cases"] == len(cases)


def test_case_fields_complete(validation_results):
    """Verify that every validation case contains all required schema fields."""
    required_fields = [
        "validation_case_id",
        "user_id",
        "staff_type",
        "role",
        "application",
        "permission",
        "risk_score",
        "risk_level",
        "evidence_flags",
        "system_recommendation",
        "simulated_reviewer_decision",
        "agreement",
        "reviewer_reason",
        "disagreement_category",
    ]
    for case in validation_results["cases"]:
        for field in required_fields:
            assert field in case, f"Field '{field}' missing from case {case.get('validation_case_id')}"
        assert case["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        assert 0 <= case["risk_score"] <= 100
        assert isinstance(case["agreement"], bool)


def test_staff_types_and_roles_covered(validation_results):
    """Verify that validation cases cover all 4 staff types and key clinical roles."""
    cases = validation_results["cases"]
    staff_types = {c["staff_type"] for c in cases}
    expected_staff_types = {"Permanent Staff", "Visiting Consultant", "Intern", "Outsourced Technician"}
    assert expected_staff_types.issubset(staff_types)

    roles = {c["role"] for c in cases}
    assert len(roles) >= 4  # Diverse healthcare roles represented


def test_system_recommendations_and_reviewer_decisions_valid(validation_results):
    """Verify that decisions and recommendations are valid domain choices and non-trivial."""
    cases = validation_results["cases"]
    for c in cases:
        assert c["system_recommendation"] in VALID_DECISIONS
        assert c["simulated_reviewer_decision"] in VALID_DECISIONS

    # Reviewer decisions must not simply mirror system recommendations
    assert validation_results["disagreement_count"] > 0
    assert validation_results["agreement_count"] > 0


def test_agreement_calculation_and_counts(validation_results):
    """Verify agreement math, counts, and subgroup partitions."""
    res = validation_results
    total = res["total_validation_cases"]
    agreed = res["agreement_count"]
    disagreed = res["disagreement_count"]

    assert total == agreed + disagreed
    expected_pct = round((agreed / total) * 100.0, 1)
    assert res["agreement_percentage"] == expected_pct

    # Subgroups
    for group_dict in [res["agreement_by_risk_level"], res["agreement_by_staff_type"], res["agreement_by_recommendation"]]:
        sum_total = sum(d["total"] for d in group_dict.values())
        sum_agreed = sum(d["agreed"] for d in group_dict.values())
        assert sum_total == total
        assert sum_agreed == agreed


def test_confusion_matrix_integrity(validation_results):
    """Verify that confusion matrix sums to total validation cases."""
    cm = validation_results["confusion_matrix"]
    matrix_sum = sum(sum(row.values()) for row in cm.values())
    assert matrix_sum == validation_results["total_validation_cases"]


def test_disagreement_analysis_structure(validation_results):
    """Verify disagreement analysis matches disagreement count and valid categories."""
    disagreements = validation_results["disagreement_analysis"]
    assert len(disagreements) == validation_results["disagreement_count"]

    for item in disagreements:
        assert item["disagreement_category"] in VALID_DISAGREEMENT_CATEGORIES
        assert len(item["reason_for_disagreement"]) > 0
        assert len(item["system_rule_assessment"]) > 0
        assert len(item["recommended_future_improvement"]) > 0


def test_empty_dataset_and_invalid_decision_handling():
    """Verify safety on empty dataset and exception on invalid decisions."""
    empty_res = run_stakeholder_validation(cases=[])
    assert empty_res["total_validation_cases"] == 0
    assert empty_res["agreement_percentage"] == 0.0

    bad_case = [{
        "validation_case_id": "VAL-BAD",
        "system_recommendation": "INVALID_CHOICE",
        "simulated_reviewer_decision": "APPROVE",
        "agreement": False
    }]
    with pytest.raises(ValueError):
        run_stakeholder_validation(cases=bad_case)


def test_source_data_immutability_and_persistence(tmp_path):
    """Verify that source CSVs are untouched and output files persist cleanly."""
    users_csv = os.path.join(DATA_DIR, "users.csv")
    ent_csv = os.path.join(DATA_DIR, "entitlements.csv")

    hash_users_before = _file_hash(users_csv)
    hash_ent_before = _file_hash(ent_csv)

    # Run validation and save to temporary directory
    res = run_stakeholder_validation()
    temp_dir = str(tmp_path)
    json_path, csv_path = save_stakeholder_validation_results(res, output_dir=temp_dir)

    hash_users_after = _file_hash(users_csv)
    hash_ent_after = _file_hash(ent_csv)

    assert hash_users_before == hash_users_after, "users.csv was modified!"
    assert hash_ent_before == hash_ent_after, "entitlements.csv was modified!"

    # Verify saved files
    assert os.path.exists(json_path)
    assert os.path.exists(csv_path)

    with open(json_path, "r", encoding="utf-8") as jf:
        loaded = json.load(jf)
    assert loaded["total_validation_cases"] == res["total_validation_cases"]

    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == res["total_validation_cases"]
    assert "validation_case_id" in df_csv.columns
