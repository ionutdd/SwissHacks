# Signal Extraction Handoff

## Run Summary

- Documents processed: 22
- Facts generated: 59
- Alerts generated: 48
- AI-validated facts: 0
- Rule-fallback facts: 59
- Risk alerts: 9
- Opportunity alerts: 11
- Ownership/control alerts: 3
- Mixed alerts: 25

## Severity Counts

- critical: 7
- high: 12
- medium: 29
- low: 0

## Top Demo Alerts

1. demo-006 - Garantex Europe OU has new digital-asset activity: sanctioned Russia-linked virtual currency exchange - critical severity, 0.94 confidence
2. demo-006 - Garantex Europe OU has jurisdiction restriction signal: Russia sanctions and virtual-currency evasion exposure - critical severity, 0.94 confidence
3. demo-007 - British American Tobacco p.l.c. business activity changed: North Korea tobacco joint-venture and export exposure - critical severity, 0.94 confidence

## Suppressed Or Skipped

- Low-confidence facts skipped: 0
- Pre-baseline context facts not alerted: 2
- Duplicate facts clustered into shared alerts: 9

## Notes For Teammate 4

- `alerts.json` includes an `evidence` list with source URL, title, published date, and excerpt.
- `changed_fields`, `baseline_value`, and `new_value` are already shaped for before/after UI display.
- `fact_ids` can be used to drill into `facts.json` for extraction details.
