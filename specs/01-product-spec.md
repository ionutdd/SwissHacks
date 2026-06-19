# Product Spec: SignalWatch for AMINA

## Problem

AMINA relationship managers may manage hundreds of customers. KYC updates happen periodically, so the bank's internal view of a customer can become stale between review cycles. This creates two problems:

- Compliance teams and RMs can miss early signs of higher financial-crime, sanctions, reputational, or AML risk.
- RMs can miss legitimate commercial moments where a customer needs additional AMINA products, such as custody, trading, lending, FX, staking, deposits, stablecoin rewards, or investment services.

## Objective

Build a prototype that continuously monitors public and approved data sources for customer changes, compares those changes against the last-known KYC snapshot, and produces evidence-backed alerts for RM review.

## Primary Users

- **Relationship Manager**: needs a prioritized, explainable list of customer changes and recommended next steps.
- **Compliance Analyst**: needs traceable evidence, risk rationale, source quality, and audit history.
- **Sales or Product Specialist**: needs qualified service opportunities, not noisy generic growth alerts.
- **Hackathon Judge / AMINA Stakeholder**: needs a clear demonstration that the prototype can find real signals in a scalable, automatable way.

## User Stories

- As an RM, I want to see which customers changed materially since their last KYC review so I can act before the next periodic call.
- As a compliance analyst, I want to see why a signal is risky and which source supports it so I can decide whether to escalate.
- As an RM, I want commercial opportunity alerts to be separated from risk alerts so I can handle each with the right tone and urgency.
- As AMINA, I want every AI conclusion to preserve source links and timestamps so alerts are auditable.
- As the hackathon team, I want to demonstrate the system on public companies or public crypto/Web3 firms without needing private AMINA customer data.

## Scope

### In Scope For MVP

- Customer profile baseline imported from a structured JSON/CSV snapshot.
- Public-source monitoring for companies, founders, executives, investors, subsidiaries, websites, news, job postings, social channels, and optionally linked wallet addresses.
- Signal extraction into typed risk and opportunity signals.
- Drift comparison between the baseline and new evidence.
- Alert scoring using impact, confidence, source quality, freshness, and regulatory relevance.
- RM dashboard or report with evidence, severity, recommended action, and review state.
- Human-in-the-loop disposition: acknowledge, dismiss, escalate, request customer update, or mark as opportunity.
- Demo using public entities and synthetic baselines.

### Out Of Scope For MVP

- Automated customer offboarding.
- Automated regulatory filings or suspicious activity reporting.
- Private banking core integration.
- Real customer PII ingestion.
- Definitive legal/regulatory classification.
- Paid data integrations unless already available during the hackathon.
- Full blockchain forensic attribution without known wallet seeds or a licensed analytics provider.

## Core Product Requirements

### P0 Requirements

- The system must ingest at least one baseline KYC profile per monitored entity.
- The system must produce alerts with a source URL, timestamp, extracted fact, changed profile field, confidence, and severity.
- The system must distinguish risk alerts from commercial opportunity alerts.
- The system must show why a signal matters to AMINA.
- The system must support RM review states and preserve an audit trail.
- The system must avoid irreversible automated decisions.

### P1 Requirements

- The system should cluster multiple sources into one alert when they describe the same underlying change.
- The system should support customer-specific watch terms, including names, aliases, domains, social handles, subsidiaries, executives, investors, and wallet addresses.
- The system should show a before/after comparison against the baseline KYC snapshot.
- The system should learn from RM feedback to reduce repeated false positives.

### P2 Requirements

- The system could recommend AMINA products based on opportunity signals.
- The system could generate a concise RM call brief before periodic customer contact.
- The system could route high-risk alerts to compliance and low-risk opportunities to the RM queue.

## Example Baseline Profile

```json
{
  "customer_id": "demo-001",
  "legal_name": "Example Web3 AG",
  "aliases": ["Example Web3"],
  "domicile": "Switzerland",
  "business_area": ["web3 infrastructure", "software"],
  "risk_rating": "medium",
  "known_jurisdictions": ["Switzerland", "Germany"],
  "known_products": ["corporate account", "crypto custody"],
  "beneficial_owners": [
    {
      "name": "Jane Founder",
      "nationality": "Switzerland",
      "pep_status": "not_pep"
    }
  ],
  "directors": ["Jane Founder", "Max Director"],
  "investors": ["Clean Capital Fund I"],
  "websites": ["https://example.com"],
  "social_handles": {
    "x": ["@exampleweb3"],
    "linkedin": ["example-web3"]
  },
  "known_wallets": [],
  "last_reviewed_at": "2026-01-15"
}
```

## Success Metrics

- Detect at least 5 meaningful signal types across demo entities.
- Each alert contains at least one verifiable evidence link.
- At least 80% of demo alerts are understandable by a non-technical RM in under 60 seconds.
- False positive handling is visible in the workflow.
- The demo shows both a risk case and an opportunity case.

## Risks And Mitigations

- **Noisy public data**: use source quality scoring, entity resolution, and human review.
- **Hallucinated extraction**: require extracted facts to cite exact source snippets and URLs.
- **Ambiguous entity matches**: keep confidence low and ask for RM confirmation when names collide.
- **Compliance overclaiming**: frame alerts as triage signals, not legal conclusions.
- **Private-source constraints**: use public data and synthetic baselines for the hackathon.

## Acceptance Criteria

- A user can load or select a monitored customer.
- A user can see baseline KYC fields and detected changes.
- A user can filter alerts by risk, opportunity, severity, source, and review state.
- A user can open an alert and see evidence, extracted fact, confidence, and recommended next action.
- A user can disposition an alert and leave an audit note.
- The prototype can run end-to-end on demo data without private AMINA systems.

