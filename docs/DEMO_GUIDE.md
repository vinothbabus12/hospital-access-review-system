# Evaluator Demo Guide

A structured 5–7 minute demonstration of the Hospital Access Review System for evaluators.

---

## Overview

This guide walks through a live demonstration of the prototype, showing how evidence-based privilege review replaces spreadsheet-driven blanket approvals. Each step includes what to show on screen and what to explain verbally.

**Prerequisites:** Run `streamlit run app.py` and open the browser at `http://localhost:8501`.

---

## Demo Flow

### Step 1: Dashboard Overview (30 seconds)

**Show:** The main Dashboard page with summary statistics and charts.

**Say:** *"This is the Hospital Access Review System. The dashboard shows a summary of 200 users, 707 entitlements, and 5,400 usage events. The charts break down entitlements by risk level — LOW, MEDIUM, and HIGH — so the reviewer immediately sees where to focus attention."*

---

### Step 2: Problem Statement (45 seconds)

**Show:** Stay on the Dashboard.

**Say:** *"Hospitals employ permanent staff, visiting consultants, interns, and outsourced technicians — each with different access needs. Today, periodic access reviews are done with spreadsheets. Managers receive a list of privileges and, lacking usage data, approve everything by default. Our baseline experiment shows an 83.5% blanket approval rate. This causes privilege creep and compliance risk."*

---

### Step 3: Navigate to Privilege Review (15 seconds)

**Show:** Click on the "Privilege Review" page in the sidebar.

**Say:** *"The Privilege Review page is where the reviewer examines each entitlement with full evidence."*

---

### Step 4: Select an Entitlement (30 seconds)

**Show:** Select a HIGH-risk or MEDIUM-risk entitlement from the list. Choose one with clear evidence flags (e.g., UNUSED_PRIVILEGE or INACTIVE_USER).

**Say:** *"I'll select a high-risk entitlement. Notice the risk score, risk level, and the system's recommendation are immediately visible."*

---

### Step 5: Evidence Details (45 seconds)

**Show:** Expand or view the evidence card for the selected entitlement. Point to:
- User usage count
- Peer average and median usage
- Difference from peer baseline
- Evidence flags (e.g., UNUSED_PRIVILEGE, HIGH_PRIVILEGE)
- Last usage date

**Say:** *"The evidence card shows exactly why this entitlement was flagged. This user has zero usage in the review period, while their peers average significantly higher. The system flagged it as UNUSED_PRIVILEGE. The reviewer doesn't have to guess — the data is right here."*

---

### Step 6: Risk Score Explanation (30 seconds)

**Show:** Point to the risk score breakdown.

**Say:** *"The risk score is computed transparently from rule-based weights: unused privilege adds 40 points, ADMIN-level access adds 30, low usage versus peers adds 20. This entitlement scored in the HIGH range, so the system recommends REVOKE. Every weight is visible and explainable — there is no black box."*

---

### Step 7: Reviewer Decision (45 seconds)

**Show:** Use the decision dropdown to select REVOKE (or MODIFY). Add a justification comment. Submit the decision.

**Say:** *"The reviewer must inspect the evidence before submitting a decision. They can APPROVE, REVOKE, or MODIFY. If they disagree with the system recommendation, they can OVERRIDE — but an override requires a mandatory written justification. This enforces accountability."*

---

### Step 8: Audit Trail (30 seconds)

**Show:** Navigate to the Audit Trail page. Show the logged decision with timestamp, reviewer, decision, and justification.

**Say:** *"Every decision is immutably recorded in the audit trail — who decided, what they decided, when, and why. This is essential for HIPAA and ISO 27001 compliance. External auditors can verify that every entitlement was reviewed with evidence."*

---

### Step 9: Data Quality (30 seconds)

**Show:** Navigate to the Data Quality page. Show duplicate detection, missing data handling, and event reordering statistics.

**Say:** *"The system monitors data quality automatically. It detects duplicate events, handles missing fields without crashing, and reorders out-of-sequence events. This ensures the evidence presented to reviewers is accurate."*

---

### Step 10: Baseline Comparison (45 seconds)

**Show:** Navigate to the Baseline Comparison page. Show the approval rate comparison chart.

**Say:** *"This is the core experiment result. The traditional spreadsheet-based review has an 83.5% approval rate — essentially blanket approvals. Our evidence-based prototype reduces this to 61.4% — a 22.1 percentage-point reduction, approximately 26.5% relative improvement. The prototype identified 203 entitlements to revoke and 70 to modify, which would have been blindly approved in the old process."*

---

### Step 11: Failure & Recovery (30 seconds)

**Show:** Reference the failure/recovery results (from the Dashboard or documentation).

**Say:** *"We tested the system against five failure scenarios — duplicate events, delayed events, out-of-order events, invalid data, and a combined failure scenario. All five pass. The data pipeline is resilient to real-world data quality issues."*

---

### Step 12: Conclusion (30 seconds)

**Show:** Return to the Dashboard.

**Say:** *"To summarize: this prototype demonstrates that evidence-based access review can reduce blanket approvals from 83.5% to 61.4%. Every decision is backed by usage data, peer comparisons, and transparent risk scores. Every decision is auditable. The system handles data quality issues gracefully. This is an MVP built with synthetic data — production deployment would require real hospital integration and stakeholder validation — but the approach is validated."*

---

## Timing Summary

| Step | Duration | Cumulative |
|------|----------|------------|
| 1. Dashboard | 0:30 | 0:30 |
| 2. Problem | 0:45 | 1:15 |
| 3. Navigate | 0:15 | 1:30 |
| 4. Select entitlement | 0:30 | 2:00 |
| 5. Evidence details | 0:45 | 2:45 |
| 6. Risk explanation | 0:30 | 3:15 |
| 7. Reviewer decision | 0:45 | 4:00 |
| 8. Audit trail | 0:30 | 4:30 |
| 9. Data quality | 0:30 | 5:00 |
| 10. Baseline comparison | 0:45 | 5:45 |
| 11. Failure/recovery | 0:30 | 6:15 |
| 12. Conclusion | 0:30 | 6:45 |

**Total: approximately 6 minutes 45 seconds**

---

## Key Numbers to Remember

- **200** users, **707** entitlements, **5,400** usage events
- **83.5%** baseline approval rate → **61.4%** prototype approval rate
- **22.1** percentage-point reduction (≈ **26.5%** relative)
- **434** APPROVE, **203** REVOKE, **70** MODIFY
- **39** automated tests passing
- **5/5** failure scenarios passing
