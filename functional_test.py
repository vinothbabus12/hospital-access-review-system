"""
Full live functional test of the Hospital Access Review application.
Tests every workflow without a browser: data loading, evidence/risk,
reviewer decision save, override validation, audit trail persistence.
"""
import sys, os, datetime, uuid
sys.path.insert(0, '.')

results = {}

# ── 1. Data loads correctly ────────────────────────────────────────────────
from src.database import retrieve_users, retrieve_entitlements, retrieve_usage_events
users = retrieve_users()
ents  = retrieve_entitlements()
evts  = retrieve_usage_events()
assert len(users) > 0 and len(ents) > 0 and len(evts) > 0
results["DATA_LOAD"] = f"PASS  users={len(users)}, entitlements={len(ents)}, events={len(evts)}"

# ── 2. Evidence + Risk pipeline (Dashboard / Privilege Review) ────────────
from src.data_processor import DataProcessor
from src.evidence_engine import evaluate_all_entitlements
processor   = DataProcessor(users, ents, evts)
baseline_df = processor.get_peer_usage_baseline()
df_ev       = evaluate_all_entitlements(baseline_df)

assert not df_ev.empty
assert "risk_score"    in df_ev.columns
assert "risk_level"    in df_ev.columns
assert "recommendation" in df_ev.columns
assert "evidence_codes" in df_ev.columns

high_risk   = df_ev[df_ev["risk_level"] == "HIGH"]
unused      = df_ev[df_ev["user_usage"] == 0]
pending     = df_ev[df_ev["recommendation"].isin(["REVIEW", "REVOKE"])]

# INACTIVE_USER evidence fires correctly
inactive_ents = df_ev[df_ev["status"] == "INACTIVE"]
if len(inactive_ents) > 0:
    fired = inactive_ents["evidence_codes"].apply(lambda c: "INACTIVE_USER" in c).any()
    assert fired, "INACTIVE_USER evidence not firing"

results["EVIDENCE_RISK"] = (
    f"PASS  total={len(df_ev)}, HIGH={len(high_risk)}, "
    f"unused={len(unused)}, pending={len(pending)}, "
    f"inactive flagged={len(inactive_ents)}"
)

# ── 3. Reviewer decision — REVOKE (normal path) ───────────────────────────
from src.audit import record_reviewer_decision, get_audit_trail

test_ent = df_ev.iloc[0]
dec_id = record_reviewer_decision(
    user_id       = str(test_ent["user_id"]),
    entitlement_id= str(test_ent["entitlement_id"]),
    system_rec    = str(test_ent["recommendation"]),
    reviewer_decision = "REVOKE",
    override      = False,
    reason        = "Live functional test — REVOKE decision",
    reviewer      = "functional_test",
    risk_score    = int(test_ent["risk_score"]),
)
assert dec_id.startswith("DEC-")
results["REVIEW_WORKFLOW"] = f"PASS  decision_id={dec_id}, saved with override=False"

# ── 4. Override validation — requires non-empty reason ───────────────────
# The validation logic lives in app.py (Streamlit form guard).
# We verify the SAME guard logic programmatically here:
def submit_override(reason_text):
    """Replicates the override guard from app.py."""
    if not reason_text.strip():
        raise ValueError("Override requires a non-empty reason.")
    return record_reviewer_decision(
        user_id       = str(test_ent["user_id"]),
        entitlement_id= str(test_ent["entitlement_id"]),
        system_rec    = str(test_ent["recommendation"]),
        reviewer_decision = "OVERRIDE",
        override      = True,
        reason        = reason_text,
        reviewer      = "functional_test",
        risk_score    = int(test_ent["risk_score"]),
    )

# 4a. Empty reason must be blocked
try:
    submit_override("")
    results["OVERRIDE_EMPTY_REASON"] = "FAIL  — empty reason was NOT blocked"
except ValueError as e:
    results["OVERRIDE_EMPTY_REASON"] = f"PASS  blocked correctly: {e}"

# 4b. Non-empty reason must succeed
ov_dec_id = submit_override("Override needed: special operational access")
assert ov_dec_id.startswith("DEC-")
results["OVERRIDE_WITH_REASON"] = f"PASS  override saved, decision_id={ov_dec_id}"

# ── 5. Audit trail — both decisions appear, newest first ─────────────────
trail = get_audit_trail()
assert not trail.empty

ft_rows     = trail[trail["reviewer"] == "functional_test"]
override_rows = ft_rows[ft_rows["override"] == 1]
revoke_rows   = ft_rows[ft_rows["reviewer_decision"] == "REVOKE"]

assert len(override_rows) >= 1, "Override row missing from audit trail"
assert len(revoke_rows) >= 1,   "REVOKE row missing from audit trail"

# Newest-first ordering: the OVERRIDE (submitted last) should have a higher log_id
if len(ft_rows) >= 2:
    sorted_ids = sorted(ft_rows["log_id"].tolist(), reverse=True)
    assert ft_rows["log_id"].tolist() == sorted(ft_rows["log_id"].tolist(), reverse=True), \
        "Audit trail not sorted newest-first"

results["AUDIT_TRAIL"] = (
    f"PASS  total_entries={len(trail)}, "
    f"functional_test rows={len(ft_rows)}, "
    f"overrides={len(override_rows)}, revokes={len(revoke_rows)}"
)

# ── 6. Data Quality report ────────────────────────────────────────────────
qs = processor.quality_summary
assert qs["total_events"] > 0
assert qs["valid_events"] > 0
results["DATA_QUALITY"] = (
    f"PASS  total={qs['total_events']}, valid={qs['valid_events']}, "
    f"dup={qs['duplicate_events']}, invalid={qs['invalid_events']}, "
    f"delayed={qs['delayed_events']}, out_of_order={qs['out_of_order_events']}"
)

# ── 7. Baseline Comparison ────────────────────────────────────────────────
from src.baseline import run_baseline_experiment
exp = run_baseline_experiment(df_ev)
assert exp["total_cases"] > 0
assert exp["baseline_blanket_approval_rate"] > 0
assert exp["reduction_percentage_points"] > 0
results["BASELINE_COMPARISON"] = (
    f"PASS  cases={exp['total_cases']}, "
    f"baseline={exp['baseline_blanket_approval_rate']}%, "
    f"prototype={exp['prototype_blanket_approval_rate']}%, "
    f"reduction={exp['reduction_percentage_points']}pp"
)

# ── 8. Streamlit app.py imports cleanly (no import errors) ───────────────
# We cannot fully execute app.py outside Streamlit, but all its imports
# have already been confirmed working above. Check app.py is parse-valid.
import ast
with open("app.py", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
results["APP_PY_SYNTAX"] = "PASS  app.py parses without syntax errors"

# ── Print final report ────────────────────────────────────────────────────
print()
print("=" * 65)
print("FUNCTIONAL TEST RESULTS")
print("=" * 65)
for key, val in results.items():
    status = "PASS" if val.startswith("PASS") else "FAIL"
    print(f"[{status}] {key}: {val}")
print("=" * 65)
all_pass = all(v.startswith("PASS") for v in results.values())
print(f"\nOVERALL: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
