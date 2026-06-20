# Task Brief

## Objective

Find and normalize public evidence for the five demo entities selected in Subtask 1:

- Robinhood.
- Polymarket.
- GameStop.
- Kraken.
- Circle.

The goal is to create a source-backed evidence layer that proves KYC drift from the synthetic baseline.

## Priority

This is the highest-priority active subtask after baselines.

If time is short, prioritize fewer but stronger sources. A single official source is better than five weak reposts.

## What To Build

Create split runnable evidence collection algorithms:

- `scripts/evidence_common.py`: shared fetch, clean, rank, schema, and output utilities.
- `scripts/collect_evidence.py`: orchestrator that runs all pipelines.
- `scripts/collect_evidence_SEC.py`: SEC EDGAR filing pipeline.
- `scripts/collect_evidence_company_site.py`: official company site discovery pipeline.
- `scripts/collect_evidence_regulator.py`: regulator source pipeline.
- `scripts/collect_evidence_news_event.py`: news/event API pipeline.
- `scripts/collect_evidence_page_diff.py`: product/legal page-diff pipeline.
- `scripts/collect_evidence_direct_sources.py`: explicitly cataloged URL pipeline.

Create `data_02/source_catalog.json`, the source/API connector configuration.

Run the collector to create `data_02/documents.json`, an array of normalized source documents.

Create `data_02/source_evidence_map.md`, a human-readable map of:

- Which source supports which customer.
- Which baseline field changed.
- Which expected signal type the source supports.
- Whether the source is strong enough for the demo.

## What Not To Do

Do not spend this subtask on:

- Extracting structured facts.
- Scoring alerts.
- Making legal conclusions.
- Inferring wallet ownership.
- Collecting private, paid, or login-gated data.
- Depending on social posts without corroboration.

The collector may fetch public websites, SEC EDGAR pages, and public API endpoints. Do not scrape login-gated LinkedIn pages; use an approved API or licensed provider placeholder instead.

## Collection Strategy

Work in this order:

1. Collect official sources for the top 3 stories.
2. Add reputable news or filing sources to corroborate.
3. Collect secondary sources for Kraken and Circle.
4. Fill gaps so every source has usable excerpts.
5. Mark weak or paywalled sources clearly.

## Top 3 Story Priority

### 1. Polymarket Risk Drift

Need sources for:

- CFTC enforcement history.
- Prediction-market/gambling regulatory sensitivity.
- Post-baseline regulatory or jurisdiction signals.
- US return or regulated-exchange acquisition.

### 2. Robinhood Ownership/Jurisdiction Drift

Need sources for:

- Bitstamp acquisition close.
- Bitstamp offices, jurisdictions, licenses, or institutional crypto services.
- Robinhood crypto expansion.

### 3. GameStop Crypto Treasury Drift

Need sources for:

- Investment policy update to allow bitcoin.
- First bitcoin purchase.
- SEC or investor-relations evidence if available.
- Risk factors around digital assets.

## Secondary Story Priority

### Kraken

Need sources for:

- NinjaTrader acquisition.
- Tokenized equities / xStocks.
- Derivatives/futures expansion.
- Relevant regulatory or geographic expansion.

### Circle

Need sources for:

- Public listing / IPO.
- Circle Payments Network.
- Stablecoin, USDC, EURC, USYC, Circle Mint, or Arc product expansion.
- SEC or investor-relations evidence.

## Handoff Requirements

For every source, capture:

- URL.
- Source name.
- Source type.
- Source quality.
- Published date if available.
- Collection timestamp.
- Title.
- Exact supporting excerpt.
- Customer ID.
- Expected signal types.
- Baseline fields likely affected.
