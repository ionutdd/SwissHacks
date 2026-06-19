# Team Workstreams Spec

## Goal

Split the SignalWatch prototype across four teammates while heavily prioritizing the work that matters most for this hackathon:

1. High-quality demo entities.
2. Strong public evidence.
3. Accurate signal extraction and scoring.
4. A simple RM-facing experience that makes the evidence understandable.

The prototype should win on insight quality, not dashboard polish. A beautiful UI with weak data will not convince AMINA. A simple UI with credible, source-backed KYC drift signals can.

## Priority Allocation

Suggested effort split:

- **50% Data sources and demo dataset**
- **30% Signal extraction and scoring**
- **15% Thin backend/integration**
- **5% UI polish**

For a four-person team, this means two teammates should focus on data/evidence, one teammate should focus on signal logic, and one teammate should focus on integration plus a minimal demo UI.

## Four Parallel Tracks

### Teammate 1: Demo Entity And Baseline Lead

Owns choosing the right demo customers and creating synthetic KYC baselines that make drift visible.

This is the most important track. The chosen entities determine whether the whole project feels real.

Deliverables:

- Select 3 to 5 demo customers.
- Create synthetic baseline KYC profiles for each customer.
- Define the "last reviewed at" date for each baseline.
- Identify the expected drift story for each customer.
- Create a clear demo narrative for each entity: risk drift, ownership/control drift, opportunity drift, or adverse/positive news.

Subtasks:

- Pick entities with public evidence and visible changes.
- Prefer entities with multiple source types: website, news, filings, job posts, GitHub, registry, crypto-native data.
- Create `baseline_snapshots.json`.
- For each baseline, intentionally omit or set older information so current public evidence can reveal drift.
- Add notes explaining why each entity is relevant to AMINA.
- Mark each entity as `risk_demo`, `opportunity_demo`, `ownership_demo`, or `mixed_demo`.

Good demo entity criteria:

- Public sources are easy to access.
- The entity has recent changes.
- The entity is plausibly relevant to crypto banking, Web3, fintech, treasury, institutional finance, or cross-border business.
- The drift can be explained in one sentence.
- The evidence is not ambiguous.

Acceptance criteria:

- At least 3 demo entities exist.
- Each entity has a baseline profile.
- Each baseline has a `last_reviewed_at` date.
- Each entity has a planned drift story.
- At least one entity supports a serious risk story.
- At least one entity supports a commercial opportunity story.

### Teammate 2: Evidence And Source Collection Lead

Owns finding, collecting, and normalizing the source documents that prove the demo stories.

This is also a critical track. If the evidence is weak, the signal engine and UI cannot save the demo.

Important boundary: this teammate owns **getting the data into a clean document format**, not the extraction/scoring algorithm. They should produce reliable `documents.json` inputs for Teammate 3.

Deliverables:

- Collect at least 15 source documents.
- Normalize all documents into the shared `Document` schema.
- Capture source URL, title, source type, source quality, published date, collected date, and text excerpt.
- Create a source evidence map linking documents to demo entities and expected signal types.
- Identify which sources are automatable after the hackathon.

Subtasks:

- Search company websites, newsrooms, blogs, press pages, career pages, filings, registries, GitHub, and official social channels.
- Collect official/regulatory sources where possible.
- Capture exact snippets that support the extracted facts.
- Avoid weak social-only evidence unless corroborated.
- Flag sources that are useful but not automatable.
- Create `documents.json`.

High-value source examples:

- Company-owned product or announcement page.
- Official careers page showing new geography or business line.
- Registry or filing showing director, domicile, subsidiary, or ownership change.
- Reputable news article about funding, lawsuit, enforcement, breach, acquisition, or expansion.
- Public GitHub repository or docs showing new crypto/payment functionality.
- Sanctions/watchlist sample for a synthetic match scenario.

Acceptance criteria:

- At least 15 source documents exist.
- Every document has source URL, source type, source quality, timestamp, and excerpt.
- At least 8 documents are high-quality sources: official, registry, filing, regulator, or reputable news.
- Every planned demo alert has at least one supporting source.
- At least 4 source types are represented.

### Teammate 3: Signal Extraction And Scoring Lead

Owns turning baselines and evidence into structured facts, KYC drift signals, severity, confidence, and recommended actions.

This is the second-most important capability after data. The output must feel accurate and explainable.

Important boundary: this teammate owns the **data extraction algorithm**. In this spec, "data extraction" means converting normalized source documents into structured facts, then comparing those facts against the KYC baseline.

Deliverables:

- Fact extraction from normalized documents.
- Baseline comparison logic.
- Risk and opportunity classification.
- Severity and confidence scoring.
- Recommended next actions for RMs and compliance.
- Alert objects that preserve evidence links.

Subtasks:

