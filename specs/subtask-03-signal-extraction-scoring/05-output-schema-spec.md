# Output Schema Spec

## Output Folder

Use:

```text
data_03/
```

## `facts.json`

`facts.json` should be an array of fact objects.

Required schema:

```json
[
  {
    "fact_id": "fact-001",
    "customer_id": "demo-001",
    "document_id": "doc-013",
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
]
```

## `alerts.json`

`alerts.json` should be an array of alert objects.

Required schema:

```json
[
  {
    "alert_id": "alert-001",
    "customer_id": "demo-001",
    "category": "ownership_control",
    "signal_type": "ownership_change",
    "title": "Robinhood acquired Bitstamp after last KYC review",
    "summary": "Official evidence indicates Robinhood closed the Bitstamp acquisition after the baseline review date.",
    "changed_fields": ["subsidiaries", "business_area"],
    "baseline_value": {
      "subsidiaries": ["Robinhood Crypto, LLC", "Robinhood Europe, UAB"]
    },
    "new_value": {
      "subsidiaries": ["Bitstamp Ltd."]
    },
    "severity": "high",
    "confidence": 0.91,
    "recommended_action": "Request updated corporate structure and beneficial ownership information before the next review.",
    "evidence_document_ids": ["doc-013"],
    "fact_ids": ["fact-001"],
    "status": "new",
    "created_at": "2026-06-20T00:00:00Z"
  }
]
```

## Field Requirements

### IDs

- `fact_id`: `fact-001`, `fact-002`, ...
- `alert_id`: `alert-001`, `alert-002`, ...

IDs should be stable within a run.

### `signal_type`

Use signal/fact types from the task specs:

- `ownership_change`
- `new_subsidiary`
- `new_jurisdiction`
- `business_activity_change`
- `digital_asset_activity`
- `treasury_policy_change`
- `regulatory_scrutiny`
- `jurisdiction_restriction`
- `new_product`
- `commercial_opportunity`
- `risk_rating_review`

### `category`

Allowed values:

- `risk`
- `opportunity`
- `ownership_control`
- `mixed`

### `severity`

Allowed values:

- `critical`
- `high`
- `medium`
- `low`

### `confidence`

Use numeric float:

```json
0.87
```

Do not use strings like `"high"`.

### Evidence Links

Every alert must include:

- `evidence_document_ids`
- `fact_ids`

Every `fact_id` must exist in `facts.json`.

Every `document_id` must exist in `data_02/documents.json`.

## Optional Run Report

Recommended:

```text
data_03/signal_run_report.md
```

Include:

- total documents processed.
- total facts generated.
- total alerts generated.
- suppressed duplicates.
- low-confidence facts skipped.
- top 3 demo alerts.
