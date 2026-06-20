# Dashboard Notification Tab Spec

## Goal

Add a top-bar TLDR notification tab that lets the RM see same-day material signals first, while keeping the full customer workspace and historical alert queue accessible.

## Required UI

- Add a primary navbar switcher:
  - `Notifications`
  - `Customer workspace`
- Default to `Notifications`.
- Notifications should be portfolio-wide, not tied to the selected customer.
- The customer workspace should keep the per-customer portfolio, filters, alert queue, alert detail, and RM brief.
- Notification cards should show:
  - Customer name.
  - Alert title and summary.
  - Material score.
  - Review lane.
  - Confidence.
  - Published date.
  - Source link.
- Clicking a notification should open the related customer and alert in the customer workspace.
- Alert detail should still show:
  - Materiality rationale.
  - Before/after KYC fields.
  - Evidence links.
  - Existing RM action buttons.

## Data Contract

Dashboard should load:

- `../data_03/alerts.json`
- `../data_06/material_alerts.json`
- `../data_06/refresh_summary.json`

If `material_alerts.json` is unavailable or empty, the notification tab should show an empty-state message rather than failing.

## Acceptance Criteria

- RM can switch between Notifications and Customer workspace.
- Notification tab only shows alerts produced by the current refresh window.
- Empty notification days clearly state that no material signals were published in the last 24 hours.
- Source links remain clickable in both views.
- Customer workspace remains available for full historical review and RM call brief creation.
