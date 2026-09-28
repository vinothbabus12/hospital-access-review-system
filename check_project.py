import sys, os, datetime, uuid
sys.path.insert(0, '.')
results = {"WORKING": [], "ERRORS": [], "MISSING": [], "NEEDS_FIXING": []}

# ─── 1. File presence check ────────────────────────────────────────────────
required_files = [
    "app.py", "requirements.txt", "README.md",
    "docs/ARCHITECTURE.md", "docs/TESTING.md", "docs/BASELINE_COMPARISON.md",
    "src/__init__.py", "src/audit.py", "src/baseline.py",
    "src/data_generator.py", "src/data_processor.py",
    "src/database.py", "src/evidence_engine.py", "src/risk_engine.py",
    "data/users.csv", "data/entitlements.csv",
    "data/usage_events.csv", "data/review_decisions.csv",
    "database/hospital_access.db",
    "tests/__init__.py",
    "tests/test_baseline.py", "tests/test_data_validation.py",
    "tests/test_database.py", "tests/test_delayed_events.py",
    "tests/test_duplicates.py", "tests/test_evidence_engine.py",
    "tests/test_missing_data.py", "tests/test_out_of_order.py",
    "tests/test_risk_engine.py",
]
for f in required_files:
    if os.path.exists(f):
        results["WORKING"].append(f"FILE PRESENT: {f}")
    else:
        results["MISSING"].append(f"FILE MISSING: {f}")

# ─── 2. Module imports ─────────────────────────────────────────────────────
modules = {
    "data_generator": "from src.data_generator import generate_synthetic_data, DATA_DIR",
    "database": "from src.database import load_csv_data_to_db, get_db_connection, save_review_decision, retrieve_review_decisions, retrieve_users, retrieve_entitlements, retrieve_usage_events",
    "data_processor": "from src.data_processor import DataProcessor",
    "evidence_engine": "from src.evidence_engine import evaluate_all_entitlements, generate_evidence_record",
    "risk_engine": "from src.risk_engine import get_risk_summary, get_high_risk_privileges_by_role, evaluate_risk",
    "audit": "from src.audit import record_reviewer_decision, get_audit_trail",
    "baseline": "from src.baseline import run_baseline_experiment",
}
for name, stmt in modules.items():
    try:
        exec(stmt)
        results["WORKING"].append(f"IMPORT OK: src/{name}.py")
    except Exception as e:
        results["ERRORS"].append(f"IMPORT FAIL src/{name}.py: {e}")

# Execute imports for real usage below
from src.database import (retrieve_users, retrieve_entitlements, retrieve_usage_events,
                          save_review_decision, retrieve_review_decisions)
from src.data_processor import DataProcessor
from src.evidence_engine import evaluate_all_entitlements
from src.risk_engine import evaluate_risk, get_risk_summary
from src.audit import record_reviewer_decision, get_audit_trail
from src.baseline import run_baseline_experiment

# ─── 3. CSV datasets ───────────────────────────────────────────────────────
import pandas as pd
csv_checks = {
    "data/users.csv": ("user_id", 100),
    "data/entitlements.csv": ("entitlement_id", 100),
    "data/usage_events.csv": ("event_id", 100),
    "data/review_decisions.csv": ("decision_id", 1),
}
for path, (col, min_rows) in csv_checks.items():
    try:
        df = pd.read_csv(path)
        if col in df.columns and len(df) >= min_rows:
            results["WORKING"].append(f"CSV OK: {path} ({len(df)} rows)")
        else:
            results["ERRORS"].append(f"CSV ISSUE: {path} missing col '{col}' or too few rows ({len(df)})")
    except Exception as e:
        results["ERRORS"].append(f"CSV FAIL: {path}: {e}")

# ─── 4. SQLite DB retrieve ─────────────────────────────────────────────────
try:
    users = retrieve_users()
    ents = retrieve_entitlements()
    events = retrieve_usage_events()
    assert len(users) > 0, "users table empty"
    assert len(ents) > 0, "entitlements table empty"
    assert len(events) > 0, "usage_events table empty"
    results["WORKING"].append(f"SQLITE RETRIEVE: users={len(users)}, entitlements={len(ents)}, events={len(events)}")
except Exception as e:
    results["ERRORS"].append(f"SQLITE RETRIEVE FAIL: {e}")

