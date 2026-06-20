# Baseline Schema Spec

## Purpose

The baseline is the old KYC snapshot. It represents what AMINA knew at the last review date.

Teammate 3 will compare new extracted facts against this baseline. Teammate 4 will show the before/after drift in the UI.

## Output File

Recommended path:

```text
data/baseline_snapshots.json
```

The file should contain an array of baseline objects.

## Required Schema

```json
[
  {
    "customer_id": "demo-001",
    "legal_name": "Example Web3 AG",
    "aliases": ["Example Web3"],
    "entity_type": "private_company",
    "domicile": "Switzerland",
    "business_area": ["web3 infrastructure", "software"],
    "risk_rating": "medium",
    "known_jurisdictions": ["Switzerland", "Germany"],
    "known_products": ["corporate account", "crypto custody"],
    "directors": ["Jane Founder"],
    "executives": ["Jane Founder"],
    "investors": ["Clean Capital Fund I"],
    "subsidiaries": [],
    "websites": ["https://example.com"],
    "social_handles": {
      "x": ["@exampleweb3"],
      "linkedin": ["example-web3"]
    },
    "known_wallets": [],
    "last_reviewed_at": "2026-01-15",
    "demo_story": "Customer expanded into a new jurisdiction after last KYC review.",
    "expected_drift_types": ["new_jurisdiction", "commercial_expansion"],
    "suggested_sources_to_check": [
      "company newsroom",
      "careers page",
      "company registry"
    ],
    "amina_relevance": [
      "jurisdiction risk review",
      "FX and corporate banking opportunity"
    ],
    "notes": "Synthetic baseline for hackathon demo."
  }
]
```

## Field Requirements

### `customer_id`

Stable ID used across all fixtures.

Format:

```text
demo-001
demo-002
demo-003
```

### `legal_name`

Official or public name of the entity.

### `aliases`

Common names, abbreviations, old names, or product names that teammate 2 should search.

### `entity_type`

Allowed values:

- `private_company`
- `public_company`
- `foundation`
- `protocol`
- `fund`
- `individual`
- `synthetic`

### `domicile`

Known legal domicile at the baseline date.

### `business_area`

Short list of baseline activities.

Examples:

- `web3 infrastructure`
- `crypto exchange`
- `payments`
- `asset management`
- `software`
- `market maker`

### `risk_rating`

Allowed values:

- `low`
- `medium`
- `high`

Use `medium` if unsure.

### `known_jurisdictions`

Jurisdictions known at the baseline date.

### `known_products`

AMINA products the customer already uses or plausibly uses in the synthetic baseline.

Examples:

- `corporate account`
- `crypto custody`
- `trading`
- `FX`
- `lending`
- `staking`
- `deposits`
- `investments`

### `directors`, `executives`, `investors`, `subsidiaries`

Only include public or synthetic demo-safe information.

### `websites` And `social_handles`

Useful for teammate 2 source collection.

### `known_wallets`

Only include wallet addresses if they are publicly attributed or synthetic. Leave empty if unsure.

### `last_reviewed_at`

Date of the fake KYC snapshot.

Choose a date before the public event teammate 2 will collect.

### `demo_story`

One sentence explaining the expected drift.

Example:

```text
Customer raised a major funding round after the last review, creating treasury and custody opportunities.
```

### `expected_drift_types`

Allowed examples:

- `new_jurisdiction`
- `new_subsidiary`
- `ownership_change`
- `new_investor`
- `business_activity_change`
- `adverse_media`
- `funding_round`
- `hiring_expansion`
- `digital_asset_activity`
- `sanctions_or_watchlist`
- `commercial_expansion`

### `suggested_sources_to_check`

Give teammate 2 a starting point.

### `amina_relevance`

Map the story to AMINA risk or product needs.

## Quality Rules

- Baselines must be plausible.
- Baselines must not include private information.
- Baselines must create visible drift when compared with current evidence.
- Every baseline should be understandable without external context.
- Avoid jokes, placeholders, or vague demo stories.

