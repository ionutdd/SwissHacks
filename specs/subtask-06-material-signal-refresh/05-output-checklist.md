# Output Checklist

## Specs

- [x] `specs/subtask-06-material-signal-refresh/` exists.
- [x] Refresh algorithm is documented.
- [x] Materiality and suppression rules are documented.
- [x] Dashboard tab behavior is documented.
- [x] Strict 24-hour notification behavior is documented.
- [x] Twice-daily automation behavior is documented.

## Implementation

- [x] One script runs collection, extraction, and material filtering.
- [x] `data_06/material_alerts.json` exists and is filtered to the current refresh window.
- [x] `data_06/noise_suppression.json` exists and explains suppressed alerts.
- [x] `data_06/refresh_summary.json` exists.
- [x] `data_06/material_refresh_report.md` exists.
- [x] Dashboard loads the material alert data.
- [x] Dashboard defaults to the TLDR Notifications tab.
- [x] Customer workspace keeps the full alert queue.
- [x] Scheduled refresh runner exists.
- [x] Windows scheduled-task installer exists.
- [x] Acknowledged notifications are hidden from the TLDR queue without deleting audit data.

## Verification

- [x] Python syntax checks pass.
- [x] Dashboard JavaScript syntax check passes.
- [x] JSON outputs parse.
- [x] Served dashboard data includes current-window material alerts or a clear empty state.
- [x] Dashboard source links still open the underlying evidence.
- [x] Scheduled runner executes successfully.
- [x] Windows scheduled task is installed for 07:00 and 13:00.
