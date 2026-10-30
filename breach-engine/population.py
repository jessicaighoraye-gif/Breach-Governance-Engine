"""Deduplicates datainventory.csv rows into confirmed/lower/upper populations
per jurisdiction. 
"""
import csv

IN_SCOPE_JURISDICTIONS = ["EU", "Nigeria", "California"]


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def compute_population(rows):
    results = {}
    row_details = []
    for jur in IN_SCOPE_JURISDICTIONS:
        jur_rows = [r for r in rows if r["jurisdiction"] == jur]
        included, excluded = [], []
        groups_yes, groups_uncertain, high_risk_by_group = {}, {}, {}

        for r in jur_rows:
            status = r["confirmed_exfiltrated"]
            if status == "no":
                excluded.append({"row_id": r["row_id"], "reason": f"confirmed_exfiltrated=no ({r['notes']})"})
                continue
            included.append(r["row_id"])
            grp = r["overlap_group"]
            n = int(r["unique_subjects"])
            hr = int(r["high_risk_subset"])
            high_risk_by_group[grp] = max(high_risk_by_group.get(grp, 0), hr)
            if status == "yes":
                groups_yes[grp] = max(groups_yes.get(grp, 0), n)
            elif status == "uncertain":
                groups_uncertain[grp] = max(groups_uncertain.get(grp, 0), n)
            else:
                raise ValueError(f"Unexpected confirmed_exfiltrated value: {status!r} on {r['row_id']}")

        confirmed = sum(groups_yes.values())
        # Guard against a group appearing in BOTH groups_yes and groups_uncertain
        # (conflicting status for the same overlap_group = same people). The
        # 'yes' status wins as more certain; only count a group's uncertain
        # contribution toward upper if it is NOT already counted as confirmed.
        upper = confirmed + sum(v for k, v in groups_uncertain.items() if k not in groups_yes)
        lower = confirmed
        high_risk_confirmed = sum(v for k, v in high_risk_by_group.items() if k in groups_yes)
        high_risk_source_rows = [
            r["row_id"] for r in jur_rows
            if r["confirmed_exfiltrated"] == "yes" and int(r["high_risk_subset"]) > 0
        ]

        results[jur] = {
            "jurisdiction": jur,
            "confirmed_unique": confirmed,
            "lower_bound_unique": lower,
            "upper_bound_unique": upper,
            "high_risk_subset_confirmed": high_risk_confirmed,
            "high_risk_source_rows": high_risk_source_rows,
            "included_rows": included,
            "excluded_rows": excluded,
        }

        # Row-level detail for population-calculation.csv - built from the
        # SAME groups_yes/groups_uncertain used above, so it can never drift
        # from the totals.
        for r in jur_rows:
            status = r["confirmed_exfiltrated"]
            grp = r["overlap_group"]
            base = {
                "row_id": r["row_id"], "jurisdiction": jur, "dataset": r["dataset"],
                "overlap_group": grp, "confirmed_exfiltrated": status,
                "unique_subjects": r["unique_subjects"], "high_risk_subset": r["high_risk_subset"],
            }
            if status == "no":
                base["contributes_to"] = "excluded"
                base["reason"] = f"confirmed_exfiltrated=no ({r['notes']})"
            elif status == "yes":
                base["contributes_to"] = "confirmed"
                base["reason"] = f"overlap_group={grp} deduplicated (max unique_subjects taken across group members)"
            elif status == "uncertain":
                if grp in groups_yes:
                    base["contributes_to"] = "already_counted_via_confirmed_group"
                    base["reason"] = f"overlap_group={grp} already counted as confirmed via a 'yes' row in the same group - not added to upper to avoid double-counting"
                else:
                    base["contributes_to"] = "upper_only"
                    base["reason"] = f"confirmed_exfiltrated=uncertain, overlap_group={grp} - counts toward upper bound only pending reconciliation"
            row_details.append(base)

    for r in rows:
        if r["jurisdiction"] == "Other US":
            row_details.append({
                "row_id": r["row_id"], "jurisdiction": "Other US", "dataset": r["dataset"],
                "overlap_group": r["overlap_group"], "confirmed_exfiltrated": r["confirmed_exfiltrated"],
                "unique_subjects": r["unique_subjects"], "high_risk_subset": r["high_risk_subset"],
                "contributes_to": "out_of_scope",
                "reason": "jurisdiction='Other US' - out of scope for this project's state-law analysis (evidence-pack.md)",
            })

    other_us_rows = [r["row_id"] for r in rows if r["jurisdiction"] == "Other US"]
    return results, other_us_rows, row_details
