#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from evidence_common import (
    PipelineResult,
    collect_sources,
    discovery_trace,
    fetch_url,
    load_baselines_and_catalog,
    load_json,
    now_utc,
    visible_text,
    write_json,
    write_pipeline_outputs,
)


PIPELINE_NAME = "page_diff"


def page_hash(clean_text: str) -> str:
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return load_json(path)


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
    output_dir: str = "data_02",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen_urls = set(existing_urls or set())
    sources: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    output_path = Path(output_dir)

    for config in catalog.get("source_discovery", []):
        if not config.get("enabled") or config.get("connector") != "page_diff_watch":
            continue

        default_customer_id = config["customer_id"]
        state_path = output_path / config.get("state_path", "page_watch_state.json")
        state = load_state(state_path)
        new_state = dict(state)
        added = 0

        for index, page in enumerate(config.get("pages", []), start=1):
            url = page["url"]
            try:
                clean_text = visible_text(fetch_url(url))
            except Exception as exc:  # noqa: BLE001
                traces.append(
                    discovery_trace(
                        "page_diff_watch",
                        page.get("customer_id", default_customer_id),
                        0,
                        status="failed",
                        url=url,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )
                continue

            digest = page_hash(clean_text)
            previous = state.get(url, {}).get("sha256")
            changed = previous != digest
            new_state[url] = {"sha256": digest, "last_seen_at": now_utc()}

            if not changed and not config.get("emit_unchanged", False):
                traces.append(
                    discovery_trace(
                        "page_diff_watch",
                        page.get("customer_id", default_customer_id),
                        0,
                        status="skipped",
                        url=url,
                        reason="Page hash unchanged.",
                    )
                )
                continue

            if url in seen_urls:
                continue

            source = dict(page)
            source.update(
                {
                    "source_id": f"page-diff-{page.get('customer_id', default_customer_id)}-{index}",
                    "customer_id": page.get("customer_id", default_customer_id),
                    "connector": "page_diff_watch",
                    "url": url,
                    "page_hash": digest,
                    "page_changed": changed,
                }
            )
            sources.append(source)
            seen_urls.add(url)
            added += 1

        write_json(state_path, new_state)
        traces.append(discovery_trace("page_diff_watch", default_customer_id, added, state_path=str(state_path)))

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
    sources, discovery_traces = discover_sources(catalog, baselines, output_dir=output_dir)
    documents, collect_traces = collect_sources(sources, baselines, timestamp, polite_delay_seconds=polite_delay_seconds)
    result = PipelineResult(PIPELINE_NAME, documents, discovery_traces + collect_traces, len(sources), len(sources))
    if write_outputs:
        write_pipeline_outputs(Path(output_dir), PIPELINE_NAME, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run only the product/legal page-diff evidence pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--polite-delay-seconds", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, polite_delay_seconds=args.polite_delay_seconds)
    print(f"Wrote {len(output.documents)} page-diff document(s).")
