# Gap Analysis Spec

## Current Strengths

The current prototype already covers important parts of the challenge:

- Public real-time intelligence from SEC, company sites, regulator pages, news, page diffs, RDAP, and direct URLs.
- Synthetic KYC baselines for demo customers.
- Evidence-backed fact extraction and alert generation.
- KYC drift comparison with before/after fields.
- Risk, ownership/control, opportunity, and mixed alert categories.
- Source links, excerpts, confidence, severity, and recommended RM actions.
- RM dashboard with alert detail, evidence, review actions, and call brief.
- 24-hour notification refresh and scheduled runs at 07:00 and 13:00.

## Biggest Missing Pieces

### 1. Simulated Internal Bank Intelligence

The challenge expects internal inputs such as KYC data, transaction screening, historical behavior, AML monitoring, risk ratings, and internal signals.

Current state:

- We have KYC baselines.
- We do not yet have simulated transaction history, expected activity bands, AML monitoring outputs, or internal alert context.

Impact:

- We can show public drift, but not the full "public plus bank context" layer AMINA asked for.

### 2. Transaction And Behavioural Anomaly Coverage

The challenge examples include:

- high-value cross-border transfers inconsistent with history
- dormant company sudden large flows
- multiple linked entities with low activity and sudden large flows
- money mule or layering patterns

Current state:

- No transaction simulator.
- No expected-volume baseline.
- No internal anomaly score.

Impact:

- We miss a major AML use-case family.

### 3. Sanctions, Registry, And Ownership Automation

Current state:

- We have some OFAC examples and RDAP/domain monitoring.
- We do not have a general OpenSanctions, EU, UN, GLEIF, Companies House, OpenCorporates, or ZEFIX connector.

Impact:

- Ownership, legal-form, beneficial-owner, and watchlist drift are mostly manual or direct-source examples.

### 4. Governance And Security Framework

Current state:

- Dashboard review actions exist, but mostly client-side.
- There is no formal RBAC, masking model, data separation model, or server-side audit trail.

Impact:

- The demo can talk about governance, but the implementation does not yet prove regulated-bank controls.

### 5. Cost Efficiency Evidence

The challenge explicitly evaluates cost efficiency and staged model usage.

Current state:

- The architecture is mostly rule-based and cheap, but we do not record cost, token usage, or model-tier decisions.

Impact:

- We cannot yet quantify cost per 1,000 monitored entities or explain when expensive reasoning is used.

### 6. Evaluation And Quality Metrics

Current state:

- We have working demo cases, but no formal labeled evaluation set.

Missing:

- true-positive cases
- false-positive cases
- stale evidence cases
- entity-name collision cases
- noisy product-page cases
- expected precision/recall or pass/fail criteria

Impact:

- Judges may like the demo, but the team has limited proof of robustness.

### 7. Production Persistence

Current state:

- Alerts and actions are local JSON/static files.
- Acknowledgements are stored in browser `localStorage`.

Impact:

- Good for the hackathon demo, weak for multi-user regulated operations.

## Judging Criteria Gap Map

### AI Intelligence Quality - 25%

Strong:

- Evidence-backed alerts.
- KYC drift comparison.
- Materiality filtering.

Missing:

- Layer 2 internal-bank context.
- Evaluation suite.
- Entity-resolution edge cases.

### Cost Efficiency - 20%

Strong:

- Rule-first pipeline.
- LLM not required for every source.

Missing:

- Cost trace.
- Token budget.
- Stage-by-stage cost estimate.

### UX And Explainability - 20%

Strong:

- RM dashboard.
- Source links.
- Before/after drift.
- TLDR notifications.

Missing:

- "Why hidden / why suppressed" dashboard view.
- Internal-bank context panel.

### Compliance And Safety - 20%

Strong:

- Human-in-the-loop actions.
- Source citations.
- No automatic legal conclusions.

Missing:

- RBAC.
- Server-side audit trail.
- Data separation and masking.
- Formal model guardrails.

### Engineering And Architecture - 15%

Strong:

- Split collectors.
- Scheduled refresh.
- Modular scripts.

Missing:

- Persistent backend.
- Job monitoring.
- Connector retry policy.
- Broader public registries and sanctions automation.
