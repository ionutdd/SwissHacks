# Connector Algorithms Spec

## Purpose

Task 2 should not depend only on manually pasted URLs. The collector should run source-specific algorithms that can discover, fetch, filter, and normalize evidence into `data_02/documents.json`.

The collector still emits one shared `Document` schema. The source connector only changes how candidate pages are found.

## Connector 1: Company Site Discovery

Use for:

- Company newsrooms.
- Press rooms.
- Official blogs.
- Investor-relations news pages.

Algorithm:

1. Start from configured company index URLs.
2. Extract public links from the page.
3. Score link text and URL against entity aliases and drift terms.
4. Keep high-scoring candidate URLs.
5. Fetch candidate pages.
6. Run evidence ranking and emit `Document` objects.

This should catch official announcements like Robinhood/Bitstamp, Kraken/NinjaTrader, Kraken xStocks, and Circle product or IR announcements.

## Connector 2: Regulator Discovery

Use for:

- Enforcement pages.
- Public regulator press releases.
- Licensing or registration pages.
- Public complaint, order, or sanction pages.

Algorithm:

1. Start from configured regulator URLs or index pages.
2. Extract candidate links or use configured candidate URLs.
3. Score candidate text against legal name, aliases, and regulatory terms.
4. Emit only pages that pass the configured match threshold.
5. Mark old enforcement pages as context if they pre-date the baseline.

This should catch evidence like CFTC Polymarket enforcement history, NFA/CFTC registration context, and future regulator notices.

## Connector 3: News/Event API Discovery

Use for:

- Reputable secondary news.
- Adverse media.
- Jurisdiction restrictions.
- M&A stories not yet available from an official source.

Algorithm:

1. Build API queries from entity aliases and drift terms.
2. Query a public or licensed news/event API.
3. Filter by trusted publisher domains and recency.
4. Fetch article pages when public.
5. Run evidence ranking and emit only source-backed documents.
6. Use configured fallback URLs when the API is unavailable or returns no useful public article.

For the hackathon, GDELT is the free public connector. In production, this can be swapped for Event Registry, Factiva, Dow Jones, Bloomberg, or another licensed provider.

## Connector 4: Product And Legal Page Diff

Use for:

- Product pages.
- Legal disclosures.
- Risk disclosures.
- Terms pages.
- Public documentation pages.

Algorithm:

1. Fetch configured watch URLs.
2. Clean visible text.
3. Hash the cleaned page text.
4. Compare with the previous run state.
5. If changed, or if hackathon `emit_unchanged` is enabled, run evidence ranking.
6. Emit the strongest changed or relevant evidence.

This should catch product or legal changes like Kraken xStocks disclosures, Circle USDC/CPN/Mint pages, Bitstamp legal entities, and future product launches.

## Connector Boundary

Do not scrape login-gated LinkedIn pages. If LinkedIn-like company/headcount/executive signals are needed, use an approved API, a licensed company-data provider, or official company careers/ATS pages.

## Minimum Run Evidence

After a run, `data_02/collection_trace.json` should show:

- SEC API discovery ran.
- Company site discovery ran.
- Regulator discovery ran.
- News/event API discovery ran.
- Product/legal page diff ran.

`data_02/documents.json` should still satisfy the normal task 2 checklist.

## Split Script Contract

Each pipeline has its own runnable script:

- `scripts/collect_evidence_SEC.py`
- `scripts/collect_evidence_company_site.py`
- `scripts/collect_evidence_regulator.py`
- `scripts/collect_evidence_news_event.py`
- `scripts/collect_evidence_page_diff.py`
- `scripts/collect_evidence_direct_sources.py`

Each script writes isolated output to `data_02/pipeline_runs/`.

`scripts/collect_evidence.py` runs the pipelines together, deduplicates candidate sources, and writes the final merged dataset.
