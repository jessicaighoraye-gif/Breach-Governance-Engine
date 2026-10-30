# Continuity Record - Stage 9 (Breach Governance)

**IMPORTANT:** Sections 1-4 below require your actual Stage 8 (Technical Treatment)
work, which is not present in this project's file set - I don't have access to it
and have not invented placeholder content to fill it. Complete these before submission.

## 1. Previous-stage commit and component reused

`[FILL IN - Stage 8's frozen commit hash and the exact component/module name you are reusing]`

Per portfolio-continuity.md: "The typed control and evidence model flows through
vendor assurance, audit, technical treatment, and breach governance." Identify which
specific typed control/evidence model component from Stage 8 this build reuses.

## 2. Interface consumed and backward-compatible extension

`[FILL IN - what interface/schema/function signature from Stage 8 does this engine
call or extend? Was the extension backward-compatible, or does it require a
migration note in Section 4?]`

## 3. Evidence of preserved raw-to-result provenance

`[FILL IN - demonstrate that Stage 8's raw evidence chain (source artifact -> claim ->
locator) is still intact and traceable through into this stage's evidence-index.csv,
not silently dropped or replaced]`

This stage's own provenance model (for reference, to extend consistently):
`datainventory.csv` row -> `breach-engine/population.py` -> `population-calculation.csv`
row-level detail -> `deadline-ledger.csv` obligation -> `work-items.json` item -> notice.
Every hop is traceable via `row_id` (`DI-XXX`) and `obligation_id` (`DL-XXX`), verified
in `evidence-index.csv` and `variant-snapshots/`.

## 4. Migration record for incompatible changes

`[FILL IN - if anything from Stage 8's model had to change shape to fit this stage
(e.g. a schema field renamed, a different dedup rule, a new required field), document
each one here with the reason. If nothing was incompatible, state that explicitly
rather than leaving this blank - portfolio-continuity.md treats an undocumented gap
as a potential failure condition ("Losing raw evidence provenance during a migration").]`

## 5. Component/schema/evidence/decision record handed to the next stage

Per portfolio-continuity.md's track progression, Stage 9 (breach governance) is the
final capstone of the GRC track ("Chapter 5 - Capstone... This is the report that
leaves the building"). There is no Stage 10 in this track to hand off to.

What this stage produces, for the record and for any future audit/reference:
- **Schema model:** 8 JSON Schema files in `schemas/` (case input, expected output,
  dataset row, population result, jurisdiction rule, deadline ledger entry, clock
  event, work item).
- **Evidence model:** `evidence-index.csv` (12 claims, each with artifact path, exact
  locator, sha256 where applicable, confidence, and a documented alternative
  considered) plus `variant-snapshots/` (7 frozen engine outputs).
- **Decision record:** the full D-001 through D-014 decision log in `README.md`,
  including two real defects found and fixed during testing (population double-count
  guard; a false evidence locator in the Art.34 work item).
- **Ownership/exception model:** `input/ownership-config.json` and the
  `assumptions_or_exception` column in `deadline-ledger.csv`, both explicitly flagged
  as role-based assumptions rather than confirmed facts (D-013).
