# Expanded Layer 2 KYC Playbook Spec

## Goal

Show the AMINA two-layer idea with one concrete company:

- Layer 1: researched public signals.
- Layer 2: simulated internal bank intelligence.

For the demo, use Alphabet Inc. / Google as the expanded case because the current 24-hour notification feed already contains public AI infrastructure and Google TPU signals.

## Required Output Files

### `data_07/expanded_kyc_profiles.json`

Each profile should define the bank-side view as if AMINA had onboarded the client.

Required fields:

- `profile_id`
- `customer_id`
- `legal_name`
- `profile_type`
- `important_demo_notice`
- `onboarding_assumption`
- `research_sources`
- `baseline_kyc_profile`
- `layer_1_public_signal_context`
- `layer_2_internal_context`
- `layer_2_highlight_flags`
- `expected_outcome`

The profile must include:

- expected business model
- expected activity description
- expected transaction volume
- expected transaction count
- expected regions
- expected payment rails
- single-payment review threshold
- initial risk rating
- risk rationale
- RM TLDR
- recommended next step
- compliance caveat

### `data_07/layer2_signal_playbook.json`

Each playbook row should map the challenge signal to:

- `signal`
- `expected_flag`
- `recommended_action`
- `layer_2_detection_logic`
- `alphabet_demo_mapping`
- `expected_outcome`

The required playbook rows are:

| Signal | Expected Flag | Recommended Action |
| --- | --- | --- |
| Sudden spike in negative news about a corporate client | High Reputational Risk | Trigger enhanced due diligence; escalate to compliance review |
| High-value cross-border transfers inconsistent with historical behaviour | Behavioural Anomaly - Potential Money Mule | Monitor transactions; flag for AML analyst review |
| Multiple linked entities, low activity, sudden large flows | Structuring / Layering Risk | Trigger AML investigation |
| Legal entity name change | Entity Identity Change - Re-KYC Required | Trigger KYC refresh; re-evaluate risk category |
| Domain switch or significant website content change | Business Activity Change Signal | Re-analyse website content; compare vs. original onboarding data |
| Public pivot, for example SaaS startup to crypto trading | Material Business Model Change | Update risk classification; escalate for compliance review |
| Jurisdiction move or change of legal form | Structural Risk Change | Trigger enhanced due diligence; re-check beneficial ownership |
| New shareholders or beneficial owners appear | Ownership Change - KYC Drift | Full ownership verification; re-screen against sanctions/PEP lists |
| Large funding round or rapid geographic expansion | Scale Risk Change | Reassess transaction monitoring thresholds; update activity profile |
| Previously dormant company begins high transaction volume | Dormancy Break - Suspicious Activation | Trigger AML review; validate business legitimacy |

### `data_07/alphabet_layer2_case_study.md`

Human-readable case study for the pitch and RM demo.

It should show:

- simulated KYC profile
- expected business model
- expected activity and transaction thresholds
- Layer 1 signals being narrowed by Layer 2
- observed, partial, watch, and not-observed playbook statuses
- expected RM/compliance outcome
- public research sources

## Dashboard Requirement

The RM dashboard should show a Layer 2 KYC baseline panel for alerts where an expanded KYC profile exists.

For Alphabet alerts, the panel should include:

- expected business model
- expected monthly volume and transaction count
- expected regions and bank products
- current risk rating
- observed Layer 2 flags
- recommended RM action

The dashboard must make clear that internal data is simulated and requires human review.

## Acceptance Criteria

- Alphabet has one expanded simulated KYC profile.
- The full signal/action playbook exists as structured JSON.
- At least three Alphabet public alerts link to the expanded profile.
- Dashboard alert details show the Layer 2 KYC context before the evidence list.
- The case study distinguishes public source research from synthetic internal-bank activity.
- No alert makes a final AML, sanctions, or legal determination.
