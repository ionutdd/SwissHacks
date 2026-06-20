# Fact Extraction Spec

## Purpose

Facts are normalized claims extracted from source documents. They are the bridge between raw evidence and alerts.

Every fact must be supported by one document and one evidence excerpt.

## Input

Use `data_02/documents.json`.

Each document already includes:

- `document_id`
- `customer_id`
- `source_quality`
- `source_type`
- `title`
- `published_at`
- `raw_text`
- `evidence_excerpt`
- `expected_signal_types`
- `baseline_fields_targeted`

## Output

Write:

```text
data_03/facts.json
```

## Fact Types

Support these fact types first:

- `ownership_change`
- `new_subsidiary`
- `new_jurisdiction`
- `business_activity_change`
- `digital_asset_activity`
- `treasury_policy_change`
- `regulatory_scrutiny`
- `jurisdiction_restriction`
- `new_product`
- `public_listing`
- `commercial_opportunity`
- `risk_rating_review`

## Required Fact Fields

```json
{
  "fact_id": "fact-001",
  "customer_id": "demo-001",
  "document_id": "doc-001",
  "fact_type": "ownership_change",
  "subject": "Robinhood Markets, Inc.",
  "object": "Bitstamp Ltd.",
  "value": "Robinhood closed its acquisition of Bitstamp Ltd.",
  "jurisdiction": null,
  "effective_date": "2025-06-02",
  "baseline_fields_targeted": ["subsidiaries", "business_area"],
  "evidence_excerpt": "Robinhood Markets, Inc. has closed its acquisition of Bitstamp Ltd.",
  "source_quality": "A",
  "extraction_method": "rule",
  "extraction_confidence": 0.92
}
```

## Extraction Rules

### Ownership Change

Trigger terms:

- `acquisition`
- `acquire`
- `has closed its acquisition`
- `entered into an agreement to acquire`

Extract:

- acquiring entity if available.
- acquired entity.
- transaction description.
- effective or publication date.

### New Subsidiary Or Legal Entity

Trigger terms:

- `legal entities`
- `Ltd.`
- `Inc.`
- `S.A.`
- `Pte Ltd`
- `subsidiary`

Extract:

- legal entity name.
- jurisdiction if stated.
- licensing or regulator if stated.

### New Jurisdiction

Trigger terms:

- country names.
- `EU`, `UK`, `US`, `Asia`, `Singapore`, `Luxembourg`, `Bermuda`, `Spain`.
- `licensed`, `authorized`, `registered`.

Extract:

- jurisdiction.
- context: office, license, restriction, eligible clients, regulator.

### Digital Asset Activity

Trigger terms:

- `Bitcoin`
- `USDC`
- `EURC`
- `stablecoin`
- `tokenized`
- `xStocks`
- `digital assets`
- `crypto`

Extract:

- asset or product.
- activity type: purchase, custody, payments, trading, tokenized equities, treasury reserve.

### Regulatory Scrutiny

Trigger terms:

- `CFTC`
- `order`
- `penalty`
- `investigation`
- `blocked access`
- `license`
- `licence`
- `sancionador`

Extract:

- regulator or authority.
- allegation/restriction.
- jurisdiction.
- penalty or status if available.

### Product / Commercial Opportunity

Trigger terms:

- `Circle Payments Network`
- `Circle Mint`
- `USDC`
- `xStocks`
- `tokenized stocks`
- `institutional`
- `payments`
- `custody`
- `treasury`

Extract:

- product name.
- customer need or AMINA opportunity.
- relevant business area.

## Confidence Guidance

Start from source quality:

- A: `0.85`
- B: `0.72`
- C: `0.55`
- D: `0.35`

Adjust:

- `+0.05` if title and excerpt both mention the entity.
- `+0.05` if the fact is directly stated.
- `-0.10` if the source is secondary news.
- `-0.15` if the excerpt is ambiguous.

Clamp confidence between `0.0` and `1.0`.

## Rejection Rules

Do not create a fact if:

- No evidence excerpt supports it.
- The document only mentions the entity in navigation or unrelated boilerplate.
- The extracted value is already too vague, such as `crypto stuff`.
- The source is a failed or skipped trace rather than a document.
