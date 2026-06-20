# Materiality Filter Spec

## Freshness Gate

Before materiality scoring can put an alert into the RM notification feed, at least one evidence item must have `published_at` inside the configured lookback window.

Default:

```text
lookback_hours = 24
freshness_policy = published_at_only
```

Suppress, but do not delete, alerts when evidence is older than the window or undated. Those alerts remain available in the full customer workspace and `noise_suppression.json`.

## What Counts As Material

Keep alerts that meet one or more of these conditions:

- Severity is `critical` or `high` and confidence is at least `0.65`.
- Category is `risk` or `ownership_control` and confidence is at least `0.72`.
- Signal changes `risk_rating`, `known_jurisdictions`, `subsidiaries`, `websites`, or `business_area` with high source quality.
- Signal type is one of:
  - `regulatory_scrutiny`
  - `jurisdiction_restriction`
  - `risk_rating_review`
  - `ownership_change`
  - `new_subsidiary`
  - `new_jurisdiction`
  - `domain_registration`
  - `treasury_policy_change`
  - `digital_asset_activity`
  - `business_activity_change`
- The materiality score reaches the threshold defined below.

## Materiality Score

Score should combine:

- Severity impact.
- Category impact.
- Confidence.
- Source quality.
- Changed KYC fields.
- Signal type.
- Freshness.
- Sensitive keywords in title, summary, or evidence.

Recommended threshold:

```text
material_score >= 100
```

## Noise Suppression

Suppress, but do not delete, alerts when:

- No evidence was published inside the configured lookback window.
- Evidence is undated and the strict `published_at_only` policy is active.
- Confidence is below `0.70`, unless severity is `high` or `critical`.
- Alert is opportunity-only and a higher-priority risk alert exists for the same customer.
- Alert only repeats a product/opportunity already covered by a stronger risk or KYC drift alert.
- Alert has no source URL.
- Alert has only weak, undated, or generic product-page evidence and does not change KYC risk fields.

## Output Fields

Each material alert should add:

- `material_rank`
- `material_score`
- `material_reasons`
- `freshness_days`
- `newest_published_at`
- `inside_refresh_window`
- `primary_source_url`
- `primary_source_name`
- `review_lane`

Each suppressed alert should add:

- `suppression_reasons`
- `material_score`