# ─── 5. save_review_decision (dict signature) ─────────────────────────────
try:
    decision = {
        "decision_id": "DEC-HEALTHCHK",
        "user_id": "USR-TEST",
        "entitlement_id": "ENT-TEST",
        "risk_score": 70,
        "recommendation": "REVOKE",
        "reviewer_decision": "REVOKE",
        "override": 0,
        "reason": "Health check test",
        "reviewer": "health_check_script",
        "decision_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_review_decision(decision)
    saved = retrieve_review_decisions()
    found = saved[saved["reviewer"] == "health_check_script"]
    assert len(found) >= 1
    results["WORKING"].append(f"SAVE/RETRIEVE DECISION: OK ({len(found)} records saved)")
except Exception as e:
    results["ERRORS"].append(f"SAVE DECISION FAIL: {e}")

# ─── 6. audit trail with override ─────────────────────────────────────────
try:
    dec_id = record_reviewer_decision(
        user_id="USR-TEST",
        entitlement_id="ENT-TEST",
        system_rec="REVOKE",
        reviewer_decision="OVERRIDE",
        override=True,
        reason="Override reason check",
        reviewer="health_check_script",
        risk_score=70,
    )
    trail = get_audit_trail()
    override_rows = trail[trail["override"] == 1]
    assert len(override_rows) >= 1, "No override=1 rows in audit trail"
    assert dec_id.startswith("DEC-"), f"Bad decision_id format: {dec_id}"
    results["WORKING"].append(f"AUDIT TRAIL + OVERRIDE: OK (dec_id={dec_id}, {len(trail)} total entries)")
except Exception as e:
    results["ERRORS"].append(f"AUDIT TRAIL FAIL: {e}")

# ─── 7. Evidence + Risk calculations ──────────────────────────────────────
try:
    processor = DataProcessor(retrieve_users(), retrieve_entitlements(), retrieve_usage_events())
    baseline_df = processor.get_peer_usage_baseline()
    assert not baseline_df.empty, "Peer baseline is empty"

    df_ev = evaluate_all_entitlements(baseline_df)
    assert not df_ev.empty, "Evaluated entitlements empty"
    assert "risk_score" in df_ev.columns
    assert "risk_level" in df_ev.columns
    assert "recommendation" in df_ev.columns
    assert "evidence_codes" in df_ev.columns

    # Verify INACTIVE_USER is correctly detected (status_x/status_y bug must be fixed)
    inactive_ents = df_ev[df_ev["status"] == "INACTIVE"]
    if len(inactive_ents) > 0:
        has_inactive_flag = inactive_ents["evidence_codes"].apply(lambda codes: "INACTIVE_USER" in codes).any()
        assert has_inactive_flag, "INACTIVE_USER evidence not firing for inactive users (status column bug)"

    high_risk = df_ev[df_ev["risk_level"] == "HIGH"]
    results["WORKING"].append(
        f"EVIDENCE+RISK CALC: OK ({len(df_ev)} entitlements, {len(high_risk)} HIGH risk)"
    )
except Exception as e:
    results["ERRORS"].append(f"EVIDENCE/RISK CALC FAIL: {e}")

# ─── 8. Baseline experiment ───────────────────────────────────────────────
try:
    processor2 = DataProcessor(retrieve_users(), retrieve_entitlements(), retrieve_usage_events())
    df_ev2 = evaluate_all_entitlements(processor2.get_peer_usage_baseline())
    exp = run_baseline_experiment(df_ev2)
    assert exp["total_cases"] > 0
    assert 0 <= exp["baseline_blanket_approval_rate"] <= 100
    assert 0 <= exp["prototype_blanket_approval_rate"] <= 100
    results["WORKING"].append(
        f"BASELINE EXPERIMENT: OK (total={exp['total_cases']}, "
        f"overall_approval: baseline={exp['baseline_approval_rate']}% prototype={exp['prototype_approval_rate']}%, "
        f"blanket_approval: baseline={exp['baseline_blanket_approval_rate']}% prototype={exp['prototype_blanket_approval_rate']}%, "
        f"reduction={exp['reduction_percentage_points']}pp)"
    )
except Exception as e:
    results["ERRORS"].append(f"BASELINE EXPERIMENT FAIL: {e}")

# ─── 9. data_generator emoji encoding check ──────────────────────────────
try:
    import ast
    with open("src/data_generator.py", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    # Find print statements with emoji
    emoji_prints = [line for line in src.splitlines() if "\\u2705" in line or "\u2705" in line]
    if emoji_prints:
        results["NEEDS_FIXING"].append(
            "data_generator.py: print() calls contain emoji that crash on Windows cp1252 terminal "
            "(UnicodeEncodeError). Fix: add encoding='utf-8' or replace emoji with ASCII text."
        )
    else:
        results["WORKING"].append("data_generator.py: No emoji encoding issues found in source")
except Exception as e:
    results["ERRORS"].append(f"data_generator check fail: {e}")

# ─── Print final report ───────────────────────────────────────────────────
print("\n" + "="*60)
print("WORKING:")
for item in results["WORKING"]:
    print(f"  - {item}")

print("\nERRORS:")
for item in results["ERRORS"]:
    print(f"  - {item}")

print("\nMISSING:")
for item in results["MISSING"]:
    print(f"  - {item}")

print("\nNEEDS FIXING:")
for item in results["NEEDS_FIXING"]:
    print(f"  - {item}")

print("="*60)
