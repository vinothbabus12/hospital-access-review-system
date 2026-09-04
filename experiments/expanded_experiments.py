# experiments/expanded_experiments.py
"""Run all expanded experiment scenarios and persist results.
The script loads the original synthetic dataset once, then executes each
scenario defined in `experiments.scenarios`.  Results are aggregated into a
dictionary keyed by scenario ID and written to both JSON and CSV files under
`experiments/results/`.
"""

import os
import sys
import json
import pandas as pd
# Ensure the project root is on PYTHONPATH when executing this script directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from experiments.scenarios import SCENARIOS

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_all_scenarios():
    """Execute every scenario and collect their metric dictionaries.
    Returns a dict: {scenario_id: metric_dict, ...}
    """
    all_results = {}
    for scenario_fn in SCENARIOS:
        result = scenario_fn()
        scenario_id = result.get("scenario_id", scenario_fn.__name__)
        all_results[scenario_id] = result
    return all_results


def _write_json(results: dict):
    json_path = os.path.join(RESULTS_DIR, "expanded_results.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2)
    return json_path


def _write_csv(results: dict):
    # Flatten each scenario dict into a flat row for CSV.
    rows = []
    for sid, data in results.items():
        flat = {"scenario_id": sid}
        # risk_score_stats is a nested dict – expand its keys.
        for k, v in data.get("risk_score_stats", {}).items():
            flat[f"risk_score_{k}"] = v
        # risk_counts is a dict of risk levels.
        for level, cnt in data.get("risk_counts", {}).items():
            flat[f"risk_{level.lower()}"] = cnt
        # copy other top‑level numeric fields.
        for key in [
            "total_cases",
            "affected_cases",
            "UNUSED_PRIVILEGE",
            "HIGH_PRIVILEGE",
            "LOW_USAGE_VS_PEERS",
            "HIGH_USAGE_VS_PEERS",
            "INACTIVE_USER",
            "validation_errors",
            "duplicate_events_detected",
            "delayed_events_detected",
            "out_of_order_events_handled",
            "processing_success",
        ]:
            if key in data:
                flat[key] = data[key]
        # recommendation counts are a dict – expand.
        for rec, cnt in data.get("recommendation_counts", {}).items():
            flat[f"rec_{rec.lower()}"] = cnt
        rows.append(flat)
    df = pd.DataFrame(rows)
    csv_path = os.path.join(RESULTS_DIR, "expanded_results.csv")
    df.to_csv(csv_path, index=False)
    return csv_path


def main():
    results = run_all_scenarios()
    json_path = _write_json(results)
    csv_path = _write_csv(results)
    print("--- Expanded Experiments Summary ---")
    for sid, data in results.items():
        print(f"{sid}: total_cases={data.get('total_cases')}, affected={data.get('affected_cases')}, risk_HIGH={data.get('risk_counts', {}).get('HIGH', 0)}")
    print(f"Results written to: {os.path.abspath(RESULTS_DIR)}")

if __name__ == "__main__":
    main()
