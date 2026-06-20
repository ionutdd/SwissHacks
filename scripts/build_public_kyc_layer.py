#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def unique_clean(values: list[Any]) -> list[str]:
    seen = set()
    rows = []
    for value in values:
        text = str(value or "").strip()
        if not text or text.lower() in seen:
            continue
        seen.add(text.lower())
        rows.append(text)
    return rows


def quality_score(source_quality: str | None) -> int:
    return {"A": 4, "B": 3, "C": 2, "internal": 1}.get(str(source_quality or ""), 0)


def source_coverage(source_notes: list[dict[str, Any]]) -> dict[str, Any]:
    source_types = sorted({source.get("source_type") for source in source_notes if source.get("source_type")})
    quality_counts = Counter(source.get("source_quality", "unknown") for source in source_notes)
    supported_fields = sorted(
        {
            field
            for source in source_notes
            for field in source.get("fields_supported", [])
            if field
        }
    )
    return {
        "source_count": len(source_notes),
        "source_types": source_types,
        "quality_counts": dict(quality_counts),
        "supported_fields": supported_fields,
        "best_source_quality": max((source.get("source_quality") for source in source_notes), key=quality_score, default=None),
    }


def completeness(profile: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "identity": bool(profile.get("identity")),
        "business_model": bool(profile.get("business_model")),
        "products_services": bool(profile.get("products_services")),
        "scale_indicators": bool(profile.get("scale_indicators")),
        "regulatory_and_licensing": bool(profile.get("regulatory_and_licensing")),
        "sanctions_adverse_media": bool(profile.get("sanctions_adverse_media")),
        "banking_relevance": bool(profile.get("banking_relevance")),
        "open_kyc_questions": bool(profile.get("open_kyc_questions")),
        "source_notes": bool(profile.get("source_notes")),
    }
    passed = sum(1 for value in checks.values() if value)
    return {
        "score": round(passed / len(checks), 2),
        "passed_checks": [key for key, value in checks.items() if value],
        "missing_checks": [key for key, value in checks.items() if not value],
    }


def alert_context(alerts: list[dict[str, Any]], customer_id: str) -> dict[str, Any]:
    customer_alerts = [alert for alert in alerts if alert.get("customer_id") == customer_id]
    categories = Counter(alert.get("category", "unknown") for alert in customer_alerts)
    signal_types = Counter(alert.get("signal_type", "unknown") for alert in customer_alerts)
    material = [alert for alert in customer_alerts if alert.get("material_score")]
    top_alerts = sorted(
        material or customer_alerts,
        key=lambda item: (
            item.get("material_score", 0),
            item.get("confidence", 0),
        ),
        reverse=True,
    )[:5]
    return {
        "alert_count": len(customer_alerts),
        "category_counts": dict(categories),
        "top_signal_types": [signal_type for signal_type, _count in signal_types.most_common(6)],
        "top_alerts": [
            {
                "alert_id": alert.get("alert_id"),
                "title": alert.get("title"),
                "signal_type": alert.get("signal_type"),
                "severity": alert.get("severity"),
                "material_score": alert.get("material_score"),
            }
            for alert in top_alerts
        ],
    }


def investor_context(founder_investor: dict[str, Any], customer_id: str) -> dict[str, Any]:
    customer = next((item for item in founder_investor.get("customers", []) if item.get("customer_id") == customer_id), None)
    if not customer:
        return {
            "records_available": 0,
            "equity_or_control_records": 0,
            "ownership_percent_unknown_count": 0,
            "top_records": [],
        }
    records = customer.get("records", [])
    top_records = sorted(
        records,
        key=lambda record: (
            record.get("advisory_vs_equity") in {"equity_control", "equity"},
            bool(record.get("ownership_percent")),
            record.get("confidence", 0),
        ),
        reverse=True,
    )[:4]
    return {
        "records_available": len(records),
        "equity_or_control_records": customer.get("summary", {}).get("equity_or_control_record_count", 0),
        "ownership_percent_unknown_count": customer.get("summary", {}).get("ownership_percent_unknown_count", 0),
        "top_records": [
            {
                "investor_record_id": record.get("investor_record_id"),
                "entity_name": record.get("entity_name"),
                "role_type": record.get("role_type"),
                "advisory_vs_equity": record.get("advisory_vs_equity"),
                "ownership_percent": record.get("ownership_percent"),
                "needs_verification": record.get("needs_verification"),
            }
            for record in top_records
        ],
    }


