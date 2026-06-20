# Review Actions And Call Brief Spec

## Purpose

Let the RM act on alerts during the demo and generate a concise customer call brief.

## Review Actions

Support these actions:

| Button | Stored action | Resulting status |
| --- | --- | --- |
| Acknowledge | `acknowledged` | `in_review` |
| Escalate | `escalated` | `escalated` |
| Request update | `customer_update_requested` | `customer_update_requested` |
| Add to brief | `added_to_call_brief` | `added_to_call_brief` |
| Dismiss | `dismissed` | `dismissed` |

Each action should capture:

- Alert ID.
- Customer ID.
- Action.
- Optional note.
- Created by.
- Created at.

## Audit Trail

For each selected alert, show:

- Current status.
- Action history.
- Timestamp.
- Note if provided.

The action trail can be local-only for the demo.

## Call Brief

Generate the brief from the selected customer:

1. **Material changes**
   - High severity alerts.
   - Ownership/control alerts.
   - Risk-rating review alerts.

2. **Open risk questions**
   - Risk alerts.
   - Escalated alerts.
   - Jurisdiction restrictions.

3. **Commercial opportunities**
   - Opportunity alerts.
   - Alerts added to the brief.
   - Digital-asset or treasury activity with commercial relevance.

4. **Suggested customer questions**
   - Ask about updated ownership or legal entities.
   - Ask about new operating jurisdictions.
   - Ask about treasury, custody, payments, FX, or lending needs.

5. **Evidence references**
   - Source name.
   - Source URL.
   - Excerpt.

## Brief Actions

Support:

- Copy brief.
- Print brief.
- Clear local demo actions.

## Acceptance Criteria

- A risk alert can be escalated.
- An opportunity alert can be added to the call brief.
- Action status updates are visible immediately.
- The call brief uses the selected customer only.
- Brief content includes evidence references and recommended next actions.
