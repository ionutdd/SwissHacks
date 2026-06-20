#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import collect_evidence_SEC
import collect_evidence_company_site
import collect_evidence_direct_sources
import collect_evidence_domain_rdap
import collect_evidence_news_event
import collect_evidence_page_diff
import collect_evidence_regulator
from evidence_common import (
    collect_sources,
    dedupe_sources,
    load_baselines_and_catalog,
    now_utc,
    write_final_outputs,
    write_json,
)


PIPELINE_MODULES = {
    "sec": collect_evidence_SEC,
    "company_site": collect_evidence_company_site,
    "regulator": collect_evidence_regulator,
    "news_event": collect_evidence_news_event,
    "page_diff": collect_evidence_page_diff,
    "domain_rdap": collect_evidence_domain_rdap,
    "direct_sources": collect_evidence_direct_sources,
}

DEFAULT_PIPELINES = [
    "sec",
    "company_site",
    "regulator",
    "news_event",
    "page_diff",
    "domain_rdap",
    "direct_sources",
]


def discover_pipeline_sources(
    pipeline: str,
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    output_dir: str,
    lookback_hours: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    module = PIPELINE_MODULES[pipeline]
    if pipeline == "page_diff":
        return module.discover_sources(catalog, baselines, output_dir=output_dir)
    if pipeline == "news_event":
        return module.discover_sources(catalog, baselines, lookback_hours=lookback_hours)
    return module.discover_sources(catalog, baselines)


def collect(args: argparse.Namespace) -> int:
    baselines, catalog = load_baselines_and_catalog(args.baseline, args.catalog)
    collected_at = now_utc()
    selected_pipelines = args.pipelines or DEFAULT_PIPELINES

    candidate_sources: list[dict[str, Any]] = []
    domain_rdap_sources: list[dict[str, Any]] = []
    discovery_traces: list[dict[str, Any]] = []

    for pipeline in selected_pipelines:
        if pipeline not in PIPELINE_MODULES:
            raise ValueError(f"Unknown pipeline: {pipeline}")
        if pipeline == "domain_rdap":
            sources, traces = collect_evidence_domain_rdap.discover_sources(catalog, baselines)
            domain_rdap_sources.extend(sources)
        elif pipeline == "direct_sources":
            existing_urls = {source["url"] for source in candidate_sources}
            sources, traces = collect_evidence_direct_sources.discover_sources(catalog, baselines, existing_urls)
            candidate_sources.extend(sources)
        else:
            sources, traces = discover_pipeline_sources(
                pipeline,
                catalog,
                baselines,
                args.output_dir,
                lookback_hours=args.lookback_hours,
            )
            candidate_sources.extend(sources)
        discovery_traces.extend(traces)

    sources = dedupe_sources(candidate_sources)
    documents, collect_traces = collect_sources(
        sources,
        baselines,
        collected_at,
        polite_delay_seconds=args.polite_delay_seconds,
    )
    domain_documents, domain_traces = collect_evidence_domain_rdap.collect_rdap_sources(
        domain_rdap_sources,
        baselines,
        collected_at,
        start_number=len(documents) + 1,
    )
    documents.extend(domain_documents)
    traces = discovery_traces + collect_traces
    traces.extend(domain_traces)

    output_dir = Path(args.output_dir)
    write_json(output_dir / "pipeline_runs" / "all_candidate_sources.json", candidate_sources + domain_rdap_sources)
    write_json(output_dir / "pipeline_runs" / "merged_sources.json", sources + domain_rdap_sources)
    write_final_outputs(output_dir, documents, traces, baselines, collected_at)

    print(f"Wrote {len(documents)} document(s) to {output_dir / 'documents.json'}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all or selected split evidence collection pipelines.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    parser.add_argument("--lookback-hours", type=int, default=None)
    parser.add_argument(
        "--pipelines",
        nargs="*",
        choices=sorted(PIPELINE_MODULES),
        help="Optional subset: sec company_site regulator news_event page_diff domain_rdap direct_sources",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(collect(parse_args()))
