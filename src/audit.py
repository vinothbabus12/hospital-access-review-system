import uuid
from datetime import datetime
import pandas as pd
from src.database import get_db_connection, execute_non_query, execute_query

def record_reviewer_decision(user_id, entitlement_id, system_rec, reviewer_decision, override, reason, reviewer, risk_score=0):
    """
    Saves a reviewer decision to SQLite and appends an immutable audit log record.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    override_val = 1 if override else 0

    # 1. Update or Insert into review_decisions
    cursor.execute("""
    INSERT INTO review_decisions (decision_id, user_id, entitlement_id, risk_score, recommendation, reviewer_decision, override, reason, reviewer, decision_timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(decision_id) DO UPDATE SET
        reviewer_decision=excluded.reviewer_decision,
        override=excluded.override,
        reason=excluded.reason,
        reviewer=excluded.reviewer,
        decision_timestamp=excluded.decision_timestamp
    """, (decision_id, user_id, entitlement_id, risk_score, system_rec, reviewer_decision, override_val, reason, reviewer, timestamp))

    # 2. Append to immutable audit_log
    cursor.execute("""
    INSERT INTO audit_log (decision_id, user_id, entitlement_id, risk_score, system_recommendation, reviewer_decision, override, reason, reviewer, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (decision_id, user_id, entitlement_id, risk_score, system_rec, reviewer_decision, override_val, reason, reviewer, timestamp))

    conn.commit()
    conn.close()
    return decision_id

def get_audit_trail():
    query = """
    SELECT 
        al.log_id,
        al.decision_id,
        al.user_id,
        COALESCE(u.name, al.user_id) as user_name,
        u.role,
        al.entitlement_id,
        e.application,
        e.permission,
        al.risk_score,
        al.system_recommendation,
        al.reviewer_decision,
        al.override,
        al.reason,
        al.reviewer,
        al.timestamp
    FROM audit_log al
    LEFT JOIN users u ON al.user_id = u.user_id
    LEFT JOIN entitlements e ON al.entitlement_id = e.entitlement_id
    ORDER BY al.log_id DESC
    """
    return execute_query(query)
