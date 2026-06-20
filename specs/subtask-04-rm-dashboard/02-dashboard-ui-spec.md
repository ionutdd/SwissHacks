# Dashboard UI Spec

## Purpose

Give RMs a production-style work surface for triaging KYC drift and commercial opportunity alerts.

## Main Layout

Use a three-zone dashboard:

1. **Portfolio rail**
   - Summary metrics.
   - Filter controls.
   - Monitored customer list.

2. **Alert workspace**
   - Alert queue for the selected customer.
   - Alert detail.
   - Before/after KYC drift.
   - Evidence sources.

3. **RM brief panel**
   - Action history.
   - Generated call brief.
   - Copy or print controls.

## Portfolio Rail

Show:

- Total monitored customers.
- New/open alerts.
- High-severity alerts.
- Risk alerts.
- Opportunity alerts.
- Last scan timestamp.

Customer rows should show:

- Legal name.
- Current baseline risk rating.
- Alert count.
- Highest severity.
- Count by category.
- Last reviewed date.
- Assigned RM placeholder.

## Filters

Support:

- Free-text search across customer name and alert title.
- Category filter: all, risk, opportunity, ownership/control, mixed.
- Severity filter: all, high, medium, low.
- Status filter: all, new, in review, escalated, dismissed, added to call brief.

Filters should update the customer queue and alert queue without a page refresh.

## Alert Queue

Each alert row should show:

- Severity.
- Category.
- Title.
- Confidence.
- Status.
- Evidence count.
- Changed fields.

Sort order:

1. Critical/high severity.
2. Risk before mixed before ownership before opportunity when severity ties.
3. Higher confidence.
4. Newer created date.

## Alert Detail

Show:

- Title.
- Summary.
- Severity.
- Category.
- Signal type.
- Confidence.
- Status.
- Recommended action.
- Changed KYC fields.
- Before and after values.
- Evidence links and excerpts.
- Fact IDs and document IDs for auditability.

The RM must be able to understand the alert without opening the raw source first.

## Visual Treatment

The UI should feel like an operational banking tool:

- Dense but readable.
- Neutral background.
- Clear severity colors.
- No marketing hero.
- No decorative layout.
- No nested cards.
- Responsive desktop-first layout that also works on laptop and mobile.

## Accessibility

Minimum expectations:

- Buttons have clear text labels.
- Focus states are visible.
- Color is not the only signal for severity.
- Long titles and source excerpts wrap cleanly.
- Tables and lists remain usable on narrow screens.
