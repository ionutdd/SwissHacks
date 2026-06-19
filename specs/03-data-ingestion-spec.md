# Data Ingestion And Evidence Spec

## Goal

Create a scalable, automatable way to collect public evidence, extract customer changes, and produce auditable KYC drift signals.

## Pipeline

1. **Baseline import**: ingest current KYC snapshot.
2. **Watchlist expansion**: generate names, aliases, domains, social handles, people, subsidiaries, investors, wallets, and products to monitor.
3. **Source collection**: collect documents from public and approved sources.
4. **Entity resolution**: decide whether a document truly refers to the monitored customer or related party.
5. **Fact extraction**: extract structured facts using rules, parsers, and LLM-assisted extraction.
6. **Drift comparison**: compare extracted facts with baseline fields.
7. **Signal scoring**: assign category, severity, confidence, source quality, and recommended action.
8. **Alert creation**: create or update RM/compliance alerts.
9. **Feedback loop**: learn from RM dispositions.

## Source Types

### Official And Regulatory

- Swiss commercial register / Zefix.
- Local company registries for demo jurisdictions.
- FINMA public pages and enforcement releases.
- SECO sanctions lists.
- UN Security Council Consolidated List.
- OFAC Sanctions List Service.
- EU sanctions map or consolidated lists.
- Court records where available.
- SEC EDGAR for public-company filings.

Use cases:

- Domicile change.
- Director/UBO change where public.
- Subsidiary creation.
- Enforcement and sanctions screening.
- Public financial filings.

### Company-Owned Sources

- Website pages.
- Newsroom and blog RSS.
- Press releases.
- Terms of service.
- Product documentation.
- Careers pages.
- Investor relations pages.
- API docs.
- GitHub organization profile and repositories, where relevant.

Use cases:

- Product/service drift.
- Expansion into new sectors or jurisdictions.
- Hiring signals.
- New digital-asset functionality.
- Treasury, staking, token, or custody announcements.

### Job And Hiring Sources

- Company careers page.
- Greenhouse.
- Lever.
- Ashby.
- Workable.
- LinkedIn jobs if legally and technically accessible.

Use cases:

- Geographic expansion.
- Hiring surge or hiring freeze.
- New compliance, finance, crypto trading, sanctions, or treasury roles.
- New business line inferred from job descriptions.

### News And Media

- Reputable news APIs.
- RSS feeds.
- GDELT or other public event datasets.
- Industry publications.
- Press-release wires.

Use cases:

- Adverse media.
- Funding rounds.
- M&A.
- Partnerships.
- Enforcement.
- Growth signals.

### Social And Community

- Official X/Twitter account.
- LinkedIn company page.
- LinkedIn executive posts if accessible and compliant.
- Discord/Telegram only if public and permitted.
- Farcaster or other Web3-native channels.

Use cases:

- Early announcements.
- Founder relocation.
- Hiring and launch signals.
- Product positioning changes.

Social signals should be marked lower confidence unless the account is verified or corroborated.

### Crypto-Native Sources

- Known wallet addresses from KYC.
- Company-published wallet addresses.
- Block explorers.
- Token contracts.
- Governance forums.
- DeFi protocol pages.
- Licensed blockchain analytics APIs if available.

Use cases:

- Treasury exposure.
- Token issuance.
- High-risk on-chain counterparties.
- Mixer/sanctioned-address proximity.
- Staking or DeFi activity.

Constraint: do not infer ownership of a wallet without credible attribution.

## Connector Requirements

Each connector should output a normalized `Document` object:

```json
{
  "document_id": "doc-001",
  "source_type": "company_website",
  "source_name": "Example Web3 Newsroom",
  "source_url": "https://example.com/news/new-subsidiary",
  "title": "Example Web3 opens Dubai subsidiary",
  "published_at": "2026-06-01",
  "collected_at": "2026-06-19T21:00:00Z",
  "raw_text": "Article body...",
  "language": "en",
  "hash": "sha256:..."
}
```

Connector behavior:

- Respect robots.txt, source terms, and rate limits.
- Store source URL, collection timestamp, and content hash.
- Avoid collecting personal data that is unnecessary for the demo.
- Retry transient failures with backoff.
- Make connector failures visible in the monitoring UI or logs.

## Entity Resolution

Entity matching should consider:

- Exact legal name.
- Common name and aliases.
- Domain ownership or company-owned URLs.
- Executive names combined with company name.
- Investor names combined with funding event.
- Registry identifiers.
- Social handles.
- Wallet addresses only when explicitly linked.

Resolution output:

```json
{
  "document_id": "doc-001",
  "customer_id": "demo-001",
  "match_confidence": 0.91,
  "matched_terms": ["Example Web3 AG", "example.com"],
  "ambiguity_reason": null
}
```

Low-confidence matches must not create high-severity alerts without corroboration.

## Fact Extraction

Structured extraction target:

```json
{
  "fact_id": "fact-001",
  "document_id": "doc-001",
  "customer_id": "demo-001",
  "fact_type": "new_subsidiary",
  "subject": "Example Web3 AG",
  "object": "Example Web3 Middle East Ltd",
  "jurisdiction": "United Arab Emirates",
  "effective_date": "2026-06-01",
  "evidence_excerpt": "Example Web3 announces its new Middle East subsidiary...",
  "extraction_confidence": 0.87
}
```

Extraction rules:

- Output must conform to a schema.
- The extractor must cite the source document.
- If the source does not support a field, leave it null.
- Do not invent facts from industry assumptions.
- Preserve uncertainty in confidence scores.

## Storage Model

Recommended collections/tables:

- `customers`
- `baseline_snapshots`
- `watch_terms`
- `documents`
- `entity_matches`
- `facts`
- `signals`
- `alerts`
- `review_actions`
- `source_runs`

## Scheduling

Hackathon MVP:

- Manual run button.
- Daily scheduled job simulation.
- Per-customer refresh.

Production direction:

- Critical sources: hourly to daily.
- Company websites/social/news: daily.
- Registries and sanctions: daily or as source updates allow.
- Low-priority opportunity sources: weekly.

## Privacy And Compliance Guardrails

- Use public data or approved customer-provided data.
- Store only necessary evidence for the demo.
- Avoid scraping behind logins.
- Flag social and personal signals as sensitive.
- Keep humans in the loop for compliance actions.
- Maintain an audit trail for every alert, score, and disposition.

## Acceptance Criteria

- At least 4 connector types run in the demo.
- Every collected document has source URL, source type, timestamp, and hash.
- Every extracted fact traces back to a document.
- Every alert traces back to at least one fact and one evidence source.
- Connector failures do not break the whole pipeline.

