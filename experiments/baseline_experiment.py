import os
import json
import pandas as pd

# Ensure the project root is in sys.path for imports
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_generator import generate_synthetic_data, DATA_DIR
from src.database import load_csv_data_to_db, retrieve_users, retrieve_entitlements, retrieve_usage_events
from src.data_processor import DataProcessor
from src.evidence_engine import evaluate_all_entitlements
from src.baseline import run_baseline_experiment


def load_and_process_data():
    """Load synthetic CSV data into the SQLite DB (if needed) and process it.

    Returns:
        tuple: (df_users, df_entitlements, df_events, processor, df_evaluated)
    """
    # Generate data if not present
    users_csv = os.path.join(DATA_DIR, "users.csv")
    if not os.path.exists(users_csv):
        generate_synthetic_data()
        load_csv_data_to_db()
    else:
        # Ensure DB is populated with the current CSVs
        load_csv_data_to_db()

    df_users = retrieve_users()
    df_entitlements = retrieve_entitlements()
    df_events = retrieve_usage_events()

    processor = DataProcessor(df_users, df_entitlements, df_events)
    df_baseline = processor.get_peer_usage_baseline()
    df_evaluated = evaluate_all_entitlements(df_baseline)
    return df_users, df_entitlements, df_events, processor, df_evaluated


def run_experiment():
    """Execute the baseline vs evidence‑based experiment and persist results.

    Returns:
        dict: Dictionary containing all calculated metrics and data frames.
    """
    _, _, _, _, df_evaluated = load_and_process_data()
    results = run_baseline_experiment(df_evaluated)

    # Prepare output directories
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    # Write JSON (exclude DataFrames as they are not JSON serialisable)
    json_path = os.path.join(results_dir, "baseline_results.json")
    json_serializable = {k: v for k, v in results.items() if not isinstance(v, (pd.DataFrame, pd.Series))}
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(json_serializable, jf, indent=2)

    # Write CSV for the summary table (human readable)
    csv_path = os.path.join(results_dir, "baseline_results.csv")
    summary_df = results.get("summary_df")
    if isinstance(summary_df, pd.DataFrame):
        summary_df.to_csv(csv_path, index=False)
    else:
        # Fallback: create an empty CSV with a warning row
        pd.DataFrame([{"Metric": "No summary available"}]).to_csv(csv_path, index=False)

    # Also optionally export the full case‑level details for deeper analysis
    case_path = os.path.join(results_dir, "case_details.csv")
    case_df = results.get("case_details_df")
    if isinstance(case_df, pd.DataFrame):
        case_df.to_csv(case_path, index=False)

    return results


if __name__ == "__main__":
    exp_results = run_experiment()
    # Print a concise human‑readable summary to the terminal
    print("--- Baseline vs Evidence-Based Experiment Summary ---")
    for key in [
        "total_cases",
        "baseline_approvals",
        "baseline_approval_rate",
        "prototype_approvals",
        "prototype_approval_rate",
        "baseline_blanket_approvals",
        "baseline_blanket_approval_rate",
        "prototype_blanket_approvals",
        "prototype_blanket_approval_rate",
        "reduction_percentage_points",
        "relative_reduction",
    ]:
        print(f"{key}: {exp_results.get(key)}")
    print(f"Results written to: {os.path.abspath(os.path.join(os.path.dirname(__file__), 'results'))}")
