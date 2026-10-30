"""Writes variant-snapshots"""
import json
import os


def write_snapshots(snapshot_dir, fixtures, incident_facts, rules, real_case_input, real_case_results):
    os.makedirs(snapshot_dir, exist_ok=True)
    from engine import run_case, to_expected_output_shape

    for fx in fixtures:
        results = run_case(fx["input"], incident_facts, rules)
        snapshot = {
            "case_id": fx["case_id"],
            "input": fx["input"],
            "expected_output_shape": to_expected_output_shape(results, fx["input"]),
            "matches_public_fixture_expected": to_expected_output_shape(results, fx["input"]) == fx["expected"],
            "full_ledger": results,
        }
        with open(os.path.join(snapshot_dir, f"{fx['case_id']}.json"), "w") as f:
            json.dump(snapshot, f, indent=2)

    real_snapshot = {
        "case_id": "REAL-CASE",
        "input": real_case_input,
        "full_ledger": real_case_results,
        "note": "Derived live from datainventory.csv via population.py, not hand-entered. See run_real_case.py.",
    }
    with open(os.path.join(snapshot_dir, "REAL-CASE.json"), "w") as f:
        json.dump(real_snapshot, f, indent=2)
