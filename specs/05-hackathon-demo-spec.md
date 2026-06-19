# Hackathon Demo And Evaluation Spec

## Demo Goal

Show that SignalWatch can detect real KYC drift and commercial opportunities from public data, explain how the data was obtained, and present it in a workflow AMINA RMs could use.

## Demo Shape

Build a demo with 3 to 5 monitored entities:

- Public company with rich filings and news.
- Crypto/Web3 company with public product, token, or wallet signals.
- Startup-like company with hiring and website/news changes.
- Optional synthetic AMINA-style customer profile to demonstrate sensitive risk drift.

Use synthetic baselines so the demo can show drift even when real historical KYC data is unavailable.

## Required Demo Scenarios

### Scenario 1: Risk Drift

Example story:

- Baseline says customer operates in Switzerland and Germany as a software provider.
- New public evidence shows expansion into a sensitive jurisdiction or sensitive business line.
- System creates high-severity risk alert.
- RM reviews evidence and escalates to compliance.

Required evidence:

- Source URL.
- Extracted fact.
- Baseline field changed.
- Explanation of why AMINA should care.

### Scenario 2: Ownership Or Control Drift

Example story:

- Baseline lists known directors/investors.
- New registry, news, or filing source shows a new director, investor, acquisition, or subsidiary.
- System creates alert with confidence score and recommended customer update request.

### Scenario 3: Commercial Opportunity

Example story:

- Customer raises funding, hires treasury roles, expands internationally, or announces crypto holdings.
- System suggests relevant AMINA products such as custody, lending, FX/trading, deposits, stablecoin rewards, staking, or investments.
- RM adds alert to call brief.

### Scenario 4: Negative Or Positive News

Example story:

- News source reports enforcement, breach, lawsuit, funding, product launch, or expansion.
- System classifies as risk or opportunity.
- User can see why it was classified that way.

## Recommended Prototype Architecture

```text
Synthetic KYC Baseline
        |
Watchlist Builder
        |
Public Source Connectors
        |
Document Store
        |
Entity Resolution
        |
Fact Extraction
        |
Drift Scoring
        |
Alert Dashboard + RM Brief
```

## Suggested Data Sources For Demo

Low-friction:

- Company website/newsroom.
- Careers page.
- Press releases.
- RSS/news search API.
- GitHub organization pages.
- Public filings for listed companies.
- Company registry pages where accessible.
- Public sanctions list samples.

Higher-effort but high-impact:

- Job board APIs from Greenhouse, Lever, or Ashby.
- SEC EDGAR API for listed companies.
- GDELT for global news events.
- Block explorer data for known public wallets.
- OpenCorporates or similar registry API if available.

## Example Demo Data Strategy

Because real AMINA customer data is unavailable, create synthetic baselines using real public entities:

1. Pick a public entity.
2. Create a "last reviewed" snapshot dated before a known public event.
3. Feed current public sources into the system.
4. Let the system detect the event as drift.
5. Show the evidence and explain how the same method scales to AMINA customers.

This is acceptable for a hackathon because it demonstrates the detection method without exposing customer data.

## Presentation Storyboard

1. **Problem**: RMs manage many customers, and periodic KYC snapshots drift.
2. **Insight**: Public signals often reveal material changes before the next RM call.
3. **Prototype**: SignalWatch monitors customers, extracts facts, compares to KYC baseline, and creates evidence-backed alerts.
4. **Risk demo**: Show a high-severity alert and compliance escalation.
5. **Opportunity demo**: Show a growth or digital-asset alert and AMINA product recommendation.
6. **Scalability**: Show connector architecture, source coverage, and audit model.
7. **Trust**: Show evidence, confidence, source quality, and human review.
8. **Next steps**: Integrate sanctioned lists, registries, premium adverse-media APIs, and AMINA CRM/KYC systems.

## Evaluation Rubric

### Accuracy

- Correct entity matching.
- Correct source attribution.
- No unsupported claims.
- Clear confidence scoring.

### Business Relevance

- Alerts map to AMINA risk or product needs.
- RM workflow is realistic.
- Output is actionable, not just informational.

### Compliance Readiness

- Human review remains mandatory.
- Audit trail is visible.
- Risk categories are explainable.
- No irreversible automated decisions.

### Scalability

- Connectors are reusable.
- Sources can be scheduled.
- Signals use a normalized schema.
- New signal types can be added.

### Demo Quality

- Shows before/after KYC drift.
- Includes at least one risk and one opportunity.
- Evidence is visible.
- The story is understandable in under 5 minutes.

## MVP Acceptance Criteria

- 3 monitored demo customers.
- 10 or more collected source documents.
- 6 or more generated alerts.
- At least 2 high-quality risk alerts.
- At least 2 commercial opportunity alerts.
- Alert detail includes evidence, changed field, severity, confidence, and action.
- RM can generate a call brief for one customer.

## Stretch Ideas

- Add sanctions-list matching demo using synthetic names.
- Add blockchain wallet monitoring for a known public treasury wallet.
- Add "why now" scoring for alert prioritization.
- Add email-style daily digest for RMs.
- Add feedback learning from dismissed alerts.
- Add heatmap of customer portfolio risk drift.

