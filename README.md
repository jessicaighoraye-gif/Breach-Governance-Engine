# Stage 9 - Breach Governance Engine

**Project:** 
**Evidence marker:** `UBI-A9-98F6CC1A8E87`
**Variant:** `V4`

## Environment this was built and tested in

- OS: Ubuntu 24.04.4 LTS
- Python: 3.12.3
- pytest: 9.1.1
- all inputs are local files in `input/`.


## Exact reproduction order

```bash
# 1. Set up environment
python3 -m venv .venv
source .venv/bin/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install pytest --break-system-packages

# 2. Run the full test suite (18 tests, must all pass before anything else)
python3 -m pytest tests/ -v

# 3. Run the real-case pipeline - derives population live from datainventory.csv,
#    writes work-items.json, population-calculation.csv, variant-snapshots/ to the submission root
python3 run_real_case.py


## Directory structure

```
breach-engine/     Engine source code (population, triggers, deadlines, notices,
                    board outputs, roadmap)
rules/              DL-001 through DL-005 jurisdiction rule configs (data, not code).
schemas/            JSON Schema files defining every data shape used.
tests/              18 tests: exact V1-V6 fixture match, population dedup correctness,
                    hidden-fixture-style stress tests (overlap-group restructuring,
                    encryption-key branching, month-boundary arithmetic).
input/              Source data: datainventory.csv, public-fixtures.json,
                    incident-facts.json (case-level constants), ownership-config.json.
                    NOT one of the 19 required names .
generated/          Internal working artifacts not in the 19 required names
                    (population-result.json).
variant-snapshots/  Frozen full engine output for V1-V6 plus the real case, each
                    with a self-check 'matches_public_fixture_expected' field.
regulator-notifications/   GDPR Art.33, NDPA s.40, and California AG sample notices.
```


## Decision log (D-001 through D-014)

Every consequential judgment made during this build, in order:

| ID | Decision | Where implemented |
|---|---|---|
| D-001 | Fact register locator corrections (original draft had systematic off-by-one line errors) | evidence-index.csv C-001, C-002 |
| D-002 | expected-output.schema.json fields made nullable - no public fixture shows an untriggered case | schemas/expected-output.schema.json |
| D-003 | population-result.schema.json is our own design - no staff template exists for this filename/shape | schemas/population-result.schema.json |
| D-004 | All V1-V6 fixtures trigger "yes" on everything - untested branches (california_unique<=500, encryption_key_acquired=false) covered by synthetic tests, not public fixtures | tests/test_public_fixtures.py, tests/test_hidden_fixture_stress.py |
| D-005 | GDPR Art.34 (DL-002) has no calculated deadline field checked by any fixture - trigger-only obligation | rules/DL-002-gdpr-art34.json |
| D-006 | California AG deadline (DL-005) date is never validated by any fixture, only its basis/required flag | rules/DL-005-ca-1798-82f.json |
| D-007/D-008 | The ">500" threshold in brief.md is grammatically scoped to DL-005 only, not DL-004 | rules/DL-004, DL-005 |
| D-009/D-010 | DL-004's actual trigger content (email+password combo, medical information) and delay conditions resolved via SB 446 primary statute text + evidence-pack.md California facts | evidence-index.csv C-008 |
| D-011 -> D-014 | GDPR/NDPA/CA trigger independence from encryption_key_acquired - initially an unverified default, later properly reasoned and partially implemented: DL-002 IS gated on it (high-risk basis lives in the encrypted dataset), DL-001/003/004/005 are not (each for a cited reason) | rules/*.json 'note' fields, evidence-index.csv C-009 |

Two real bugs found and fixed during testing:
1. **Population double-count**: an overlap_group split across a 'yes' row and an
   'uncertain' row was being counted in both confirmed and upper bound. Fixed in
   `breach-engine/population.py`; proven via a failing-then-passing test.
2. **False evidence locator**: the GDPR Art.34 work item originally cited all of a
   jurisdiction's included rows as source, including one (DI-003) that contributed
   zero to the high-risk count. Fixed via a new `high_risk_source_rows` field.

## Known open items

- D-006: California AG deadline date has zero fixture-based validation.
- D-013: Obligation owners and regulator recipients (input/ownership-config.json) are
  role-based assumptions, not confirmed named contacts. The exact lead EU supervisory
  authority is never named in evidence-pack.md.
- The GDPR/NDPA encryption-independence reasoning (D-014) is a documented legal
  judgment call, not settled law - see board-memo.pdf Section 4.

