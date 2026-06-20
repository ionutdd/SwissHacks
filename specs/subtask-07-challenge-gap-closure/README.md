# Subtask 07: Challenge Gap Closure

## Purpose

Turn the AMINA challenge requirements into a realistic gap-closure plan for the current SignalWatch prototype.

The prototype is already strong on public evidence collection, KYC drift alerts, source links, RM dashboarding, 24-hour notifications, and scheduled refreshes. The remaining gaps are mostly around simulated internal bank intelligence, governance, cost tracking, evaluation, and broader source coverage.

## Specs

- `01-task-brief.md`: scope, owner outcome, and what this subtask should deliver.
- `02-gap-analysis-spec.md`: realistic gap analysis against the challenge brief and judging criteria.
- `03-layer-2-internal-bank-intelligence-spec.md`: simulated KYC, AML, transaction, and monitoring inputs.
- `04-source-coverage-hardening-spec.md`: sanctions, registries, adverse media, and source reliability gaps.
- `05-governance-cost-evaluation-spec.md`: guardrails, auditability, cost tracking, and evaluation.
- `06-output-checklist.md`: acceptance checklist for challenge-readiness.

## Output Targets

- `data_07/customer_activity_baselines.json`
- `data_07/simulated_transactions.json`
- `data_07/internal_monitoring_signals.json`
- `data_07/entity_resolution_review.json`
- `data_07/cost_trace.json`
- `data_07/evaluation_cases.json`
- `data_07/challenge_readiness_report.md`

## Definition Of Done

- The demo can show both public intelligence and simulated internal-bank context.
- Every high-risk alert has source evidence, baseline drift, and a recommended human workflow.
- The team can explain security, guardrails, auditability, and cost efficiency in the pitch.
- The system has a small evaluation set showing true positives, false positives, and known limitations.
