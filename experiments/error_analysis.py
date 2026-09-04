# experiments/error_analysis.py
"""Error and Disagreement Analysis for Hospital Access Review System.
Analyzes results from Simulated Stakeholder Validation (stakeholder_validation_results.json)
to evaluate discrepancies between automated system recommendations and reviewer decisions.

NOTE ON CREDIBILITY:
The stakeholder validation data analyzed here is explicitly SIMULATED.
Reviewer decisions represent documented operational healthcare access-review heuristics
and must not be described as live hospital stakeholder feedback.
"""

import os
import sys
import json
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.validation_cases import VALID_DECISIONS, VALID_DISAGREEMENT_CATEGORIES

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
STAKEHOLDER_RESULTS_PATH = os.path.join(RESULTS_DIR, "stakeholder_validation_results.json")

# Taxonomy of Root Cause Types
ROOT_CAUSE_TYPES = {
    "A": "System error",
    "B": "Legitimate reviewer override",
    "C": "Missing context",
    "D": "Data-quality issue",
    "E": "Rule limitation",
}

# Mapping of categories to primary root-cause classification
CATEGORY_ROOT_CAUSE_MAP = {
    "peer-group mismatch": "E. Rule limitation",
    "stale/incomplete data": "D. Data-quality issue",
    "legitimate exception": "B. Legitimate reviewer override",
    "insufficient context": "C. Missing context",
    "unusual but valid usage": "E. Rule limitation",
    "rule too aggressive": "E. Rule limitation",
    "rule too conservative": "E. Rule limitation",
    "other": "C. Missing context"
}


