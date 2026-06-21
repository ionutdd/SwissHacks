from __future__ import annotations

import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from run_material_signal_refresh import (  # noqa: E402
    alert_in_refresh_window,
    freshness_days,
    has_source_url,
    material_score,
    newest_alert_datetime,
    primary_evidence,
    review_lane,
)


def evaluate_alerts(
    alerts: list[dict[str, Any]],
    preferences: dict[str, Any],
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cutoff = now - timedelta(hours=preferences["lookback_hours"])
    watchlist = set(preferences["watchlist_customer_ids"])
    categories = set(preferences["categories"])
    severities = set(preferences["severities"])
    signal_types = set(preferences.get("signal_types") or [])
    suppression_counts: Counter[str] = Counter()
    qualified: list[dict[str, Any]] = []

    for alert in alerts:
        score, reasons = material_score(alert, now)
        evidence = primary_evidence(alert)
        newest = newest_alert_datetime(alert)
        in_window = alert_in_refresh_window(
            alert,
            cutoff,
            now,
            preferences["include_undated_collected"],
            preferences["include_collected_evidence"],
        )
        failures: list[str] = []
        if alert.get("customer_id") not in watchlist:
            failures.append("outside_watchlist")
        if not in_window:
            failures.append("outside_refresh_window")
        if preferences["require_source_url"] and not has_source_url(alert):
            failures.append("missing_source_url")
        if float(alert.get("confidence") or 0) < preferences["minimum_confidence"]:
            failures.append("below_minimum_confidence")
        if score < preferences["minimum_material_score"]:
            failures.append("below_minimum_material_score")
        if alert.get("category") not in categories:
            failures.append("category_disabled")
        if alert.get("severity") not in severities:
            failures.append("severity_disabled")
        if signal_types and alert.get("signal_type") not in signal_types:
            failures.append("signal_type_disabled")

        if failures:
            suppression_counts.update(failures)
            continue

        qualified.append(
            {
                **alert,
                "material_score": score,
                "material_reasons": reasons,
                "freshness_days": freshness_days(alert, now),
                "newest_published_at": newest.isoformat().replace("+00:00", "Z") if newest else None,
                "inside_refresh_window": in_window,
                "primary_source_url": evidence.get("source_url"),
                "primary_source_name": evidence.get("source_name") or evidence.get("title"),
                "review_lane": review_lane(alert),
            }
        )

    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    qualified.sort(
        key=lambda alert: (
            severity_rank.get(alert.get("severity"), 0),
            alert["material_score"],
            float(alert.get("confidence") or 0),
        ),
        reverse=True,
    )
    for rank, alert in enumerate(qualified, start=1):
        alert["material_rank"] = rank

    summary = {
        "generated_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "cutoff_at": cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "lookback_hours": preferences["lookback_hours"],
        "total_alerts": len(alerts),
        "material_alerts": len(qualified),
        "suppressed_alerts": len(alerts) - len(qualified),
        "suppression_reason_counts": dict(suppression_counts),
    }
    return qualified, summary
