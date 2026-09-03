import os
import pandas as pd
from datetime import datetime


def calculate_risk_score(entitlement_row):
    """
    Computes a transparent, rule-based risk score for a single entitlement record.

    Rules:
    - Unused privilege (user_usage == 0): +40
    - ADMIN permission (permission == 'ADMIN'): +30
    - Usage significantly below peer baseline (user_usage < 0.2 * peer_average and peer_average >= 1.0): +20
    - Inactive user (status == 'INACTIVE'): +20
    - Recently granted privilege (< 30 days): +10

    Risk Levels:
    - 0-29: LOW
    - 30-59: MEDIUM
    - 60+: HIGH

    Recommendations:
    - LOW -> APPROVE
    - MEDIUM -> REVIEW
    - HIGH -> REVOKE (if unused or inactive) or REVIEW (if active high-risk)
    """
    if isinstance(entitlement_row, pd.Series):
        row = entitlement_row.to_dict()
    else:
        row = dict(entitlement_row)

    risk_score = 0
    evidence_items = []

    user_usage = int(row.get("user_usage", 0))
    peer_avg = float(row.get("peer_average", 0.0))
    permission = str(row.get("permission", "")).upper()
    user_status = str(row.get("status", "")).upper()
    granted_date_str = str(row.get("granted_date", ""))

    # 1. Unused privilege (+40)
    if user_usage == 0:
        risk_score += 40
        evidence_items.append("Privilege unused (+40)")

    # 2. ADMIN permission (+30)
    if permission in ["ADMIN", "ALL"]:
        risk_score += 30
        evidence_items.append("ADMIN permission (+30)")
    elif permission == "READ_WRITE":
        risk_score += 10
        evidence_items.append("Elevated permission (READ_WRITE) (+10)")

    # 3. Usage significantly below peer baseline (+20) (applied when user_usage > 0)
    if user_usage > 0 and peer_avg >= 1.0 and user_usage < (peer_avg * 0.2):
        risk_score += 20
        evidence_items.append(f"Usage significantly below peer baseline (User: {user_usage}, Peer Avg: {peer_avg:.1f}) (+20)")

    # 4. Inactive user (+20)
    if user_status == "INACTIVE":
        risk_score += 20
        evidence_items.append("Inactive user account (+20)")

    # 5. Recently granted privilege (+10)
    try:
        granted_dt = datetime.strptime(granted_date_str, "%Y-%m-%d")
        if (datetime.now() - granted_dt).days < 30:
            risk_score += 10
            evidence_items.append(f"Recently granted privilege (< 30 days, granted {granted_date_str}) (+10)")
    except Exception:
        pass

    # Determine Risk Level (0-29: LOW, 30-59: MEDIUM, 60+: HIGH)
    if risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Determine Recommendation and Explainable Reason
    if risk_level == "LOW":
        recommendation = "APPROVE"
        recommendation_reason = "Privilege usage aligns with low risk guidelines. Access should be approved."
    elif risk_level == "MEDIUM":
        recommendation = "REVIEW"
        recommendation_reason = "Elevated risk factors detected. Manual reviewer verification recommended."
    else:  # HIGH risk (60+)
        if user_usage == 0:
            recommendation = "REVOKE"
            recommendation_reason = "High risk entitlement with zero actual usage. Recommend revoking access."
        elif user_status == "INACTIVE":
            recommendation = "REVOKE"
            recommendation_reason = "High risk entitlement for inactive employee account. Recommend immediate revocation."
        else:
            recommendation = "REVIEW"
            recommendation_reason = "High risk entitlement for active staff member. Requires manager review before decision."

    evidence_text = "\n".join([f"* {item}" for item in evidence_items]) if evidence_items else "* Standard usage aligned with peer baseline"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "evidence": evidence_text,
        "evidence_list": evidence_items,
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason
    }


def evaluate_risk(df_baseline):
    """
    Evaluates risk scores and recommendations across a DataFrame of entitlements.
    """
    if df_baseline is None or df_baseline.empty:
        return pd.DataFrame()

    records = []
    for _, row in df_baseline.iterrows():
        eval_res = calculate_risk_score(row)
        row_dict = row.to_dict()
        row_dict.update({
            "risk_score": eval_res["risk_score"],
            "risk_level": eval_res["risk_level"],
            "evidence": eval_res["evidence"],
            "recommendation": eval_res["recommendation"],
            "recommendation_reason": eval_res["recommendation_reason"]
        })
        records.append(row_dict)

    return pd.DataFrame(records)


def get_risk_summary(df_evaluated):
    """
    Computes overall risk and entitlement summary metrics for UI dashboard.
    """
    if df_evaluated is None or df_evaluated.empty:
        return {
            "total_users": 0,
            "total_entitlements": 0,
            "high_risk_count": 0,
            "unused_count": 0,
            "pending_reviews": 0
        }

    total_users = df_evaluated["user_id"].nunique() if "user_id" in df_evaluated.columns else 0
    total_entitlements = len(df_evaluated)
    high_risk_count = len(df_evaluated[df_evaluated["risk_level"] == "HIGH"]) if "risk_level" in df_evaluated.columns else 0
    unused_count = len(df_evaluated[df_evaluated["user_usage"] == 0]) if "user_usage" in df_evaluated.columns else 0
    pending_reviews = len(df_evaluated[df_evaluated["recommendation"].isin(["REVIEW", "REVOKE"])]) if "recommendation" in df_evaluated.columns else 0

    return {
        "total_users": total_users,
        "total_entitlements": total_entitlements,
        "high_risk_count": high_risk_count,
        "unused_count": unused_count,
        "pending_reviews": pending_reviews
    }


def get_high_risk_privileges_by_role(df_evaluated):
    if df_evaluated is None or df_evaluated.empty or "risk_level" not in df_evaluated.columns:
        return pd.DataFrame()

    high_risk_df = df_evaluated[df_evaluated["risk_level"] == "HIGH"]
    if high_risk_df.empty:
        return pd.DataFrame(columns=["role", "high_risk_count"])
    grouped = high_risk_df.groupby("role").size().reset_index(name="high_risk_count")
    return grouped.sort_values(by="high_risk_count", ascending=False)

