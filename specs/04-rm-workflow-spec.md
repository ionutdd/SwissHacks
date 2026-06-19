# Relationship Manager Workflow Spec

## Goal

Give RMs and compliance reviewers a practical interface for triaging KYC drift without forcing them to inspect raw web data.

## Main Views

### 1. Customer Monitoring Queue

Shows all monitored customers with:

- Current risk rating.
- Number of new risk alerts.
- Number of new opportunity alerts.
- Highest severity.
- Last reviewed date.
- Last scan date.
- Assigned RM.
- Required action state.

Filters:

- Severity.
- Category.
- RM owner.
- Review state.
- Jurisdiction.
- Product opportunity.
- Last scan date.

### 2. Customer Profile Timeline

Shows:

- Baseline KYC snapshot.
- Changes over time.
- Risk rating history.
- Opportunity history.
- RM notes.
- Compliance decisions.
- Source evidence history.

Timeline event types:

- Baseline imported.
- Signal detected.
- Alert opened.
- RM note added.
- Compliance escalation.
- Customer contacted.
- Alert dismissed.
- Baseline updated.

### 3. Alert Detail

Each alert detail page should include:

- Alert title.
- Risk or opportunity category.
- Severity.
- Confidence.
- Customer field changed.
- Before/after comparison.
- Evidence sources.
- Source quality.
- Reasoning summary.
- Suggested next action.
- Similar previous alerts.
- Action buttons.

Action buttons:

- Acknowledge.
- Dismiss as false positive.
- Escalate to compliance.
- Request customer update.
- Add to next RM call brief.
- Mark as commercial opportunity.
- Update baseline after confirmation.

### 4. RM Call Brief

Before a periodic customer call, generate:

- Material changes since last review.
- Open risk questions.
- Commercial product opportunities.
- Suggested customer questions.
- Evidence links for internal use.
- Items requiring compliance input.

The brief should be concise enough for a 5-minute prep read.

## Alert Lifecycle

```text
new -> in_review -> escalated -> resolved
new -> in_review -> dismissed
new -> added_to_call_brief -> customer_contacted -> baseline_updated
new -> marked_opportunity -> actioned -> closed
```

## Review States

- **New**: not yet seen by RM.
- **In review**: RM opened or assigned it.
- **Escalated**: compliance needs to assess.
- **Customer update requested**: RM needs clarification from customer.
- **Opportunity**: commercial follow-up, no immediate risk escalation.
- **Dismissed**: false positive, duplicate, or not material.
- **Resolved**: action complete.
- **Baseline updated**: confirmed change has been added to KYC profile.

## Recommended Actions

Risk alerts:

- Check sanctions/watchlist match.
- Ask customer for updated ownership or operations documentation.
- Escalate to compliance.
- Increase monitoring frequency.
- Trigger enhanced due diligence workflow.
- Add question to next KYC review.

Opportunity alerts:

- Suggest custody.
- Suggest staking.
- Suggest lending.
- Suggest FX/trading.
- Suggest deposits or stablecoin rewards.
- Suggest investment products.
- Suggest corporate banking services.

## Explainability Requirements

Every AI-generated explanation must include:

- The exact fact extracted.
- Why the fact differs from baseline.
- Why the change matters.
- Which source supports it.
- What uncertainty remains.

Bad explanation:

> This customer looks risky.

Good explanation:

> The customer's baseline lists Switzerland and Germany as known jurisdictions. A company-owned careers page now lists five roles in Country X, including "Head of Payments - Country X". This may indicate new operating exposure and should be confirmed by the RM.

## Audit Trail

Store:

- Who viewed the alert.
- Who changed the alert state.
- Timestamp of each state change.
- Notes and rationale.
- Source evidence used at decision time.
- Old and new baseline values if updated.

## Notification Rules

- Critical risk: notify RM and compliance immediately.
- High risk: notify RM and add to compliance queue.
- Medium risk: add to RM queue and daily digest.
- Low risk: add to customer timeline.
- Opportunity: add to RM opportunity queue and call brief.

## MVP UI Requirements

- Dashboard table of customers and alerts.
- Alert detail view.
- Evidence drawer or section.
- Review action buttons.
- Generated RM call brief.
- Basic filters.

## Acceptance Criteria

- An RM can understand the top reason for an alert without reading the raw source first.
- An RM can take a review action in one click plus optional note.
- A compliance reviewer can trace every alert to evidence.
- The system preserves dismissed false positives.
- The call brief includes both open risks and commercial opportunities.

