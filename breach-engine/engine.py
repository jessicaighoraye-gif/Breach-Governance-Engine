"""Orchestrates trigger evaluation and deadline computation for one case,
reading logic entirely from rules/*.json (see rules_loader.py).
"""
from clocks import parse_utc, add_hours, add_calendar_days, fmt_utc, fmt_wat


def _evaluate_trigger(rule, case_input, incident_facts, prior_results):
    cond = rule["trigger_condition"]
    ttype = cond["trigger_type"]

    if ttype == "population_nonzero":
        return case_input[cond["population_field"]] > 0

    if ttype == "high_risk_subset_nonzero":
        base = bool(incident_facts.get(cond["case_fact_field"], False))
        if cond.get("requires_key_acquired") and not case_input.get("encryption_key_acquired", False):
            return False
        return base

    if ttype == "population_and_category":
        pop_ok = case_input[cond["population_field"]] > 0
        cats = set(incident_facts.get("categories_present", []))
        cat_ok = bool(cats.intersection(cond["qualifying_categories"]))
        return pop_ok and cat_ok

    if ttype == "dependent_threshold":
        dep_id = cond["requires_rule_id_triggered"]
        if not prior_results.get(dep_id, {}).get("triggered_yes_no"):
            return False
        val = case_input[cond["population_field"]]
        op, threshold = cond["threshold_operator"], cond["threshold_value"]
        return {">": val > threshold, ">=": val >= threshold,
                "<": val < threshold, "<=": val <= threshold,
                "==": val == threshold}[op]

    raise ValueError(f"Unknown trigger_type: {ttype}")


def _compute_deadline(rule, triggered, case_input, prior_results):
    if not triggered or rule.get("no_fixed_deadline"):
        return None, None

    basis = rule["clock_basis"]
    if basis == "awareness_utc":
        start = parse_utc(case_input["awareness_utc"])
    elif basis == "consumer_notice_utc":
        dep = prior_results[rule["depends_on_rule_id"]]
        if dep["calculated_deadline_utc"] is None:
            return None, None
        start = parse_utc(dep["calculated_deadline_utc"])
    else:
        raise ValueError(f"Unknown clock_basis: {basis}")

    if rule["duration_unit"] == "hours":
        deadline = add_hours(start, rule["duration_value"])
    elif rule["duration_unit"] == "calendar_days":
        deadline = add_calendar_days(start, rule["duration_value"])
    else:
        return fmt_utc(start), None
    return fmt_utc(start), fmt_utc(deadline)


def run_case(case_input, incident_facts, rules):
    """Returns full ledger rows for all rules, in rule_id order, respecting
    dependencies (DL-005 needs DL-004 resolved first)."""
    order = ["DL-001", "DL-002", "DL-003", "DL-004", "DL-005"]
    results = {}
    for rid in order:
        rule = rules[rid]
        triggered = _evaluate_trigger(rule, case_input, incident_facts, results)
        clock_start_utc, deadline_utc = _compute_deadline(rule, triggered, case_input, results)
        results[rid] = {
            "obligation_id": rid,
            "jurisdiction": rule["jurisdiction"],
            "authority": rule["authority"],
            "role": rule["role"],
            "triggered_yes_no": triggered,
            "clock_rule": rule["citation"],
            "clock_basis": rule["clock_basis"],
            "clock_start_utc": clock_start_utc,
            "clock_start_local": fmt_wat(parse_utc(clock_start_utc)) if clock_start_utc else None,
            "calculated_deadline_utc": deadline_utc,
            "calculated_deadline_local": fmt_wat(parse_utc(deadline_utc)) if deadline_utc else None,
        }
    return results


def to_expected_output_shape(results, case_input):
    """Projects full ledger results down to exactly the fields
    public-fixtures.json checks, for direct fixture comparison."""
    dl004, dl005 = results["DL-001"], results["DL-005"]
    return {
        "california_ag_sample_required": results["DL-005"]["triggered_yes_no"],
        "california_ag_deadline_basis": (
            "consumer_notice_plus_15_calendar_days" if results["DL-005"]["triggered_yes_no"] else None
        ),
        "california_consumer_deadline_utc": results["DL-004"]["calculated_deadline_utc"],
        "gdpr_article_33_deadline_utc": results["DL-001"]["calculated_deadline_utc"],
        "ndpa_section_40_deadline_utc": results["DL-003"]["calculated_deadline_utc"],
    }
