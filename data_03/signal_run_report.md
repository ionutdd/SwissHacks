# Signal Extraction Handoff

## Run Summary

- Documents processed: 22
- Facts generated: 71
- Alerts generated: 63
- AI-validated facts: 37
- Rule-fallback facts: 34
- Risk alerts: 12
- Opportunity alerts: 15
- Ownership/control alerts: 4
- Mixed alerts: 32

## Severity Counts

- critical: 5
- high: 17
- medium: 41
- low: 0

## Top Demo Alerts

1. demo-006 - Garantex Europe OU has new digital-asset activity: sanctioned Russia-linked virtual currency exchange - critical severity, 0.94 confidence
2. demo-006 - Garantex Europe OU has jurisdiction restriction signal: Russia sanctions and virtual-currency evasion exposure - critical severity, 0.94 confidence
3. demo-007 - British American Tobacco p.l.c. has new jurisdiction exposure: North Korea - critical severity, 0.94 confidence

## Suppressed Or Skipped

- Low-confidence facts skipped: 0
- Pre-baseline context facts not alerted: 2
- Duplicate facts clustered into shared alerts: 6

## Notes For Teammate 4

- `alerts.json` includes an `evidence` list with source URL, title, published date, and excerpt.
- `changed_fields`, `baseline_value`, and `new_value` are already shaped for before/after UI display.
- `fact_ids` can be used to drill into `facts.json` for extraction details.
