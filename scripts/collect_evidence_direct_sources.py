#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    load_baselines_and_catalog,
    now_utc,
    source_key,
    write_pipeline_outputs,
)


PIPELINE_NAME = "direct_sources"


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    existing = set(existing_urls or set())
    existing_url_set = {item for item in existing if isinstance(item, str)}
    seen_keys = {item for item in existing if not isinstance(item, str)}
    sources: list[dict[str, Any]] = []

    for source in catalog.get("sources", []):
        if source.get("source_type") == "sec_filing" or str(source.get("connector", "")).startswith("sec_"):
            continue
        if source["url"] in existing_url_set:
            continue
        key = source_key(source)
        if key in seen_keys:
            continue
        sources.append(dict(source))
        seen_keys.add(key)

    return sources, [discovery_trace("direct_sources", "portfolio", len(sources))]


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
    parser = argparse.ArgumentParser(description="Run only the explicitly cataloged URL evidence pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} direct-source document(s).")
