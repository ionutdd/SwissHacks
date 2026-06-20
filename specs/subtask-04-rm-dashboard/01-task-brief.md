# Task Brief

## Objective

Build the Relationship Manager facing experience for SignalWatch.

Tasks 1 to 3 create the baseline, evidence, facts, and scored alerts. Task 4 turns those outputs into a workflow an RM can use during monitoring and customer preparation.

## What Task 4 Is About

Task 4 is not about better scraping, better extraction, or changing the scoring model.

It is about answering:

- Which customers need attention first?
- What changed since the last KYC review?
- Why does the change matter?
- Which evidence supports it?
- What action should the RM take next?
- What should go into the next customer call brief?

## What To Build

Create a dashboard that can run locally from static fixtures:

1. Portfolio queue.
2. Customer alert list.
3. Alert detail panel.
4. Before/after KYC drift view.
5. Evidence view with source URLs and excerpts.
6. RM review action buttons.
7. Generated call brief for the selected customer.

## Priority Demo Stories

Support these stories first:

1. **Polymarket risk escalation**
   - RM opens regulatory/jurisdiction alert.
   - Evidence is visible.
   - RM escalates to compliance.

2. **Robinhood ownership/control update**
   - RM opens Bitstamp acquisition alert.
   - Before/after subsidiaries and jurisdictions are visible.
   - RM requests updated ownership or structure documentation.

3. **GameStop treasury opportunity**
   - RM opens Bitcoin treasury alert.
   - RM adds custody/lending opportunity to the call brief.

4. **Circle commercial opportunity**
   - RM opens payments/stablecoin alert.
   - Call brief includes payments, FX, and stablecoin settlement talking points.

## What Not To Do

- Do not edit generated alert facts just for UI convenience.
- Do not hide low-confidence evidence without making the filter clear.
- Do not make irreversible workflow actions.
- Do not build complex authentication, database, or CRM integrations for the hackathon.
- Do not create a marketing landing page instead of the actual RM tool.

## Implementation Recommendation

Use the static fixture files and store review actions in browser local storage for the demo.

Recommended flow:

1. Load baseline, documents, facts, and alerts.
2. Build customer aggregates.
3. Sort alerts by severity, category, confidence, and status.
4. Let the RM filter and select an alert.
5. Render evidence and before/after fields.
6. Store review actions locally.
7. Generate call brief from selected customer alerts and saved actions.

The dashboard should be quiet, dense, and operational. It should look like a real work queue, not a landing page.
