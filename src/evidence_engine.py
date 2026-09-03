import pandas as pd
from datetime import datetime


def generate_evidence_record(entitlement_row):
    """
    Generates a transparent, explainable evidence record for an entitlement based on peer-role baselines
    and deterministic security rules. No machine learning is used.

    Calculates:
    - user's usage count (user_usage)
    - last usage date (last_usage_date)
    - peer average usage (peer_average)
    - peer median usage (peer_median)
    - difference from peer usage (difference_from_peer)

    Generates evidence codes:
    - UNUSED_PRIVILEGE: user usage count is 0
    - HIGH_PRIVILEGE: ADMIN or READ_WRITE permission assigned
    - LOW_USAGE_VS_PEERS: user usage significantly below role peer average/median
    - HIGH_USAGE_VS_PEERS: user usage anomalously high compared to role peer average/median
    - INACTIVE_USER: account is marked INACTIVE in HR database
    """
    if isinstance(entitlement_row, pd.Series):
        row = entitlement_row.to_dict()
    else:
        row = dict(entitlement_row)

    risk_score = 0
    evidence_codes = []
    evidence_descriptions = []

    user_usage = int(row.get("user_usage", 0))
    peer_avg = float(row.get("peer_average", 0.0))
    peer_med = float(row.get("peer_median", 0.0))
    permission = str(row.get("permission", "")).upper()
    user_status = str(row.get("status", "")).upper()
    role = str(row.get("role", "Peer"))
    granted_date_str = str(row.get("granted_date", ""))
    last_usage_date = str(row.get("last_usage_date", "Never"))

    # 1. UNUSED_PRIVILEGE (+40)
    if user_usage == 0:
        risk_score += 40
        evidence_codes.append("UNUSED_PRIVILEGE")
        evidence_descriptions.append("Privilege is completely unused in application logs (0 accesses) (+40)")

    # 2. HIGH_PRIVILEGE (+30 for ADMIN, +10 for READ_WRITE)
    if permission in ["ADMIN", "ALL"]:
        risk_score += 30
        evidence_codes.append("HIGH_PRIVILEGE")
        evidence_descriptions.append("High-level permission (ADMIN) assigned (+30)")
    elif permission == "READ_WRITE":
        risk_score += 10
        evidence_codes.append("HIGH_PRIVILEGE")
        evidence_descriptions.append("Elevated permission (READ_WRITE) assigned (+10)")

    # 3. Peer Usage Deviations (LOW_USAGE_VS_PEERS / HIGH_USAGE_VS_PEERS)
    if user_usage > 0 and peer_avg >= 1.0 and user_usage < (peer_avg * 0.2):
        risk_score += 20
        evidence_codes.append("LOW_USAGE_VS_PEERS")
        evidence_descriptions.append(
            f"Usage ({user_usage}) is significantly lower than {role} peer average ({peer_avg:.1f}) & median ({peer_med:.1f}) (+20)"
        )
    elif peer_avg >= 5.0 and user_usage > (peer_avg * 3.0):
        risk_score += 15
        evidence_codes.append("HIGH_USAGE_VS_PEERS")
        evidence_descriptions.append(
            f"Usage ({user_usage}) is anomalously higher than {role} peer average ({peer_avg:.1f}) & median ({peer_med:.1f}) (+15)"
        )

    # 4. INACTIVE_USER (+20)
    if user_status == "INACTIVE":
        risk_score += 20
        evidence_codes.append("INACTIVE_USER")
        evidence_descriptions.append("User account is marked INACTIVE in HR database (+20)")

    # 5. Recently Granted Privilege (+10)
    try:
        granted_dt = datetime.strptime(granted_date_str, "%Y-%m-%d")
        if (datetime.now() - granted_dt).days < 30:
            risk_score += 10
            evidence_codes.append("RECENTLY_GRANTED")
            evidence_descriptions.append(f"Privilege recently granted within past 30 days ({granted_date_str}) (+10)")
    except Exception:
        pass

    # Determine Risk Level
    if risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Determine System Recommendation
    if risk_score >= 60:
        if user_usage == 0 or user_status == "INACTIVE":
            recommendation = "REVOKE"
        else:
            recommendation = "REVIEW"
    elif risk_score >= 30:
        recommendation = "REVIEW"
    else:
        recommendation = "APPROVE"

    evidence_text = "\n".join([f"• {e}" for e in evidence_descriptions]) if evidence_descriptions else "• Standard low-risk usage aligned with peer role"

    # Transparent, human-explainable baseline calculation string
    diff_val = round(user_usage - peer_avg, 1)
    explanation = (
        f"Role: {role} | User Usage: {user_usage} | Peer Avg: {peer_avg:.1f} | "
        f"Peer Median: {peer_med:.1f} | Diff: {diff_val:+.1f} | "
        f"Last Used: {last_usage_date} | Evidence Codes: {', '.join(evidence_codes) if evidence_codes else 'NONE'}"
    )

    return {
        "user_usage": user_usage,
        "last_usage_date": last_usage_date,
        "peer_average": peer_avg,
        "peer_median": peer_med,
        "difference_from_peer": diff_val,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "evidence_codes": evidence_codes,
        "evidence_list": evidence_descriptions,
        "evidence": evidence_text,
        "recommendation": recommendation,
        "explanation": explanation
    }


def calculate_evidence_and_risk(entitlement_row):
    """
    Alias function for backwards compatibility with existing application components.
    """
    return generate_evidence_record(entitlement_row)


def evaluate_all_entitlements(df_baseline):
    """
    Evaluates all entitlements in df_baseline and returns an enriched DataFrame with
    peer metrics, evidence codes, risk scores, levels, evidence summaries, and recommendations.
    """
    if df_baseline is None or df_baseline.empty:
        return pd.DataFrame()

    records = []
    for _, row in df_baseline.iterrows():
        eval_res = generate_evidence_record(row)
        row_dict = row.to_dict()
        row_dict.update({
            "user_usage": eval_res["user_usage"],
            "last_usage_date": eval_res["last_usage_date"],
            "peer_average": eval_res["peer_average"],
            "peer_median": eval_res["peer_median"],
            "difference_from_peer": eval_res["difference_from_peer"],
            "risk_score": eval_res["risk_score"],
            "risk_level": eval_res["risk_level"],
            "evidence_codes": eval_res["evidence_codes"],
            "evidence": eval_res["evidence"],
            "recommendation": eval_res["recommendation"],
            "explanation": eval_res["explanation"]
        })
        records.append(row_dict)

    return pd.DataFrame(records)

