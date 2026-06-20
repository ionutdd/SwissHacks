#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SEVERITY_POINTS = {
    "critical": 85,
    "high": 70,
    "medium": 45,
    "low": 20,
}

CATEGORY_POINTS = {
    "risk": 18,
    "ownership_control": 16,
    "mixed": 8,
    "opportunity": 3,
}

SOURCE_POINTS = {
    "A": 12,
    "B": 8,
    "C": 4,
    "D": 0,
}

FIELD_POINTS = {
    "risk_rating": 10,
    "known_jurisdictions": 10,
    "subsidiaries": 9,
    "business_area": 8,
    "websites": 6,
    "known_products": 4,
    "entity_type": 4,
}

SIGNAL_POINTS = {
    "regulatory_scrutiny": 26,
    "jurisdiction_restriction": 25,
    "risk_rating_review": 22,
    "ownership_change": 20,
    "new_subsidiary": 17,
    "new_jurisdiction": 16,
    "treasury_policy_change": 16,
    "digital_asset_activity": 15,
    "business_activity_change": 14,
    "domain_registration": 14,
    "new_product": 2,
    "public_listing": 2,
    "commercial_opportunity": 1,
}

MATERIAL_KEYWORDS = {
    "sanction": 12,
    "ofac": 12,
    "north korea": 12,
    "dprk": 12,
    "russia": 9,
    "ransomware": 11,
    "darknet": 11,
    "aml": 9,
    "cftc": 9,
    "regulatory": 8,
    "blocked": 8,
    "jurisdiction": 6,
    "acquisition": 8,
    "subsidiary": 7,
    "bitcoin": 8,
    "treasury": 8,
    "country-code": 7,
    "domain": 6,
    "gambling": 8,
    "virtual currency exchange": 9,
    "ai chip": 9,
    "tpu": 9,
    "tensor processing unit": 9,
    "ai infrastructure": 8,
    "google cloud": 7,
    "anthropic": 7,
    "nvidia": 6,
}

MATERIAL_THRESHOLD = 100
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DEFAULT_NOTIFICATION_CUSTOMER_IDS = ("demo-003", "demo-004", "demo-008", "demo-009")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None
    try:
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def value_in_window(value: str | None, cutoff: datetime, now: datetime) -> bool:
    if not value:
        return False
    candidate = str(value).strip()
    if DATE_ONLY_RE.match(candidate):
        value_date = datetime.fromisoformat(candidate).date()
        return cutoff.date() <= value_date <= now.date()
    parsed = parse_datetime(candidate)
    return bool(parsed and cutoff <= parsed <= now)


def newest_alert_datetime(alert: dict[str, Any], include_operational_dates: bool = False) -> datetime | None:
    dates: list[datetime] = []
    for evidence in alert.get("evidence") or []:
        parsed = parse_datetime(evidence.get("published_at"))
        if parsed:
            dates.append(parsed)
        if include_operational_dates:
            parsed_collected = parse_datetime(evidence.get("collected_at"))
            if parsed_collected:
                dates.append(parsed_collected)
    if include_operational_dates:
        parsed_created = parse_datetime(alert.get("created_at"))
        if parsed_created:
            dates.append(parsed_created)
    return max(dates) if dates else None


def freshness_days(alert: dict[str, Any], now: datetime) -> int | None:
    newest = newest_alert_datetime(alert)
    if not newest:
        return None
    return max(0, (now - newest).days)


def freshness_points(alert: dict[str, Any], now: datetime) -> int:
    days = freshness_days(alert, now)
    if days is None:
        return -3
    if days <= 30:
        return 12
    if days <= 180:
        return 8
    if days <= 365:
        return 5
    if alert.get("category") == "risk" or alert.get("signal_type") in {"regulatory_scrutiny", "jurisdiction_restriction"}:
        return 4
    return -6


def alert_text(alert: dict[str, Any]) -> str:
    evidence_text = " ".join(
        " ".join(str(evidence.get(key) or "") for key in ("title", "excerpt", "source_name"))
        for evidence in alert.get("evidence") or []
    )
    return " ".join(
        [
            str(alert.get("title") or ""),
            str(alert.get("summary") or ""),
            str(alert.get("comparison_reason") or ""),
            evidence_text,
        ]
    ).lower()


