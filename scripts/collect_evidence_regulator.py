#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    entity_terms,
    fetch_url,
    load_baselines_and_catalog,
    now_utc,
    rule_signal_terms,
    source_query_terms,
    term_score,
    visible_text,
    write_pipeline_outputs,
)


PIPELINE_NAME = "regulator"


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
        if not config.get("enabled") or config.get("connector") != "regulator_discovery":
            continue

        customer_id = config["customer_id"]
        entity = baseline_by_id.get(customer_id, {})
        min_score = int(config.get("min_score", 3))
        added = 0

        for url in config.get("candidate_urls", []):
            if added >= int(config.get("max_documents", 1)):
                break
            if url in seen_urls:
                continue
            try:
                clean_text = visible_text(fetch_url(url))
            except Exception as exc:  # noqa: BLE001
                traces.append(
                    discovery_trace(
                        "regulator_discovery",
                        customer_id,
                        0,
                        status="failed",
                        url=url,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            score = term_score(clean_text, entity_terms(entity) + source_query_terms(config) + rule_signal_terms(config))
            if score < min_score:
                traces.append(
                    discovery_trace(
                        "regulator_discovery",
                        customer_id,
                        0,
                        status="skipped",
                        url=url,
                        reason=f"Regulator candidate score {score} below threshold {min_score}.",
                    )
                )
                continue

            sources.append(
                {
                    "source_id": f"regulator-{customer_id}-{added + 1}",
                    "customer_id": customer_id,
                    "connector": "regulator_discovery",
                    "url": url,
                    "source_type": config["source_type"],
                    "source_name": config["source_name"],
                    "source_quality": config["source_quality"],
                    "title_hint": config.get("title_hint"),
                    "published_at_hint": config.get("published_at_hint"),
                    "query_terms": config.get("query_terms", []),
                    "expected_signal_types": config.get("expected_signal_types", []),
                    "baseline_fields_targeted": config.get("baseline_fields_targeted", []),
                    "automation_potential": config.get("automation_potential", "high"),
                    "limitations": config.get("limitations"),
                }
            )
            seen_urls.add(url)
            added += 1

        traces.append(discovery_trace("regulator_discovery", customer_id, added))

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
    parser = argparse.ArgumentParser(description="Run only the regulator evidence discovery pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} regulator document(s).")
