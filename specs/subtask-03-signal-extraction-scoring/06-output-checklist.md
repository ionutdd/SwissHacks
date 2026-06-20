# Output Checklist

Use this before handing off to teammate 4.

## Required Files

- [ ] `data_03/facts.json`
- [ ] `data_03/alerts.json`

Recommended:

- [ ] `scripts/extract_signals.py`
- [ ] `data_03/signal_run_report.md`

## Facts Checklist

For every fact:

- [ ] Has stable `fact_id`.
- [ ] Has valid `customer_id`.
- [ ] Has valid `document_id`.
- [ ] Has `fact_type`.
- [ ] Has `subject`.
- [ ] Has `value` or `object`.
- [ ] Has `baseline_fields_targeted`.
- [ ] Has `evidence_excerpt`.
- [ ] Has `source_quality`.
- [ ] Has `extraction_confidence`.
- [ ] Does not invent unsupported fields.

## Alerts Checklist

For every alert:

- [ ] Has stable `alert_id`.
- [ ] Has valid `customer_id`.
- [ ] Has `category`.
- [ ] Has `signal_type`.
- [ ] Has clear `title`.
- [ ] Has clear `summary`.
- [ ] Has `changed_fields`.
- [ ] Has `baseline_value`.
- [ ] Has `new_value`.
- [ ] Has `severity`.
- [ ] Has numeric `confidence`.
- [ ] Has `recommended_action`.
- [ ] Has `evidence_document_ids`.
- [ ] Has `fact_ids`.
- [ ] Has `status`.
- [ ] Has `created_at`.

## Portfolio Checklist

Across all alerts:

- [ ] At least 8 alerts generated.
- [ ] At least 3 risk alerts.
- [ ] At least 3 opportunity alerts.
- [ ] At least 1 ownership/control alert.
- [ ] Each top 3 demo story has at least 1 alert.
- [ ] No alert exists without evidence.
- [ ] High-severity alerts use A or B quality sources.

## Handoff To Teammate 4

Before UI integration:

- [ ] Alert shape matches `05-output-schema-spec.md`.
- [ ] Every alert can show source excerpt and URL.
- [ ] Every alert has before/after fields.
- [ ] Every alert has a recommended RM/compliance action.
- [ ] Top 3 demo alerts are easy to identify.

## Ready-To-Handoff Summary Template

```markdown
# Signal Extraction Handoff

## Run Summary

- Documents processed:
- Facts generated:
- Alerts generated:
- Risk alerts:
- Opportunity alerts:
- Ownership/control alerts:

## Top Demo Alerts

1. [Customer] - [Alert title] - [why strong]
2. [Customer] - [Alert title] - [why strong]
3. [Customer] - [Alert title] - [why strong]

## Suppressed Or Skipped

- [Reason]

## Notes For Teammate 4

- [UI display hints]
```
