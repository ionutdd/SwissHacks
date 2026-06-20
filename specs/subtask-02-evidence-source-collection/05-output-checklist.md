# Output Checklist

Use this before handing off to teammates 3 and 4.

## Required Files

- [x] `scripts/collect_evidence.py`
- [x] `scripts/evidence_common.py`
- [x] `scripts/collect_evidence_SEC.py`
- [x] `scripts/collect_evidence_company_site.py`
- [x] `scripts/collect_evidence_regulator.py`
- [x] `scripts/collect_evidence_news_event.py`
- [x] `scripts/collect_evidence_page_diff.py`
- [x] `scripts/collect_evidence_direct_sources.py`
- [x] `data_02/source_catalog.json`
- [x] `data_02/documents.json`
- [x] `data_02/source_evidence_map.md`
- [x] `data_02/collection_trace.json`
- [x] `data_02/collection_run_report.md`
- [x] `data_02/page_watch_state.json`
- [x] `data_02/pipeline_runs/`

## Documents Checklist

For each document:

- [x] Has a stable `document_id`.
- [x] Has a valid `customer_id`.
- [x] Has `source_type`.
- [x] Has `source_name`.
- [x] Has `source_url`.
- [x] Has `source_quality`.
- [x] Has `title`.
- [x] Has `collected_at`.
- [x] Has `evidence_excerpt`.
- [x] Has `expected_signal_types`.
- [x] Has `baseline_fields_targeted`.
- [x] Has `automation_potential`.
- [x] Has `confidence_hint`.

## Portfolio Checklist

Across all documents:

- [x] At least 15 documents collected.
- [x] At least 8 documents are A or B quality.
- [x] At least 4 source types represented.
- [x] Each top 3 story has at least 2 documents.
- [x] Each top 3 story has at least 1 official source.
- [x] No high-risk story depends only on C or D quality sources.

## Evidence Map Checklist

`data_02/source_evidence_map.md` should include:

- [x] Top 3 stories.
- [x] Source list by customer.
- [x] Which baseline fields each source supports changing.
- [x] Which signal types each source supports.
- [x] Known source limitations.
- [x] Replacement notes for paywalled or weak sources.

## Handoff To Teammate 3

Before extraction/scoring starts:

- [x] `data_02/documents.json` parses as valid JSON.
- [x] Every `customer_id` exists in `data_01/baseline_snapshots.json`.
- [x] Every document has at least one `expected_signal_type`.
- [x] Every document has at least one `baseline_fields_targeted`.
- [x] Evidence excerpts are specific enough to extract facts from.

## Handoff To Teammate 4

Before UI work uses evidence:

- [x] Source URLs are public.
- [x] Evidence excerpts are readable on screen.
- [x] Source quality is available for display.
- [x] Top 3 demo sources are easy to show in the pitch.

## Ready-To-Handoff Summary Template

```markdown
# Evidence Collection Handoff

## Collection Summary

- Total documents: 18
- A/B quality documents: 18
- Source types represented: 7
- Top 3 stories covered: Robinhood/Bitstamp, Polymarket regulatory access, GameStop bitcoin treasury
- Algorithm run: `scripts/collect_evidence.py`
- Split pipelines used: SEC, company site, regulator, news/event, page diff, direct sources

## Strongest Sources

1. Robinhood - Robinhood Completes Acquisition of Bitstamp - official ownership and subsidiary evidence.
2. GameStop - SEC Form 8-K bitcoin purchase announcement - official filing evidence for treasury policy drift.
3. Kraken - official NinjaTrader acquisition and xStocks launch - official ownership and product drift evidence.

## Weak Or Replacement Needed

- Axios Polymarket/QCX source - blocked automated fetch with HTTP 403; kept in catalog as a candidate but not emitted.
- GDELT news API returned HTTP 429 during the latest merged run; configured Guardian, El Pais, and Cadena SER fallbacks were used.
- Guardian, El Pais, and Cadena SER Polymarket/Kalshi Spain sources - secondary sources; keep as jurisdiction restriction evidence, but corroborate with official BOE/DGOJ notice if time allows.
- LinkedIn - provider/API-only; do not scrape login-gated pages.

## Notes For Teammate 3

- Start extraction with A-quality official sources, then use B-quality news only as corroboration.
- Preserve source timestamps so old background events do not become false "new drift" alerts.
- Use `source_quality`, `confidence_hint`, and `baseline_fields_targeted` as priors in scoring.

## Notes For Teammate 4

- Show source badges for official filings/newsrooms versus secondary news.
- Use Robinhood/Bitstamp, GameStop bitcoin, and Kraken xStocks as the cleanest demo cards.
- Keep excerpts short and link back to the source URL from each alert.
```
