# Refresh Algorithm Spec

## Pipeline

1. Run `scripts/collect_evidence.py` to refresh normalized evidence documents from the configured source catalog.
2. Run `scripts/extract_signals.py` to regenerate facts and all alerts.
3. Run the freshness gate and material filter to score and split alerts into:
   - TLDR notifications from the last 24 hours
   - suppressed/noise/stale alerts
4. Write a run summary and dashboard-ready JSON files.

## Reused Collection Sources

The refresh must reuse the existing split collectors:

- SEC filings and recent filing API.
- Company website/newsroom discovery.
- Regulator source discovery.
- News/event discovery with public fallbacks.
- Product/legal page-diff watch.
- RDAP domain watch.
- Explicit cataloged public URLs.

## Runtime Behavior

- Default mode should run end to end.
- Default lookback should be the last `24` hours.
- A `--skip-collection` mode should exist for fast local reruns when evidence was already refreshed.
- A `--skip-extraction` mode should exist for dashboard-only material filter changes.
- A `--lookback-hours` option should allow a different refresh window for testing or demos.
- Failures from individual collectors should be visible in existing collection traces and must not stop material filtering if valid alerts already exist.

## Freshness

The TLDR notification feed must be freshness-first:

- Only alerts with evidence `published_at` inside the refresh window should be shown as current notifications.
- Date-only values such as `2026-06-20` count for that calendar day.
- `collected_at` and alert `created_at` must not make old documents look like same-day news.
- Undated evidence should be retained in suppression/audit outputs, not shown in the TLDR feed by default.
- An optional `--include-undated-collected` mode may be used for technical page-diff demos, but it is not the default RM behavior.

Older official enforcement or sanctions evidence can remain in the full customer workspace and audit queue, but it should not appear in the current-day notification tab unless it was newly published inside the configured window.

## News Discovery Window

The news/event connector should request a 24-hour window from the upstream discovery API where supported, then locally reject candidates outside the same lookback window before fetching and normalizing documents.
