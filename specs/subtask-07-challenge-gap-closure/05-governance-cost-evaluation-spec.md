# Governance, Cost, And Evaluation Spec

## Goal

Make the prototype credible for a regulated bank by documenting and implementing the minimum governance, safety, cost, and evaluation controls expected by the AMINA challenge.

## Security And Governance Requirements

### Data Separation

Separate:

- public source documents
- synthetic KYC baselines
- simulated internal-bank activity
- generated facts and alerts
- RM review actions

No public-source connector should write into internal-bank baseline files.

### Role-Based Access Model

Demo roles:

- `relationship_manager`: can view assigned customers, acknowledge, add notes, create call brief.
- `compliance_analyst`: can view all risk alerts, escalate, request KYC refresh, review suppressed items.
- `admin`: can manage source catalog and scheduled jobs.

P0 implementation can be documented or mocked. P1 implementation should enforce it in an API layer.

### Audit Trail

Every review action should store:

- action ID
- alert ID
- customer ID
- actor
- timestamp
- action type
- note
- previous status
- new status

Important gap:

- Current dashboard uses browser `localStorage`; this is acceptable for demo UX but not a regulated audit trail.

Target:

- Persist review actions to `data_07/review_actions_audit.json` for the demo or to a backend API for production.

### Model Guardrails

Rules:

- No alert without source evidence.
- No final legal determination.
- Low-confidence or ambiguous matches must route to review.
- LLM reasoning, if used, must cite source excerpts.
- Suppressed alerts must be retained with reasons.
- Human approval required before KYC baseline updates.

## Cost Efficiency Requirements

Track cost by stage:

1. Cheap source filtering.
2. Deterministic extraction.
3. Small-model or embedding reranking if used.
4. LLM reasoning only for escalated or ambiguous cases.

Target file:

`data_07/cost_trace.json`

Required fields:

- `run_id`
- `stage`
- `customer_count`
- `document_count`
- `model_used`
- `estimated_tokens_in`
- `estimated_tokens_out`
- `estimated_cost_usd`
- `notes`

Pitch metric:

- estimated cost per 1,000 monitored customers per day
- estimated cost per 1,000 generated alerts
- percentage of documents handled without LLM reasoning

## Evaluation Requirements

Target file:

`data_07/evaluation_cases.json`

Each case should include:

- `case_id`
- `customer_id`
- `expected_signal_type`
- `expected_category`
- `expected_outcome`
- `evidence_document_ids`
- `should_alert`
- `reason`

Minimum evaluation set:

- 5 true positive cases.
- 3 false positive or suppression cases.
- 2 stale evidence cases.
- 2 ambiguous entity-resolution cases.
- 1 internal-plus-public fusion case.

Metrics:

- alert precision on labeled cases
- stale-evidence suppression rate
- source-link coverage
- percentage of alerts with recommended action
- average time for RM to understand top alert in demo rehearsal

## Acceptance Criteria

- Cost trace exists for at least one end-to-end run.
- Evaluation cases exist and map to current demo alerts.
- Governance narrative is visible in specs and pitch.
- The team can explain why the system is assistive, not autonomous.
