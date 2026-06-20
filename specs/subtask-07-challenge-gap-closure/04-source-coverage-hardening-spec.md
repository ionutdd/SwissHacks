# Source Coverage Hardening Spec

## Goal

Close the biggest source-coverage gaps from the AMINA challenge brief: sanctions and watchlists, corporate registries, beneficial ownership, legal-form changes, funding events, and adverse media.

## Current Coverage

Already implemented or partially implemented:

- SEC filings.
- Company sites and official blogs.
- Regulator pages.
- News/event discovery.
- Page-diff monitoring.
- RDAP/domain monitoring.
- Direct URL catalog.
- Some OFAC examples through direct regulator pages.

## Missing Source Families

### 1. Sanctions And Watchlists

Target sources:

- OpenSanctions.
- OFAC Sanctions List Service.
- EU Financial Sanctions Database.
- UN Security Council Consolidated List.
- Swiss SECO sanctions references.

Required output:

- `watchlist_candidate_matches.json`
- `watchlist_match_review.json`

Important rule:

- Treat all matches as candidates requiring review unless identifiers are strong enough.

Entity-resolution fields:

- legal name
- aliases
- date of birth or incorporation date where available
- jurisdiction
- identifiers
- source list
- match score
- match reason

### 2. Corporate Registry And Ownership

Target sources:

- GLEIF LEI API.
- UK Companies House.
- OpenCorporates.
- Swiss ZEFIX.

Signals:

- legal entity name change
- legal form change
- domicile change
- new directors
- dissolved or inactive status
- new branches or subsidiaries
- beneficial-owner review required

### 3. Funding And Startup Intelligence

Target sources:

- Crunchbase if credentials exist.
- Wellfound where public.
- reputable funding news.
- company announcements.

Signals:

- large funding round
- rapid expansion
- new investors
- valuation or scale change
- product-market pivot

### 4. Website And Business-Model Monitoring

Already partially covered by page diffs.

Hardening requirements:

- Store previous hash and current hash.
- Show changed text snippets.
- Distinguish cosmetic changes from material content changes.
- Prioritize changes to:
  - regulated products
  - jurisdiction availability
  - crypto/digital asset language
  - payment rails
  - legal entity names
  - terms and risk disclosures

## Connector Priority

P0:

- OpenSanctions candidate match connector.
- GLEIF LEI lookup connector.
- Companies House connector for UK examples.

P1:

- EU/UN/SECO sanctions connectors.
- ZEFIX Swiss registry lookup.
- OpenCorporates fallback.

P2:

- Crunchbase or paid-provider adapter.
- Wayback Machine historical page comparison.

## Acceptance Criteria

- At least one sanctions/watchlist candidate example exists.
- At least one registry-driven legal entity or director-change example exists.
- At least one source produces a candidate match that is intentionally rejected as too weak.
- Source coverage report clearly separates implemented, mocked, and future/provider-only connectors.