def keyword_points(alert: dict[str, Any]) -> tuple[int, list[str]]:
    text = alert_text(alert)
    matched: list[str] = []
    points = 0
    for keyword, value in MATERIAL_KEYWORDS.items():
        if keyword in text:
            matched.append(keyword)
            points += value
    return min(points, 26), matched


def source_quality_points(alert: dict[str, Any]) -> int:
    qualities = [
        SOURCE_POINTS.get(str(evidence.get("source_quality") or "D"), 0)
        for evidence in alert.get("evidence") or []
    ]
    return max(qualities) if qualities else 0


def changed_field_points(alert: dict[str, Any]) -> int:
    return min(28, sum(FIELD_POINTS.get(field, 0) for field in alert.get("changed_fields") or []))


def primary_evidence(alert: dict[str, Any]) -> dict[str, Any]:
    evidence = alert.get("evidence") or []
    if not evidence:
        return {}
    return sorted(
        evidence,
        key=lambda item: (
            SOURCE_POINTS.get(str(item.get("source_quality") or "D"), 0),
            parse_datetime(item.get("published_at")) or parse_datetime(item.get("collected_at")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )[0]


def review_lane(alert: dict[str, Any]) -> str:
    signal_type = alert.get("signal_type")
    category = alert.get("category")
    severity = alert.get("severity")
    if category == "risk" or severity in {"critical", "high"}:
        return "Compliance review"
    if signal_type in {"ownership_change", "new_subsidiary", "new_jurisdiction", "domain_registration"}:
        return "KYC update"
    if category == "opportunity":
        return "RM opportunity"
    return "RM review"


def material_score(alert: dict[str, Any], now: datetime) -> tuple[int, list[str]]:
    keyword_score, keywords = keyword_points(alert)
    score = (
        SEVERITY_POINTS.get(alert.get("severity"), 0)
        + CATEGORY_POINTS.get(alert.get("category"), 0)
        + round(float(alert.get("confidence") or 0.0) * 20)
        + source_quality_points(alert)
        + changed_field_points(alert)
        + SIGNAL_POINTS.get(alert.get("signal_type"), 0)
        + freshness_points(alert, now)
        + keyword_score
    )

    reasons = [
        f"{alert.get('severity', 'unknown')} severity",
        f"{alert.get('category', 'unknown')} category",
        f"{round(float(alert.get('confidence') or 0.0) * 100)}% confidence",
    ]
    if alert.get("changed_fields"):
        reasons.append(f"KYC fields changed: {', '.join(alert['changed_fields'])}")
    if keywords:
        reasons.append(f"Material keywords: {', '.join(keywords[:5])}")
    days = freshness_days(alert, now)
    if days is not None:
        reasons.append(f"Newest published evidence is {days} day(s) old")
    return score, reasons


def has_source_url(alert: dict[str, Any]) -> bool:
    return any(evidence.get("source_url") for evidence in alert.get("evidence") or [])


def alert_in_refresh_window(
    alert: dict[str, Any],
    cutoff: datetime,
    now: datetime,
    include_undated_collected: bool,
    include_collected_evidence: bool = False,
) -> bool:
    for evidence in alert.get("evidence") or []:
        if value_in_window(evidence.get("published_at"), cutoff, now):
            return True
        if include_collected_evidence and value_in_window(evidence.get("collected_at"), cutoff, now):
            return True
        if include_undated_collected and not evidence.get("published_at") and value_in_window(evidence.get("collected_at"), cutoff, now):
            return True
    return False


def refresh_window_reason(
    alert: dict[str, Any],
    lookback_hours: int,
    include_undated_collected: bool,
    include_collected_evidence: bool = False,
) -> str:
    if include_collected_evidence:
        return f"No evidence was published or collected inside the {lookback_hours} hour notification window."
    if not any(evidence.get("published_at") for evidence in alert.get("evidence") or []):
        if include_undated_collected:
            return f"No dated or collected evidence fell inside the {lookback_hours} hour refresh window."
        return f"No dated evidence is attached, so it is not eligible for the strict {lookback_hours}-hour notification feed."
    return f"No evidence was published inside the strict {lookback_hours}-hour notification window."


def classify_alerts(
    alerts: list[dict[str, Any]],
    now: datetime,
    cutoff: datetime,
    lookback_hours: int,
    include_undated_collected: bool,
    include_collected_evidence: bool,
    notification_customer_ids: set[str] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[dict[str, Any]] = []
    for alert in alerts:
        score, reasons = material_score(alert, now)
        evidence = primary_evidence(alert)
        in_window = alert_in_refresh_window(alert, cutoff, now, include_undated_collected, include_collected_evidence)
        newest_published_at = newest_alert_datetime(alert)
        enriched = {
            **alert,
            "material_score": score,
            "material_reasons": reasons,
            "freshness_days": freshness_days(alert, now),
            "newest_published_at": newest_published_at.isoformat().replace("+00:00", "Z") if newest_published_at else None,
            "inside_refresh_window": in_window,
            "primary_source_url": evidence.get("source_url"),
            "primary_source_name": evidence.get("source_name") or evidence.get("title"),
            "review_lane": review_lane(alert),
        }
        scored.append(enriched)

    material_risk_by_customer = defaultdict(bool)
    for alert in scored:
        if alert.get("inside_refresh_window") and alert.get("category") == "risk" and alert["material_score"] >= MATERIAL_THRESHOLD:
            material_risk_by_customer[alert["customer_id"]] = True

    material: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []

    for alert in scored:
        suppression_reasons: list[str] = []
        confidence = float(alert.get("confidence") or 0.0)
        severity = alert.get("severity")
        category = alert.get("category")
        signal_type = alert.get("signal_type")

        if notification_customer_ids is not None and alert.get("customer_id") not in notification_customer_ids:
            suppression_reasons.append("Customer is outside the TLDR notification watchlist.")
        if not alert.get("inside_refresh_window"):
            suppression_reasons.append(
                refresh_window_reason(alert, lookback_hours, include_undated_collected, include_collected_evidence)
            )
        if not has_source_url(alert):
            suppression_reasons.append("No source URL is attached.")
        if confidence < 0.70 and severity not in {"critical", "high"}:
            suppression_reasons.append("Confidence below material refresh threshold.")
        if (
            category == "opportunity"
            and material_risk_by_customer[alert["customer_id"]]
            and alert["material_score"] < 120
        ):
            suppression_reasons.append("Opportunity is shadowed by a stronger risk alert for the same customer.")
        if (
            signal_type in {"commercial_opportunity", "new_product", "public_listing"}
            and category == "opportunity"
            and alert["material_score"] < 115
            and alert.get("detection_method") != "ai_validated"
        ):
            suppression_reasons.append("Generic opportunity or product update is below material threshold.")

        qualifies = (
            alert["material_score"] >= MATERIAL_THRESHOLD
            or (severity in {"critical", "high"} and confidence >= 0.65)
            or (category in {"risk", "ownership_control"} and confidence >= 0.72)
        )

        if qualifies and not suppression_reasons:
            material.append(alert)
        else:
            if not suppression_reasons and not qualifies:
                suppression_reasons.append("Material score below threshold and no high-priority override matched.")
            suppressed.append({**alert, "suppression_reasons": suppression_reasons})

    material.sort(
        key=lambda alert: (
            SEVERITY_POINTS.get(alert.get("severity"), 0),
            alert["material_score"],
            float(alert.get("confidence") or 0.0),
            -(alert.get("freshness_days") or 99999),
        ),
        reverse=True,
    )
    for index, alert in enumerate(material, start=1):
        alert["material_rank"] = index

    suppressed.sort(key=lambda alert: (alert["customer_id"], alert["alert_id"]))
    return material, suppressed


def summary_payload(
    alerts: list[dict[str, Any]],
    material: list[dict[str, Any]],
    suppressed: list[dict[str, Any]],
    generated_at: str,
    cutoff_at: str,
    lookback_hours: int,
    include_undated_collected: bool,
    include_collected_evidence: bool,
    notification_customer_ids: set[str] | None,
) -> dict[str, Any]:
    window_alerts = [alert for alert in [*material, *suppressed] if alert.get("inside_refresh_window")]
    if include_collected_evidence:
        freshness_policy = "published_at_or_collected_at"
    elif include_undated_collected:
        freshness_policy = "published_at_or_undated_collected_at"
    else:
        freshness_policy = "published_at_only"
    return {
        "generated_at": generated_at,
        "cutoff_at": cutoff_at,
        "lookback_hours": lookback_hours,
        "freshness_policy": freshness_policy,
        "notification_customer_ids": sorted(notification_customer_ids) if notification_customer_ids else "all",
        "total_alerts": len(alerts),
        "alerts_inside_refresh_window": len(window_alerts),
        "material_alerts": len(material),
        "suppressed_alerts": len(suppressed),
        "stale_or_undated_alerts": len(alerts) - len(window_alerts),
        "material_by_category": dict(Counter(alert["category"] for alert in material)),
        "material_by_severity": dict(Counter(alert["severity"] for alert in material)),
        "top_material_alert_ids": [alert["alert_id"] for alert in material[:5]],
        "suppression_reason_counts": dict(
            Counter(reason for alert in suppressed for reason in alert.get("suppression_reasons", []))
        ),
    }


def report_lines(summary: dict[str, Any], material: list[dict[str, Any]], suppressed: list[dict[str, Any]]) -> str:
    lines = [
        "# Material Signal Refresh Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Refresh window: last {summary['lookback_hours']} hour(s), cutoff {summary['cutoff_at']}",
        f"- Freshness policy: {summary['freshness_policy']}",
        f"- Notification customer scope: {summary['notification_customer_ids']}",
        f"- Total alerts reviewed: {summary['total_alerts']}",
        f"- Alerts inside refresh window: {summary['alerts_inside_refresh_window']}",
        f"- Material alerts: {summary['material_alerts']}",
        f"- Suppressed/noise alerts: {summary['suppressed_alerts']}",
        f"- Stale or undated alerts: {summary['stale_or_undated_alerts']}",
        "",
        "## TLDR Notifications",
        "",
    ]
    if not material:
        lines.append("- No material notifications were published inside the refresh window.")
    else:
        for alert in material[:10]:
            lines.append(
                f"{alert['material_rank']}. `{alert['alert_id']}` `{alert['customer_id']}` "
                f"{alert['severity']} / {alert['category']} / score {alert['material_score']}: {alert['title']}"
            )
    lines.extend(["", "## Suppression Summary", ""])
    if not summary["suppression_reason_counts"]:
        lines.append("- None.")
    else:
        for reason, count in sorted(summary["suppression_reason_counts"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {count}: {reason}")
    lines.extend(["", "## Dashboard Notes", ""])
    lines.append("- `material_alerts.json` is the top-bar TLDR notification feed for the current refresh window.")
    lines.append("- `alerts.json` remains the complete audit queue.")
    lines.append("- Suppressed alerts are retained in `noise_suppression.json` with reasons.")
    return "\n".join(lines) + "\n"


def run_command(command: list[str], label: str) -> None:
    print(f"Running {label}...")
    subprocess.run(command, check=True)


def build_material_outputs(args: argparse.Namespace) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.lookback_hours)
    generated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    cutoff_at = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    alerts = load_json(Path(args.alerts))
    material, suppressed = classify_alerts(
        alerts,
        now,
        cutoff,
        args.lookback_hours,
        args.include_undated_collected,
        args.include_collected_evidence,
        args.notification_customer_ids,
    )
    summary = summary_payload(
        alerts,
        material,
        suppressed,
        generated_at,
        cutoff_at,
        args.lookback_hours,
        args.include_undated_collected,
        args.include_collected_evidence,
        args.notification_customer_ids,
    )

    output_dir = Path(args.output_dir)
    write_json(output_dir / "material_alerts.json", material)
    write_json(output_dir / "noise_suppression.json", suppressed)
    write_json(output_dir / "refresh_summary.json", summary)
    (output_dir / "material_refresh_report.md").write_text(
        report_lines(summary, material, suppressed),
        encoding="utf-8",
        newline="\n",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-to-end refresh and material alert filtering.")
    parser.add_argument("--baseline", default="data_01/baseline_snapshots.json")
    parser.add_argument("--catalog", default="data_02/source_catalog.json")
    parser.add_argument("--documents", default="data_02/documents.json")
    parser.add_argument("--data02-dir", default="data_02")
    parser.add_argument("--data03-dir", default="data_03")
    parser.add_argument("--output-dir", default="data_06")
    parser.add_argument("--alerts", default="data_03/alerts.json")
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument(
        "--include-undated-collected",
        action="store_true",
        default=False,
        help="Allow undated evidence collected during the window.",
    )
    parser.add_argument(
        "--include-collected-evidence",
        action="store_true",
        default=False,
        help="Allow any evidence collected during the notification window, even if the source publication date is old.",
    )
    parser.add_argument(
        "--strict-published-only",
        action="store_true",
        help="Use only published_at for the notification window.",
    )
    parser.add_argument("--skip-collection", action="store_true")
    parser.add_argument("--skip-extraction", action="store_true")
    parser.add_argument(
        "--notification-customer-ids",
        default=",".join(DEFAULT_NOTIFICATION_CUSTOMER_IDS),
        help=(
            "Comma-separated customer IDs eligible for the TLDR notification feed. "
            "Defaults to Coinbase, GameStop, Kraken, and Alphabet demo entities."
        ),
    )
    parser.add_argument(
        "--all-notification-customers",
        action="store_true",
        help="Allow every customer to appear in the TLDR notification feed.",
    )
    parser.add_argument(
        "--ai-mode",
        choices=["off", "mock", "live"],
        default="off",
        help="Run Apertus evidence analysis before extraction. off is deterministic-only; mock makes no API calls.",
    )
    parser.add_argument("--ai-analysis-output", default="data_03/ai_evidence_analysis.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.lookback_hours <= 0:
        raise ValueError("--lookback-hours must be greater than zero")
    if args.all_notification_customers:
        args.notification_customer_ids = None
    else:
        args.notification_customer_ids = {
            customer_id.strip()
            for customer_id in str(args.notification_customer_ids).split(",")
            if customer_id.strip()
        }
    if args.strict_published_only:
        args.include_undated_collected = False
        args.include_collected_evidence = False
    if not args.skip_collection:
        run_command(
            [
                sys.executable,
                "scripts/collect_evidence.py",
                "--baseline",
                args.baseline,
                "--catalog",
                args.catalog,
                "--output-dir",
                args.data02_dir,
                "--lookback-hours",
                str(args.lookback_hours),
            ],
            "evidence collection",
        )

    if not args.skip_extraction and args.ai_mode != "off":
        run_command(
            [
                sys.executable,
                "scripts/ai_evidence_analysis.py",
                "--baselines",
                args.baseline,
                "--documents",
                args.documents,
                "--output",
                args.ai_analysis_output,
                "--mode",
                args.ai_mode,
            ],
            "AI evidence analysis",
        )

    if not args.skip_extraction:
        extraction_command = [
            sys.executable,
            "scripts/extract_signals.py",
            "--baselines",
            args.baseline,
            "--documents",
            args.documents,
            "--output-dir",
            args.data03_dir,
        ]
        if args.ai_mode != "off":
            extraction_command.extend(["--ai-analysis", args.ai_analysis_output])
        run_command(
            extraction_command,
            "signal extraction",
        )

    summary = build_material_outputs(args)
    print(
        "Material refresh complete: "
        f"{summary['material_alerts']} material alert(s), "
        f"{summary['suppressed_alerts']} suppressed alert(s), "
        f"{summary['total_alerts']} total reviewed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
