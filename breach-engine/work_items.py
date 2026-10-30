"""Builds work items from ledger rows. Every item carries source_row_ids
pointing back to datainventory.csv."""

ACTION_TEXT = {
    "DL-001": "Submit GDPR Article 33 notice to lead EU supervisory authority",
    "DL-002": "Assess and notify high-risk EU data subjects under GDPR Article 34",
    "DL-003": "Submit Nigeria Data Protection Act 2023 section 40 notice to NDPC",
    "DL-004": "Notify affected California residents under Civil Code 1798.82",
    "DL-005": "Submit AG sample notice to California Attorney General under 1798.82(f)",
}

JURISDICTION_BY_RULE = {
    "DL-001": "EU", "DL-002": "EU", "DL-003": "Nigeria",
    "DL-004": "California", "DL-005": "California",
}

DEPENDS_ON = {"DL-005": "DL-004"}


def build_work_items(ledger_rows, population_results):
    items = []
    counter = 1
    ledger_by_id = {r["obligation_id"]: r for r in ledger_rows}
    wi_id_by_rule = {}

    for row in ledger_rows:
        rid = row["obligation_id"]
        if not row["triggered_yes_no"]:
            continue
        jur = JURISDICTION_BY_RULE[rid]
        source_rows = (
            population_results[jur]["high_risk_source_rows"] if rid == "DL-002"
            else population_results[jur]["included_rows"]
        )
        wi_id = f"WI-{counter:03d}"
        wi_id_by_rule[rid] = wi_id
        counter += 1

        dep_rule = DEPENDS_ON.get(rid)
        dep_wi = wi_id_by_rule.get(dep_rule) if dep_rule else None

        items.append({
            "work_item_id": wi_id,
            "obligation_id": rid,
            "jurisdiction": jur,
            "action": ACTION_TEXT[rid],
            "due_utc": row["calculated_deadline_utc"],
            "owner": row["owner"],
            "depends_on_work_item_id": dep_wi,
            "source_row_ids": source_rows,
            "status": "pending",
            "notes": None if row["calculated_deadline_utc"] else "No fixed statutory deadline (without undue delay) - track as an active item without a hard due date.",
        })
    return items
