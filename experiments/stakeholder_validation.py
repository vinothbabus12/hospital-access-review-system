# experiments/stakeholder_validation.py
"""Simulated Stakeholder Validation Experiment Runner.
NOTE ON CREDIBILITY & METHODOLOGY:
This experiment is explicitly a "Simulated Stakeholder Validation".
It evaluates the prototype against realistic, documented independent reviewer decisions
representing clinical, operational, and vendor contexts, without claiming that actual
hospital personnel participated.
"""

import os
import sys
import json
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.validation_cases import get_curated_validation_cases, VALID_DECISIONS

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_stakeholder_validation(cases=None, df_evaluated=None):
    """Executes the simulated stakeholder validation workflow.
    Calculates summary metrics, subgroup agreements, confusion matrix,
    and disagreement error analysis.
    """
    if cases is None:
        cases = get_curated_validation_cases(df_evaluated=df_evaluated)

    total_cases = len(cases)
    if total_cases == 0:
        return {
            "validation_type": "Simulated Stakeholder Validation",
            "total_validation_cases": 0,
            "system_approvals": 0,
            "system_revocations": 0,
            "system_modifications": 0,
            "system_review_recommendations": 0,
            "reviewer_approvals": 0,
            "reviewer_revocations": 0,
            "reviewer_modifications": 0,
            "reviewer_review_decisions": 0,
            "agreement_count": 0,
            "disagreement_count": 0,
            "agreement_percentage": 0.0,
            "agreement_by_risk_level": {},
            "agreement_by_staff_type": {},
            "agreement_by_recommendation": {},
            "confusion_matrix": {},
            "disagreement_analysis": [],
            "cases": []
        }

    # Validate decision values
    for c in cases:
        if c["simulated_reviewer_decision"] not in VALID_DECISIONS:
            raise ValueError(f"Invalid simulated reviewer decision: {c['simulated_reviewer_decision']}")
        if c["system_recommendation"] not in VALID_DECISIONS:
            raise ValueError(f"Invalid system recommendation: {c['system_recommendation']}")

    # 1-5. System Recommendation Counts
    sys_app = sum(1 for c in cases if c["system_recommendation"] == "APPROVE")
    sys_rev = sum(1 for c in cases if c["system_recommendation"] == "REVOKE")
    sys_mod = sum(1 for c in cases if c["system_recommendation"] == "MODIFY")
    sys_chk = sum(1 for c in cases if c["system_recommendation"] == "REVIEW")

    # 6-9. Reviewer Decision Counts
    rev_app = sum(1 for c in cases if c["simulated_reviewer_decision"] == "APPROVE")
    rev_rev = sum(1 for c in cases if c["simulated_reviewer_decision"] == "REVOKE")
    rev_mod = sum(1 for c in cases if c["simulated_reviewer_decision"] == "MODIFY")
    rev_chk = sum(1 for c in cases if c["simulated_reviewer_decision"] == "REVIEW")

    # 10-12. Overall Agreement Metrics
    agreement_count = sum(1 for c in cases if c["agreement"] is True)
    disagreement_count = total_cases - agreement_count
    agreement_pct = round((agreement_count / total_cases) * 100.0, 1)

    # Subgroup Agreement Helpers
    def calc_subgroup_agreement(group_key):
        groups = {}
        for c in cases:
            g = c[group_key]
            if g not in groups:
                groups[g] = {"total": 0, "agreed": 0, "disagreed": 0}
            groups[g]["total"] += 1
            if c["agreement"]:
                groups[g]["agreed"] += 1
            else:
                groups[g]["disagreed"] += 1

        res = {}
        for g, d in groups.items():
            pct = round((d["agreed"] / d["total"]) * 100.0, 1) if d["total"] > 0 else 0.0
            res[g] = {
                "total": d["total"],
                "agreed": d["agreed"],
                "disagreed": d["disagreed"],
                "agreement_percentage": pct
            }
        return res

    agreement_by_risk = calc_subgroup_agreement("risk_level")
    agreement_by_staff = calc_subgroup_agreement("staff_type")
    agreement_by_rec = calc_subgroup_agreement("system_recommendation")

    # Confusion Matrix: {System_Rec: {Reviewer_Dec: count}}
    confusion_matrix = {s: {r: 0 for r in VALID_DECISIONS} for s in VALID_DECISIONS}
    for c in cases:
        confusion_matrix[c["system_recommendation"]][c["simulated_reviewer_decision"]] += 1

    # Disagreement Analysis Mapping
    disagreement_analysis = []
    disagreement_recs = {
        "peer-group mismatch": {
            "rule_assessment": "System baseline computed general Doctor usage without segregating clinical vs administrative Department Heads.",
            "future_improvement": "Introduce sub-role or administrative title segmentation within peer comparison groups."
        },
        "stale/incomplete data": {
            "rule_assessment": "System relies on periodic HR batch synchronization which missed recent ward transfer or scheduled study leave.",
            "future_improvement": "Integrate real-time HR event webhooks for immediate ward reassignment and leave tracking."
        },
        "legitimate exception": {
            "rule_assessment": "System flagged low 30-day usage without factoring in bi-monthly visiting consultant rotation schedules.",
            "future_improvement": "Add role-specific activity windows (e.g., 90-day evaluation for Visiting Consultants vs 30 days for staff)."
        },
        "insufficient context": {
            "rule_assessment": "System evaluated access logs correctly, but lacked visibility into vendor contract scope renegotiation.",
            "future_improvement": "Incorporate Vendor Management System (VMS) contract metadata into entitlement risk scoring."
        },
        "unusual but valid usage": {
            "rule_assessment": "System flagged high peer deviation caused by scheduled automated calibration batches.",
            "future_improvement": "Exclude service-account and automated calibration batch runs from human user peer baselines."
        }
    }

    for c in cases:
        if not c["agreement"]:
            cat = c.get("disagreement_category", "other")
            guidance = disagreement_recs.get(cat, {
                "rule_assessment": "Reviewer context contained situational information not currently ingested by automated logs.",
                "future_improvement": "Expand evidence engine data sources to capture situational justification notes."
            })
            disagreement_analysis.append({
                "validation_case_id": c["validation_case_id"],
                "user_id": c["user_id"],
                "staff_type": c["staff_type"],
                "role": c["role"],
                "application": c["application"],
                "system_recommendation": c["system_recommendation"],
                "reviewer_decision": c["simulated_reviewer_decision"],
                "reason_for_disagreement": c["reviewer_reason"],
                "disagreement_category": cat,
                "system_rule_assessment": guidance["rule_assessment"],
                "recommended_future_improvement": guidance["future_improvement"]
            })

    results = {
        "validation_type": "Simulated Stakeholder Validation",
        "methodology_statement": (
            "This experiment uses simulated reviewer decisions designed to represent realistic "
            "hospital access-review scenarios and does not claim real hospital stakeholders participated."
        ),
        "total_validation_cases": total_cases,
        "system_approvals": sys_app,
        "system_revocations": sys_rev,
        "system_modifications": sys_mod,
        "system_review_recommendations": sys_chk,
        "reviewer_approvals": rev_app,
        "reviewer_revocations": rev_rev,
        "reviewer_modifications": rev_mod,
        "reviewer_review_decisions": rev_chk,
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "agreement_percentage": agreement_pct,
        "agreement_by_risk_level": agreement_by_risk,
        "agreement_by_staff_type": agreement_by_staff,
        "agreement_by_recommendation": agreement_by_rec,
        "confusion_matrix": confusion_matrix,
        "disagreement_analysis": disagreement_analysis,
        "cases": cases
    }

    return results


