# Output Checklist

Use this before the final demo.

## Required Files

- [ ] `dashboard/index.html`
- [ ] `dashboard/styles.css`
- [ ] `dashboard/app.js`

## Data Loading

- [ ] Loads `data_01/baseline_snapshots.json`.
- [ ] Loads `data_02/documents.json`.
- [ ] Loads `data_03/facts.json`.
- [ ] Loads `data_03/alerts.json`.
- [ ] Handles missing files gracefully.
- [ ] Does not modify generated fixture JSON.

## Dashboard

- [ ] Shows all demo customers.
- [ ] Shows at least 8 generated alerts.
- [ ] Shows portfolio metrics.
- [ ] Supports search.
- [ ] Supports category filter.
- [ ] Supports severity filter.
- [ ] Supports status filter.
- [ ] Selecting a customer updates the alert queue.
- [ ] Selecting an alert updates the detail panel.

## Alert Detail

- [ ] Shows severity, category, confidence, and status.
- [ ] Shows changed fields.
- [ ] Shows before/after KYC values.
- [ ] Shows recommended action.
- [ ] Shows evidence URLs and excerpts.
- [ ] Shows document IDs and fact IDs.

## RM Workflow

- [ ] Acknowledge action works.
- [ ] Escalate action works.
- [ ] Request update action works.
- [ ] Add to brief action works.
- [ ] Dismiss action works.
- [ ] Action history is visible.
- [ ] Local demo state can be reset.

## Call Brief

- [ ] Generates brief for selected customer.
- [ ] Includes material changes.
- [ ] Includes risk questions.
- [ ] Includes commercial opportunities.
- [ ] Includes suggested questions.
- [ ] Includes evidence references.
- [ ] Copy or print action works.

## Demo Readiness

- [ ] Polymarket risk escalation can be shown.
- [ ] Robinhood ownership/control drift can be shown.
- [ ] GameStop treasury opportunity can be shown.
- [ ] Circle commercial opportunity can be shown.
- [ ] Demo runs end to end from local server.
