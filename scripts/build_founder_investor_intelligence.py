#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WATCHLIST_CUSTOMERS = {"demo-001", "demo-002", "demo-003", "demo-004", "demo-005", "demo-008", "demo-009"}


def load_json(path: str | Path, default: Any = None) -> Any:
    target = Path(path)
    if not target.exists():
        return default
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def clean_spaces(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def document_text(document: dict[str, Any]) -> str:
    return clean_spaces(" ".join(str(document.get(key) or "") for key in ("title", "evidence_excerpt", "raw_text")))


def first_sentence_with(text: str, terms: list[str], fallback: str = "") -> str:
    sentences = [clean_spaces(item) for item in re.split(r"(?<=[.!?])\s+", text) if clean_spaces(item)]
    for sentence in sentences:
        lower = sentence.lower()
        if any(term in lower for term in terms):
            return sentence[:450]
    return clean_spaces(fallback or text)[:450]


def source_payload(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": document.get("source_name"),
        "source_url": document.get("source_url"),
        "source_quality": document.get("source_quality"),
        "published_at": document.get("published_at"),
        "document_id": document.get("document_id"),
    }


def make_record(
    *,
    customer_id: str,
    event_type: str,
    entity_name: str,
    role_type: str,
    capital_role: str,
    advisory_vs_equity: str,
    confidence: float,
    rm_impact: str,
    rm_impact_reason: str,
    recommended_action: str,
    source: dict[str, Any],
    amount: str | None = None,
    valuation: str | None = None,
    ownership_percent: str | None = None,
    ownership_basis: str | None = None,
    evidence_quote: str | None = None,
    needs_verification: bool = True,
) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "event_type": event_type,
        "entity_name": clean_spaces(entity_name),
        "role_type": role_type,
        "capital_role": capital_role,
        "amount": amount,
        "valuation": valuation,
        "ownership_percent": ownership_percent,
        "ownership_basis": ownership_basis or "Not disclosed in collected public evidence.",
        "advisory_vs_equity": advisory_vs_equity,
        "confidence": round(float(confidence), 2),
        "rm_impact": rm_impact,
        "rm_impact_reason": clean_spaces(rm_impact_reason),
        "recommended_action": clean_spaces(recommended_action),
        "needs_verification": needs_verification,
        "evidence_quote": clean_spaces(evidence_quote),
        **source,
    }


