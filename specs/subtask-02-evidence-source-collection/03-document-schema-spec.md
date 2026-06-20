# Document Schema Spec

## Purpose

`documents.json` is the normalized evidence layer. It should be simple enough for teammate 3 to parse and rich enough for teammate 4 to show in the UI.

## Output File

Recommended path:

```text
data_02/documents.json
```

The file should contain an array of document objects.

## Required Schema

```json
[
  {
    "document_id": "doc-001",
    "customer_id": "demo-001",
    "source_type": "company_newsroom",
    "source_name": "Robinhood Newsroom",
    "source_url": "https://robinhood.com/us/en/newsroom/robinhood-completes-acquisition-of-bitstamp/",
    "source_quality": "A",
    "title": "Robinhood Completes Acquisition of Bitstamp",
    "published_at": "2025-06-02",
    "collected_at": "2026-06-19T22:00:00Z",
    "language": "en",
    "raw_text": "Short page text or relevant cleaned text...",
    "evidence_excerpt": "Robinhood has closed its acquisition of Bitstamp Ltd., a global cryptocurrency exchange.",
    "expected_signal_types": [
      "ownership_change",
      "new_subsidiary",
      "business_activity_change"
    ],
    "baseline_fields_targeted": [
      "subsidiaries",
      "known_jurisdictions",
      "business_area"
    ],
    "automation_potential": "high",
    "confidence_hint": "high",
    "limitations": null
  }
]
```

## Field Requirements

### `document_id`

Stable ID used by facts and alerts.

Format:

```text
doc-001
doc-002
doc-003
```

### `customer_id`

Must match a `customer_id` in `data_01/baseline_snapshots.json`.

### `source_type`

Use values from `02-source-collection-spec.md`.

### `source_name`

Human-readable source name.

Examples:

- `Robinhood Newsroom`
- `CFTC`
- `GameStop Investor Relations`
- `SEC EDGAR`
- `Kraken Blog`

### `source_url`

Public URL for the source.

### `source_quality`

Allowed values:

- `A`
- `B`
- `C`
- `D`

### `title`

Page title, filing title, or article headline.

### `published_at`

Use ISO date if known:

```text
2025-06-02
```

If unavailable, use `null`.

### `collected_at`

Use ISO timestamp.

```text
2026-06-19T22:00:00Z
```

### `language`

Use ISO language code.

Examples:

- `en`
- `de`
- `fr`

### `raw_text`

Cleaned text from the source page. For the hackathon, this can be a relevant excerpt block rather than the entire page.

### `evidence_excerpt`

The exact sentence or short passage that supports the drift.

### `expected_signal_types`

Machine-readable signal hints for teammate 3.

Allowed examples:

- `ownership_change`
- `new_subsidiary`
- `new_jurisdiction`
- `business_activity_change`
- `digital_asset_activity`
- `treasury_policy_change`
- `regulatory_scrutiny`
- `jurisdiction_restriction`
- `public_listing`
- `new_product`
- `commercial_opportunity`

### `baseline_fields_targeted`

Fields likely affected in the baseline.

Examples:

- `known_jurisdictions`
- `business_area`
- `known_products`
- `subsidiaries`
- `investors`
- `risk_rating`

### `automation_potential`

Allowed values:

- `high`
- `medium`
- `low`

### `confidence_hint`

Allowed values:

- `high`
- `medium`
- `low`

This is a source-collection hint, not final extraction confidence.

### `limitations`

Use `null` when no limitation is known.

Examples:

- `Paywalled; use only for corroboration.`
- `Source is secondary news, not official filing.`
- `Social post; requires corroboration.`

## Quality Rules

- Every document must support at least one expected signal type.
- Every document must target at least one baseline field.
- Every showcased alert should have at least one A or B source.
- High-risk alerts should not depend only on C or D sources.
- Do not include unsupported claims in `raw_text`.
