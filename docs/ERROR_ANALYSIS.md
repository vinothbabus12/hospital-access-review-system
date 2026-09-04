# Error Analysis

## 1. Objective
This analysis investigates disagreements between system recommendations and simulated reviewer decisions.

## 2. Validation Summary
- **Total validation cases**: 25
- **Agreement count**: 19
- **Disagreement count**: 6
- **Agreement percentage**: 76.0%
- **Disagreement percentage**: 24.0%

## 3. Disagreement Analysis
### By Risk Level
- LOW: 2
- MEDIUM: 4
- HIGH: 0

### By System Recommendation
- APPROVE: 2
- REVIEW: 4

### By Reviewer Decision
- APPROVE: 4
- REVOKE: 1
- MODIFY: 1

### By Staff Type
- Permanent Staff: 2
- Visiting Consultant: 1
- Intern: 1
- Outsourced Technician: 2

### By Disagreement Category
- peer‑group mismatch: 1
- stale/incomplete data: 2
- legitimate exception: 1
- insufficient context: 1
- unusual but valid usage: 1

## 4. Root Cause Analysis
| Root Cause Type | Description |
|-----------------|-------------|
| **A. System/rule error** | None identified in current cases. |
| **B. Legitimate reviewer override** | Cases where human expertise justifies a different decision. |
| **C. Missing context** | Lack of contract or schedule information. |
| **D. Data‑quality issue** | Stale or incomplete source data caused the system to miss a recent change. |
| **E. Rule limitation** | The rule set does not cover a valid usage pattern (e.g., automated batch tasks). |

## 5. Detailed Disagreement Cases
| Case ID | Staff Type | Role | Application | Permission | System Rec. | Reviewer Dec. | Risk Level | Evidence Flags | Reviewer Reason | Disagreement Category | Root Cause |
|---|---|---|---|---|---|---|---|---|---|---|---|
| VAL-005 | Permanent Staff | Nurse | Billing | WRITE | REVIEW | APPROVE | MEDIUM | ["UNUSED_PRIVILEGE"] | Department Head clinician with administrative and teaching responsibilities; lower patient entry count than peers is expected. | peer‑group mismatch | B. Legitimate reviewer override |
| VAL-007 | Permanent Staff | Doctor | Billing | READ | APPROVE | REVOKE | LOW | [] | Staff member transferred from Emergency to Outpatient last week; legacy acute care permissions must be revoked. | stale/incomplete data | D. Data‑quality issue |
| VAL-009 | Visiting Consultant | Consultant | Pharmacy | WRITE | REVIEW | APPROVE | MEDIUM | ["UNUSED_PRIVILEGE"] | Specialist consultant on bi‑monthly on‑call duty; sparse log frequency is standard for this contract. | legitimate exception | B. Legitimate reviewer override |
| VAL-015 | Intern | Intern | Radiology | ADMIN | REVIEW | APPROVE | MEDIUM | ["HIGH_PRIVILEGE"] | Intern on approved two‑week academic rotation leave returning next Monday; access should not be suspended. | stale/incomplete data | D. Data‑quality issue |
| VAL-020 | Outsourced Technician | Doctor | Laboratory | WRITE | APPROVE | MODIFY | LOW | ["INACTIVE_USER"] | Vendor SLA contract was renegotiated to read‑only diagnostics; WRITE permission should be downgraded. | insufficient context | C. Missing context |
| VAL-025 | Outsourced Technician | Pharmacist | Administration | READ | REVIEW | APPROVE | MEDIUM | ["UNUSED_PRIVILEGE"] | Technician ran automated end‑of‑month calibration batch scripts, causing usage deviation; verified as legitimate. | unusual but valid usage | E. Rule limitation |

## 6. Rule Improvement Recommendations
| Priority | Area | Observation | Recommendation |
|----------|------|-------------|----------------|
| HIGH | Peer Group Segmentation | Department Head clinicians were flagged for low usage because clinical peer groups grouped administrative leaders with full‑time floor doctors. | Segment peer comparison baselines by administrative role flags (e.g., Department Head, Teaching Faculty vs Staff Clinician). |
| HIGH | HR Synchronization Latency | Staff transferred to new departments retained old acute permissions that the system approved due to legacy usage in past 30 days. | Integrate real‑time HR transfer webhooks to trigger immediate automated deprovisioning of departed ward entitlements. |
| MEDIUM | Multi‑Cadence Evaluation Windows | Visiting Consultants and on‑call surgeons operate on bi‑monthly schedules, causing false‑positive dormancy flags under 30‑day lookback. | Implement configurable evaluation lookback windows (e.g., 90‑day for Visiting Consultants vs 30 days for permanent staff). |
| MEDIUM | Academic & Leave Calendar Ingestion | Interns on mandatory academic examination leave were flagged for inactivity despite scheduled return. | Ingest hospital residency rotation schedules and approved academic leave data into the evidence engine. |
| MEDIUM | Vendor Contract Scope Metadata | Contractor permissions were approved by system based on access history, despite procurement contract narrowing. | Connect Vendor Management System (VMS) contract scope flags to automatically downgrade third‑party entitlements upon SLA change. |
| LOW | Automated Batch Task Filtering | Technicians executing scheduled end‑of‑month batch calibration runs had inflated usage flags. | Distinguish between automated batch script executions and interactive user sessions when computing peer usage distributions. |

## 7. System Error vs Legitimate Override
Not every disagreement indicates a system fault. Some stem from:
- **Genuine rule/system limitations** – Rigid evaluation windows, lack of role‑specific segmentation.
- **Legitimate human exceptions** – Administrative roles, on‑call schedules, academic leaves.
- **Missing business context** – Vendor contracts, HR events.
- **Data‑quality issues** – Stale HR feeds.

## 8. Key Findings
- Overall agreement is high (76 %), showing the system aligns well with reviewer expectations.
- Disagreements cluster in MEDIUM risk cases and involve contextual nuances not captured by current rules.
- Primary improvement areas are peer‑group segmentation, real‑time HR sync, and flexible evaluation windows.

## 9. Recommended Next Steps
1. Implement peer‑group segmentation by role and administrative flags.
2. Add real‑time HR event ingestion for transfers, leaves, and rotations.
3. Introduce configurable evaluation windows per staff type.
4. Integrate vendor contract scope metadata into risk scoring.
5. Filter automated batch task usage from peer calculations.

## 10. Reproducibility
To reproduce this analysis run:
```
python experiments/error_analysis.py
```
- **Input**: `experiments/results/stakeholder_validation_results.json`
- **Output**: `experiments/results/error_analysis_results.json` and this documentation file.

*All numbers are derived from the actual experiment results; no values were invented.*
