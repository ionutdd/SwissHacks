# Task Brief

## Goal

Close the realistic gaps between the current SignalWatch prototype and the AMINA challenge brief:

https://github.com/SwissHacks-2026/Amina-BANK

The challenge asks for a two-layer system:

- Layer 1: public real-time intelligence.
- Layer 2: simulated internal bank intelligence.

Our current prototype is strongest on Layer 1. Subtask 07 should make the Layer 2 story, governance story, cost story, and evaluation story credible enough for judges.

## Why This Matters

The current build can impress on evidence-backed public alerts, but AMINA's brief explicitly asks for:

- internal KYC and AML context
- transaction-monitoring style anomalies
- security and governance framework
- explainability and guardrails
- cost-efficient AI pipeline
- auditability and human approval workflow

Without these pieces, the demo risks looking like a good public-news monitor instead of a regulated-bank risk intelligence system.

## Deliverables

- A simulated internal-bank dataset for selected demo customers.
- A mapping from public signals to internal KYC/AML context.
- Specs for sanctions, registry, and ownership-source hardening.
- Specs for governance, RBAC, audit logs, model guardrails, and cost tracking.
- A challenge-readiness checklist tied to AMINA judging criteria.

## Priority

P0:

- Simulated internal bank signals.
- Cost trace and staged pipeline explanation.
- Governance and audit story.
- Evaluation cases for the demo alerts.

P1:

- OpenSanctions, GLEIF, Companies House, and ZEFIX connector specs.
- Entity-resolution review workflow.
- Backend persistence for review actions.

P2:

- Full RBAC implementation.
- Real model-cost telemetry.
- Production monitoring and alerting.

## Non-Goals

- Do not ingest real AMINA data.
- Do not make automated compliance decisions.
- Do not claim sanctions, PEP, or AML conclusions as final legal determinations.
- Do not build paid-provider integrations unless credentials are already available.
