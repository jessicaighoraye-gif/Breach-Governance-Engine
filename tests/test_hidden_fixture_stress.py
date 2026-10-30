"""Stress tests targeting overlap-group restructuring and encryption-key status
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "breach-engine"))
from population import compute_population
from rules_loader import load_rules
from engine import run_case

BASE = os.path.join(os.path.dirname(__file__), "..")
RULES = load_rules(os.path.join(BASE, "rules"))
INCIDENT_FACTS = {
    "categories_present": ["email_password_combo", "medical_information"],
    "high_risk_subset_present_eu": True,
    "high_risk_subset_present_nigeria": True,
}


def _row(row_id, jur, dataset, cats, unique, records, group, status, high_risk, notes=""):
    return {
        "row_id": row_id, "jurisdiction": jur, "dataset": dataset,
        "data_categories": cats, "unique_subjects": str(unique), "records": str(records),
        "overlap_group": group, "confirmed_exfiltrated": status,
        "high_risk_subset": str(high_risk), "notes": notes,
    }


# ---------------------------------------------------------------------
# The bug: same overlap_group split across a 'yes' row and an 'uncertain'
# row should represent the SAME people, not be double-counted in upper.
# ---------------------------------------------------------------------
def test_mixed_status_same_overlap_group_not_double_counted():
    rows = [
        _row("X-001", "EU", "patient_support", "email|mobile", 200, 200, "EU-Z", "yes", 0),
        _row("X-002", "EU", "account_profile", "email|password_hash", 200, 200, "EU-Z", "uncertain", 0,
             "same people as X-001, re-flagged uncertain pending review"),
    ]
    results, _, _ = compute_population(rows)
    eu = results["EU"]
    # Same 200 people, split status. Confirmed must be 200 (from the 'yes' row).
    assert eu["confirmed_unique"] == 200
    # Upper must ALSO be 200 - NOT 400. A naive implementation adds the
    # uncertain row's 200 on top of the confirmed 200, double-counting.
    assert eu["upper_bound_unique"] == 200, (
        f"BUG: upper_bound_unique={eu['upper_bound_unique']}, expected 200. "
        "Same overlap_group counted in both confirmed and upper additions."
    )


def test_three_way_overlap_still_dedups_to_one_count():
    rows = [
        _row("X-010", "Nigeria", "patient_support", "email", 500, 500, "NG-Z", "yes", 0),
        _row("X-011", "Nigeria", "account_profile", "email|password_hash", 500, 500, "NG-Z", "yes", 0),
        _row("X-012", "Nigeria", "archived_cases", "case_text", 500, 500, "NG-Z", "yes", 0),
    ]
    results, _, _ = compute_population(rows)
    assert results["Nigeria"]["confirmed_unique"] == 500
    assert len(results["Nigeria"]["included_rows"]) == 3


def test_overlap_group_label_reused_across_jurisdictions_stays_scoped():
    # Same literal group label "A" used independently in two jurisdictions -
    # must not merge into a single cross-jurisdiction dedup.
    rows = [
        _row("X-020", "EU", "patient_support", "email", 300, 300, "A", "yes", 0),
        _row("X-021", "Nigeria", "patient_support", "email", 900, 900, "A", "yes", 0),
    ]
    results, _, _ = compute_population(rows)
    assert results["EU"]["confirmed_unique"] == 300
    assert results["Nigeria"]["confirmed_unique"] == 900


def test_new_unseen_dataset_or_group_ingests_without_special_casing():
    rows = [
        _row("X-030", "California", "support_chat_export", "email|mobile", 50, 50, "CA-Z", "yes", 0),
    ]
    results, _, _ = compute_population(rows)
    assert results["California"]["confirmed_unique"] == 50


# ---------------------------------------------------------------------
# encryption_key_acquired - D-014 now properly implemented (was D-011,
# fully unimplemented before). DL-002 (Art.34) is gated on it because its
# high-risk basis lives only in the encrypted patient_support dataset.
# DL-001/003/004/005 stay independent of it - each for a specific, cited
# reason, not by default/oversight. See rules/*.json 'note' fields.
# ---------------------------------------------------------------------
def test_encryption_key_acquired_false_disables_art34_but_nothing_else():
    base = {"awareness_utc": "2026-07-13T07:35:00Z", "california_unique": 530,
            "eu_unique": 620, "nigeria_unique": 1280}
    true_case = dict(base, encryption_key_acquired=True)
    false_case = dict(base, encryption_key_acquired=False)

    r_true = run_case(true_case, INCIDENT_FACTS, RULES)
    r_false = run_case(false_case, INCIDENT_FACTS, RULES)

    # DL-002 (Art.34) is the ONLY obligation that should flip.
    assert r_true["DL-002"]["triggered_yes_no"] is True
    assert r_false["DL-002"]["triggered_yes_no"] is False

    # Everything else - DL-001, DL-003, DL-004, DL-005 - stays triggered,
    # each for a documented reason (see rules/*.json), not by default.
    for rid in ["DL-001", "DL-003", "DL-004", "DL-005"]:
        assert r_true[rid]["triggered_yes_no"] == r_false[rid]["triggered_yes_no"] is True, (
            f"{rid} unexpectedly changed with encryption_key_acquired - check its rule note."
        )


def test_month_boundary_arithmetic_does_not_break_30_day_or_72_hour_math():
    case_input = {"awareness_utc": "2026-12-30T10:00:00Z", "california_unique": 530,
                  "encryption_key_acquired": True, "eu_unique": 620, "nigeria_unique": 1280}
    results = run_case(case_input, INCIDENT_FACTS, RULES)
    assert results["DL-001"]["calculated_deadline_utc"] == "2027-01-02T10:00:00Z"
    assert results["DL-004"]["calculated_deadline_utc"] == "2027-01-29T10:00:00Z"


def test_mixed_status_row_details_flag_not_double_counted():
    rows = [
        _row("X-001", "EU", "patient_support", "email|mobile", 200, 200, "EU-Z", "yes", 0),
        _row("X-002", "EU", "account_profile", "email|password_hash", 200, 200, "EU-Z", "uncertain", 0,
             "same people as X-001, re-flagged uncertain pending review"),
    ]
    _, _, row_details = compute_population(rows)
    by_id = {d["row_id"]: d for d in row_details}
    assert by_id["X-001"]["contributes_to"] == "confirmed"
    assert by_id["X-002"]["contributes_to"] == "already_counted_via_confirmed_group"