def baseline_records(baseline: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source = {
        "source_name": "KYC baseline",
        "source_url": None,
        "source_quality": "internal",
        "published_at": baseline.get("last_reviewed_at"),
        "document_id": None,
    }
    for investor in baseline.get("investors") or []:
        records.append(
            make_record(
                customer_id=baseline["customer_id"],
                event_type="baseline_investor",
                entity_name=investor,
                role_type="investor",
                capital_role="unknown",
                advisory_vs_equity="unknown",
                confidence=0.55,
                rm_impact="unknown",
                rm_impact_reason="Investor was present in the last baseline, but ownership percentage and investor rights are not captured.",
                recommended_action="Request updated investor schedule and distinguish passive equity, advisory role, board rights, and control rights.",
                source=source,
                evidence_quote=f"Baseline investor: {investor}",
                needs_verification=True,
            )
        )
    for executive in baseline.get("executives") or []:
        records.append(
            make_record(
                customer_id=baseline["customer_id"],
                event_type="baseline_control_person",
                entity_name=executive,
                role_type="executive_or_control_person",
                capital_role="management_control",
                advisory_vs_equity="management",
                confidence=0.55,
                rm_impact="neutral",
                rm_impact_reason="Executive/control person is in the KYC baseline; equity ownership is not captured here.",
                recommended_action="Screen control persons and request ownership percentage if they hold founder, board, or voting-control rights.",
                source=source,
                evidence_quote=f"Baseline executive/control person: {executive}",
                needs_verification=True,
            )
        )
    return records


def document_records(document: dict[str, Any]) -> list[dict[str, Any]]:
    text = document_text(document)
    lower = text.lower()
    source = source_payload(document)
    customer_id = document["customer_id"]
    records: list[dict[str, Any]] = []

    if "robinhood" in lower and "bitstamp" in lower and "acquisition" in lower:
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="acquisition_control_change",
                entity_name="Bitstamp Ltd.",
                role_type="acquisition_target",
                capital_role="acquisition",
                advisory_vs_equity="equity_control",
                amount=None,
                ownership_percent=None,
                ownership_basis="Official announcement confirms acquisition close; consideration and final ownership percentage are not in the collected excerpt.",
                confidence=0.88,
                rm_impact="positive",
                rm_impact_reason="Adds institutional crypto exchange capabilities and new licensed entities, creating custody/trading opportunities and ownership-control KYC work.",
                recommended_action="Request post-close corporate structure, Bitstamp legal-entity ownership chart, and whether consideration was cash, equity, or mixed.",
                source=source,
                evidence_quote=first_sentence_with(text, ["acquisition", "bitstamp"], document.get("evidence_excerpt")),
            )
        )

    if "kraken" in lower and "ninjatrader" in lower and "$1.5 billion" in lower:
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="acquisition_control_change",
                entity_name="NinjaTrader",
                role_type="acquisition_target",
                capital_role="acquisition",
                advisory_vs_equity="equity_control",
                amount="$1.5 billion",
                ownership_percent=None,
                ownership_basis="Official source discloses acquisition price, not seller ownership or final cap-table effects.",
                confidence=0.91,
                rm_impact="positive",
                rm_impact_reason="Material strategic M&A expands Kraken into U.S. retail futures and multi-asset trading, increasing financing, treasury, and regulatory needs.",
                recommended_action="Ask for acquisition funding source, seller rollover equity if any, post-close subsidiary structure, and regulatory approvals.",
                source=source,
                evidence_quote=first_sentence_with(text, ["$1.5 billion", "ninjatrader"], document.get("evidence_excerpt")),
            )
        )

    if "xstocks" in lower and "do not have ownership" in lower:
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="synthetic_exposure_no_equity",
                entity_name="xStocks holders",
                role_type="product_investor",
                capital_role="synthetic_exposure",
                advisory_vs_equity="not_equity",
                ownership_percent="0% underlying equity ownership",
                ownership_basis="Product disclosure says holders do not own underlying shares.",
                confidence=0.86,
                rm_impact="mixed",
                rm_impact_reason="Clarifies that product users get economic exposure rather than shareholder control; still relevant for securities, suitability, and custody risk.",
                recommended_action="Do not treat xStocks holders as shareholders of underlying companies; review issuer, distributor, custody, and client-suitability obligations.",
                source=source,
                evidence_quote=first_sentence_with(text, ["do not have ownership", "underlying stock"], document.get("evidence_excerpt")),
                needs_verification=False,
            )
        )

    if customer_id == "demo-003" and "future debt and equity issuances" in lower:
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="potential_financing_source",
                entity_name="Future debt and equity investors",
                role_type="financing_source",
                capital_role="debt_or_equity",
                advisory_vs_equity="financing",
                ownership_basis="Filing permits future debt/equity financing for Bitcoin purchases, but no named investor or stake is disclosed.",
                confidence=0.78,
                rm_impact="mixed",
                rm_impact_reason="Future issuances could dilute shareholders or increase leverage while funding digital-asset treasury exposure.",
                recommended_action="Monitor financing announcements, noteholder identities if public, dilution, covenants, and custody banking needs.",
                source=source,
                evidence_quote=first_sentence_with(text, ["future debt and equity issuances"], document.get("evidence_excerpt")),
            )
        )

    if customer_id == "demo-008" and "coinbase.au" in lower and "registrant name coinbase" in lower:
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="domain_control_signal",
                entity_name="Coinbase, Inc.",
                role_type="registrant_or_trademark_owner",
                capital_role="control_evidence",
                advisory_vs_equity="not_equity",
                ownership_basis="RDAP links domain eligibility to Coinbase identity data; it is not equity ownership evidence.",
                confidence=0.86,
                rm_impact="mixed",
                rm_impact_reason="Country-code domain control may indicate market-entry preparation, but it is not proof of active operations or beneficial ownership.",
                recommended_action="Ask whether the domain is defensive, pre-launch, or tied to Australian operating activity; do not treat as cap-table evidence.",
                source=source,
                evidence_quote=first_sentence_with(text, ["registrant name", "coinbase.au"], document.get("evidence_excerpt")),
                needs_verification=True,
            )
        )

    if customer_id == "demo-005" and document.get("source_type") == "investor_relations":
        records.append(
            make_record(
                customer_id=customer_id,
                event_type="public_company_investor_relations",
                entity_name="Public equity investors",
                role_type="public_shareholders",
                capital_role="public_equity",
                advisory_vs_equity="equity",
                ownership_basis="Investor-relations page confirms public-company monitoring source, but does not disclose principal shareholders in the collected text.",
                confidence=0.62,
                rm_impact="positive",
                rm_impact_reason="Public-company status improves filing availability and enables systematic shareholder/proxy monitoring.",
                recommended_action="Collect latest S-1/424B4/proxy principal-stockholder table to identify founder and institutional ownership percentages.",
                source=source,
                evidence_quote=first_sentence_with(text, ["investor relations", "global financial technology"], document.get("evidence_excerpt")),
            )
        )

    return records


