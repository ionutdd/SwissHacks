# Scoring And Alert Spec

## Purpose

Convert compared facts into actionable alerts for the RM and compliance workflow.

Every alert must be explainable:

- What changed?
- Why does it matter?
- What evidence supports it?
- What should the user do?

## Alert Categories

Use:

- `risk`
- `opportunity`
- `ownership_control`
- `mixed`

## Severity

Allowed values:

- `critical`
- `high`
- `medium`
- `low`

### Critical

Use for:

- sanctions or prohibited activity.
- confirmed criminal enforcement.
- direct severe regulatory action.

The current demo probably does not need `critical` unless we add sanctions data.

### High

Use for:

- regulatory scrutiny.
- jurisdiction restrictions.
- acquisition materially changing KYC scope.
- sudden digital-asset treasury activity.
- sensitive sector exposure.

### Medium

Use for:

- new product/activity that changes business profile.
- new jurisdiction or legal entity with good evidence but moderate risk.
- commercial opportunity with risk review relevance.

### Low

Use for:

- opportunity-only update.
- weak or undated product-page evidence.
- useful RM brief item but not a compliance queue item.

## Confidence Score

Alert confidence should combine:

- fact extraction confidence.
- source quality.
- evidence directness.
- number of corroborating documents.
- baseline comparison clarity.

Recommended formula for hackathon:

```text
confidence =
  0.45 * average_fact_confidence
  + 0.25 * source_quality_score
  + 0.20 * comparison_clarity
  + 0.10 * corroboration_score
```

Source quality score:

- A: `0.95`
- B: `0.80`
- C: `0.55`
- D: `0.30`

Comparison clarity:

- Direct missing baseline field: `0.95`
- Review needed, not direct replacement: `0.75`
- Context only: `0.50`

Corroboration:

- 2 or more sources: `1.0`
- 1 official source: `0.85`
- 1 secondary source: `0.65`

Clamp to `0.0` to `1.0`.

## Recommended Actions

Use deterministic actions for the demo.

### Regulatory Scrutiny

Recommended action:

```text
Escalate to compliance for enhanced due diligence and confirm whether the customer has licensing or market-access changes.
```

### Jurisdiction Restriction

Recommended action:

```text
Ask RM to confirm operating jurisdictions and route to compliance if customer activity includes restricted markets.
```

### Ownership Change

Recommended action:

```text
Request updated corporate structure and beneficial ownership information before the next review.
```

### New Subsidiary / Jurisdiction

Recommended action:

```text
Request customer confirmation and update KYC jurisdiction and entity structure fields.
```

### Digital Asset / Treasury Activity

Recommended action:

```text
Review custody, trading, and lending suitability; assess digital-asset risk impact.
```

### Commercial Opportunity

Recommended action:

```text
Add to RM call brief for custody, payments, FX, lending, or treasury discussion.
```

## Demo Alert Targets

Generate at least:

- Polymarket: 2 risk alerts.
- Robinhood: 2 ownership/jurisdiction alerts.
- GameStop: 2 digital-asset/treasury alerts.
- Kraken: 1 ownership or product alert.
- Circle: 1 commercial opportunity alert.

More alerts are fine, but avoid noisy duplicates.

## Alert Status

Initial alerts should use:

```text
new
```

Teammate 4 can later support:

- `acknowledged`
- `dismissed`
- `escalated`
- `added_to_call_brief`
