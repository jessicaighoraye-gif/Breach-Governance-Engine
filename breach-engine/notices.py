"""Generates regulator and subject notices directly from engine output 

NOTE: the four-part structure (nature of breach / contact / consequences /
measures) mirrors GDPR Article 33(3)'s standard content requirements. That
structure is GENERAL LEGAL KNOWLEDGE, flagged here explicitly.
"""

CONTACT = "dpo@example.invalid (Data Protection Officer)"  # evidence-pack.md, Organisation and roles


def _population_line(pop):
    if pop["upper_bound_unique"] > pop["confirmed_unique"]:
        return (
            f"{pop['confirmed_unique']:,} individuals confirmed affected. "
            f"An additional {pop['upper_bound_unique'] - pop['confirmed_unique']:,} are "
            f"still under investigation (backup index reconciliation pending) and are "
            f"not yet confirmed - upper bound {pop['upper_bound_unique']:,}."
        )
    return f"{pop['confirmed_unique']:,} individuals confirmed affected."


def _california_consumer_notice_body(dl004_row, ca_population, case_input):
    """The actual notice text sent to California consumers."""
    if not dl004_row["triggered_yes_no"]:
        return "Trigger condition not met for this case. No notice generated.\n"
    return (
        f"**Status:** triggered. **Deadline:** {dl004_row['calculated_deadline_utc']} "
        f"({dl004_row['calculated_deadline_local']}), 30 calendar days from "
        f"{dl004_row['awareness_time_utc']}.\n\n"
        f"What happened: an unauthorized actor accessed data including your account "
        f"email and password hash, and for some individuals, medical information. "
        f"Attribution of the actor is not established.\n\n"
        f"{_population_line(ca_population)}\n\n"
        f"What we know vs. still investigating: the account-credential exposure "
        f"(email and password hash) is confirmed. The scope of medical-information "
        f"exposure depends on the encryption-key assessment for this case "
        f"(encryption_key_acquired={case_input['encryption_key_acquired']}) and may be "
        f"updated as the investigation continues.\n\n"
        f"What we are doing: containment is complete. We recommend monitoring your "
        f"accounts and are finalizing further remediation steps.\n\n"
        f"No law-enforcement delay has been requested for this notice.\n\n"
        f"Contact: {CONTACT}\n"
    )


def build_ag_sample_notice(dl005_row, dl004_row, ca_population, case_input):
    if not dl005_row["triggered_yes_no"]:
        return (
            "# California Attorney General - AG Sample Notice Not Required\n\n"
            f"california_unique ({ca_population['confirmed_unique']}) does not exceed the "
            "500-resident threshold under Civil Code 1798.82(f). No sample notice submitted. "
            "See rules/DL-005-ca-1798-82f.json.\n"
        )
    body = _california_consumer_notice_body(dl004_row, ca_population, case_input)
    return f"""# California Attorney General - Sample Notice Submission (Civil Code 1798.82(f))

**Obligation ID:** {dl005_row['obligation_id']} · **Status:** {dl005_row['status']}
**Submission deadline:** {dl005_row['calculated_deadline_utc']} ({dl005_row['calculated_deadline_local']})
**Clock basis:** 15 calendar days after the consumer notice deadline below (a DEPENDENT clock, not a fresh 15 days from awareness).
**California residents notified:** {ca_population['confirmed_unique']:,} (exceeds the 500-resident threshold)

This submission is a sample copy of the notice being sent to affected California residents,
per Civil Code 1798.82(f). It is not an independently drafted document.

## Sample notice text

{body}

---
*Generated directly from deadline-ledger.csv rows DL-004 and DL-005 - the notice body above
is the SAME content used in subject-notice.md's California section, not a separate draft.*
"""


