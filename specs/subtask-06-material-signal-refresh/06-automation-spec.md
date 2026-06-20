# Automation Spec

## Goal

Run the material signal refresh automatically twice per day so the RM dashboard has a fresh last-24-hours notification view before morning and early-afternoon review windows.

## Schedule

- Run daily at `07:00`.
- Run daily at `13:00`.
- Each run uses `--lookback-hours 24`.
- Each run refreshes evidence, extracts signals, applies the materiality filter, and rewrites `data_06/` outputs.

## Windows Implementation

Use Windows Task Scheduler:

- `scripts/run_material_refresh_scheduled.ps1` is the task runner.
- `scripts/install_material_refresh_schedule.ps1` installs or updates the scheduled task.
- Runtime logs are appended to `logs/material_refresh.log`.

## Commands

Install or update the scheduled task:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_material_refresh_schedule.ps1
```

Run the same scheduled refresh manually:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_material_refresh_scheduled.ps1
```

## Notification Retention

Acknowledged notifications should disappear from the dashboard TLDR queue for that browser session/user profile through local review-action state. The underlying alert, evidence, and action history must remain available in the Customer workspace for audit.