def curated_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in items:
        source = {
            "source_name": item.get("source_name"),
            "source_url": item.get("source_url"),
            "source_quality": item.get("source_quality", "B"),
            "published_at": item.get("published_at"),
            "document_id": item.get("document_id"),
        }
        records.append(
            make_record(
                customer_id=item["customer_id"],
                event_type=item.get("event_type", "investor_news"),
                entity_name=item.get("entity_name", "Unknown investor"),
                role_type=item.get("role_type", "investor"),
                capital_role=item.get("capital_role", "unknown"),
                advisory_vs_equity=item.get("advisory_vs_equity", "unknown"),
                amount=item.get("amount"),
                valuation=item.get("valuation"),
                ownership_percent=item.get("ownership_percent"),
                ownership_basis=item.get("ownership_basis"),
                confidence=item.get("confidence", 0.7),
                rm_impact=item.get("rm_impact", "unknown"),
                rm_impact_reason=item.get("rm_impact_reason", ""),
                recommended_action=item.get("recommended_action", ""),
                source=source,
                evidence_quote=item.get("evidence_quote", ""),
                needs_verification=item.get("needs_verification", True),
            )
        )
    return records


def impact_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    impact_counts = Counter(record["rm_impact"] for record in records)
    equity_records = [record for record in records if record["advisory_vs_equity"] in {"equity", "equity_control"}]
    unknown_stakes = [
        record
        for record in records
        if record["advisory_vs_equity"] in {"equity", "equity_control", "management"}
        and not record.get("ownership_percent")
    ]
    return {
        "record_count": len(records),
        "impact_counts": dict(impact_counts),
        "equity_or_control_record_count": len(equity_records),
        "ownership_percent_unknown_count": len(unknown_stakes),
        "top_rm_questions": rm_questions(records),
    }


def rm_questions(records: list[dict[str, Any]]) -> list[str]:
    questions = []
    if any(record["advisory_vs_equity"] in {"equity", "equity_control", "management"} for record in records):
        questions.append("Who owns what percentage today, and are any stakes voting/control rights rather than passive economics?")
    if any(record["advisory_vs_equity"] == "unknown" for record in records):
        questions.append("Which named investors are equity holders, advisors, board observers, or purely commercial partners?")
    if any(record["event_type"] in {"strategic_investment", "funding_round_backers"} for record in records):
        questions.append("Did the round add board seats, veto rights, side letters, token warrants, or information rights?")
    if any(record["rm_impact"] == "mixed" for record in records):
        questions.append("Does the investor/advisor profile create reputational, PEP, sanctions, or regulatory sensitivity?")
    if not questions:
        questions.append("Request latest cap table or beneficial ownership schedule at next KYC refresh.")
    return questions[:4]


