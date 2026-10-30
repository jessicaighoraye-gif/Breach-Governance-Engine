"""Writes population-calculation.csv.
"""
import csv

FIELDNAMES = [
    "row_type", "row_id", "jurisdiction", "dataset", "overlap_group",
    "confirmed_exfiltrated", "unique_subjects", "high_risk_subset",
    "contributes_to", "reason",
    "confirmed_unique_total", "lower_bound_unique_total", "upper_bound_unique_total",
]


def write_population_calculation_csv(path, row_details, population_results):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for d in row_details:
            writer.writerow({
                "row_type": "detail",
                "row_id": d["row_id"],
                "jurisdiction": d["jurisdiction"],
                "dataset": d["dataset"],
                "overlap_group": d["overlap_group"],
                "confirmed_exfiltrated": d["confirmed_exfiltrated"],
                "unique_subjects": d["unique_subjects"],
                "high_risk_subset": d["high_risk_subset"],
                "contributes_to": d["contributes_to"],
                "reason": d["reason"],
                "confirmed_unique_total": "", "lower_bound_unique_total": "", "upper_bound_unique_total": "",
            })

        for jur, pop in population_results.items():
            writer.writerow({
                "row_type": "jurisdiction_total",
                "row_id": "", "jurisdiction": jur, "dataset": "", "overlap_group": "",
                "confirmed_exfiltrated": "", "unique_subjects": "",
                "high_risk_subset": pop["high_risk_subset_confirmed"],
                "contributes_to": "", "reason": "",
                "confirmed_unique_total": pop["confirmed_unique"],
                "lower_bound_unique_total": pop["lower_bound_unique"],
                "upper_bound_unique_total": pop["upper_bound_unique"],
            })
