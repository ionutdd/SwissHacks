#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from evidence_common import (
    PipelineResult,
    USER_AGENT,
    discovery_trace,
    load_baselines_and_catalog,
    load_json,
    normalize_text,
    now_utc,
    write_json,
    write_pipeline_outputs,
)


PIPELINE_NAME = "domain_rdap"

TLD_JURISDICTIONS = {
    ".au": "Australia",
    ".br": "Brazil",
    ".ch": "Switzerland",
    ".jp": "Japan",
    ".sg": "Singapore",
    ".uk": "United Kingdom",
    ".ae": "United Arab Emirates",
}


def normalize_match_value(value: str) -> str:
    value = normalize_text(value).lower()
    value = value.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def identity_terms(entity: dict[str, Any]) -> list[str]:
    terms = [entity.get("legal_name", "")]
    terms.extend(entity.get("aliases", []))
    return [term for term in (normalize_match_value(str(item)) for item in terms) if term]


def domain_to_url(domain: str) -> str:
    return f"https://{domain}"


def infer_jurisdiction(domain: str, source: dict[str, Any]) -> str | None:
    if source.get("jurisdiction"):
        return source["jurisdiction"]
    domain = f".{domain.lower().lstrip('.')}"
    for suffix, jurisdiction in TLD_JURISDICTIONS.items():
        if domain.endswith(suffix):
            return jurisdiction
    return None


