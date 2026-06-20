#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    extract_links,
    fetch_url,
    link_score,
    load_baselines_and_catalog,
    now_utc,
    write_pipeline_outputs,
)


PIPELINE_NAME = "company_site"


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_by_id = {entity["customer_id"]: entity for entity in baselines}
    seen_urls = set(existing_urls or set())
    sources: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for config in catalog.get("source_discovery", []):
        if not config.get("enabled") or config.get("connector") != "company_site_discovery":
            continue

        customer_id = config["customer_id"]
        entity = baseline_by_id.get(customer_id, {})
        candidates: list[tuple[int, dict[str, str]]] = []

        for index_url in config.get("index_urls", []):
            try:
                html_text = fetch_url(index_url)
            except Exception as exc:  # noqa: BLE001 - trace should keep collection moving.
                traces.append(
                    discovery_trace(
                        "company_site_discovery",
                        customer_id,
                        0,
                        status="failed",
                        url=index_url,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            index_host = urlparse(index_url).netloc.lower().replace("www.", "")
            for link in extract_links(html_text, index_url):
                link_host = urlparse(link["url"]).netloc.lower().replace("www.", "")
                if index_host and link_host and index_host != link_host:
                    continue
                score = link_score(link, entity, config)
                if score >= int(config.get("min_score", 3)):
                    candidates.append((score, link))

        added = 0
        for score, link in sorted(candidates, key=lambda item: item[0], reverse=True):
            if added >= int(config.get("max_documents", 2)):
                break
            if link["url"] in seen_urls:
                continue
            title_hint = link.get("text") or config.get("title_hint")
            sources.append(
                {
                    "source_id": f"company-{customer_id}-{added + 1}",
                    "customer_id": customer_id,
                    "connector": "company_site_discovery",
                    "url": link["url"],
                    "source_type": config["source_type"],
                    "source_name": config["source_name"],
                    "source_quality": config["source_quality"],
                    "title_hint": title_hint,
                    "published_at_hint": config.get("published_at_hint"),
                    "query_terms": config.get("query_terms", []),
                    "expected_signal_types": config.get("expected_signal_types", []),
                    "baseline_fields_targeted": config.get("baseline_fields_targeted", []),
                    "automation_potential": config.get("automation_potential", "high"),
                    "limitations": config.get("limitations"),
                }
            )
            seen_urls.add(link["url"])
            added += 1

        traces.append(discovery_trace("company_site_discovery", customer_id, added))

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
    parser = argparse.ArgumentParser(description="Run only the company site discovery evidence pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} company-site document(s).")
