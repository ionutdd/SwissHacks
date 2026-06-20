# Layer 2 Internal Bank Intelligence Spec

## Goal

Add a simulated internal-bank layer that contextualizes public intelligence with expected customer behavior, transaction patterns, AML screening signals, and KYC review data.

This should remain synthetic. No real AMINA customer data should be used.

## Required Data Files

### `data_07/customer_activity_baselines.json`

Defines the bank's expected view of each customer.

Required fields:

- `customer_id`
- `expected_monthly_volume_chf`
- `expected_transaction_count_monthly`
- `expected_counterparty_regions`
- `expected_products`
- `expected_activity_description`
- `allowed_risk_band`
- `last_kyc_refresh_at`
- `transaction_monitoring_thresholds`

Example:

```json
{
  "customer_id": "demo-009",
  "expected_monthly_volume_chf": 15000000,
  "expected_transaction_count_monthly": 80,
  "expected_counterparty_regions": ["United States", "European Union", "United Kingdom"],
  "expected_products": ["corporate banking", "FX", "treasury"],
  "expected_activity_description": "Large-cap technology treasury and operating flows.",
  "allowed_risk_band": "low_to_medium",
  "last_kyc_refresh_at": "2026-06-01",
  "transaction_monitoring_thresholds": {
    "single_payment_chf": 5000000,
    "new_region_monthly_count": 3,
    "volume_spike_multiplier": 2.5
  }
}
```

### `data_07/simulated_transactions.json`

Synthetic transaction events for anomaly detection.

Required fields:

- `transaction_id`
- `customer_id`
- `booked_at`
- `amount_chf`
- `direction`
- `counterparty_name`
- `counterparty_country`
- `payment_rail`
- `purpose`
- `related_public_signal_ids`

Scenario examples:

- Dormant or low-volume entity suddenly sends large cross-border transfers.
- Customer with no prior crypto treasury activity sends funds to a digital-asset custodian.
- Customer with new jurisdiction news starts transacting with counterparties in that jurisdiction.
- Multiple linked entities move funds through common counterparties.

### `data_07/internal_monitoring_signals.json`

Aggregated internal monitoring outputs.

Required fields:

- `internal_signal_id`
- `customer_id`
- `signal_type`
- `severity`
- `confidence`
- `summary`
- `supporting_transaction_ids`
- `baseline_comparison`
- `recommended_action`
- `created_at`

Supported signal types:

- `transaction_volume_spike`
- `new_counterparty_region`
- `dormancy_break`
- `linked_entity_flow`
- `activity_profile_mismatch`
- `screening_review_required`

### `data_07/public_internal_fused_alerts.json`

Links public alerts from `data_03` or `data_06` to internal monitoring signals.

Required fields:

- `fused_alert_id`
- `alert_id`
- `customer_id`
- `fusion_type`
- `public_signal_type`
- `public_title`
- `internal_signal_ids`
- `internal_signal_summaries`
- `fusion_rationale`
- `fused_score`
- `recommended_workflow`

## Public Plus Internal Fusion

The alert engine should combine public and internal signals when both point to the same customer drift.

Examples:

- Public signal: Google AI infrastructure expansion.
- Internal signal: higher treasury or FX activity.
- Output: commercial opportunity with stronger confidence.

- Public signal: sanctioned-country exposure.
- Internal signal: payment to new high-risk region.
- Output: compliance escalation.

- Public signal: new country-code domain.
- Internal signal: new counterparties in that country.
- Output: KYC refresh and jurisdiction review.

## Acceptance Criteria

- At least 3 demo customers have internal activity baselines.
- At least 20 synthetic transactions exist.
- At least 5 internal monitoring signals are generated or mocked.
- At least 2 final alerts combine public evidence with internal-bank context.
- No internal signal is treated as final AML or sanctions determination.
