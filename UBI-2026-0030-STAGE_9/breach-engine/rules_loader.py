import json
import glob
import os


def load_rules(rules_dir):
    """Loads every rule config in rules_dir, keyed by rule_id."""
    rules = {}
    for path in sorted(glob.glob(os.path.join(rules_dir, "*.json"))):
        with open(path) as f:
            rule = json.load(f)
        rules[rule["rule_id"]] = rule
    return rules