def build_regulator_notice(rule_id, ledger_row, population_result, case_input):
    if not ledger_row["triggered_yes_no"]:
        return (
            f"# {ledger_row['authority']} - Not Required\n\n"
            f"Trigger condition not met for this case. No notice generated.\n"
        )

    phased_note = ""
    if population_result["upper_bound_unique"] > population_result["confirmed_unique"]:
        phased_note = (
            "\n**This notice is being submitted within the statutory clock on the basis of "
            "currently confirmed facts, in phased form, per standard practice of not delaying a "
            "triggered notification solely to await full reconciliation of an under-investigation "
            "figure.** A supplementary update will follow once the pending backup-index "
            "reconciliation is complete.\n"
        )

    return f"""# {ledger_row['authority']} - Breach Notification

**Obligation ID:** {ledger_row['obligation_id']} · **Status:** {ledger_row['status']}
**Notice deadline:** {ledger_row['calculated_deadline_utc']} ({ledger_row['calculated_deadline_local']})
**Clock basis:** {ledger_row['clock_rule']}, from {ledger_row['awareness_time_utc']} ({ledger_row['awareness_time_local']})

## 1. Nature of the breach

An unauthorized actor accessed the support database and obtained a data export together
with an application service credential able to decrypt fields during normal operation
(current assessment, subject to ongoing investigation). Attribution of the actor is not
established and is not asserted here.

Categories of personal data concerned for this jurisdiction include contact details and,
for some records, diagnosis-category and identifier information, subject to what remains
readable under the current encryption-key assessment for this case
(encryption_key_acquired = {case_input['encryption_key_acquired']}).

**Population affected:** {_population_line(population_result)}
{phased_note}
## 2. Contact point

{CONTACT}

## 3. Likely consequences

Individuals whose account credentials were exposed face a residual risk of phishing or
credential-based account access attempts. Where diagnosis-category or identifier data is
confirmed readable, the potential impact is higher for that subset. Password values
themselves use the Argon2id hashing algorithm and are not confirmed to be directly
recoverable.

## 4. Measures taken or proposed

Containment of the incident was completed. Further remediation measures (e.g. credential
rotation, enhanced monitoring) are to be finalized and confirmed separately - not yet
stated as fact in the source evidence available at notice time.

---
*Generated directly from deadline-ledger.csv row {ledger_row['obligation_id']} and the
population engine - not hand-edited. Trace: rules/{ledger_row['obligation_id']}*.json ->
breach-engine/engine.py -> this file.*
"""


def build_subject_notice(dl002_row, dl004_row, eu_population, ca_population, case_input):
    sections = []

    sections.append("# Subject Notice\n")
    sections.append(
        "This notice covers direct communication to affected individuals under two separate "
        "obligations: GDPR Article 34 (EU high-risk subjects) and California Civil Code "
        "1798.82 (California consumers). Each section is generated independently from its "
        "own ledger row - they are not the same clock or the same population.\n"
    )

    # --- EU Article 34 section ---
    sections.append("## EU high-risk individuals - GDPR Article 34\n")
    if dl002_row["triggered_yes_no"]:
        sections.append(
            f"**Status:** triggered, no fixed statutory deadline (\"without undue delay\").\n\n"
            f"What we know: your data may have included information beyond basic contact "
            f"details. {_population_line(eu_population)}\n\n"
            f"What this means: if your record falls within the higher-risk subset, the "
            f"exposure may include category-specific information rather than only contact "
            f"details. We are notifying you directly because of this elevated risk.\n\n"
            f"What we are doing: containment of the incident is complete. Further remediation "
            f"steps are being finalized.\n\n"
            f"Contact: {CONTACT}\n"
        )
    else:
        sections.append(
            "Trigger condition not currently met for this case "
            f"(encryption_key_acquired={case_input['encryption_key_acquired']} - see "
            "rules/DL-002-gdpr-art34.json for the reasoning). No individual notice generated "
            "under this obligation.\n"
        )

    # --- California section ---
    sections.append("\n## California consumers - Civil Code 1798.82\n")
    sections.append(_california_consumer_notice_body(dl004_row, ca_population, case_input))

    sections.append(
        "\n---\n*Generated directly from deadline-ledger.csv rows DL-002 and DL-004 - not "
        "hand-edited.*\n"
    )
    return "\n".join(sections)
