# experiments/validation_cases.py
"""Validation Case Cohort for Simulated Stakeholder Validation.
Selects 25 representative access-review cases from the evaluated synthetic dataset
spanning all 4 staff types, multiple roles, applications, permissions, risk levels,
and evidence profiles.

Simulates realistic, independent reviewer decisions grounded in clinical, operational,
and compliance context, including documented intentional disagreements for error analysis.
"""

import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# List of valid disagreement categories
VALID_DISAGREEMENT_CATEGORIES = [
    "legitimate exception",
    "insufficient context",
    "peer-group mismatch",
    "unusual but valid usage",
    "stale/incomplete data",
    "rule too aggressive",
    "rule too conservative",
    "other"
]

VALID_DECISIONS = ["APPROVE", "REVOKE", "MODIFY", "REVIEW"]


def get_curated_validation_cases(df_evaluated=None):
    """Extracts and annotates 25 realistic validation cases from the evaluated dataset.
    The system recommendation is taken strictly from existing engine output.
    Reviewer decisions are simulated using documented operational criteria.
    """
    if df_evaluated is None or df_evaluated.empty:
        from experiments.baseline_experiment import load_and_process_data
        _, _, _, _, df_evaluated = load_and_process_data()

    if df_evaluated.empty:
        return []

    # Filter subsets across staff types to ensure balanced, realistic representation
    perm_df = df_evaluated[df_evaluated["staff_type"] == "Permanent Staff"]
    visit_df = df_evaluated[df_evaluated["staff_type"] == "Visiting Consultant"]
    intern_df = df_evaluated[df_evaluated["staff_type"] == "Intern"]
    out_df = df_evaluated[df_evaluated["staff_type"] == "Outsourced Technician"]

    # Helper to pick row safely matching filters, with fallback
    def pick_row(source_df, risk=None, rec=None, perm=None, app=None):
        sub = source_df
        if risk:
            match = sub[sub["risk_level"] == risk]
            if not match.empty:
                sub = match
        if rec:
            match = sub[sub["recommendation"] == rec]
            if not match.empty:
                sub = match
        if perm:
            match = sub[sub["permission"] == perm]
            if not match.empty:
                sub = match
        if app:
            match = sub[sub["application"] == app]
            if not match.empty:
                sub = match
        return sub.iloc[0] if not sub.empty else source_df.iloc[0]

    case_definitions = [
        # =========================================================================
        # 1. PERMANENT STAFF (7 cases)
        # =========================================================================
        {
            "id": "VAL-001",
            "source": perm_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "Permanent nurse with routine clinical EMR usage matching department peer baseline.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-002",
            "source": perm_df,
            "filters": {"risk": "LOW", "rec": "APPROVE", "app": "Pharmacy"},
            "reviewer_decision": "APPROVE",
            "reason": "Hospital pharmacist actively dispensing medication; daily usage matches role requirements.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-003",
            "source": perm_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "REVIEW",
            "reason": "Staff member with unused WRITE permission for 60 days; secondary supervisor confirmation needed.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-004",
            "source": perm_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Administrative privilege completely unused in logs; violates principle of least privilege.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-005",
            "source": perm_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "APPROVE",
            "reason": "Department Head clinician with administrative and teaching responsibilities; lower patient entry count than peers is expected.",
            "disagreement_cat": "peer-group mismatch"
        },
        {
            "id": "VAL-006",
            "source": perm_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Staff account flagged INACTIVE in HR registry; immediate credential deprovisioning mandatory.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-007",
            "source": perm_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "REVOKE",
            "reason": "Staff member transferred from Emergency to Outpatient last week; legacy acute care permissions must be revoked.",
            "disagreement_cat": "stale/incomplete data"
        },

        # =========================================================================
        # 2. VISITING CONSULTANT (6 cases)
        # =========================================================================
        {
            "id": "VAL-008",
            "source": visit_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "Visiting surgeon with confirmed surgical schedule and verified EMR clinical access.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-009",
            "source": visit_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "APPROVE",
            "reason": "Specialist consultant on bi-monthly on-call duty; sparse log frequency is standard for this contract.",
            "disagreement_cat": "legitimate exception"
        },
        {
            "id": "VAL-010",
            "source": visit_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Visiting cardiologist contract concluded; unmonitored privileges must be deprovisioned.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-011",
            "source": visit_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "REVIEW",
            "reason": "Elevated access privileges on Laboratory portal require written sign-off from Head of Pathology.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-012",
            "source": visit_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Visiting consultant inactive in HR system with zero accesses in 90 days.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-013",
            "source": visit_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "PACS radiology image viewing access verified for active clinical diagnostic consults.",
            "disagreement_cat": None
        },

        # =========================================================================
        # 3. INTERN (6 cases)
        # =========================================================================
        {
            "id": "VAL-014",
            "source": intern_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "Medical intern assigned to general ward rotation with documented supervisor oversight.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-015",
            "source": intern_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "APPROVE",
            "reason": "Intern on approved two-week academic rotation leave returning next Monday; access should not be suspended.",
            "disagreement_cat": "stale/incomplete data"
        },
        {
            "id": "VAL-016",
            "source": intern_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Intern possessing ADMIN/unrestricted WRITE access violates trainee role policies.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-017",
            "source": intern_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "Laboratory viewer role active and appropriate for internal medicine residency training.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-018",
            "source": intern_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "REVIEW",
            "reason": "Trainee usage patterns show infrequent access; clinical mentor needs to re-validate scope.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-019",
            "source": intern_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Completed internship residency period; accounts must be closed according to HR exit policy.",
            "disagreement_cat": None
        },

        # =========================================================================
        # 4. OUTSOURCED TECHNICIAN (6 cases)
        # =========================================================================
        {
            "id": "VAL-020",
            "source": out_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "MODIFY",
            "reason": "Vendor SLA contract was renegotiated to read-only diagnostics; WRITE permission should be downgraded.",
            "disagreement_cat": "insufficient context"
        },
        {
            "id": "VAL-021",
            "source": out_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Third-party technician retaining dormant root administrative access without active statement of work.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-022",
            "source": out_df,
            "filters": {"risk": "LOW", "rec": "APPROVE"},
            "reviewer_decision": "APPROVE",
            "reason": "Contract biomedical engineer actively servicing diagnostic radiology imaging hardware.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-023",
            "source": out_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "REVIEW",
            "reason": "Contractor access to billing database has had low usage; requires vendor management verification.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-024",
            "source": out_df,
            "filters": {"risk": "HIGH", "rec": "REVOKE"},
            "reviewer_decision": "REVOKE",
            "reason": "Contractor employment terminated by vendor agency; immediate credential revocation mandated.",
            "disagreement_cat": None
        },
        {
            "id": "VAL-025",
            "source": out_df,
            "filters": {"risk": "MEDIUM", "rec": "REVIEW"},
            "reviewer_decision": "APPROVE",
            "reason": "Technician ran automated end-of-month calibration batch scripts, causing usage deviation; verified as legitimate.",
            "disagreement_cat": "unusual but valid usage"
        },
    ]

    selected_cases = []
    used_entitlements = set()

    for item in case_definitions:
        source_df = item["source"]
        filters = item["filters"]

        # Find row matching criteria not already selected
        candidates = source_df
        if "risk" in filters:
            candidates = candidates[candidates["risk_level"] == filters["risk"]]
        if "rec" in filters:
            candidates = candidates[candidates["recommendation"] == filters["rec"]]
        if "app" in filters:
            c_app = candidates[candidates["application"] == filters["app"]]
            if not c_app.empty:
                candidates = c_app

        # Filter out already used
        fresh_candidates = candidates[~candidates["entitlement_id"].isin(used_entitlements)]
        if not fresh_candidates.empty:
            chosen = fresh_candidates.iloc[0]
        elif not candidates.empty:
            chosen = candidates.iloc[0]
        else:
            chosen = source_df.iloc[0]

        used_entitlements.add(chosen["entitlement_id"])

        system_rec = str(chosen["recommendation"]).upper()
        rev_dec = item["reviewer_decision"].upper()
        agreement = (system_rec == rev_dec)

        ev_flags = chosen.get("evidence_codes", [])
        if isinstance(ev_flags, str):
            try:
                import ast
                ev_flags = ast.literal_eval(ev_flags)
            except Exception:
                ev_flags = [ev_flags]

        selected_cases.append({
            "validation_case_id": item["id"],
            "entitlement_id": str(chosen.get("entitlement_id", "")),
            "user_id": str(chosen.get("user_id", "")),
            "staff_type": str(chosen.get("staff_type", "")),
            "role": str(chosen.get("role", "")),
            "application": str(chosen.get("application", "")),
            "permission": str(chosen.get("permission", "")),
            "risk_score": int(chosen.get("risk_score", 0)),
            "risk_level": str(chosen.get("risk_level", "LOW")).upper(),
            "evidence_flags": ev_flags,
            "system_recommendation": system_rec,
            "simulated_reviewer_decision": rev_dec,
            "agreement": bool(agreement),
            "reviewer_reason": item["reason"],
            "disagreement_category": item["disagreement_cat"] if not agreement else None
        })

    return selected_cases
