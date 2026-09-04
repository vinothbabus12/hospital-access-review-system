# Hospital Access Review System — User Guide

---

## 1. Purpose

The Hospital Access Review System supports **evidence-based review** of access privileges for hospital personnel, including:

- **Permanent Staff** (Doctors, Nurses, Administrators, Pharmacists, Radiologists)
- **Visiting Consultants**
- **Interns**
- **Outsourced Technicians** (Lab Technicians)

The system replaces spreadsheet-driven blanket approvals with a transparent, data-driven review workflow. Each entitlement is evaluated against usage history, peer-role baselines, and privilege level before the reviewer makes a decision. All decisions are immutably logged for regulatory compliance.

---

## 2. Installation

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Dependencies: Streamlit, Pandas, Plotly, Pytest.

---

## 3. Start the Application

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`. The application automatically generates the synthetic dataset and initializes the SQLite database on first run.

---

## 4. Dashboard

The **Dashboard** page provides a high-level summary of the current review cycle:

- **Total users** under review
- **Total entitlements** to be reviewed
- **Total usage events** processed
- **Risk distribution** — A breakdown of entitlements by risk level (LOW, MEDIUM, HIGH)
- **Decision progress** — How many entitlements have been reviewed vs. pending

Use the Dashboard to understand the scope of the review and identify where to focus attention.

---

## 5. Privilege Review

The **Privilege Review** page is the primary reviewer workspace.

1. Browse the list of entitlements awaiting review.
2. Entitlements are displayed with their associated user, application, permission level, risk score, and system recommendation.
3. Select an entitlement to view its full evidence card.
4. High-risk and medium-risk entitlements should be prioritized for detailed review.

---

## 6. Evidence Details

When an entitlement is selected, the evidence card displays:

| Field | Description |
|-------|-------------|
| **User Information** | User name, ID, department, role, and status (active/inactive) |
| **Entitlement** | Application name, permission level (READ, WRITE, ADMIN), and grant date |
| **Usage History** | Number of times the user accessed this entitlement during the review period |
| **Peer-Role Comparison** | The user's usage compared to the average and median usage of peers in the same role |
| **Last Usage Date** | The most recent date the user accessed this entitlement |
| **Peer Average** | Mean usage count for all users with the same role and entitlement |
| **Peer Median** | Median usage count for all users with the same role and entitlement |
| **Evidence Flags** | Transparent flags indicating why the entitlement was flagged (see below) |
| **Risk Score** | Composite score based on rule-based weights |
| **Risk Level** | LOW (0–29), MEDIUM (30–59), or HIGH (60+) |
| **Recommendation** | System-generated suggestion: APPROVE, REVIEW, or REVOKE |

### Evidence Flags

- **UNUSED_PRIVILEGE** — The user has not accessed this entitlement during the review period.
- **HIGH_PRIVILEGE** — The entitlement grants elevated (e.g., ADMIN) access.
- **LOW_USAGE_VS_PEERS** — The user's usage is significantly below the peer-role average.
- **HIGH_USAGE_VS_PEERS** — The user's usage is significantly above the peer-role average.
- **INACTIVE_USER** — The user's status is inactive or terminated.

### Risk Score Weights

| Factor | Weight |
|--------|--------|
| Unused privilege | +40 |
| ADMIN permission | +30 |
| Usage below peer baseline | +20 |
| Inactive user | +20 |
| Recently granted | +10 |

---

## 7. Reviewer Decision

After inspecting the evidence card, the reviewer submits a decision:

| Decision | When to Use |
|----------|-------------|
| **APPROVE** | The entitlement is actively used, appropriately scoped, and the user needs continued access. |
| **REVOKE** | The entitlement is unused, the user is inactive, or the privilege level exceeds operational need. |
| **MODIFY** | The entitlement is partially needed but should be downgraded (e.g., ADMIN → WRITE). |
| **OVERRIDE** | The reviewer disagrees with the system recommendation and wants to record an alternative decision. **A written justification is mandatory.** |

> **Important:** The reviewer must inspect the evidence card before submitting a decision. The system enforces this requirement.

> **Override Policy:** OVERRIDE decisions require a mandatory justification comment explaining why the reviewer is overriding the system recommendation. This justification is permanently recorded in the audit trail.

---

## 8. Audit Trail

The **Audit Trail** page displays a complete, immutable log of all reviewer actions:

- **Reviewer identity** — Who made the decision
- **Decision** — APPROVE, REVOKE, MODIFY, or OVERRIDE
- **Timestamp** — When the decision was recorded
- **Justification** — The reviewer's reason (mandatory for OVERRIDE, optional for other decisions)
- **Entitlement details** — Which user and entitlement the decision applies to

The audit trail is stored in SQLite and cannot be modified after recording. This supports regulatory compliance requirements for HIPAA and ISO 27001 audits.

---

## 9. Data Quality

The **Data Quality** page shows how the system handled data integrity issues during ingestion:

| Issue | How the System Handles It |
|-------|---------------------------|
| **Duplicate events** | Detected by `event_id` and removed to prevent double-counting usage |
| **Delayed events** | Absorbed on re-processing; events are ordered by timestamp regardless of arrival time |
| **Out-of-order events** | Re-ordered chronologically by `event_timestamp` before usage calculation |
| **Invalid/missing data** | Rows with missing user IDs or unparseable timestamps are flagged and excluded without crashing the pipeline |

The Data Quality page reports the counts of each issue detected, so the reviewer can assess data reliability before making decisions.

---

## 10. Baseline Comparison

The **Baseline Comparison** page shows the quantitative difference between the traditional spreadsheet-based review process and the evidence-based prototype:

| Metric | Value |
|--------|-------|
| Baseline overall approval rate | **83.5%** |
| Prototype overall approval rate | **61.4%** |
| Absolute reduction | **22.1 percentage points** |
| Relative reduction | **≈ 26.5%** |

- The **baseline** simulates a traditional spreadsheet review where reviewers approve without usage evidence.
- The **prototype** presents evidence and risk scores, enabling informed REVOKE and MODIFY decisions.

The prototype's decision distribution: 434 APPROVE, 203 REVOKE, 70 MODIFY (707 total entitlements).

> **Note:** The system also tracks a "blanket-approval" metric (approvals made without evidence inspection), which may show 0.0% in the prototype. This is a separate metric from the overall approval rate and reflects the fact that the prototype enforces evidence inspection before every decision.

---

## 11. Failure and Recovery

The system includes experiments that test data pipeline resilience against five failure scenarios:

1. **Duplicate Event Recovery** — Pipeline correctly deduplicates repeated events.
2. **Delayed Event Recovery** — Late-arriving events are correctly incorporated.
3. **Out-of-Order Event Recovery** — Events are reordered chronologically regardless of arrival sequence.
4. **Missing/Invalid Data Recovery** — Corrupt rows are handled gracefully without pipeline failure.
5. **Combined Failure Scenario** — Multiple failure types occurring simultaneously are handled correctly.

All five scenarios pass automated testing.

---

## 12. Stakeholder Validation

> **Disclaimer:** Stakeholder validation in this prototype was **simulated**. No real hospital stakeholders participated.

The simulated validation used constructed personas representing:
- **Hospital Security & Compliance Officers**
- **Department Managers**
- **External IT Auditors**

Each persona evaluated the system against role-specific acceptance criteria. The results are documented in [STAKEHOLDER_VALIDATION.md](STAKEHOLDER_VALIDATION.md).

---

## 13. Limitations

- **Synthetic data** — The dataset (200 users, 707 entitlements, 5,400 usage events) is programmatically generated and may not represent real hospital access patterns.
- **Simulated validation** — No real hospital stakeholders reviewed the system.
- **Peer-group accuracy** — Peer baselines depend on the accuracy of role assignments in the upstream data. Users with hybrid or changing roles may not fit a single peer group.
- **Data freshness** — The prototype processes a static dataset. In production, user status and usage data would need real-time or near-real-time feeds from HR and IAM systems.
- **Production integration** — The prototype is not connected to real hospital IAM, HR, or VMS systems. Production deployment would require authentication, authorization, encryption, privacy controls, monitoring, and integration with hospital identity infrastructure.

---

## 14. Important Reviewer Guidance

1. **Always inspect the evidence card** before submitting a decision. The system is designed to present transparent, data-driven evidence — use it.
2. **Compare against peer baselines.** If a user's usage is significantly below peer average, investigate whether the privilege is still needed.
3. **Pay attention to evidence flags.** Flags like UNUSED_PRIVILEGE and INACTIVE_USER indicate high-risk entitlements that should rarely be approved without justification.
4. **Use OVERRIDE only when justified.** If you disagree with the system recommendation, document your reasoning clearly. Overrides are permanently recorded in the audit trail and may be reviewed by auditors.
5. **Prioritize HIGH-risk entitlements.** Focus review time on entitlements with the highest risk scores, especially those with ADMIN privileges or inactive users.
6. **Review the Data Quality page** to understand whether the usage data underlying the evidence is reliable for the current review cycle.
