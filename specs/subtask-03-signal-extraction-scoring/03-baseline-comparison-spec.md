# Baseline Comparison Spec

## Purpose

Compare extracted facts against `data_01/baseline_snapshots.json` to decide whether the fact is new, already known, or not material.

## Input

- `data_01/baseline_snapshots.json`
- `data_03/facts.json`

## Comparison Result

Each fact should produce an internal comparison result:

```json
{
  "fact_id": "fact-001",
  "customer_id": "demo-001",
  "is_new_information": true,
  "changed_fields": ["subsidiaries"],
  "baseline_value": ["Robinhood Crypto, LLC"],
  "new_value": ["Robinhood Crypto, LLC", "Bitstamp Ltd."],
  "materiality": "high",
  "comparison_reason": "Bitstamp Ltd. is not listed in the baseline subsidiaries."
}
```

This comparison result can be embedded into alerts; it does not need a separate file unless useful for debugging.

## Field Mapping

Map fact types to baseline fields:

| Fact type | Baseline fields |
| --- | --- |
| `ownership_change` | `subsidiaries`, `business_area`, `risk_rating` |
| `new_subsidiary` | `subsidiaries`, `known_jurisdictions`, `risk_rating` |
| `new_jurisdiction` | `known_jurisdictions`, `risk_rating` |
| `business_activity_change` | `business_area`, `known_products`, `risk_rating` |
| `digital_asset_activity` | `business_area`, `known_products`, `risk_rating` |
| `treasury_policy_change` | `business_area`, `known_products`, `risk_rating` |
| `regulatory_scrutiny` | `risk_rating`, `business_area` |
| `jurisdiction_restriction` | `known_jurisdictions`, `risk_rating` |
| `new_product` | `known_products`, `business_area` |
| `commercial_opportunity` | `known_products`, `business_area` |
| `public_listing` | `entity_type`, `known_products` |

## Comparison Rules

### Array Fields

For fields like:

- `known_jurisdictions`
- `known_products`
- `subsidiaries`
- `investors`
- `directors`
- `executives`

Normalize values:

- lowercase.
- strip punctuation.
- remove corporate suffix noise only for matching, not display.
- compare aliases where obvious.

Flag drift when extracted value is not already present.

### Scalar Fields

For fields like:

- `risk_rating`
- `entity_type`
- `domicile`

Do not overwrite automatically.

Instead, create a review alert:

- `risk_rating_review`
- `entity_type_review`
- `domicile_review`

### Date Logic

Use `baseline.last_reviewed_at`.

If `fact.effective_date` or source `published_at` is before the baseline review date:

- Use it as context.
- Do not create a fresh drift alert unless it contradicts the baseline materially.

If date is missing:

- Allow alert only if evidence is material and source quality is A or B.
- Reduce confidence slightly.

## Materiality

Use:

- `high`: regulatory/enforcement, acquisition, new crypto treasury, high-risk jurisdiction.
- `medium`: new product, new legal entity, jurisdiction expansion, product risk disclosure.
- `low`: weak opportunity, product description with no clear newness, undated page.

## Suppression

Suppress duplicate comparisons where:

- same customer.
- same fact type.
- same normalized object.
- same changed field.
- same source event.

Keep the highest-confidence evidence and attach additional documents as corroboration where useful.
