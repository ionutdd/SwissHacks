# Subtask 06: Material Signal Refresh

## Purpose

Create an end-to-end refresh layer that runs the existing evidence and signal pipeline, then filters the output down to the alerts an RM or compliance reviewer should actually look at first.

## Specs

- `01-task-brief.md`: scope, owner outcome, and acceptance criteria.
- `02-refresh-algorithm-spec.md`: how the refresh reuses existing collectors and extractors.
- `03-materiality-filter-spec.md`: rules for highlighting important signals and suppressing noise.
- `04-dashboard-tab-spec.md`: dashboard changes for the TLDR notifications tab.
- `05-output-checklist.md`: verification checklist for the implemented output.
- `06-automation-spec.md`: Windows Task Scheduler automation for 07:00 and 13:00 refreshes.

## Output Targets

- `data_06/material_alerts.json`
- `data_06/noise_suppression.json`
- `data_06/refresh_summary.json`
- `data_06/material_refresh_report.md`
- `logs/material_refresh.log`
