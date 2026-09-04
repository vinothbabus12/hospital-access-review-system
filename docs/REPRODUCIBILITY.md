# Reproducibility Guide

This document provides step-by-step instructions to reproduce all results in the Hospital Access Review System prototype.

---

## 1. Prerequisites

- **Python**: 3.10 or later (developed on Python 3.13)
- **Operating System**: Windows, macOS, or Linux
- **Git**: For cloning the repository (optional)

---

## 2. Environment Setup

### Clone the Repository

```bash
git clone <repository_url>
cd hospital-access-review
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies installed:
- `streamlit>=1.30.0`
- `pandas>=2.0.0`
- `plotly>=5.18.0`
- `pytest>=8.0.0`

---

## 3. Run the Streamlit Application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`. The application will automatically generate synthetic data and initialize the SQLite database on first run.

---

## 4. Run Automated Tests

```bash
pytest -q
```

Expected result: **39 tests passed**.

To run with verbose output:

```bash
pytest -v
```

---

## 5. Run Project Validation

```bash
python check_project.py
```

This script validates that all required project files, modules, and structure are present and correct.

---

## 6. Run Baseline Experiment

```bash
python -m experiments.baseline_experiment
```

This compares the traditional spreadsheet-based review (baseline) against the evidence-based prototype. Expected key result: baseline approval rate 83.5% vs. prototype approval rate 61.4%.

---

## 7. Run Expanded Experiments

```bash
python -m experiments.expanded_experiments
```

This runs additional experiment scenarios including per-role and per-risk-level analysis.

---

## 8. Run Before/After Analysis

```bash
python -m experiments.before_after_analysis
```

This produces a detailed comparison of decision distributions before and after applying evidence-based review.

---

## 9. Run Stakeholder Validation

```bash
python -m experiments.stakeholder_validation
```

This runs the **simulated** stakeholder validation using constructed personas (Security Officer, Department Manager, IT Auditor). No real hospital stakeholders participated.

---

## 10. Run Error Analysis

```bash
python -m experiments.error_analysis
```

This performs systematic analysis of decision accuracy, edge cases, and confidence calibration.

---

## 11. Run Failure/Recovery Experiment

```bash
python -m experiments.failure_recovery_test
```

This tests the system against five failure scenarios:
1. Duplicate event recovery
2. Delayed event recovery
3. Out-of-order event recovery
4. Missing/invalid data recovery
5. Combined failure scenario

---

## 12. Verification Checklist

After running all steps, verify the following:

| Check | Expected Result |
|-------|-----------------|
| `pytest -q` | 39 tests passed |
| `python check_project.py` | No errors |
| `streamlit run app.py` | Dashboard loads at localhost:8501 |
| Baseline experiment | 83.5% → 61.4% approval rate |
| Failure/recovery | All 5 scenarios pass |

---

## Notes

- All experiments use the synthetic dataset in the `data/` directory.
- The SQLite database is created automatically in the `database/` directory.
- Experiment results may be saved to the `experiments/results/` directory.
- No external services or API keys are required.