def save_stakeholder_validation_results(results, output_dir=RESULTS_DIR):
    """Persists stakeholder validation results to JSON and flat CSV format."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "stakeholder_validation_results.json")
    csv_path = os.path.join(output_dir, "stakeholder_validation_results.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Save case-level details as CSV
    cases_df = pd.DataFrame(results["cases"])
    # Convert list of evidence flags to string for CSV compatibility
    if "evidence_flags" in cases_df.columns:
        cases_df["evidence_flags"] = cases_df["evidence_flags"].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
    cases_df.to_csv(csv_path, index=False)

    return json_path, csv_path


def main():
    results = run_stakeholder_validation()
    json_path, csv_path = save_stakeholder_validation_results(results)

    print("===================================================================")
    print("       SIMULATED STAKEHOLDER VALIDATION RESULTS                    ")
    print("===================================================================")
    print(f"Validation Type:              {results['validation_type']}")
    print(f"Total Validation Cases:       {results['total_validation_cases']}")
    print(f"System vs Reviewer Agreement: {results['agreement_count']} / {results['total_validation_cases']} ({results['agreement_percentage']}%)")
    print(f"Disagreements:                {results['disagreement_count']}")
    print("-------------------------------------------------------------------")
    print("Decision Breakdown:")
    print(f"  System:   APPROVE={results['system_approvals']}, REVIEW={results['system_review_recommendations']}, REVOKE={results['system_revocations']}, MODIFY={results['system_modifications']}")
    print(f"  Reviewer: APPROVE={results['reviewer_approvals']}, REVIEW={results['reviewer_review_decisions']}, REVOKE={results['reviewer_revocations']}, MODIFY={results['reviewer_modifications']}")
    print("-------------------------------------------------------------------")
    print("Agreement by Staff Type:")
    for stype, data in results["agreement_by_staff_type"].items():
        print(f"  - {stype:22s}: {data['agreed']}/{data['total']} ({data['agreement_percentage']}%)")
    print("-------------------------------------------------------------------")
    print("Agreement by Risk Level:")
    for rlevel, data in results["agreement_by_risk_level"].items():
        print(f"  - {rlevel:10s}: {data['agreed']}/{data['total']} ({data['agreement_percentage']}%)")
    print("-------------------------------------------------------------------")
    print(f"Results written to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print("===================================================================")


if __name__ == "__main__":
    main()
