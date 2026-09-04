# Project Summary

## Hospital Access Review System — Evaluator Summary

---

### Problem

Hospitals employ permanent staff, visiting consultants, interns, and outsourced technicians, each requiring different levels of access to clinical and administrative systems. Periodic access reviews are mandated by HIPAA and ISO 27001 to enforce the principle of least privilege.

In current practice, these reviews are conducted using **static spreadsheets**. Reviewers lack visibility into actual usage patterns and default to **blanket approvals** — approving privileges without examining whether they are actively used, appropriately scoped, or still needed. This results in privilege creep, security vulnerabilities, and compliance audit failures.

---

### Proposed Solution

The Hospital Access Review System is an **evidence-based privilege review prototype** that presents reviewers with transparent, data-driven evidence before every access decision. Instead of a spreadsheet with no usage context, the reviewer sees:

- How frequently the user accessed the entitlement (usage history)
- How the user's usage compares to peers in the same role (peer-role baseline)
- Whether the entitlement grants elevated access (privilege level)
- Whether the user is active, inactive, or terminated (user status)
- A transparent, rule-based risk score with explainable weights
- A system recommendation (APPROVE / REVIEW / REVOKE)

The reviewer can accept, modify, or override the recommendation — but overrides require a mandatory written justification. All decisions are immutably logged in an audit trail.

---

### Technical Contribution

| Component | Implementation |
|-----------|---------------|
| Data processing | CSV ingestion with duplicate detection, missing-data handling, and chronological reordering (`src/data_processor.py`) |
| Evidence engine | Peer-role grouping with per-entitlement usage counts, peer averages, peer medians, and transparent evidence flags (`src/evidence_engine.py`) |
| Risk scoring | Rule-based scoring: unused (+40), ADMIN (+30), low vs. peers (+20), inactive (+20), recently granted (+10). Risk levels: LOW/MEDIUM/HIGH (`src/risk_engine.py`) |
| Audit trail | Immutable SQLite logging of all decisions, overrides, and justifications (`src/audit.py`) |
| Reviewer interface | Streamlit multi-page dashboard with enforced evidence inspection before decision submission (`app.py`) |
| Baseline experiment | Quantitative comparison of spreadsheet-based vs. evidence-based review (`src/baseline.py`, `experiments/baseline_experiment.py`) |
| Failure testing | Five failure/recovery scenarios with automated tests (`experiments/failure_recovery_test.py`) |

---

### Evidence and Experiments

The following experiments were conducted to validate the prototype:

1. **Quantitative Baseline Experiment** — Compared blanket approval rates between spreadsheet-based review and evidence-based prototype.
2. **Expanded Experiments** — Per-role and per-risk-level analysis of decision distributions.
3. **Before/After Analysis** — Detailed comparison of decision distributions before and after evidence-based review.
4. **Simulated Stakeholder Validation** — Constructed personas (Security Officer, Department Manager, IT Auditor) evaluated system outputs against acceptance criteria. **No real hospital stakeholders participated.**
5. **Error Analysis** — Systematic analysis of decision accuracy, false positives/negatives, and edge cases.
6. **Failure/Recovery Testing** — Five scenarios testing pipeline resilience against data quality issues.

---

### Quantitative Results

#### Primary Metric: Overall Approval Rate

| Metric | Value |
|--------|-------|
| Baseline overall approval rate | **83.5%** |
| Prototype overall approval rate | **61.4%** |
| Absolute reduction | **22.1 percentage points** |
| Relative reduction | **≈ 26.5%** |

#### Prototype Decision Distribution

| Decision | Count | Percentage |
|----------|-------|------------|
| APPROVE | 434 | 61.4% |
| REVOKE | 203 | 28.7% |
| MODIFY | 70 | 9.9% |
| **Total** | **707** | **100%** |

The prototype identified **273 entitlements** (203 REVOKE + 70 MODIFY) that would have been blindly approved under the traditional spreadsheet-based process.

---

### Reliability

- **39 automated tests passed** covering database operations, data validation, evidence calculations, risk scoring, duplicate/delayed/out-of-order/missing data handling, baseline experiments, expanded experiments, before/after analysis, stakeholder validation, and failure recovery.
- **Project validation** (`check_project.py`) passes with no errors.

---

### Failure Handling

The data pipeline was tested against five failure scenarios:

| ID | Scenario | Result |
|----|----------|--------|
| F1 | Duplicate event recovery | ✅ Pass |
| F2 | Delayed event recovery | ✅ Pass |
| F3 | Out-of-order event recovery | ✅ Pass |
| F4 | Missing/invalid data recovery | ✅ Pass |
| F5 | Combined failure scenario | ✅ Pass |

---

### Validation

Stakeholder validation was **simulated** using constructed personas representing hospital Security Officers, Department Managers, and IT Auditors. Each persona evaluated the system against role-specific acceptance criteria.

**No real hospital stakeholders participated in the validation.** This limitation is explicitly documented throughout the project.

Error analysis was conducted to identify decision accuracy, edge cases, and areas where the risk scoring model may produce unexpected results.

---

### Limitations

- **Synthetic dataset** — All data (200 users, 707 entitlements, 5,400 usage events) is programmatically generated and may not represent real hospital access patterns.
- **Simulated stakeholder validation** — No real hospital staff reviewed the system.
- **MVP prototype** — Not production-ready.
- **No real system integration** — Not connected to hospital IAM, HR, or VMS systems.
- **Single-reviewer model** — Production systems may require multi-level approval workflows.
- **No authentication/authorization** — The prototype does not implement user access controls.

---

### Future Work

1. **Real stakeholder validation** — Conduct usability and acceptance testing with hospital Security Officers, Department Managers, and IT Auditors.
2. **Real data validation** — Test with anonymized real hospital access logs to validate risk weights and peer baselines.
3. **IAM/HR/VMS integration** — Connect to hospital identity and workforce management systems for real-time user status and entitlement data.
4. **Authentication and RBAC** — Implement role-based access control with SSO/SAML integration.
5. **Production security** — Add encryption, privacy controls, and secure audit storage.
6. **Monitoring and alerting** — Implement operational monitoring for data pipeline health, event lag, and decision throughput.
7. **Multi-level approval** — Support escalation workflows for high-risk entitlements.
8. **Continuous review** — Move from periodic batch review to continuous, event-driven access monitoring.