- Implement or mock `extractFacts(document)`.
- Implement `compareToBaseline(fact, baseline)`.
- Implement `scoreSignal(signal)`.
- Implement `generateRecommendedAction(signal)`.
- Map signals to the taxonomy in `02-signal-taxonomy-spec.md`.
- Add deterministic rules for the demo so the output is stable.
- Avoid unsupported AI claims by requiring every fact to point to a source excerpt.

Extraction algorithm responsibilities:

- Parse each normalized document.
- Identify facts such as new jurisdiction, new subsidiary, new director, funding event, adverse media, hiring expansion, or digital-asset activity.
- Attach the exact evidence excerpt that supports each fact.
- Assign extraction confidence.
- Output facts in the shared `Fact` schema.
- Leave uncertain fields empty instead of guessing.

Minimum signal types to support:

- New jurisdiction exposure.
- Business activity drift.
- Ownership/control drift.
- New subsidiary or office.
- Adverse media or enforcement.
- Funding/growth opportunity.
- Hiring/geographic expansion.
- Digital asset activity or custody/staking/trading opportunity.

Acceptance criteria:

- Generates at least 8 alerts from demo data.
- Produces at least 3 risk alerts.
- Produces at least 3 opportunity alerts.
- Produces at least 1 ownership/control alert.
- Every alert includes changed fields, source evidence, confidence, severity, and recommended action.
- No alert can exist without at least one evidence document.

### Teammate 4: Integration, Minimal UI, And Pitch Flow Lead

Owns making the demo usable and presentable, without overbuilding visual polish.

The UI should be simple: a dashboard table, alert detail, evidence view, and RM action buttons. The main job is to make the evidence and reasoning easy to understand.

Deliverables:

- Load baseline, documents, facts, and alerts from fixtures or local API.
- Customer monitoring queue.
- Alert detail view with evidence.
- Before/after KYC drift view.
- RM action buttons.
- Generated call brief.
- Demo script.

Subtasks:

- Define fixture file locations with teammates 1 to 3.
- Build a minimal local data layer or API.
- Create dashboard table grouped by customer.
- Create alert detail panel.
- Show source excerpts and URLs.
- Add actions: acknowledge, dismiss, escalate, add to call brief.
- Create a 3 to 5 minute demo path.

Acceptance criteria:

- Dashboard loads all demo customers.
- At least 8 alerts appear in the UI.
- Opening an alert shows evidence and before/after drift.
- A risk alert can be escalated.
- An opportunity alert can be added to the call brief.
- The demo can run end to end without manual file editing.

## Shared Data Contracts

Agree on these schemas before splitting up. Teammates can then work independently using fixtures or mocked data.

### Customer Baseline

```json
{
  "customer_id": "demo-001",
  "legal_name": "Example Web3 AG",
  "aliases": ["Example Web3"],
  "domicile": "Switzerland",
  "business_area": ["web3 infrastructure"],
  "risk_rating": "medium",
  "known_jurisdictions": ["Switzerland", "Germany"],
  "known_products": ["corporate account", "crypto custody"],
  "directors": ["Jane Founder"],
  "investors": ["Clean Capital Fund I"],
  "subsidiaries": [],
  "websites": ["https://example.com"],
  "social_handles": {
    "x": ["@exampleweb3"]
  },
  "known_wallets": [],
  "last_reviewed_at": "2026-01-15",
  "demo_story": "Customer expanded into a new jurisdiction after last KYC review."
}
```

### Document

```json
{
  "document_id": "doc-001",
  "customer_id": "demo-001",
  "source_type": "company_website",
  "source_name": "Example Web3 Newsroom",
  "source_url": "https://example.com/news/new-market",
  "title": "Example Web3 expands into new market",
  "published_at": "2026-06-01",
  "collected_at": "2026-06-19T21:00:00Z",
  "raw_text": "Article body...",
  "evidence_excerpt": "Example Web3 opens a new office in...",
  "source_quality": "A",
  "expected_signal_types": ["new_jurisdiction", "commercial_expansion"]
}
```

### Fact

```json
{
  "fact_id": "fact-001",
  "document_id": "doc-001",
  "customer_id": "demo-001",
  "fact_type": "new_jurisdiction",
  "subject": "Example Web3 AG",
  "object": "United Arab Emirates",
  "effective_date": "2026-06-01",
  "evidence_excerpt": "Example Web3 opens a new office...",
  "extraction_confidence": 0.87
}
```

### Alert

```json
{
  "alert_id": "alert-001",
  "customer_id": "demo-001",
  "category": "risk",
  "signal_type": "jurisdiction_drift",
  "title": "New jurisdiction exposure detected",
  "summary": "The customer appears to have expanded beyond the jurisdictions in its KYC baseline.",
  "changed_fields": ["known_jurisdictions"],
  "baseline_value": ["Switzerland", "Germany"],
  "new_value": ["Switzerland", "Germany", "United Arab Emirates"],
  "severity": "high",
  "confidence": 0.84,
  "recommended_action": "Request customer confirmation and route to compliance review.",
  "evidence_document_ids": ["doc-001"],
  "fact_ids": ["fact-001"],
  "status": "new",
  "created_at": "2026-06-19T21:30:00Z"
}
```

