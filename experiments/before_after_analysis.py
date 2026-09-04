# experiments/before_after_analysis.py
"""Before vs After Analysis for Hospital Access Review System.
Synthesizes results from baseline_results.json and expanded_results.json
to evaluate the quantitative impact of the evidence-based access review prototype
against traditional spreadsheet-based reviews.
"""

import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_experiment_inputs(results_dir=RESULTS_DIR, data_dir=DATA_DIR):
    """Load actual results from baseline_results.json, expanded_results.json,
    case_details.csv, and review_decisions.csv without mutating them.
    """
    baseline_json_path = os.path.join(results_dir, "baseline_results.json")
    expanded_json_path = os.path.join(results_dir, "expanded_results.json")
    case_details_path = os.path.join(results_dir, "case_details.csv")
    review_decisions_path = os.path.join(data_dir, "review_decisions.csv")

    baseline_data = {}
    if os.path.exists(baseline_json_path):
        with open(baseline_json_path, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

    expanded_data = {}
    if os.path.exists(expanded_json_path):
        with open(expanded_json_path, "r", encoding="utf-8") as f:
            expanded_data = json.load(f)

    case_details_df = pd.DataFrame()
    if os.path.exists(case_details_path):
        case_details_df = pd.read_csv(case_details_path)

    review_decisions_df = pd.DataFrame()
    if os.path.exists(review_decisions_path):
        review_decisions_df = pd.read_csv(review_decisions_path)

    return {
        "baseline": baseline_data,
        "expanded": expanded_data,
        "case_details": case_details_df,
        "review_decisions": review_decisions_df,
    }


def calculate_before_after_metrics(inputs=None):
    """Calculate the 17 specified before-and-after comparison metrics dynamically
    from the actual generated experimental data.
    """
    if inputs is None:
        inputs = load_experiment_inputs()

    baseline = inputs.get("baseline", {})
    expanded = inputs.get("expanded", {})
    case_df = inputs.get("case_details", pd.DataFrame())
    decisions_df = inputs.get("review_decisions", pd.DataFrame())

    # Scenario E1 serves as the baseline access review under the prototype
    e1 = expanded.get("E1", {})

    # 1. Total review cases
    total_cases = baseline.get("total_cases", e1.get("total_cases", len(case_df) if not case_df.empty else 0))

    # 2. Baseline approvals
    baseline_approvals = baseline.get("baseline_approvals", 0)

    # 3. Prototype approvals
    prototype_approvals = baseline.get("prototype_approvals", e1.get("recommendation_counts", {}).get("APPROVE", 0))

    # 4. Prototype revocations
    if not case_df.empty and "prototype_decision" in case_df.columns:
        prototype_revocations = int((case_df["prototype_decision"] == "REVOKE").sum())
    else:
        prototype_revocations = e1.get("recommendation_counts", {}).get("REVOKE", 0)

    # 5. Prototype modifications
    if not case_df.empty and "prototype_decision" in case_df.columns:
        prototype_modifications = int((case_df["prototype_decision"] == "MODIFY").sum())
    else:
        prototype_modifications = e1.get("recommendation_counts", {}).get("MODIFY", 0)

    # 6. Prototype review/override decisions where available
    # Checks recorded human reviewer overrides and reviews
    if not decisions_df.empty:
        if "override" in decisions_df.columns:
            # Overrides where human reviewer diverged from recommendation
            override_count = int(decisions_df["override"].apply(lambda x: str(x).lower() in ["true", "1"]).sum())
        else:
            override_count = 0
        review_count = int((decisions_df["reviewer_decision"] == "REVIEW").sum()) if "reviewer_decision" in decisions_df.columns else 0
        prototype_review_override_decisions = {
            "recorded_human_decisions": len(decisions_df),
            "reviewer_reviews": review_count,
            "reviewer_overrides": override_count,
            "system_review_recommendations": e1.get("recommendation_counts", {}).get("REVIEW", 0)
        }
    else:
        prototype_review_override_decisions = {
            "recorded_human_decisions": 0,
            "reviewer_reviews": 0,
            "reviewer_overrides": 0,
            "system_review_recommendations": e1.get("recommendation_counts", {}).get("REVIEW", 0)
        }

    # 7. Baseline approval rate
    baseline_approval_rate = baseline.get("baseline_approval_rate", 0.0)
    if baseline_approval_rate == 0.0 and total_cases > 0:
        baseline_approval_rate = round((baseline_approvals / total_cases) * 100.0, 1)

    # 8. Prototype approval rate
    prototype_approval_rate = baseline.get("prototype_approval_rate", 0.0)
    if prototype_approval_rate == 0.0 and total_cases > 0:
        prototype_approval_rate = round((prototype_approvals / total_cases) * 100.0, 1)

    # 9. Approval-rate reduction in percentage points
    approval_rate_reduction_percentage_points = round(baseline_approval_rate - prototype_approval_rate, 1)

    # 10. Relative approval-rate reduction
    if baseline_approval_rate > 0:
        relative_approval_rate_reduction = round(
            ((baseline_approval_rate - prototype_approval_rate) / baseline_approval_rate) * 100.0,
            1
        )
    else:
        relative_approval_rate_reduction = 0.0

    # 11. High-risk cases
    high_risk_cases = e1.get("risk_counts", {}).get("HIGH", 0)
    if high_risk_cases == 0 and not case_df.empty and "risk_level" in case_df.columns:
        high_risk_cases = int((case_df["risk_level"] == "HIGH").sum())

    # 12. Medium-risk cases
    medium_risk_cases = e1.get("risk_counts", {}).get("MEDIUM", 0)
    if medium_risk_cases == 0 and not case_df.empty and "risk_level" in case_df.columns:
        medium_risk_cases = int((case_df["risk_level"] == "MEDIUM").sum())

    # 13. Low-risk cases
    low_risk_cases = e1.get("risk_counts", {}).get("LOW", 0)
    if low_risk_cases == 0 and not case_df.empty and "risk_level" in case_df.columns:
        low_risk_cases = int((case_df["risk_level"] == "LOW").sum())

    # 14. Unused privilege cases
    unused_privilege_cases = e1.get("UNUSED_PRIVILEGE", 0)

    # 15. High privilege cases
    high_privilege_cases = e1.get("HIGH_PRIVILEGE", 0)

    # 16. Low usage vs peer cases
    low_usage_vs_peer_cases = e1.get("LOW_USAGE_VS_PEERS", 0)

    # 17. Inactive user cases
    inactive_user_cases = e1.get("INACTIVE_USER", 0)

    metrics = {
        "total_cases": int(total_cases),
        "baseline_approvals": int(baseline_approvals),
        "prototype_approvals": int(prototype_approvals),
        "prototype_revocations": int(prototype_revocations),
        "prototype_modifications": int(prototype_modifications),
        "prototype_review_override_decisions": prototype_review_override_decisions,
        "baseline_approval_rate": float(baseline_approval_rate),
        "prototype_approval_rate": float(prototype_approval_rate),
        "approval_rate_reduction_percentage_points": float(approval_rate_reduction_percentage_points),
        "relative_approval_rate_reduction": float(relative_approval_rate_reduction),
        "high_risk_cases": int(high_risk_cases),
        "medium_risk_cases": int(medium_risk_cases),
        "low_risk_cases": int(low_risk_cases),
        "unused_privilege_cases": int(unused_privilege_cases),
        "high_privilege_cases": int(high_privilege_cases),
        "low_usage_vs_peer_cases": int(low_usage_vs_peer_cases),
        "inactive_user_cases": int(inactive_user_cases),
    }

    return metrics


# -----------------------------------------------------------------------------
# Visualization Functions (Plotly)
# -----------------------------------------------------------------------------

def create_approval_rate_chart(metrics):
    """Visualization 1: Baseline vs Prototype Approval Rate."""
    df_chart = pd.DataFrame([
        {
            "Approach": "Baseline (Spreadsheet)",
            "Approval Rate (%)": metrics["baseline_approval_rate"],
            "Description": "Active staff approved by default"
        },
        {
            "Approach": "Prototype (Evidence-Based)",
            "Approval Rate (%)": metrics["prototype_approval_rate"],
            "Description": "Usage history, peer baseline, & risk scoring"
        }
    ])
    fig = px.bar(
        df_chart,
        x="Approach",
        y="Approval Rate (%)",
        color="Approach",
        text="Approval Rate (%)",
        color_discrete_map={
            "Baseline (Spreadsheet)": "#EF4444",
            "Prototype (Evidence-Based)": "#10B981"
        },
        title=f"Baseline vs Prototype Approval Rate (-{metrics['approval_rate_reduction_percentage_points']} pp Reduction)"
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        yaxis_range=[0, 105],
        showlegend=False,
        plot_bgcolor="#F8FAFC",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_decision_distribution_chart(metrics):
    """Visualization 2: Prototype Decision Distribution."""
    df_chart = pd.DataFrame([
        {"Decision": "APPROVE", "Count": metrics["prototype_approvals"], "Color": "#10B981"},
        {"Decision": "REVOKE", "Count": metrics["prototype_revocations"], "Color": "#EF4444"},
        {"Decision": "MODIFY", "Count": metrics["prototype_modifications"], "Color": "#F59E0B"},
    ])
    fig = px.bar(
        df_chart,
        x="Decision",
        y="Count",
        color="Decision",
        text="Count",
        color_discrete_map={
            "APPROVE": "#10B981",
            "REVOKE": "#EF4444",
            "MODIFY": "#F59E0B"
        },
        title="Prototype Review Decision Breakdown"
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="#F8FAFC",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_risk_distribution_chart(metrics):
    """Visualization 3: Risk Distribution."""
    df_chart = pd.DataFrame([
        {"Risk Level": "LOW", "Count": metrics["low_risk_cases"]},
        {"Risk Level": "MEDIUM", "Count": metrics["medium_risk_cases"]},
        {"Risk Level": "HIGH", "Count": metrics["high_risk_cases"]},
    ])
    fig = px.pie(
        df_chart,
        names="Risk Level",
        values="Count",
        color="Risk Level",
        color_discrete_map={
            "LOW": "#10B981",
            "MEDIUM": "#F59E0B",
            "HIGH": "#EF4444"
        },
        title="Entitlement Risk Classification Breakdown",
        hole=0.4
    )
    fig.update_traces(textinfo="label+percent+value")
    fig.update_layout(
        plot_bgcolor="#F8FAFC",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def create_scenario_comparison_chart(expanded_data=None):
    """Visualization 4: Expanded Experiment Scenario Comparison (E1 to E10)."""
    if expanded_data is None:
        inputs = load_experiment_inputs()
        expanded_data = inputs.get("expanded", {})

    rows = []
    for sid in [f"E{i}" for i in range(1, 11)]:
        if sid in expanded_data:
            s = expanded_data[sid]
            rows.append({
                "Scenario": sid,
                "Total Cases": s.get("total_cases", 0),
                "Affected Cases": s.get("affected_cases", 0),
                "High Risk": s.get("risk_counts", {}).get("HIGH", 0),
                "Medium Risk": s.get("risk_counts", {}).get("MEDIUM", 0),
                "Low Risk": s.get("risk_counts", {}).get("LOW", 0),
                "Avg Risk Score": s.get("risk_score_stats", {}).get("avg", 0.0)
            })

    if not rows:
        return go.Figure()

    df_scenarios = pd.DataFrame(rows)
    fig = px.bar(
        df_scenarios,
        x="Scenario",
        y=["Affected Cases", "High Risk"],
        barmode="group",
        title="Expanded Experiments (E1-E10): Affected Cases & High-Risk Counts",
        labels={"value": "Case Count", "variable": "Metric"},
        color_discrete_map={
            "Affected Cases": "#3B82F6",
            "High Risk": "#EF4444"
        }
    )
    fig.update_layout(
        plot_bgcolor="#F8FAFC",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


# -----------------------------------------------------------------------------
# Results Persistence
# -----------------------------------------------------------------------------

def save_before_after_results(metrics, output_dir=RESULTS_DIR):
    """Save calculated metrics to both JSON and CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "before_after_results.json")
    csv_path = os.path.join(output_dir, "before_after_results.csv")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Flatten metrics dictionary for tabular CSV format
    flat_rows = []
    for k, v in metrics.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat_rows.append({"Metric": f"{k}_{sub_k}", "Value": str(sub_v)})
        else:
            flat_rows.append({"Metric": k, "Value": str(v)})

    df = pd.DataFrame(flat_rows)
    df.to_csv(csv_path, index=False)

    return json_path, csv_path


def main():
    inputs = load_experiment_inputs()
    metrics = calculate_before_after_metrics(inputs)
    json_path, csv_path = save_before_after_results(metrics)

    print("=========================================================")
    print("   HOSPITAL ACCESS REVIEW: BEFORE vs AFTER ANALYSIS      ")
    print("=========================================================")
    print(f"Total Review Cases:                         {metrics['total_cases']}")
    print(f"Baseline Approvals (Spreadsheet):           {metrics['baseline_approvals']} ({metrics['baseline_approval_rate']}%)")
    print(f"Prototype Approvals (Evidence-Based):       {metrics['prototype_approvals']} ({metrics['prototype_approval_rate']}%)")
    print(f"Prototype Revocations:                      {metrics['prototype_revocations']}")
    print(f"Prototype Modifications:                    {metrics['prototype_modifications']}")
    print(f"Reduction in Percentage Points (pp):        {metrics['approval_rate_reduction_percentage_points']} pp")
    print(f"Relative Approval-Rate Reduction:           {metrics['relative_approval_rate_reduction']}%")
    print("---------------------------------------------------------")
    print("Risk Breakdown:")
    print(f"  - High Risk Cases:                        {metrics['high_risk_cases']}")
    print(f"  - Medium Risk Cases:                      {metrics['medium_risk_cases']}")
    print(f"  - Low Risk Cases:                         {metrics['low_risk_cases']}")
    print("Evidence Trigger Cases:")
    print(f"  - Unused Privileges:                      {metrics['unused_privilege_cases']}")
    print(f"  - High Privileges:                        {metrics['high_privilege_cases']}")
    print(f"  - Low Usage vs Peers:                     {metrics['low_usage_vs_peer_cases']}")
    print(f"  - Inactive Users:                         {metrics['inactive_user_cases']}")
    print("---------------------------------------------------------")
    print(f"Outputs written to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")
    print("=========================================================")


if __name__ == "__main__":
    main()
