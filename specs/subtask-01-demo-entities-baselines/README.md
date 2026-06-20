# Subtask 01: Demo Entities And Baselines

Owner: Teammate 1

Mission: choose the demo customers and create synthetic KYC baseline profiles that make KYC drift visible.

This is the most important subtask because the entire demo depends on credible entities, clean baseline assumptions, and strong drift stories.

## Files In This Folder

- [01-task-brief.md](01-task-brief.md): what teammate 1 owns and must deliver.
- [02-entity-selection-spec.md](02-entity-selection-spec.md): how to choose good demo entities.
- [03-baseline-schema-spec.md](03-baseline-schema-spec.md): required baseline fields and JSON structure.
- [04-output-checklist.md](04-output-checklist.md): final checklist before handoff to teammates 2, 3, and 4.

## Required Outputs

Teammate 1 should produce:

- `data/baseline_snapshots.json`
- `data/demo_entity_notes.md`

If there is no `data/` folder yet, create it at repo root when implementation starts.

## Handoff Contract

Teammate 1 hands off to:

- Teammate 2, who uses the selected entities to collect evidence.
- Teammate 3, who uses the baselines to compare extracted facts against known KYC.
- Teammate 4, who uses the demo stories to design the pitch flow.

## Definition Of Done

- At least 3 demo entities are selected.
- Each entity has a synthetic KYC baseline.
- Each baseline has a `last_reviewed_at` date.
- Each entity has a one-sentence drift story.
- At least one entity supports a risk demo.
- At least one entity supports an opportunity demo.
- At least one entity supports ownership/control, subsidiary, or jurisdiction drift.