### Review Action

```json
{
  "review_action_id": "review-001",
  "alert_id": "alert-001",
  "action": "escalate_to_compliance",
  "note": "Needs confirmation before next KYC review.",
  "created_by": "demo-rm",
  "created_at": "2026-06-19T21:35:00Z"
}
```

## Suggested Fixture Files

Use fixtures first so everyone can work in parallel before the full pipeline is connected.

```text
data/
  baseline_snapshots.json
  documents.json
  facts.json
  alerts.json
  review_actions.json
```

Ownership:

- Teammate 1 owns `baseline_snapshots.json`.
- Teammate 2 owns `documents.json`.
- Teammate 3 owns `facts.json` and `alerts.json`.
- Teammate 4 owns `review_actions.json` only if needed for the demo UI.

## Minimal API Or Function Surface

If using a backend:

- `GET /customers`
- `GET /customers/:customerId`
- `GET /customers/:customerId/alerts`
- `GET /alerts/:alertId`
- `POST /alerts/:alertId/actions`
- `GET /customers/:customerId/call-brief`

If building a static/local prototype:

- `listCustomers()`
- `getCustomer(customerId)`
- `listAlerts(customerId)`
- `getAlert(alertId)`
- `createReviewAction(alertId, action)`
- `generateCallBrief(customerId)`

Do not spend hackathon time on advanced backend infrastructure unless the data and signals are already strong.

## Parallel Build Plan

### First 30 Minutes: Alignment

Agree on:

- Demo customer IDs.
- Fixture file locations.
- Severity values: `critical`, `high`, `medium`, `low`.
- Categories: `risk`, `opportunity`.
- Source quality values: `A`, `B`, `C`, `D`.
- Required alert fields.
- Which teammate owns each file.

### Phase 1: Evidence First

Teammate 1:

- Finalizes demo entities and baselines.
- Writes each entity's planned drift story.

Teammate 2:

- Finds and normalizes source evidence.
- Flags weak or ambiguous evidence early.

Teammate 3:

- Builds signal engine using placeholder fixtures.
- Defines rules for severity and confidence.

Teammate 4:

- Builds UI from mocked `alerts.json`.
- Keeps layout simple.

Definition of done:

- At least 3 baselines exist.
- At least 10 documents exist.
- At least 4 mocked alerts exist.
- UI can display mocked alerts.

### Phase 2: Signal Integration

Teammate 1:

- Checks whether generated alerts match intended customer stories.

Teammate 2:

- Adds more evidence where confidence is weak.

Teammate 3:

- Runs extraction and scoring on real fixtures.
- Produces `facts.json` and `alerts.json`.

Teammate 4:

- Connects UI to real fixtures or API.

Definition of done:

- At least 8 generated alerts exist.
- Every alert has evidence.
- Dashboard loads real alerts.
- Alert detail shows before/after drift.

### Phase 3: Demo Tightening

Everyone focuses on the demo story, not new features.

Teammate 1:

- Selects the top 3 alerts for the final pitch.

Teammate 2:

- Verifies source links and excerpts.

Teammate 3:

- Tunes severity, confidence, and recommended actions.

Teammate 4:

- Rehearses the click path and fixes confusing screens.

Definition of done:

- Demo shows one risk drift, one ownership/control drift, and one commercial opportunity.
- Evidence is visible on screen.
- The team can explain how each signal was obtained and why it scales.

## What Not To Overbuild

Avoid spending time on:

- Fancy charts before evidence quality is strong.
- Complex authentication.
- Complex database migrations.
- Pixel-perfect dashboard polish.
- Fully automated scraping for every source.
- LLM agents that cannot show exact evidence.
- Large product surfaces beyond the demo path.

## Dependency Map

- Frontend depends on alert shape, but can start with mocked `alerts.json`.
- Signal extraction depends on baselines and documents, but can start with placeholder fixtures.
- Source collection depends on chosen entities, so teammate 1 and teammate 2 should coordinate continuously.
- Demo pitch depends on the strongest alerts, so all teammates should know the top 3 scenarios.

## Final Demo Checklist

- 3 or more monitored customers.
- 15 or more source documents.
- 8 or more generated alerts.
- 3 or more risk alerts.
- 3 or more opportunity alerts.
- 1 ownership/control drift alert.
- 1 high-severity alert backed by high-quality evidence.
- Every showcased alert has source URL, excerpt, changed field, confidence, severity, and recommended action.
- UI shows before/after KYC drift.
- RM action changes alert state.
- Call brief can be generated.
- Demo script is rehearsed once end to end.
