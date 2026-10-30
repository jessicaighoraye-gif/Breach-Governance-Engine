import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "breach-engine"))
from population import load_rows, compute_population

BASE = os.path.join(os.path.dirname(__file__), "..")
ROWS = load_rows(os.path.join(BASE, "input", "datainventory.csv"))


def test_confirmed_population_matches_v1_fixture_inputs():
    """V1's case_input eu_unique/nigeria_unique/california_unique are the
    REAL derived numbers, not arbitrary test values (see chat discussion).
    This proves population.py reproduces them purely from datainventory.csv."""
    results, _, _ = compute_population(ROWS)
    assert results["EU"]["confirmed_unique"] == 620
    assert results["Nigeria"]["confirmed_unique"] == 1280
    assert results["California"]["confirmed_unique"] == 530


def test_overlap_group_deduped_not_summed():
    # DI-001 (620) + DI-002 (620) share overlap_group EU-A ("same people").
    # A naive sum would wrongly give 1240.
    results, _, _ = compute_population(ROWS)
    assert results["EU"]["confirmed_unique"] != 620 + 620
    assert "DI-001" in results["EU"]["included_rows"]
    assert "DI-002" in results["EU"]["included_rows"]


def test_network_disproved_row_excluded():
    # DI-009: confirmed_exfiltrated=no, "network evidence excludes archive"
    results, _, _ = compute_population(ROWS)
    excluded_ids = [e["row_id"] for e in results["California"]["excluded_rows"]]
    assert "DI-009" in excluded_ids
    included_ids = results["California"]["included_rows"]
    assert "DI-009" not in included_ids


def test_uncertain_rows_only_count_toward_upper_bound():
    # DI-003 (EU-B, uncertain, 85) - backup index reconciliation pending
    results, _, _ = compute_population(ROWS)
    eu = results["EU"]
    assert eu["confirmed_unique"] == eu["lower_bound_unique"] == 620
    assert eu["upper_bound_unique"] == 620 + 85


def test_other_us_tracked_but_excluded_from_all_jurisdiction_totals():
    results, other_us_rows, _ = compute_population(ROWS)
    assert other_us_rows == ["DI-010"]
    for jur_result in results.values():
        assert "DI-010" not in jur_result["included_rows"]
        assert "DI-010" not in [e["row_id"] for e in jur_result["excluded_rows"]]


def test_high_risk_subset_deduped_by_group_not_summed():
    # DI-001 high_risk_subset=214, DI-002 (same people, EU-A)=0 - should
    # take the representative 214, not sum to 214.
    results, _, _ = compute_population(ROWS)
    assert results["EU"]["high_risk_subset_confirmed"] == 214
    assert results["Nigeria"]["high_risk_subset_confirmed"] == 506


def test_high_risk_source_rows_exclude_zero_contribution_duplicates():
    # DI-003 (EU-B, uncertain, high_risk_subset=0) must NOT appear as a
    # source row for the Art.34 trigger - it never contributed to the count.
    results, _, _ = compute_population(ROWS)
    assert results["EU"]["high_risk_source_rows"] == ["DI-001"]
    assert "DI-003" not in results["EU"]["high_risk_source_rows"]
    assert results["Nigeria"]["high_risk_source_rows"] == ["DI-004"]
