#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    fetch_url,
    load_baselines_and_catalog,
    now_utc,
    write_pipeline_outputs,
)


PIPELINE_NAME = "news_event"


def domain_allowed(url: str, trusted_domains: list[str]) -> bool:
    if not trusted_domains:
        return True
    host = urlparse(url).netloc.lower().replace("www.", "")
    return any(host == domain or host.endswith(f".{domain}") for domain in trusted_domains)


def source_name_from_url(url: str, fallback: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if not host:
        return fallback
    return host


def gdelt_articles(query: str, max_records: int = 10) -> list[dict[str, Any]]:
    endpoint = (
        "https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={quote_plus(query)}&mode=ArtList&format=json&maxrecords={max_records}&sort=HybridRel"
    )
    payload = json.loads(fetch_url(endpoint))
    return list(payload.get("articles", []))


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen_urls = set(existing_urls or set())
    sources: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for config in catalog.get("source_discovery", []):
        if not config.get("enabled") or config.get("connector") != "news_event_discovery":
            continue

        customer_id = config["customer_id"]
        trusted_domains = list(config.get("trusted_domains", []))
        candidates: list[dict[str, Any]] = []

        for query in config.get("queries", []):
            try:
                for article in gdelt_articles(query):
                    url = article.get("url")
                    if not url or not domain_allowed(url, trusted_domains):
                        continue
                    candidates.append(
                        {
                            "url": url,
                            "title_hint": article.get("title"),
                            "published_at_hint": article.get("seendate"),
                            "source_name": source_name_from_url(url, config.get("source_name", "News Discovery")),
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                traces.append(
                    discovery_trace(
                        "news_event_discovery",
                        customer_id,
                        0,
                        status="skipped",
                        query=query,
                        reason=f"News API query unavailable; using configured fallbacks. {type(exc).__name__}: {exc}",
                    )
                )

        for fallback_url in config.get("fallback_urls", []):
            candidates.append(
                {
                    "url": fallback_url,
                    "title_hint": config.get("title_hint"),
                    "published_at_hint": config.get("published_at_hint"),
                    "source_name": source_name_from_url(fallback_url, config.get("source_name", "News Discovery")),
                }
            )

        added = 0
        for candidate in candidates:
            if added >= int(config.get("max_documents", 3)):
                break
            url = candidate["url"]
            if url in seen_urls:
                continue
            sources.append(
                {
                    "source_id": f"news-{customer_id}-{added + 1}",
                    "customer_id": customer_id,
                    "connector": "news_event_discovery",
                    "url": url,
                    "source_type": config["source_type"],
                    "source_name": candidate.get("source_name") or config["source_name"],
                    "source_quality": config["source_quality"],
                    "title_hint": candidate.get("title_hint"),
                    "published_at_hint": candidate.get("published_at_hint"),
                    "query_terms": config.get("query_terms", []),
                    "expected_signal_types": config.get("expected_signal_types", []),
                    "baseline_fields_targeted": config.get("baseline_fields_targeted", []),
                    "automation_potential": config.get("automation_potential", "medium"),
                    "limitations": config.get("limitations"),
                }
            )
            seen_urls.add(url)
            added += 1

        traces.append(discovery_trace("news_event_discovery", customer_id, added))

    return sources, traces


def run_pipeline(
    baseline_path: str,
    catalog_path: str,
    output_dir: str,
    collected_at: str | None = None,
    polite_delay_seconds: float = 0.0,
    write_outputs: bool = True,
) -> PipelineResult:
    baselines, catalog = load_baselines_and_catalog(baseline_path, catalog_path)
    timestamp = collected_at or now_utc()
    sources, discovery_traces = discover_sources(catalog, baselines)
    documents, collect_traces = collect_sources(sources, baselines, timestamp, polite_delay_seconds=polite_delay_seconds)
    result = PipelineResult(PIPELINE_NAME, documents, discovery_traces + collect_traces, len(sources), len(sources))
    if write_outputs:
        write_pipeline_outputs(Path(output_dir), PIPELINE_NAME, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run only the news/event evidence discovery pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} news/event document(s).")
