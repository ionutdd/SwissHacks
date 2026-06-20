# Subtask 03: Signal Extraction And Scoring

Owner: Teammate 3

Mission: turn normalized evidence documents into structured facts, compare those facts against the baseline KYC snapshots, and generate explainable alerts for RMs and compliance.

This is the signal engine. It should be deterministic enough for a stable hackathon demo and evidence-backed enough that every alert can be defended.

## Files In This Folder

- [01-task-brief.md](01-task-brief.md): what teammate 3 owns and must deliver.
- [02-fact-extraction-spec.md](02-fact-extraction-spec.md): how to extract structured facts from documents.
- [03-baseline-comparison-spec.md](03-baseline-comparison-spec.md): how to compare facts against KYC baselines.
- [04-scoring-alert-spec.md](04-scoring-alert-spec.md): severity, confidence, category, and alert rules.
- [05-output-schema-spec.md](05-output-schema-spec.md): required `facts.json` and `alerts.json` schemas.
- [06-output-checklist.md](06-output-checklist.md): validation checklist before handoff to teammate 4.

## Required Inputs

Teammate 3 starts from:

- `data_01/baseline_snapshots.json`
- `data_02/documents.json`
- `specs/02-signal-taxonomy-spec.md`

## Required Outputs

Teammate 3 should produce:

- `data_03/facts.json`
- `data_03/alerts.json`
- optional: `data_03/signal_run_report.md`
- optional: `scripts/extract_signals.py`

## Runnable Algorithm

Recommended command:

```powershell
python scripts\extract_signals.py --baselines data_01\baseline_snapshots.json --documents data_02\documents.json --output-dir data_03
```

The extractor should parse documents, produce facts, compare facts against baseline fields, score material changes, and write alert objects.

## Definition Of Done

- At least 8 alerts are generated.
- At least 3 risk alerts exist.
- At least 3 opportunity alerts exist.
- At least 1 ownership/control alert exists.
- Every fact cites exactly one `document_id`.
- Every alert cites at least one `fact_id` and one `document_id`.
- Every alert has severity, confidence, category, changed fields, and recommended action.
- No alert exists without evidence.