def baseline_context(baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "last_reviewed_at": baseline.get("last_reviewed_at"),
        "baseline_risk_rating": baseline.get("risk_rating"),
        "baseline_business_area": baseline.get("business_area", []),
        "baseline_known_jurisdictions": baseline.get("known_jurisdictions", []),
        "baseline_products": baseline.get("known_products", []),
        "baseline_executives": baseline.get("executives", []),
        "baseline_investors": baseline.get("investors", []),
        "baseline_subsidiaries": baseline.get("subsidiaries", []),
        "amina_relevance": baseline.get("amina_relevance", []),
    }


def build_customer_profile(
    profile: dict[str, Any],
    baseline: dict[str, Any],
    alerts: list[dict[str, Any]],
    founder_investor: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    source_notes = profile.get("source_notes", [])
    identity = profile.get("identity", {})
    merged_websites = unique_clean(as_list(identity.get("websites")) + baseline.get("websites", []))
    identity = {
        "legal_name": identity.get("legal_name") or baseline.get("legal_name"),
        "aliases": unique_clean(as_list(identity.get("trading_names")) + baseline.get("aliases", [])),
        "entity_type": identity.get("entity_type") or baseline.get("entity_type"),
        "public_listing": identity.get("public_listing"),
        "headquarters": identity.get("headquarters"),
        "primary_domicile": identity.get("primary_domicile") or baseline.get("domicile"),
        "operating_regions": unique_clean(as_list(identity.get("operating_regions")) + baseline.get("known_jurisdictions", [])),
        "websites": merged_websites,
    }

    return {
        "kyc_profile_id": f"public-kyc-{profile['customer_id']}",
        "customer_id": profile["customer_id"],
        "legal_name": baseline.get("legal_name") or identity.get("legal_name"),
        "generated_at": generated_at,
        "profile_type": "public_source_kyc_enrichment",
        "important_notice": (
            "Public-source KYC enrichment for RM review. It does not replace customer-provided KYC, "
            "beneficial ownership documentation, sanctions screening, or compliance approval."
        ),
        "kyc_status": profile.get("kyc_status"),
        "identity": identity,
        "public_kyc_risk_rating": profile.get("public_kyc_risk_rating"),
        "risk_rationale": profile.get("risk_rationale", []),
        "business_model": profile.get("business_model", []),
        "products_services": profile.get("products_services", []),
        "scale_indicators": profile.get("scale_indicators", []),
        "regulatory_and_licensing": profile.get("regulatory_and_licensing", []),
        "sanctions_adverse_media": profile.get("sanctions_adverse_media", []),
        "banking_relevance": profile.get("banking_relevance", []),
        "open_kyc_questions": profile.get("open_kyc_questions", []),
        "baseline_context": baseline_context(baseline),
        "founder_investor_context": investor_context(founder_investor, profile["customer_id"]),
        "alert_context": alert_context(alerts, profile["customer_id"]),
        "source_coverage": source_coverage(source_notes),
        "completeness": completeness(profile),
        "source_notes": source_notes,
        "recommended_next_steps": recommended_next_steps(profile),
    }


def recommended_next_steps(profile: dict[str, Any]) -> list[str]:
    rating = profile.get("public_kyc_risk_rating", "")
    steps = [
        "Verify legal entity, registration number, and address against registry or latest filing.",
        "Request current beneficial ownership/control-person schedule before changing the internal KYC profile.",
    ]
    if rating in {"critical", "high"}:
        steps.insert(0, "Route to enhanced due diligence before onboarding, renewal, or relationship expansion.")
    if "prohibited" in str(profile.get("kyc_status", "")):
        steps.insert(0, "Check sanctions policy for exit, reject, or freeze instructions before any relationship action.")
    if any("stablecoin" in item.lower() or "crypto" in item.lower() for item in profile.get("products_services", [])):
        steps.append("Document blockchain analytics, custody, travel-rule, and sanctions-screening controls.")
    if profile.get("open_kyc_questions"):
        steps.append("Use the open KYC questions in the RM call brief.")
    return steps


def build_payload(
    baselines: list[dict[str, Any]],
    curated_profiles: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    founder_investor: dict[str, Any],
) -> dict[str, Any]:
    generated_at = now_utc()
    baselines_by_id = {baseline["customer_id"]: baseline for baseline in baselines}
    customers = [
        build_customer_profile(
            profile,
            baselines_by_id.get(profile["customer_id"], {}),
            alerts,
            founder_investor,
            generated_at,
        )
        for profile in curated_profiles
    ]
    risk_counts = Counter(customer.get("public_kyc_risk_rating", "unknown") for customer in customers)
    status_counts = Counter(customer.get("kyc_status", "unknown") for customer in customers)
    source_count = sum(customer.get("source_coverage", {}).get("source_count", 0) for customer in customers)
    return {
        "generated_at": generated_at,
        "scope": "Public-source KYC enrichment for all demo customers.",
        "method": [
            "Starts from the existing baseline_snapshots customer set.",
            "Adds curated online public-source KYC facts and source links.",
            "Cross-references founder/investor context when data_08 exists.",
            "Cross-references current alerts to connect KYC profile to monitoring output.",
            "Marks customer confirmation and compliance review as required before internal KYC changes."
        ],
        "summary": {
            "customers_covered": len(customers),
            "public_source_count": source_count,
            "risk_rating_counts": dict(risk_counts),
            "kyc_status_counts": dict(status_counts),
            "average_completeness": round(
                sum(customer["completeness"]["score"] for customer in customers) / len(customers),
                2,
            ) if customers else 0,
        },
        "customers": customers,
    }


def report(payload: dict[str, Any]) -> str:
    lines = [
        "# Public Source KYC Enrichment",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Customers covered: {payload['summary']['customers_covered']}",
        f"- Public sources: {payload['summary']['public_source_count']}",
        f"- Average completeness: {payload['summary']['average_completeness']}",
        "",
        "## Customer Summaries",
        "",
    ]
    for customer in payload["customers"]:
        identity = customer.get("identity", {})
        lines.extend(
            [
                f"### {customer['legal_name']} (`{customer['customer_id']}`)",
                "",
                f"- Public KYC risk: {customer.get('public_kyc_risk_rating')}",
                f"- Status: {customer.get('kyc_status')}",
                f"- Listing: {identity.get('public_listing') or 'private / not listed'}",
                f"- Domicile: {identity.get('primary_domicile') or 'unknown'}",
                f"- Source count: {customer['source_coverage']['source_count']}",
                f"- Completeness: {customer['completeness']['score']}",
                "- Top RM questions:",
            ]
        )
        for question in customer.get("open_kyc_questions", [])[:4]:
            lines.append(f"  - {question}")
        lines.append("- Public source links:")
        for source in customer.get("source_notes", [])[:5]:
            lines.append(f"  - {source['source_name']}: {source['source_url']}")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build public-source KYC enrichment profiles.")
    parser.add_argument("--baselines", default="data_01/baseline_snapshots.json")
    parser.add_argument("--curated-kyc", default="data_09/curated_public_kyc_sources.json")
    parser.add_argument("--alerts", default="data_03/alerts.json")
    parser.add_argument("--founder-investor", default="data_08/founder_investor_intelligence.json")
    parser.add_argument("--output-dir", default="data_09")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        load_json(args.baselines, []),
        load_json(args.curated_kyc, []),
        load_json(args.alerts, []),
        load_json(args.founder_investor, {"customers": []}),
    )
    output_dir = Path(args.output_dir)
    write_json(output_dir / "public_kyc_profiles.json", payload)
    (output_dir / "public_kyc_report.md").write_text(report(payload), encoding="utf-8", newline="\n")
    print(
        "Public KYC layer complete: "
        f"{payload['summary']['customers_covered']} customers, "
        f"{payload['summary']['public_source_count']} public source(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
