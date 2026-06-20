# Task Brief

## Goal

Pull the latest available public evidence using the existing collection scripts, regenerate facts and alerts, then show only material alerts in a new dashboard tab.

## User Need

The RM should not read every collected document or every generated alert. The system should highlight the alerts that are most likely to affect KYC, compliance triage, or an RM call, while suppressing generic or low-impact noise.

## Inputs

- `data_01/baseline_snapshots.json`
- `data_02/source_catalog.json`
- Existing collector scripts in `scripts/collect_evidence*.py`
- Existing signal extractor in `scripts/extract_signals.py`
- Business requirements in the product, signal taxonomy, ingestion, scoring, and RM workflow specs.

## Outputs

- Refreshed evidence in `data_02/documents.json`
- Refreshed facts and alerts in `data_03/`
- Filtered material alerts in `data_06/material_alerts.json`
- Suppressed/noise alerts with reasons in `data_06/noise_suppression.json`
- Dashboard tab for material alerts.

## Acceptance Criteria

- One command can run collection, extraction, and material filtering end to end.
- Each material alert preserves original evidence links, confidence, severity, changed fields, and recommended action.
- Noise is not deleted; it is recorded with suppression reasons.
- The dashboard can switch between `Material alerts` and `All alerts`.
- The material tab defaults to high-signal items suitable for RM review.

