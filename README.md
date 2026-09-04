# Hospital Access Review System

An evidence-based privilege review and risk scoring prototype for hospital environments, designed to replace spreadsheet-driven blanket approvals with transparent, data-driven access decisions.

---

## 1. Problem Statement

Hospitals employ a diverse workforce — **permanent staff**, **visiting consultants**, **interns**, and **outsourced technicians** — each requiring different levels of access to clinical and administrative systems. Regulatory frameworks such as HIPAA and ISO 27001 mandate periodic access reviews to ensure the principle of least privilege is maintained.

In practice, these reviews are conducted using **static spreadsheets** distributed to department managers. Because reviewers lack visibility into actual application usage patterns, they routinely default to **blanket approvals**, approving privileges even for inactive employees or unused high-level permissions. This leads to:

- **Privilege creep** — users accumulate access rights beyond their operational needs.
- **Security vulnerabilities** — dormant or excessive privileges become attack vectors.
- **Compliance failures** — audit evidence lacks justification for approval decisions.

---

## 2. Proposed Solution

This prototype provides **evidence-based privilege review** by presenting reviewers with actionable data before every decision. The system evaluates each entitlement using:

| Evidence Dimension     | Description                                                  |
|------------------------|--------------------------------------------------------------|
| **Usage History**      | How frequently the user has accessed the entitlement         |
| **Peer-Role Comparison** | How the user's usage compares to others in the same role   |
| **Privilege Level**    | Whether the entitlement grants elevated (e.g., ADMIN) access |
| **User Status**        | Whether the user is active, inactive, or terminated          |
| **Risk Scoring**       | A transparent, rule-based composite risk score               |
| **Reviewer Decisions** | Structured APPROVE / REVOKE / MODIFY workflow                |
| **Manual Override**    | Reviewer can override the system recommendation with mandatory justification |
| **Audit Trail**        | Every decision is immutably logged for compliance            |

---

## 3. Key Features

1. **Evidence-Based Access Review** — Every entitlement is evaluated against usage history, peer baselines, and privilege level before the reviewer makes a decision.
2. **Transparent Risk Scoring** — Rule-based scoring with explainable weights: unused privilege (+40), ADMIN permission (+30), low usage vs. peers (+20), inactive user (+20), recently granted (+10). Risk levels: LOW (0–29), MEDIUM (30–59), HIGH (60+).
3. **Peer-Role Baselines** — Users are grouped by hospital role (Nurse, Doctor, Consultant, Lab Technician, Intern) and compared against peer average and median usage.
4. **Reviewer Workflow** — Reviewers must inspect the evidence card before submitting a decision. Choices: APPROVE, REVOKE, MODIFY.
5. **Manual Override** — Reviewers can override the system recommendation with a mandatory justification comment.
6. **Immutable Audit Trail** — All decisions, overrides, and justifications are persisted in SQLite for regulatory compliance.
7. **Data-Quality Monitoring** — Detects and handles duplicate events, missing fields, and corrupt rows without pipeline failure.
8. **Failure & Recovery Handling** — Tested resilience against duplicate, delayed, out-of-order, and invalid data scenarios.
9. **Baseline Comparison** — Quantitative comparison of spreadsheet-based review vs. evidence-based prototype.
10. **Before/After Analysis** — Detailed analysis of decision distribution changes across risk levels and roles.

---

## 4. System Workflow

```
┌──────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Data   │───▶│    Evidence      │───▶│  Risk            │───▶│  Privilege        │───▶│  Reviewer         │───▶│  Audit      │
│  Ingest  │    │  Processing     │    │  Assessment      │    │  Review           │    │  Decision         │    │  Trail      │
└──────────┘    └─────────────────┘    └─────────────────┘    └──────────────────┘    └──────────────────┘    └─────────────┘
  users.csv       Usage counts          Risk scores            Evidence cards          APPROVE/REVOKE/         Immutable
  entitlements    Peer baselines        Risk levels            Recommendations         MODIFY/OVERRIDE         SQLite log
  usage_events    Evidence flags        (LOW/MED/HIGH)                                 + justification
```

---

## 5. Architecture

The system follows a layered pipeline architecture:

- **Data Layer** — CSV ingestion, SQLite persistence (`src/database.py`, `src/data_processor.py`)
- **Evidence Layer** — Peer-role baselines and evidence flag generation (`src/evidence_engine.py`)
- **Risk Layer** — Rule-based risk scoring and recommendations (`src/risk_engine.py`)
- **Audit Layer** — Immutable decision and override logging (`src/audit.py`)
- **Presentation Layer** — Streamlit multi-page dashboard (`app.py`)

For full architectural details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 6. Technology Stack

| Component              | Technology                |
|------------------------|---------------------------|
| Language               | Python 3.13               |
| Web Framework          | Streamlit (≥1.30.0)       |
| Database               | SQLite3 (stdlib)          |
| Data Processing        | Pandas (≥2.0.0)           |
| Visualization          | Plotly (≥5.18.0)          |
| Testing                | Pytest (≥8.0.0)           |

All dependencies are listed in `requirements.txt`.

---

## 7. Dataset

The system uses a **synthetic hospital dataset** generated to simulate realistic access patterns:

| Dataset         | Records |
|-----------------|---------|
| Users           | 200     |
| Entitlements    | 707     |
| Usage Events    | 5,400   |

Roles represented: Doctor, Nurse, Consultant, Lab Technician, Intern, Administrator, Pharmacist, Radiologist.

---

## 8. Quantitative Results

### Primary Metric: Overall Approval Rate

| Metric                        | Value                    |
|-------------------------------|--------------------------|
| Baseline overall approval rate | **83.5%**               |
| Prototype overall approval rate | **61.4%**              |
| Absolute reduction            | **22.1 percentage points** |
| Relative reduction            | **≈ 26.5%**             |

The baseline represents a traditional spreadsheet-based review where reviewers approve without usage evidence. The prototype presents evidence and risk scores, enabling reviewers to make informed REVOKE and MODIFY decisions.

### Prototype Decision Distribution

| Decision   | Count | Percentage |
|------------|-------|------------|
| APPROVE    | 434   | 61.4%      |
| REVOKE     | 203   | 28.7%      |
| MODIFY     | 70    | 9.9%       |
| **Total**  | **707** | **100%** |

For detailed experiment methodology and results, see:
- [docs/BASELINE_COMPARISON.md](docs/BASELINE_COMPARISON.md)
- [docs/QUANTITATIVE_BASELINE.md](docs/QUANTITATIVE_BASELINE.md)
- [docs/BEFORE_AFTER_ANALYSIS.md](docs/BEFORE_AFTER_ANALYSIS.md)
- [docs/EXPERIMENT_RESULTS.md](docs/EXPERIMENT_RESULTS.md)

---

## 9. Failure & Recovery Testing

The system was tested against five failure scenarios to validate data pipeline resilience:

| ID  | Scenario                      | Result  |
|-----|-------------------------------|---------|
| F1  | Duplicate Event Recovery      | ✅ Pass |
| F2  | Delayed Event Recovery        | ✅ Pass |
| F3  | Out-of-Order Event Recovery   | ✅ Pass |
| F4  | Missing/Invalid Data Recovery | ✅ Pass |
| F5  | Combined Failure Scenario     | ✅ Pass |

For details, see [docs/FAILURE_RECOVERY.md](docs/FAILURE_RECOVERY.md).

---

## 10. Stakeholder Validation

> **Disclaimer:** Stakeholder validation in this prototype was **simulated**. No real hospital stakeholders participated. The validation exercise used constructed personas (Security Officer, Department Manager, IT Auditor) to evaluate system outputs against expected acceptance criteria.

For the simulated validation methodology and results, see [docs/STAKEHOLDER_VALIDATION.md](docs/STAKEHOLDER_VALIDATION.md).

---

## 11. Error Analysis

Systematic analysis of system decision accuracy, including false-positive and false-negative identification, edge cases, and confidence calibration.

For details, see [docs/ERROR_ANALYSIS.md](docs/ERROR_ANALYSIS.md).

---

## 12. Testing

All automated tests pass:

```
39 tests passed
```

Test coverage includes:

- Database CRUD operations
- Data validation and quality checks
- Evidence engine calculations
- Risk scoring logic
- Duplicate event handling
- Delayed event processing
- Out-of-order event recovery
- Missing/invalid data handling
- Baseline experiment correctness
- Expanded experiment scenarios
- Before/after analysis
- Stakeholder validation logic
- Failure/recovery scenarios

For details, see [docs/TESTING.md](docs/TESTING.md).

---

## 13. How to Run

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### Run Tests

```bash
pytest -q
```

### Run Project Validation

```bash
python check_project.py
```

---

## 14. Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and component design |
| [TESTING.md](docs/TESTING.md) | Test strategy, coverage, and results |
| [BASELINE_COMPARISON.md](docs/BASELINE_COMPARISON.md) | Baseline vs. prototype comparison methodology |
| [QUANTITATIVE_BASELINE.md](docs/QUANTITATIVE_BASELINE.md) | Quantitative baseline experiment details |
| [BEFORE_AFTER_ANALYSIS.md](docs/BEFORE_AFTER_ANALYSIS.md) | Before/after decision distribution analysis |
| [EXPERIMENT_RESULTS.md](docs/EXPERIMENT_RESULTS.md) | Expanded experiment results |
| [STAKEHOLDER_VALIDATION.md](docs/STAKEHOLDER_VALIDATION.md) | Simulated stakeholder validation |
| [ERROR_ANALYSIS.md](docs/ERROR_ANALYSIS.md) | Error analysis and edge cases |
| [FAILURE_RECOVERY.md](docs/FAILURE_RECOVERY.md) | Failure scenario testing and recovery |

---

## 15. Limitations

This project is an **MVP prototype** built for an industry challenge. The following limitations apply:

- **Synthetic dataset** — All user, entitlement, and usage data is programmatically generated and does not represent real hospital operations.
- **Simulated stakeholder validation** — No real hospital stakeholders participated in the validation exercise.
- **No real system integration** — The prototype is not connected to real IAM, HR, or VMS systems.
- **Production readiness** — A production deployment would require authentication, authorization, encryption, privacy controls, monitoring, alerting, and integration with hospital identity infrastructure.
- **Single-reviewer workflow** — The prototype demonstrates a single-reviewer model; production systems may require multi-level approval chains.

---

## 16. Project Structure

```text
hospital-access-review/
├── app.py                          # Streamlit multi-page dashboard
├── check_project.py                # Project validation script
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── data/                           # Synthetic datasets
│   ├── users.csv
│   ├── entitlements.csv
│   ├── usage_events.csv
│   └── review_decisions.csv
├── database/                       # SQLite database storage
│   └── hospital_access.db
├── docs/                           # Documentation
│   ├── ARCHITECTURE.md
│   ├── BASELINE_COMPARISON.md
│   ├── BEFORE_AFTER_ANALYSIS.md
│   ├── ERROR_ANALYSIS.md
│   ├── EXPERIMENT_RESULTS.md
│   ├── FAILURE_RECOVERY.md
│   ├── QUANTITATIVE_BASELINE.md
│   ├── STAKEHOLDER_VALIDATION.md
│   └── TESTING.md
├── experiments/                    # Experiment scripts
│   ├── baseline_experiment.py
│   ├── before_after_analysis.py
│   ├── error_analysis.py
│   ├── expanded_experiments.py
│   ├── failure_recovery_test.py
│   ├── scenarios.py
│   ├── stakeholder_validation.py
│   └── validation_cases.py
├── src/                            # Core application engine
│   ├── __init__.py
│   ├── audit.py
│   ├── baseline.py
│   ├── data_generator.py
│   ├── data_processor.py
│   ├── database.py
│   ├── evidence_engine.py
│   └── risk_engine.py
└── tests/                          # Automated test suite (39 tests)
    ├── __init__.py
    ├── test_baseline.py
    ├── test_baseline_experiment.py
    ├── test_before_after_analysis.py
    ├── test_data_validation.py
    ├── test_database.py
    ├── test_delayed_events.py
    ├── test_duplicates.py
    ├── test_evidence_engine.py
    ├── test_expanded_experiments.py
    ├── test_failure_recovery.py
    ├── test_missing_data.py
    ├── test_out_of_order.py
    ├── test_risk_engine.py
    └── test_stakeholder_validation.py
```