def load_validation_data(filepath=STAKEHOLDER_RESULTS_PATH):
    """Loads stakeholder validation results safely without modifying the source."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback to generating on the fly if file does not exist yet
    from experiments.stakeholder_validation import run_stakeholder_validation
    return run_stakeholder_validation()


def perform_error_and_disagreement_analysis(val_data=None):
    """Performs deep error and disagreement analysis across validation cases."""
    if val_data is None:
        val_data = load_validation_data()

    cases = val_data.get("cases", [])
    total_cases = len(cases)

    if total_cases == 0:
        return {
            "validation_type": "Simulated Stakeholder Validation",
            "total_validation_cases": 0,
            "agreement_count": 0,
            "disagreement_count": 0,
            "agreement_percentage": 0.0,
            "disagreement_percentage": 0.0,
            "disagreements_by_risk_level": {},
            "disagreements_by_staff_type": {},
            "disagreements_by_system_recommendation": {},
            "disagreements_by_reviewer_decision": {},
            "disagreement_category_counts": {},
            "disagreement_cases": [],
            "confusion_matrix": {},
            "rule_improvement_recommendations": []
        }

    agreed_cases = [c for c in cases if c.get("agreement") is True]
    disagreed_cases = [c for c in cases if c.get("agreement") is False]

    agreement_count = len(agreed_cases)
    disagreement_count = len(disagreed_cases)

    agreement_pct = round((agreement_count / total_cases) * 100.0, 1)
    disagreement_pct = round((disagreement_count / total_cases) * 100.0, 1)

    # Breakdown of disagreements
    dis_by_risk = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for c in disagreed_cases:
        r = c.get("risk_level", "LOW")
        dis_by_risk[r] = dis_by_risk.get(r, 0) + 1

    dis_by_staff = {}
    for c in disagreed_cases:
        st = c.get("staff_type", "Unknown")
        dis_by_staff[st] = dis_by_staff.get(st, 0) + 1

    dis_by_sys_rec = {dec: 0 for dec in VALID_DECISIONS}
    for c in disagreed_cases:
        sr = c.get("system_recommendation")
        if sr in dis_by_sys_rec:
            dis_by_sys_rec[sr] += 1

    dis_by_rev_dec = {dec: 0 for dec in VALID_DECISIONS}
    for c in disagreed_cases:
        rd = c.get("simulated_reviewer_decision")
        if rd in dis_by_rev_dec:
            dis_by_rev_dec[rd] += 1

    dis_category_counts = {}
    for c in disagreed_cases:
        cat = c.get("disagreement_category", "other")
        dis_category_counts[cat] = dis_category_counts.get(cat, 0) + 1

    # Disagreement Case Details
    detailed_disagreements = []
    default_recs = {
        "peer-group mismatch": (
            "System baseline computes peer averages across all clinicians without title distinction.",
            "Introduce sub-role or administrative title segmentation within peer comparison groups.",
            "B. Legitimate reviewer override"
        ),
        "stale/incomplete data": (
            "System depends on periodic HR batch synchronization which lags recent ward reassignments.",
            "Integrate real-time HR event webhooks for immediate ward reassignment and leave tracking.",
            "D. Data-quality issue"
        ),
        "legitimate exception": (
            "System evaluated access within a rigid 30-day window without considering bi-monthly specialty shifts.",
            "Add role-specific activity windows (e.g., 90-day evaluation for Visiting Consultants).",
            "B. Legitimate reviewer override"
        ),
        "insufficient context": (
            "Access logs showed valid technical usage, but contract scope was narrowed in procurement records.",
            "Incorporate Vendor Management System (VMS) contract metadata into entitlement risk scoring.",
            "C. Missing context"
        ),
        "unusual but valid usage": (
            "System flagged high peer deviation caused by scheduled automated calibration batches.",
            "Exclude service-account and automated calibration batch runs from human user peer baselines.",
            "E. Rule limitation"
        )
    }

    for c in disagreed_cases:
        cat = c.get("disagreement_category", "other")
        issue, imp, root = default_recs.get(
            cat,
            (
                "Reviewer possessed external organizational context not captured in application logs.",
                "Expand evidence engine data integrations to ingest clinical shift and duty calendars.",
                CATEGORY_ROOT_CAUSE_MAP.get(cat, "C. Missing context")
            )
        )
        detailed_disagreements.append({
            "validation_case_id": c.get("validation_case_id"),
            "user_id": c.get("user_id"),
            "staff_type": c.get("staff_type"),
            "role": c.get("role"),
            "application": c.get("application"),
            "permission": c.get("permission"),
            "system_recommendation": c.get("system_recommendation"),
            "reviewer_decision": c.get("simulated_reviewer_decision"),
            "risk_score": c.get("risk_score"),
            "risk_level": c.get("risk_level"),
            "evidence_flags": c.get("evidence_flags", []),
            "reviewer_reason": c.get("reviewer_reason"),
            "disagreement_category": cat,
            "possible_rule_issue": issue,
            "suggested_improvement": imp,
            "root_cause_type": root
        })

    # Confusion-style matrix with marginal totals
    matrix = {s: {r: 0 for r in VALID_DECISIONS} for s in VALID_DECISIONS}
    for c in cases:
        matrix[c["system_recommendation"]][c["simulated_reviewer_decision"]] += 1

    confusion_summary = {}
    for s in VALID_DECISIONS:
        row_dict = dict(matrix[s])
        row_dict["Total_System"] = sum(matrix[s].values())
        confusion_summary[s] = row_dict

    col_totals = {r: sum(matrix[s][r] for s in VALID_DECISIONS) for r in VALID_DECISIONS}
    col_totals["Total_System"] = total_cases
    confusion_summary["Total_Reviewer"] = col_totals

    # Actionable Rule Improvement Recommendations
    rule_recommendations = [
        {
            "priority": "HIGH",
            "area": "Peer Group Segmentation",
            "observation": "Department Head clinicians were flagged for low usage because clinical peer groups grouped administrative leaders with full-time floor doctors.",
            "recommendation": "Segment peer comparison baselines by administrative role flags (e.g., Department Head, Teaching Faculty vs Staff Clinician)."
        },
        {
            "priority": "HIGH",
            "area": "HR Synchronization Latency",
            "observation": "Staff transferred to new departments retained old acute permissions that the system approved due to legacy usage in past 30 days.",
            "recommendation": "Integrate real-time HR transfer webhooks to trigger immediate automated deprovisioning of departed ward entitlements."
        },
        {
            "priority": "MEDIUM",
            "area": "Multi-Cadence Evaluation Windows",
            "observation": "Visiting Consultants and on-call surgeons operate on bi-monthly schedules, causing false-positive dormancy flags under 30-day lookback.",
            "recommendation": "Implement configurable evaluation lookback windows (e.g., 90-day evaluation for Visiting Consultants vs 30 days for permanent staff)."
        },
        {
            "priority": "MEDIUM",
            "area": "Academic & Leave Calendar Ingestion",
            "observation": "Interns on mandatory academic examination leave were flagged for inactivity despite scheduled return.",
            "recommendation": "Ingest hospital residency rotation schedules and approved academic leave data into the evidence engine."
        },
        {
            "priority": "MEDIUM",
            "area": "Vendor Contract Scope Metadata",
            "observation": "Contractor permissions were approved by system based on access history, despite procurement contract narrowing.",
            "recommendation": "Connect Vendor Management System (VMS) contract scope flags to automatically downgrade third-party entitlements upon SLA change."
        },
        {
            "priority": "LOW",
            "area": "Automated Batch Task Filtering",
            "observation": "Technicians executing scheduled end-of-month batch calibration runs had inflated usage flags.",
            "recommendation": "Distinguish between automated batch script executions and interactive user sessions when computing peer usage distributions."
        }
    ]

    analysis_results = {
        "analysis_type": "Error and Disagreement Analysis (Simulated Stakeholder Validation)",
        "methodology_statement": (
            "This analysis evaluates discrepancies between automated evidence-based recommendations "
            "and simulated reviewer decisions. The validation is explicitly simulated and does not claim "
            "real hospital stakeholder feedback."
        ),
        "total_validation_cases": total_cases,
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "agreement_percentage": agreement_pct,
        "disagreement_percentage": disagreement_pct,
        "disagreements_by_risk_level": dis_by_risk,
        "disagreements_by_staff_type": dis_by_staff,
        "disagreements_by_system_recommendation": dis_by_sys_rec,
        "disagreements_by_reviewer_decision": dis_by_rev_dec,
        "disagreement_category_counts": dis_category_counts,
        "confusion_matrix": confusion_summary,
        "disagreement_cases": detailed_disagreements,
        "rule_improvement_recommendations": rule_recommendations
    }

    return analysis_results


def save_error_analysis_results(results, output_dir=RESULTS_DIR):
    """Persists error analysis results to JSON and flat CSV formats."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "error_analysis_results.json")
    csv_path = os.path.join(output_dir, "error_analysis_results.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Save detailed disagreement cases as CSV
    dis_cases = results.get("disagreement_cases", [])
    if dis_cases:
        df_csv = pd.DataFrame(dis_cases)
        if "evidence_flags" in df_csv.columns:
            df_csv["evidence_flags"] = df_csv["evidence_flags"].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
        df_csv.to_csv(csv_path, index=False)
    else:
        pd.DataFrame([{"Message": "No disagreements found"}]).to_csv(csv_path, index=False)

    return json_path, csv_path


def main():
    val_data = load_validation_data()
    results = perform_error_and_disagreement_analysis(val_data)
    json_path, csv_path = save_error_analysis_results(results)

    print("===================================================================")
    print("       ERROR AND DISAGREEMENT ANALYSIS (SIMULATED VALIDATION)      ")
    print("===================================================================")
    print(f"Total Validation Cases:       {results['total_validation_cases']}")
    print(f"Agreements:                   {results['agreement_count']} ({results['agreement_percentage']}%)")
    print(f"Disagreements:                {results['disagreement_count']} ({results['disagreement_percentage']}%)")
    print("-------------------------------------------------------------------")
    print("Disagreement Breakdown:")
    print(f"  By Risk Level:    LOW={results['disagreements_by_risk_level'].get('LOW', 0)}, MEDIUM={results['disagreements_by_risk_level'].get('MEDIUM', 0)}, HIGH={results['disagreements_by_risk_level'].get('HIGH', 0)}")
    print("  By Staff Type:")
    for stype, cnt in results["disagreements_by_staff_type"].items():
        print(f"    - {stype:22s}: {cnt}")
    print("  Top Disagreement Categories:")
    for cat, cnt in sorted(results["disagreement_category_counts"].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {cat:25s}: {cnt}")
    print("-------------------------------------------------------------------")
    print(f"Detailed Disagreements Logged: {len(results['disagreement_cases'])}")
    print(f"Rule Recommendations Formulated: {len(results['rule_improvement_recommendations'])}")
    print(f"Outputs written to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print("===================================================================")


if __name__ == "__main__":
    main()
