# Evidence-Based Hospital Access Review System

An automated, evidence-driven privilege review and risk scoring system designed for hospital environments to eliminate blanket approvals during periodic identity access reviews.

---

## 🎯 Problem Statement

Healthcare organizations conduct periodic privilege access reviews to comply with regulations such as HIPAA and ISO 27001. Historically, these reviews are performed using static spreadsheets. Because managers lack visibility into actual application usage logs, they default to **blanket approvals** (~90-95%+ approval rate), approving privileges even for inactive employees or unused high-level permissions. This results in **privilege creep**, severe security vulnerabilities, and compliance audit failures.

---

## 🚀 Objective

To develop a transparent, evidence-based access review prototype that ingests actual application log events, calculates peer-role usage baselines, computes rule-based risk scores, and enforces evidence inspection before reviewer decision-making, thereby significantly reducing blanket approvals.

---

## 👥 Stakeholder Assumptions

* **Hospital Security & Compliance Officers:** Require transparent, explainable evidence and immutable audit trails for regulatory compliance.
* **Department Managers:** Require role-aligned peer baselines (e.g., comparing Nurses against Nurses, Consultants against Consultants) to make informed access decisions without guesswork.
* **External IT Auditors:** Require tamper-proof historical logs of all reviewer decisions and decision overrides.

---

## 🛠️ Technology Stack

* **Language:** Python 3.13
* **Web Application Framework:** Streamlit (`>=1.30.0`)
* **Database Layer:** SQLite3
* **Data Science & Processing:** Pandas (`>=2.0.0`), NumPy
* **Visualization:** Plotly Express (`>=5.18.0`)
* **Testing Framework:** Pytest (`>=8.0.0`)

---

## ✨ Key Features

1. **SQLite Database Layer (`src/database.py`):**
   - Tables: `users`, `entitlements`, `usage_events`, `review_decisions`, `audit_log`.
   - Full persistence and backward-compatible helper routines.

2. **Data Quality & Event Processing (`src/data_processor.py`):**
   - Ingests raw data without modifying raw CSV sources.
   - Detects and removes duplicate `event_id` records to prevent double-counting.
   - Flags corrupt rows (missing user IDs, unparseable timestamps) without pipeline crashes.
   - Re-orders log events chronologically by `event_timestamp` to handle out-of-order and delayed arrivals.

3. **Peer-Role Baseline Engine (`src/evidence_engine.py`):**
   - Groups users by identical hospital role (e.g., Nurse, Doctor, Consultant, Lab Technician, Intern).
   - Computes `user_usage`, `last_usage_date`, `peer_average`, `peer_median`, and `difference_from_peer` for every entitlement.
   - Generates transparent evidence flags: `UNUSED_PRIVILEGE`, `HIGH_PRIVILEGE`, `LOW_USAGE_VS_PEERS`, `HIGH_USAGE_VS_PEERS`, `INACTIVE_USER`.

4. **Transparent Risk Scoring System (`src/risk_engine.py`):**
   - Rule weights: Unused privilege (`+40`), ADMIN permission (`+30`), Usage below peer baseline (`+20`), Inactive user (`+20`), Recently granted (`+10`).
   - Risk levels: `LOW` (0-29), `MEDIUM` (30-59), `HIGH` (60+).
   - Explainable system recommendations: `APPROVE`, `REVIEW`, `REVOKE`.

5. **Enforced Decision & Audit Trail Workflow (`src/audit.py` & `app.py`):**
   - Reviewers must inspect the evidence card before submitting decisions.
   - Decision choices: `APPROVE`, `REVOKE`, `MODIFY`, `OVERRIDE`.
   - Enforces a mandatory justification comment for `OVERRIDE` decisions.
   - Persists all decisions immutably in SQLite database table `audit_log`.

6. **Empirical Baseline Experiment (`src/baseline.py`):**
   - Evaluates traditional spreadsheet review vs. evidence-based prototype on 708 synthetic cases.
   - Measures primary project metric: **Reduction in blanket approvals**.

---

## 📂 Project Structure

```text
hospital-access-review/
├── app.py                     # Streamlit Multi-Page MVP Interface
├── requirements.txt           # Python dependencies
├── README.md                  # Project Overview & Quickstart
├── data/                      # Synthetic Raw Datasets (users, entitlements, usage_events, decisions)
│   ├── users.csv
│   ├── entitlements.csv
│   ├── usage_events.csv
│   └── review_decisions.csv
├── database/                  # SQLite Database Storage
│   └── hospital_access.db
├── docs/                      # Architectural & Experimental Documentation
│   ├── ARCHITECTURE.md
│   ├── TESTING.md
│   └── BASELINE_COMPARISON.md
├── src/                       # Core Application Engine
│   ├── __init__.py
│   ├── audit.py               # Immutable SQLite Audit Logging
│   ├── baseline.py            # Spreadsheet vs Prototype Experiment Engine
│   ├── data_generator.py      # Synthetic Hospital Data Generator
│   ├── data_processor.py      # Data Quality & Event Normalization
│   ├── database.py            # SQLite Database Connection & CRUD Operations
│   ├── evidence_engine.py     # Peer-Role Baseline & Evidence Calculation
│   └── risk_engine.py         # Transparent Rule-Based Risk Scoring
└── tests/                     # Automated Pytest Test Suite
    ├── test_baseline.py
    ├── test_data_validation.py
    ├── test_database.py
    ├── test_delayed_events.py
    ├── test_duplicates.py
    ├── test_evidence_engine.py
    ├── test_missing_data.py
    ├── test_out_of_order.py
    └── test_risk_engine.py
```

---

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd hospital-access-review
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 How to Run the Application

Start the Streamlit web dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 How to Run Tests

Run the complete automated pytest suite:
```bash
python -m pytest -v
```
To run specific test modules:
```bash
python -m pytest tests/test_duplicates.py -v
python -m pytest tests/test_delayed_events.py -v
python -m pytest tests/test_out_of_order.py -v
python -m pytest tests/test_missing_data.py -v
```
