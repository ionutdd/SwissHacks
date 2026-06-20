#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    fetch_url,
    load_baselines_and_catalog,
    now_utc,
    write_pipeline_outputs,
)


PIPELINE_NAME = "sec"


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline_by_id = {entity["customer_id"]: entity for entity in baselines}
    seen_urls = set(existing_urls or set())
    sources: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for source in catalog.get("sources", []):
        if source.get("source_type") == "sec_filing" or str(source.get("connector", "")).startswith("sec_"):
            sources.append(dict(source))
            seen_urls.add(source["url"])

    if sources:
        traces.append(discovery_trace("sec_catalog_sources", "portfolio", len(sources)))

    for config in catalog.get("api_discovery", []):
        if not config.get("enabled") or config.get("connector") != "sec_recent_filings":
            continue

        cik = re.sub(r"\D", "", config["cik"]).zfill(10)
        customer_id = config["customer_id"]
        entity = baseline_by_id.get(customer_id, {})
        baseline_date = entity.get("last_reviewed_at", "0000-00-00")
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            payload = json.loads(fetch_url(submissions_url))
            recent = payload.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            filing_dates = recent.get("filingDate", [])
            accession_numbers = recent.get("accessionNumber", [])
            primary_documents = recent.get("primaryDocument", [])
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            traces.append(
                discovery_trace(
                    "sec_recent_filings",
                    customer_id,
                    0,
                    status="failed",
                    url=submissions_url,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        allowed_forms = set(config.get("allowed_forms", []))
        max_documents = int(config.get("max_documents", 2))
        added = 0

        for form, filing_date, accession, primary_document in zip(
            forms, filing_dates, accession_numbers, primary_documents
        ):
            if added >= max_documents:
                break
            if allowed_forms and form not in allowed_forms:
                continue
            if filing_date < baseline_date:
                continue

            accession_no_dash = accession.replace("-", "")
            archive_url = (
                f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dash}/{primary_document}"
            )
            if archive_url in seen_urls:
                continue

            sources.append(
                {
                    "source_id": f"api-sec-{customer_id}-{accession_no_dash}",
                    "customer_id": customer_id,
                    "connector": "sec_recent_filings",
                    "url": archive_url,
                    "source_type": config["source_type"],
                    "source_name": config["source_name"],
                    "source_quality": config["source_quality"],
                    "title_hint": f"{entity.get('legal_name', customer_id)} {form} filed {filing_date}",
                    "published_at_hint": filing_date,
                    "query_terms": config.get("query_terms", []),
                    "expected_signal_types": config.get("expected_signal_types", []),
                    "baseline_fields_targeted": config.get("baseline_fields_targeted", []),
                    "automation_potential": config.get("automation_potential", "high"),
                    "limitations": config.get("limitations"),
                }
            )
            seen_urls.add(archive_url)
            added += 1

        traces.append(discovery_trace("sec_recent_filings", customer_id, added, url=submissions_url))

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
    parser = argparse.ArgumentParser(description="Run only the SEC evidence collection pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} SEC document(s).")
