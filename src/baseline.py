import os
import pandas as pd
import numpy as np


def run_baseline_experiment(df_evaluated):
    """
    Simulates the traditional spreadsheet review (Baseline) vs the evidence-based (Prototype) approach
    on the exact same synthetic entitlement review cases.

    Calculates from actual generated data:
    1. Baseline approval rate (%)
    2. Prototype approval rate (%)
    3. Baseline blanket approval rate (%)
    4. Prototype blanket approval rate (%)
    5. Reduction in percentage points (pp)
    6. Relative reduction (%)

    Primary project metric: Reduction in blanket approvals during periodic access review.
    """
    if df_evaluated is None or df_evaluated.empty:
        return {
            "total_cases": 0,
            "baseline_approvals": 0,
            "baseline_approval_rate": 0.0,
            "prototype_approvals": 0,
            "prototype_approval_rate": 0.0,
            "baseline_blanket_approvals": 0,
            "baseline_blanket_approval_rate": 0.0,
            "prototype_blanket_approvals": 0,
            "prototype_blanket_approval_rate": 0.0,
            "reduction_percentage_points": 0.0,
            "relative_reduction": 0.0,
            "summary_df": pd.DataFrame(),
            "case_details_df": pd.DataFrame()
        }

    df = df_evaluated.copy()
    total_cases = len(df)

    # 1. BASELINE SPREADSHEET PROCESS SIMULATION
    # Reviewer sees user and entitlement. NO usage logs, NO peer baseline, NO risk score.
    # Blanket approval behavior: Active staff accounts are approved by default (~90-95%+ rate).
    # Only inactive accounts flagged by HR are revoked in spreadsheets.
    baseline_decisions = []
    for _, row in df.iterrows():
        status = str(row.get("status", "")).upper()
        if status == "INACTIVE":
            baseline_decisions.append("REVOKE")
        else:
            baseline_decisions.append("APPROVE")

    df["baseline_decision"] = baseline_decisions

    baseline_approvals = int((df["baseline_decision"] == "APPROVE").sum())
    baseline_approval_rate = round((baseline_approvals / total_cases) * 100.0, 1)

    # Blanket approvals in baseline: Approving active users' access without inspecting usage or risk
    baseline_blanket_approvals = baseline_approvals
    baseline_blanket_approval_rate = baseline_approval_rate

    # 2. PROTOTYPE EVIDENCE-BASED PROCESS SIMULATION
    # Reviewer receives usage history, peer baseline, risk score, and system recommendation.
    prototype_decisions = []
    for _, row in df.iterrows():
        rec = str(row.get("recommendation", "APPROVE")).upper()
        if rec == "APPROVE":
            prototype_decisions.append("APPROVE")
        elif rec == "REVOKE":
            prototype_decisions.append("REVOKE")
        else:  # REVIEW
            usage = int(row.get("user_usage", 0))
            if usage == 0:
                prototype_decisions.append("REVOKE")
            else:
                prototype_decisions.append("MODIFY")

    df["prototype_decision"] = prototype_decisions

    prototype_approvals = int((df["prototype_decision"] == "APPROVE").sum())
    prototype_approval_rate = round((prototype_approvals / total_cases) * 100.0, 1)

    # Blanket approvals in prototype: Approvals granted without peer-baseline verification (high risk approved)
    prototype_blanket_mask = (df["prototype_decision"] == "APPROVE") & (df["risk_score"] >= 30)
    prototype_blanket_count = int(prototype_blanket_mask.sum())
    prototype_blanket_approval_rate = round((prototype_blanket_count / total_cases) * 100.0, 1)

    # 3. STATISTICAL REDUCTION METRICS
    reduction_pp = round(baseline_blanket_approval_rate - prototype_blanket_approval_rate, 1)

    if baseline_blanket_approval_rate > 0:
        relative_reduction = round((reduction_pp / baseline_blanket_approval_rate) * 100.0, 1)
    else:
        relative_reduction = 0.0

    # Summary table comparing before vs after
    summary_data = [
        {
            "Metric": "Total Review Cases",
            "Baseline (Spreadsheet)": f"{total_cases:,}",
            "Prototype (Evidence-Based)": f"{total_cases:,}",
            "Comparison Impact": "Identical synthetic dataset"
        },
        {
            "Metric": "1. Overall Approval Rate (%)",
            "Baseline (Spreadsheet)": f"{baseline_approval_rate}%",
            "Prototype (Evidence-Based)": f"{prototype_approval_rate}%",
            "Comparison Impact": f"{round(prototype_approval_rate - baseline_approval_rate, 1):+} pp change"
        },
        {
            "Metric": "2. Blanket Approval Rate (%)",
            "Baseline (Spreadsheet)": f"{baseline_blanket_approval_rate}%",
            "Prototype (Evidence-Based)": f"{prototype_blanket_approval_rate}%",
            "Comparison Impact": f"-{reduction_pp} pp reduction"
        },
        {
            "Metric": "3. Reduction in Percentage Points (pp)",
            "Baseline (Spreadsheet)": "0.0 pp",
            "Prototype (Evidence-Based)": f"{reduction_pp} pp",
            "Comparison Impact": f"Primary Metric: {reduction_pp} pp reduction"
        },
        {
            "Metric": "4. Relative Reduction (%)",
            "Baseline (Spreadsheet)": "0.0%",
            "Prototype (Evidence-Based)": f"{relative_reduction}%",
            "Comparison Impact": f"{relative_reduction}% relative reduction"
        }
    ]

    summary_df = pd.DataFrame(summary_data)

    return {
        "total_cases": total_cases,
        "baseline_approvals": baseline_approvals,
        "baseline_approval_rate": baseline_approval_rate,
        "prototype_approvals": prototype_approvals,
        "prototype_approval_rate": prototype_approval_rate,
        "baseline_blanket_approvals": baseline_blanket_approvals,
        "baseline_blanket_approval_rate": baseline_blanket_approval_rate,
        "prototype_blanket_approvals": prototype_blanket_count,
        "prototype_blanket_approval_rate": prototype_blanket_approval_rate,
        "reduction_percentage_points": reduction_pp,
        "relative_reduction": relative_reduction,
        "summary_df": summary_df,
        "case_details_df": df
    }
