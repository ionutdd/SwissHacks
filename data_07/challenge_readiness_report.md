# Challenge Readiness Report

- Generated at: 2026-06-20T09:28:14Z
- Internal activity baselines: 6
- Synthetic transactions: 24
- Internal monitoring signals: 7
- Public + internal fused alerts: 14
- Entity-resolution reviews: 5
- Evaluation cases: 12
- Expanded Layer 2 KYC profiles: 1
- Layer 2 signal playbook items: 10
- Estimated AI cost for this run: USD 0.00

## What Is Now Covered

- Layer 1 public intelligence remains in `data_02`, `data_03`, and `data_06`.
- Layer 2 simulated bank intelligence now lives in `data_07`.
- Alphabet now has an expanded simulated KYC profile with expected business model, transaction volumes, regions, thresholds, and RM outcomes.
- The bank-side playbook maps each challenge signal to an expected flag, detection logic, and recommended action.
- Transaction anomalies, new counterparty regions, screening review triggers, and linked-entity flows are represented.
- Public alerts can be fused with synthetic internal monitoring signals.
- Entity-resolution review includes accepted, review-required, and rejected-too-weak examples.
- Cost trace shows the current demo is rule-first and does not invoke LLM reasoning by default.

## Internal Signal Mix

- activity_profile_mismatch: 1
- linked_entity_flow: 1
- new_counterparty_region: 2
- screening_review_required: 2
- transaction_volume_spike: 1

## Expanded Alphabet KYC Case

- Signal playbook items mapped to Alphabet as observed or partially observed: 3
- The demo uses public AI infrastructure evidence to narrow the RM question, then Layer 2 synthetic transactions to decide what should be checked internally.
- Outcome: update the activity narrative and monitoring thresholds only after RM/client confirmation.

## Entity Resolution Outcomes

- accepted_for_demo_registry_context: 1
- rejected_too_weak: 1
- review_required_high_confidence: 2
- review_required_medium_confidence: 1

## Evaluation Set

- Positive or should-alert cases: 9
- Suppression / should-not-alert cases: 3

## Demo Talking Points

1. SignalWatch does not only scrape public news; it can combine public intelligence with internal-bank activity context.
2. The current pipeline is cost-efficient because discovery, extraction, filtering, and internal monitoring are deterministic by default.
3. High-risk outputs remain human-in-the-loop and should not be treated as final legal, AML, or sanctions determinations.
4. The system keeps suppressed, stale, and weak-match cases for audit instead of silently deleting them.

## Remaining Honest Gaps

- Review actions are still browser-local in the dashboard; production needs server-side audit persistence.
- Sanctions and registry connectors are represented through specs and candidate examples, not full live-provider automation.
- Simulated transactions are synthetic and should never be represented as AMINA production data.
- RBAC is specified but not enforced by a backend API in this static prototype.
