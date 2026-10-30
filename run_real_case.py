"""Runs the full pipeline for the REAL case 
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "breach-engine"))
from population import load_rows, compute_population
from rules_loader import load_rules
from engine import run_case
from ledger import build_ledger_rows, write_csv
from work_items import build_work_items
from population_calc import write_population_calculation_csv
from snapshots import write_snapshots

BASE = os.path.dirname(__file__)


def main():
    rows = load_rows(os.path.join(BASE, "input", "datainventory.csv"))
    population_results, other_us_rows, row_details = compute_population(rows)

    with open(os.path.join(BASE, "input", "incident-facts.json")) as f:
        incident_facts = json.load(f)
    with open(os.path.join(BASE, "input", "ownership-config.json")) as f:
        ownership_config = json.load(f)

   
    case_input = {
        "awareness_utc": "2026-07-13T07:35:00Z",
        "encryption_key_acquired": True, 
        "eu_unique": population_results["EU"]["confirmed_unique"],
        "nigeria_unique": population_results["Nigeria"]["confirmed_unique"],
        "california_unique": population_results["California"]["confirmed_unique"],
    }

    print("Derived case_input (should match public-fixtures.json V1 exactly):")
    print(json.dumps(case_input, indent=2))
    assert case_input["eu_unique"] == 620
    assert case_input["nigeria_unique"] == 1280
    assert case_input["california_unique"] == 530
    print("Matches V1 fixture input - confirmed.\n")

    rules = load_rules(os.path.join(BASE, "rules"))
    engine_results = run_case(case_input, incident_facts, rules)
    ledger_rows = build_ledger_rows(engine_results, ownership_config)
    work_items = build_work_items(ledger_rows, population_results)

    os.makedirs(os.path.join(BASE, "generated"), exist_ok=True)
    write_csv(ledger_rows, os.path.join(BASE, "deadline-ledger.csv"))
    with open(os.path.join(BASE, "work-items.json"), "w") as f:
        json.dump(work_items, f, indent=2)
    # population-result.json is our own internal working artifact, not one
    # of the 19 required names
    with open(os.path.join(BASE, "generated", "population-result.json"), "w") as f:
        json.dump({"jurisdictions": population_results, "other_us_rows": other_us_rows}, f, indent=2)

    # population-calculation.csv is REQUIRED at the submission root.
    write_population_calculation_csv(
        os.path.join(BASE, "population-calculation.csv"), row_details, population_results
    )

    # variant-snapshots/ is REQUIRED - freeze full engine output for V1-V6
    # plus the real case.
    with open(os.path.join(BASE, "input", "public-fixtures.json")) as f:
        fixtures = json.load(f)["fixtures"]
    write_snapshots(
        os.path.join(BASE, "variant-snapshots"), fixtures, incident_facts, rules, case_input, engine_results
    )

    print(f"Wrote {len(ledger_rows)} ledger rows to deadline-ledger.csv and {len(work_items)} work items to work-items.json (submission root)")
    print("Wrote population-calculation.csv")
    print("Wrote variant-snapshots/ (V1-V6 + REAL-CASE)")
    return case_input, engine_results, ledger_rows, work_items, population_results


if __name__ == "__main__":
    main()
