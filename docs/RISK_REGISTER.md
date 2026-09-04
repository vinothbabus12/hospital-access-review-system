# Risk Register

This document identifies key risks associated with the Hospital Access Review System prototype, their impact, and mitigation strategies.

---

## Risk Assessment Matrix

| ID | Risk | Impact | Likelihood | Current Mitigation | Residual Risk | Future Recommendation |
|----|------|--------|------------|---------------------|---------------|------------------------|
| R1 | **Incorrect reviewer decision** — Reviewer approves a privilege that should be revoked, or revokes a privilege that is operationally needed | High | Medium | System presents evidence card with usage history, peer baselines, and risk score before every decision. Override requires mandatory justification. All decisions are logged in audit trail. | Reviewer may still override system recommendation without thorough review. | Implement multi-level approval chains for HIGH-risk entitlements. Add periodic re-review triggers for overridden decisions. |
| R2 | **Missing or stale HR data** — User status (active/inactive/terminated) is outdated, leading to incorrect risk assessments | High | Medium | Data processor flags missing user IDs and invalid fields. Evidence engine checks user status when generating flags. | If HR feed is delayed, an inactive user may appear active during the review window. | Integrate with real-time HR/VMS systems. Implement automated status reconciliation before each review cycle. |
| R3 | **Incorrect peer-group assignment** — User is compared against the wrong role group, producing misleading peer baselines | Medium | Low | Peer grouping is based on the `role` field in user data. Evidence engine computes per-role averages and medians transparently. | Role data depends on upstream accuracy. Users with hybrid roles may not fit a single peer group. | Support multi-role or weighted peer-group assignment. Allow reviewers to reassign peer groups during review. |
| R4 | **Synthetic data does not represent real hospital behavior** — Usage patterns, role distributions, and access volumes in the prototype may not match production reality | Medium | High | Dataset was designed with realistic role types (Doctor, Nurse, Consultant, Intern, Lab Technician, etc.) and varied usage patterns. Limitations are explicitly documented. | All quantitative results are based on synthetic data and may not generalize. | Validate with real anonymized hospital access logs before production deployment. Recalibrate risk weights based on real data. |
| R5 | **Simulated stakeholder validation** — Validation was performed with constructed personas, not real hospital staff | Medium | High | Simulated validation used realistic acceptance criteria aligned with compliance, security, and operational needs. Limitation is clearly disclosed in all documentation. | Actual stakeholder preferences and workflows may differ from simulated assumptions. | Conduct validation sessions with real hospital Security Officers, Department Managers, and IT Auditors. |
| R6 | **Delayed or duplicate usage events** — Events arrive late, out of order, or are duplicated, corrupting usage counts and risk scores | High | Medium | Data processor detects and removes duplicate `event_id` records. Events are re-ordered chronologically by timestamp. Delayed events are absorbed on re-processing. All five failure scenarios pass automated tests. | Edge cases with very large delays or concurrent pipeline runs may not be fully covered. | Implement idempotent event ingestion with event-sourcing architecture. Add real-time monitoring for event lag and duplicate rates. |
| R7 | **Unauthorized access to the review system** — An unauthorized user accesses the review dashboard and modifies decisions | High | Low | Prototype runs locally. Audit trail logs all decisions immutably in SQLite. | No authentication or authorization is implemented in the MVP. | Implement role-based access control (RBAC), SSO/SAML integration, and session management before production deployment. |
| R8 | **Production integration complexity** — Integrating with real hospital IAM, HR, VMS, and EHR systems introduces unforeseen technical and organizational challenges | High | High | Prototype uses a clean data interface (CSV ingestion + SQLite) that can be adapted to different data sources. Architecture is modular with separated data, evidence, risk, and audit layers. | No integration testing with real hospital systems has been performed. | Conduct integration proof-of-concept with a partner hospital. Define API contracts for IAM/HR/VMS data feeds. Plan phased rollout with fallback to manual review. |

---

## Risk Level Summary

| Risk Level | Count | Risk IDs |
|------------|-------|----------|
| High Impact | 5 | R1, R2, R6, R7, R8 |
| Medium Impact | 3 | R3, R4, R5 |

---

## Notes

- This risk register reflects the current state of the **MVP prototype**.
- All risks are assessed in the context of a synthetic-data, single-reviewer prototype — not a production deployment.
- Risk weights and likelihoods should be reassessed when moving toward production.
