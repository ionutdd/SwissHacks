# Subtask 04: RM Dashboard And Demo Flow

Owner: Teammate 4

Mission: turn the generated facts and alerts into a usable Relationship Manager console that can be demoed end to end.

This workstream should not invent new signals. It should make the existing evidence-backed alerts easy to triage, explain, action, and present.

## Files In This Folder

- [01-task-brief.md](01-task-brief.md): what teammate 4 owns and must deliver.
- [02-dashboard-ui-spec.md](02-dashboard-ui-spec.md): required RM dashboard views and interaction behavior.
- [03-data-integration-spec.md](03-data-integration-spec.md): fixture loading and frontend data model.
- [04-review-actions-call-brief-spec.md](04-review-actions-call-brief-spec.md): RM action states, audit trail, and call brief generation.
- [05-output-checklist.md](05-output-checklist.md): validation checklist before demo.

## Required Inputs

Teammate 4 starts from:

- `data_01/baseline_snapshots.json`
- `data_02/documents.json`
- `data_03/facts.json`
- `data_03/alerts.json`

## Required Outputs

Teammate 4 should produce:

- `dashboard/index.html`
- `dashboard/styles.css`
- `dashboard/app.js`
- optional demo notes in `dashboard/README.md`

## Runnable Demo

Recommended command from the repo root:

```powershell
python -m http.server 8765
```

Then open:

```text
http://localhost:8765/dashboard/
```

## Definition Of Done

- Dashboard loads all demo customers.
- At least 8 generated alerts appear.
- RM can filter by category, severity, and review status.
- Opening an alert shows summary, before/after fields, evidence links, and recommended action.
- RM can acknowledge, escalate, dismiss, request customer update, or add alert to the call brief.
- Generated call brief includes risk questions, opportunities, customer questions, and evidence references.
- Demo works without editing files manually.