def build_payload(baselines: list[dict[str, Any]], documents: list[dict[str, Any]], curated: list[dict[str, Any]]) -> dict[str, Any]:
    generated_at = now_utc()
    baselines_by_customer = {baseline["customer_id"]: baseline for baseline in baselines}
    records: list[dict[str, Any]] = []

    for baseline in baselines:
        if baseline["customer_id"] in WATCHLIST_CUSTOMERS:
            records.extend(baseline_records(baseline))

    for document in documents:
        if document.get("customer_id") in WATCHLIST_CUSTOMERS:
            records.extend(document_records(document))

    records.extend(curated_records(curated))

    for index, record in enumerate(records, start=1):
        record["investor_record_id"] = f"fi-{index:03d}"

    customer_payloads = []
    for customer_id in sorted(WATCHLIST_CUSTOMERS):
        baseline = baselines_by_customer.get(customer_id, {})
        customer_records = [record for record in records if record["customer_id"] == customer_id]
        customer_payloads.append(
            {
                "customer_id": customer_id,
                "legal_name": baseline.get("legal_name", customer_id),
                "baseline_investors": baseline.get("investors", []),
                "baseline_executives": baseline.get("executives", []),
                "records": customer_records,
                "summary": impact_summary(customer_records),
            }
        )

    all_impact = Counter(record["rm_impact"] for record in records)
    return {
        "generated_at": generated_at,
        "scope": "Founder, investor, funding-round, advisory-vs-equity, and ownership-control intelligence.",
        "method": [
            "Extracted deterministic investor/control facts from collected evidence documents.",
            "Merged curated public-source notes for investor/funding cases not yet present in data_02 documents.",
            "Explicitly marks ownership percentages as unknown unless a source states them.",
        ],
        "summary": {
            "customers_covered": len(customer_payloads),
            "records_total": len(records),
            "impact_counts": dict(all_impact),
            "records_needing_ownership_verification": sum(1 for record in records if record.get("needs_verification")),
        },
        "customers": customer_payloads,
    }


def report(payload: dict[str, Any]) -> str:
    lines = [
        "# Founder And Investor Intelligence",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Records: {payload['summary']['records_total']}",
        f"- Records needing ownership verification: {payload['summary']['records_needing_ownership_verification']}",
        "",
        "## Customer Summaries",
        "",
    ]
    for customer in payload["customers"]:
        lines.extend(
            [
                f"### {customer['legal_name']} (`{customer['customer_id']}`)",
                "",
                f"- Records: {customer['summary']['record_count']}",
                f"- Equity/control records: {customer['summary']['equity_or_control_record_count']}",
                f"- Unknown ownership percentages: {customer['summary']['ownership_percent_unknown_count']}",
                "- RM questions:",
            ]
        )
        for question in customer["summary"]["top_rm_questions"]:
            lines.append(f"  - {question}")
        for record in customer["records"][:5]:
            stake = record.get("ownership_percent") or "not disclosed"
            lines.append(
                f"- `{record['investor_record_id']}` {record['entity_name']} | {record['role_type']} | "
                f"{record['advisory_vs_equity']} | stake {stake} | impact {record['rm_impact']}"
            )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build founder/investor/cap-table intelligence for RM review.")
    parser.add_argument("--baselines", default="data_01/baseline_snapshots.json")
    parser.add_argument("--documents", default="data_02/documents.json")
    parser.add_argument("--curated-sources", default="data_08/curated_founder_investor_sources.json")
    parser.add_argument("--output-dir", default="data_08")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baselines = load_json(args.baselines, [])
    documents = load_json(args.documents, [])
    curated = load_json(args.curated_sources, [])
    payload = build_payload(baselines, documents, curated)
    output_dir = Path(args.output_dir)
    write_json(output_dir / "founder_investor_intelligence.json", payload)
    (output_dir / "founder_investor_report.md").write_text(report(payload), encoding="utf-8", newline="\n")
    print(
        "Founder/investor intelligence complete: "
        f"{payload['summary']['records_total']} records across {payload['summary']['customers_covered']} customers."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
