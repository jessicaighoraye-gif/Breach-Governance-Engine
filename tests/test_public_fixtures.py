import json
import os
import sys

# breach-engine/ has a hyphen (fixed by submission-contract.md's required
# deliverable name) so it can't be imported as a normal Python package -
# add it directly to sys.path instead of using dotted imports.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "breach-engine"))
from rules_loader import load_rules
from engine import run_case, to_expected_output_shape

BASE = os.path.join(os.path.dirname(__file__), "..")


def _load_json(rel):
    with open(os.path.join(BASE, rel)) as f:
        return json.load(f)


RULES = load_rules(os.path.join(BASE, "rules"))
INCIDENT_FACTS = _load_json("input/incident-facts.json")
FIXTURES = _load_json("input/public-fixtures.json")["fixtures"]


def _run(case_input):
    results = run_case(case_input, INCIDENT_FACTS, RULES)
    return to_expected_output_shape(results, case_input), results


def test_all_public_fixtures_match_exactly():
    failures = []
    for fx in FIXTURES:
        actual, _ = _run(fx["input"])
        expected = fx["expected"]
        if actual != expected:
            failures.append((fx["case_id"], actual, expected))
    assert not failures, "\n".join(
        f"{cid} MISMATCH\n  actual:   {a}\n  expected: {e}" for cid, a, e in failures
    )


def test_dl002_art34_always_triggers_but_has_no_deadline():
    # Not checked by any fixture's expected block - verified separately here.
    for fx in FIXTURES:
        _, results = _run(fx["input"])
        assert results["DL-002"]["triggered_yes_no"] is True
        assert results["DL-002"]["calculated_deadline_utc"] is None


def test_california_threshold_branch_ca_unique_below_500():
    """No public fixture covers this (D-004) - synthetic input built from V1
    with california_unique dropped below 500 to exercise the untested branch."""
    case_input = dict(FIXTURES[0]["input"])
    case_input["california_unique"] = 300
    actual, results = _run(case_input)
    assert actual["california_ag_sample_required"] is False
    assert actual["california_ag_deadline_basis"] is None
    # DL-004 (consumer notice) must still trigger - its trigger is category-based,
    # not population-threshold-based (D-009).
    assert results["DL-004"]["triggered_yes_no"] is True
    assert results["DL-004"]["calculated_deadline_utc"] is not None


def test_california_zero_residents_dl004_does_not_trigger():
    case_input = dict(FIXTURES[0]["input"])
    case_input["california_unique"] = 0
    _, results = _run(case_input)
    assert results["DL-004"]["triggered_yes_no"] is False
    assert results["DL-005"]["triggered_yes_no"] is False
