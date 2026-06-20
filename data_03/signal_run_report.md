# Signal Extraction Handoff

## Run Summary

- Documents processed: 18
- Facts generated: 42
- Alerts generated: 31
- Risk alerts: 3
- Opportunity alerts: 9
- Ownership/control alerts: 3
- Mixed alerts: 16

## Severity Counts

- critical: 0
- high: 9
- medium: 22
- low: 0

## Top Demo Alerts

1. demo-001 - Robinhood Markets, Inc. has new jurisdiction exposure: Luxembourg; British Virgin Islands; Singapore - high severity, 0.95 confidence
2. demo-001 - Robinhood Markets, Inc. has ownership/control drift involving Bitstamp Ltd. - high severity, 0.94 confidence
3. demo-003 - GameStop Corp. treasury activity changed: 4,710 Bitcoin purchase - high severity, 0.94 confidence

## Suppressed Or Skipped

- Low-confidence facts skipped: 0
- Pre-baseline context facts not alerted: 2
- Duplicate facts clustered into shared alerts: 9

## Notes For Teammate 4

- `alerts.json` includes an `evidence` list with source URL, title, published date, and excerpt.
- `changed_fields`, `baseline_value`, and `new_value` are already shaped for before/after UI display.
- `fact_ids` can be used to drill into `facts.json` for extraction details.
