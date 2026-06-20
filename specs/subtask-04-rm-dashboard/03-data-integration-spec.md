# Data Integration Spec

## Purpose

Connect the RM dashboard to the generated local fixture files without requiring a backend.

## Inputs

Load these files from the repo root:

```text
data_01/baseline_snapshots.json
data_02/documents.json
data_03/facts.json
data_03/alerts.json
```

## Frontend Data Model

Build derived maps:

- `customersById`
- `documentsById`
- `factsById`
- `alertsByCustomerId`
- `reviewActionsByAlertId`

## Customer Aggregate

For each customer, compute:

```json
{
  "customer_id": "demo-001",
  "legal_name": "Robinhood Markets, Inc.",
  "risk_rating": "medium",
  "last_reviewed_at": "2025-05-15",
  "alert_count": 5,
  "risk_alert_count": 0,
  "opportunity_alert_count": 0,
  "ownership_alert_count": 2,
  "highest_severity": "high",
  "last_scan_at": "2026-06-20T00:00:03Z"
}
```

## Alert Enrichment

Every alert displayed in the UI should include:

- Baseline customer details.
- Current review status.
- Evidence document details.
- Fact details.
- UI sort rank.

Do not mutate `data_03/alerts.json`. Keep user/demo actions in local storage.

## Local Storage Contract

Store review actions under:

```text
signalwatch.reviewActions.v1
```

Action object:

```json
{
  "id": "action-001",
  "alert_id": "alert-001",
  "customer_id": "demo-001",
  "action": "escalated",
  "note": "Escalated during demo review.",
  "created_by": "demo-rm",
  "created_at": "2026-06-20T00:00:00Z"
}
```

Derived alert status should use the latest local action when present, otherwise use `alert.status`.

## Failure States

Handle:

- Missing fixture file.
- Empty alert list.
- Invalid JSON.
- Alert references a missing document or fact.

The UI should show a clear operational error message and keep the shell visible.
