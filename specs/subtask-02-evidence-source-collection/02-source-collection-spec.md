# Source Collection Spec

## Goal

Collect public, verifiable, automatable evidence that supports the demo KYC drift stories.

The source collection teammate is not responsible for turning evidence into facts or alerts. The output should be clean enough that teammate 3 can do extraction without re-researching the entity.

## Source Quality Levels

### A: Official Or Primary Source

Use whenever possible.

Examples:

- Company newsroom.
- Investor relations.
- SEC filing.
- Regulator page.
- Court filing.
- Company registry.
- Official product documentation.
- Official careers page.

### B: Reputable Secondary Source

Useful for corroboration or when official sources are hard to parse.

Examples:

- Reuters.
- Bloomberg.
- Wall Street Journal.
- Financial Times.
- CNBC.
- Axios.
- Investopedia.
- MarketWatch.
- Business Insider.

### C: Third-Party Database Or Industry Blog

Use carefully and preferably with corroboration.

Examples:

- Crunchbase-like pages.
- CoinDesk-style industry coverage.
- Wikipedia for discovery only, not final evidence.
- Aggregated company profile pages.

### D: Weak Or Unverified Source

Avoid for showcased alerts.

Examples:

- Anonymous forum posts.
- Unverified social posts.
- Reposts without links.
- SEO spam.
- Rumors.

## Source Type Values

Use these machine-readable values in `documents.json`:

- `company_newsroom`
- `investor_relations`
- `sec_filing`
- `regulator`
- `court_or_legal`
- `company_registry`
- `product_page`
- `careers_page`
- `official_blog`
- `official_social`
- `reputable_news`
- `industry_news`
- `block_explorer`
- `github`
- `other`

## Collection Rules

- Prefer source quality A, then B.
- Capture exact excerpts that prove the drift.
- Keep excerpts short but sufficient.
- Do not paraphrase inside `evidence_excerpt`.
- If a page is paywalled, mark it and find a free replacement if possible.
- If a source is ambiguous, mark `confidence_hint` as `low`.
- Do not infer legal conclusions.
- Do not infer wallet ownership unless the company itself publishes the address.
- Store one document object per source page, not one per signal.

## Evidence Excerpt Rules

Good excerpt:

```text
Robinhood has closed its acquisition of Bitstamp Ltd., a global cryptocurrency exchange.
```

Bad excerpt:

```text
Robinhood is doing crypto stuff.
```

Good excerpts are:

- Specific.
- Source-backed.
- Short.
- Directly linked to a baseline field change.

## Automation Potential

For each source, mark `automation_potential`:

- `high`: source can be monitored by URL, RSS, filing feed, API, or structured page.
- `medium`: source can be monitored but may require scraping or search.
- `low`: source is useful manually but hard to automate.

Examples:

- SEC filings: `high`
- Company newsroom RSS: `high`
- Company product page: `medium`
- One-off news article: `medium`
- Paywalled article: `low`

## Runnable Source Connectors

Task 2 uses these connector algorithms:

- `sec_recent_filings`: SEC EDGAR submissions API discovery.
- `company_site_discovery`: company newsroom, press, blog, and IR link discovery.
- `regulator_discovery`: regulator page or index discovery.
- `news_event_discovery`: GDELT or licensed news/event API discovery.
- `page_diff_watch`: product, legal, disclosure, and documentation page monitoring.

All connectors must emit the same normalized `Document` schema so teammate 3 can treat SEC, regulator, company, news, and product evidence the same way.

## Minimum Evidence Targets

Across the whole dataset:

- 15 or more documents.
- 8 or more A/B quality documents.
- 4 or more source types.
- 2 or more documents for each top 3 story.
- 1 or more official source for each top 3 story.

## Weak Source Handling

If a source is weak but useful for discovery:

- Include it only if needed.
- Set `source_quality` to `C` or `D`.
- Add `limitations`.
- Do not use it as the only evidence for a high-risk alert.

## Duplicate Handling

Avoid duplicates unless they add value.

Useful duplicate:

- Official company announcement plus SEC filing.

Not useful duplicate:

- Five news articles repeating the same press release.