def fetch_rdap(url: str, timeout: int = 20) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rdap+json, application/json;q=0.9, */*;q=0.4",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def rdap_self_url(data: dict[str, Any], fallback: str) -> str:
    for link in data.get("links", []):
        if link.get("rel") == "self" and link.get("href"):
            return link["href"]
    return fallback


def eligibility_map(data: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in data.get("auData_eligibility", []):
        name = normalize_text(item.get("name", "")).lower()
        value = normalize_text(item.get("value", ""))
        if name and value:
            values[name] = value
    return values


def event_date(data: dict[str, Any], event_action: str) -> str | None:
    for event in data.get("events", []):
        if event.get("eventAction") == event_action:
            return event.get("eventDate")
    return None


def redacted_registration_date(data: dict[str, Any]) -> bool:
    for item in data.get("redacted", []):
        name = item.get("name", {})
        if "registration date" in normalize_match_value(str(name)):
            return True
    return False


def nameservers(data: dict[str, Any]) -> list[str]:
    return [
        normalize_text(item.get("ldhName") or item.get("unicodeName") or "")
        for item in data.get("nameservers", [])
        if normalize_text(item.get("ldhName") or item.get("unicodeName") or "")
    ]


def matched_identity_fields(data: dict[str, Any], entity: dict[str, Any]) -> list[str]:
    eligibility = eligibility_map(data)
    candidates = {
        "registrant name": eligibility.get("registrant name", ""),
        "eligibility name": eligibility.get("eligibility name", ""),
    }
    terms = identity_terms(entity)
    matched: list[str] = []
    for field, value in candidates.items():
        normalized_value = normalize_match_value(value)
        if not normalized_value:
            continue
        if any(term == normalized_value or term in normalized_value or normalized_value in term for term in terms):
            matched.append(field)
    return matched


def build_summary_text(
    domain: str,
    data: dict[str, Any],
    source: dict[str, Any],
    jurisdiction: str | None,
) -> tuple[str, str, str]:
    eligibility = eligibility_map(data)
    ns_values = nameservers(data)
    last_changed = event_date(data, "last changed")
    rdap_updated = event_date(data, "last update of RDAP database")
    registration_redacted = redacted_registration_date(data)

    registrant = eligibility.get("registrant name", "not public")
    eligibility_type = eligibility.get("eligibility type", "not public")
    eligibility_name = eligibility.get("eligibility name", "not public")
    eligibility_id = eligibility.get("eligibility id", "not public")
    jurisdiction_text = jurisdiction or "unknown jurisdiction"
    redaction_note = (
        "The registry redacts the original registration date."
        if registration_redacted
        else "The registry did not report a redacted registration date marker."
    )

    raw_text = (
        f"RDAP record for {domain} lists registrant name {registrant}; "
        f"eligibility type {eligibility_type}; eligibility name {eligibility_name}; "
        f"eligibility id {eligibility_id}; inferred country-code jurisdiction {jurisdiction_text}; "
        f"nameservers {', '.join(ns_values) if ns_values else 'not listed'}; "
        f"last changed {last_changed or 'not listed'}; RDAP database updated {rdap_updated or 'not listed'}. "
        f"{redaction_note} Treat the domain as a country-code domain monitoring signal requiring RM confirmation, "
        "not as proof of an active local launch."
    )
    excerpt = (
        f"RDAP for {domain} lists registrant name {registrant}, eligibility type {eligibility_type}, "
        f"eligibility name {eligibility_name}, eligibility id {eligibility_id}, and last changed {last_changed or 'not listed'}."
    )
    title = source.get("title_hint") or f"RDAP record for {domain}"
    return title, raw_text, excerpt


def build_document(
    document_number: int,
    source: dict[str, Any],
    entity: dict[str, Any],
    data: dict[str, Any],
    collected_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    domain = data.get("ldhName") or source["domain"]
    jurisdiction = infer_jurisdiction(domain, source)
    title, raw_text, excerpt = build_summary_text(domain, data, source, jurisdiction)
    last_changed = event_date(data, "last changed")
    source_url = rdap_self_url(data, source["url"])
    matched_fields = matched_identity_fields(data, entity)

    document = {
        "document_id": f"doc-{document_number:03d}",
        "customer_id": source["customer_id"],
        "source_type": source.get("source_type", "domain_rdap"),
        "source_name": source.get("source_name", "RDAP"),
        "source_url": source_url,
        "source_quality": source.get("source_quality", "A"),
        "title": title,
        "published_at": last_changed[:10] if last_changed else None,
        "collected_at": collected_at,
        "language": source.get("language_hint", "en"),
        "raw_text": raw_text,
        "evidence_excerpt": excerpt,
        "expected_signal_types": list(source.get("expected_signal_types", [])),
        "baseline_fields_targeted": list(source.get("baseline_fields_targeted", [])),
        "automation_potential": source.get("automation_potential", "high"),
        "confidence_hint": "high" if matched_fields else "low",
        "limitations": source.get("limitations"),
    }

    trace = {
        "source_id": source.get("source_id"),
        "document_id": document["document_id"],
        "url": source_url,
        "status": "ok",
        "connector": PIPELINE_NAME,
        "domain": domain,
        "jurisdiction": jurisdiction,
        "matched_identity_fields": matched_fields,
        "last_changed": last_changed,
        "registration_date_redacted": redacted_registration_date(data),
        "nameserver_count": len(nameservers(data)),
    }
    return document, trace


def discover_sources(
    catalog: dict[str, Any],
    baselines: list[dict[str, Any]],
    existing_urls: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen_urls = set(existing_urls or set())
    sources: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for config in catalog.get("source_discovery", []):
        if not config.get("enabled") or config.get("connector") != "domain_rdap_watch":
            continue

        customer_id = config["customer_id"]
        added = 0
        for index, domain_config in enumerate(config.get("domains", []), start=1):
            domain = domain_config["domain"].lower()
            url = domain_config.get("rdap_url") or f"https://rdap.org/domain/{domain}"
            if url in seen_urls:
                continue

            source = {
                "source_id": f"domain-rdap-{customer_id}-{index}",
                "customer_id": customer_id,
                "connector": PIPELINE_NAME,
                "domain": domain,
                "url": url,
                "jurisdiction": domain_config.get("jurisdiction") or config.get("jurisdiction"),
                "source_type": config.get("source_type", "domain_rdap"),
                "source_name": config.get("source_name", "RDAP"),
                "source_quality": config.get("source_quality", "A"),
                "title_hint": domain_config.get("title_hint") or f"RDAP record for {domain}",
                "expected_signal_types": config.get("expected_signal_types", []),
                "baseline_fields_targeted": config.get("baseline_fields_targeted", []),
                "automation_potential": config.get("automation_potential", "high"),
                "limitations": config.get("limitations"),
            }
            sources.append(source)
            seen_urls.add(url)
            added += 1

        traces.append(discovery_trace(PIPELINE_NAME, customer_id, added))

    return sources, traces


def collect_rdap_sources(
    sources: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
    collected_at: str,
    start_number: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baselines_by_id = {entity["customer_id"]: entity for entity in baselines}
    documents: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for source in sources:
        entity = baselines_by_id.get(source["customer_id"])
        if not entity:
            traces.append(
                {
                    "source_id": source.get("source_id"),
                    "url": source["url"],
                    "status": "failed",
                    "connector": PIPELINE_NAME,
                    "error": f"Unknown customer_id {source['customer_id']}",
                }
            )
            continue

        try:
            data = fetch_rdap(source["url"])
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            traces.append(
                {
                    "source_id": source.get("source_id"),
                    "url": source["url"],
                    "status": "failed",
                    "connector": PIPELINE_NAME,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        matched_fields = matched_identity_fields(data, entity)
        if not matched_fields:
            traces.append(
                {
                    "source_id": source.get("source_id"),
                    "url": source["url"],
                    "status": "skipped",
                    "connector": PIPELINE_NAME,
                    "domain": data.get("ldhName") or source["domain"],
                    "reason": "RDAP registrant or trademark ownership did not match baseline identity terms.",
                    "observed_identity": eligibility_map(data),
                }
            )
            continue

        document, trace = build_document(
            start_number + len(documents),
            source,
            entity,
            data,
            collected_at,
        )
        documents.append(document)
        traces.append(trace)

    return documents, traces


def next_document_number(documents: list[dict[str, Any]]) -> int:
    numbers = []
    for document in documents:
        match = re.match(r"doc-(\d+)$", str(document.get("document_id", "")))
        if match:
            numbers.append(int(match.group(1)))
    return (max(numbers) + 1) if numbers else 1


def append_final_documents(output_dir: Path, documents: list[dict[str, Any]], traces: list[dict[str, Any]]) -> None:
    if not documents:
        return

    documents_path = output_dir / "documents.json"
    trace_path = output_dir / "collection_trace.json"
    existing_documents = load_json(documents_path) if documents_path.exists() else []
    existing_traces = load_json(trace_path) if trace_path.exists() else []

    replacement_urls = {document["source_url"] for document in documents}
    replacement_customer_ids = {document["customer_id"] for document in documents}
    retained_documents = [
        document
        for document in existing_documents
        if not (document.get("source_type") == "domain_rdap" and document.get("source_url") in replacement_urls)
    ]
    retained_traces = [
        trace
        for trace in existing_traces
        if not (
            trace.get("connector") == PIPELINE_NAME
            and (
                trace.get("url") in replacement_urls
                or trace.get("customer_id") in replacement_customer_ids
            )
        )
    ]

    write_json(documents_path, retained_documents + documents)
    write_json(trace_path, retained_traces + traces)


def run_pipeline(
    baseline_path: str,
    catalog_path: str,
    output_dir: str,
    collected_at: str | None = None,
    append_final: bool = False,
    write_outputs: bool = True,
) -> PipelineResult:
    baselines, catalog = load_baselines_and_catalog(baseline_path, catalog_path)
    output_path = Path(output_dir)
    timestamp = collected_at or now_utc()
    sources, discovery_traces = discover_sources(catalog, baselines)

    start_number = 1
    if append_final and (output_path / "documents.json").exists():
        existing_documents = load_json(output_path / "documents.json")
        existing_documents = [
            document
            for document in existing_documents
            if document.get("source_type") != "domain_rdap"
        ]
        start_number = next_document_number(existing_documents)

    documents, collect_traces = collect_rdap_sources(sources, baselines, timestamp, start_number=start_number)
    result = PipelineResult(PIPELINE_NAME, documents, discovery_traces + collect_traces, len(sources), len(sources))
    if write_outputs:
        write_pipeline_outputs(output_path, PIPELINE_NAME, result)
    if append_final:
        append_final_documents(output_path, documents, result.traces)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the domain RDAP evidence collection pipeline.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--output-dir", default="data_02")
    parser.add_argument("--append-final", action="store_true", help="Append generated documents to data_02/documents.json.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output = run_pipeline(args.baseline, args.catalog, args.output_dir, append_final=args.append_final)
    print(f"Wrote {len(output.documents)} domain RDAP document(s).")
