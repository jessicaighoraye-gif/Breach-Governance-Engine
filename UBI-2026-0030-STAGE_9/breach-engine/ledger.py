"""Projects engine results (breach-engine/engine.py) into rows matching
deadlineledger.csv's exact column order. status='final' for triggered rows
"""

TRIGGER_TEST_DESCRIPTIONS = {
    "DL-001": "eu_unique > 0 (risk threshold assumed met - D-011 open, independent of encryption_key_acquired)",
    "DL-002": "high_risk_subset_present_eu == true AND encryption_key_acquired == true (D-014: high-risk basis is diagnosis_category+id_suffix, only readable if the export key was acquired)",
    "DL-003": "nigeria_unique > 0 (mirrors D-011 assumption)",
    "DL-004": "california_unique > 0 AND categories_present intersects [email_password_combo, medical_information] (D-009)",
    "DL-005": "DL-004.triggered AND california_unique > 500",
}

ASSUMPTIONS = {
    "DL-001": "Feasibility-qualified 72h ceiling per GDPR Art.33 ('without undue delay and, where feasible, within 72 hours'). D-014: trigger stays independent of encryption_key_acquired - Art.33's low bar is cleared by the unconditionally-unencrypted account_profile dataset (email+password_hash) alone, even if the patient_support export stays protected.",
    "DL-002": "No fixed offset - 'without undue delay' per GDPR Art.34. D-014: trigger IS gated on encryption_key_acquired - the high_risk_subset basis (diagnosis_category + id_suffix) lives only in the encrypted patient_support dataset.",
    "DL-003": "72h ceiling, NOT feasibility-qualified - brief.md attaches 'where feasible' only to GDPR Art.33, not NDPA s.40. D-014: same encryption-independence reasoning as DL-001.",
    "DL-004": "Trigger is category-based (D-009, resolved via SB 446 text + evidence-pack California facts), not population-threshold-gated. No law-enforcement delay requested (D-010) - 30-day clock runs unmodified. Independent of encryption_key_acquired - email+password_hash is explicitly unencrypted.",
    "DL-005": "Clock basis is DL-004's calculated deadline, not awareness_utc directly - this is a DEPENDENT clock. D-006 unverified: no fixture checks the actual AG deadline date, only the basis string and required flag.",
}


def build_ledger_rows(engine_results, ownership_config):
    rows = []
    for rid in ["DL-001", "DL-002", "DL-003", "DL-004", "DL-005"]:
        r = engine_results[rid]
        own = ownership_config[rid]
        triggered = r["triggered_yes_no"]
        rows.append({
            "obligation_id": r["obligation_id"],
            "jurisdiction": r["jurisdiction"],
            "authority": r["authority"],
            "role": r["role"],
            "trigger_test": TRIGGER_TEST_DESCRIPTIONS[rid],
            "triggered_yes_no": triggered,
            "awareness_time_local": r["clock_start_local"] if triggered else None,
            "awareness_time_utc": r["clock_start_utc"] if triggered else None,
            "clock_rule": r["clock_rule"],
            "calculated_deadline_local": r["calculated_deadline_local"],
            "calculated_deadline_utc": r["calculated_deadline_utc"],
            "recipient": own["recipient"] if triggered else None,
            "owner": own["owner"],
            "status": "final" if triggered else "not_applicable",
            "assumptions_or_exception": ASSUMPTIONS[rid],
        })
    return rows


def write_csv(rows, path):
    import csv
    fieldnames = [
        "obligation_id", "jurisdiction", "authority", "role", "trigger_test",
        "triggered_yes_no", "awareness_time_local", "awareness_time_utc",
        "clock_rule", "calculated_deadline_local", "calculated_deadline_utc",
        "recipient", "owner", "status", "assumptions_or_exception",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
