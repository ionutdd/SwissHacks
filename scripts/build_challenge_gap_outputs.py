#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_DIR = Path("data_07")


def load_json(path: str | Path, fallback: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def customer_activity_baselines() -> list[dict[str, Any]]:
    return [
        {
            "customer_id": "demo-002",
            "expected_monthly_volume_chf": 2_000_000,
            "expected_transaction_count_monthly": 18,
            "expected_counterparty_regions": ["United States", "European Union"],
            "expected_products": ["corporate account", "USDC settlement monitoring"],
            "expected_activity_description": "Prediction-market operating flows with limited fiat treasury movement.",
            "allowed_risk_band": "high",
            "last_kyc_refresh_at": "2024-10-01",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 500_000,
                "new_region_monthly_count": 2,
                "volume_spike_multiplier": 2.0,
            },
        },
        {
            "customer_id": "demo-003",
            "expected_monthly_volume_chf": 12_000_000,
            "expected_transaction_count_monthly": 55,
            "expected_counterparty_regions": ["United States", "Canada", "European Union"],
            "expected_products": ["corporate account", "FX", "cash management"],
            "expected_activity_description": "Retail treasury, vendor payments, and inventory-related flows.",
            "allowed_risk_band": "low_to_medium",
            "last_kyc_refresh_at": "2025-02-28",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 3_000_000,
                "new_region_monthly_count": 2,
                "volume_spike_multiplier": 2.5,
            },
        },
        {
            "customer_id": "demo-006",
            "expected_monthly_volume_chf": 500_000,
            "expected_transaction_count_monthly": 8,
            "expected_counterparty_regions": ["Estonia"],
            "expected_products": ["VASP relationship monitoring"],
            "expected_activity_description": "Legacy low-volume exchange monitoring profile pending enhanced due diligence.",
            "allowed_risk_band": "medium_to_high",
            "last_kyc_refresh_at": "2022-02-01",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 100_000,
                "new_region_monthly_count": 1,
                "volume_spike_multiplier": 1.5,
            },
        },
        {
            "customer_id": "demo-007",
            "expected_monthly_volume_chf": 25_000_000,
            "expected_transaction_count_monthly": 120,
            "expected_counterparty_regions": ["United Kingdom", "Singapore", "European Union"],
            "expected_products": ["corporate account", "trade finance", "FX"],
            "expected_activity_description": "Large multinational operating and trade-finance flows.",
            "allowed_risk_band": "medium",
            "last_kyc_refresh_at": "2023-01-31",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 8_000_000,
                "new_region_monthly_count": 2,
                "volume_spike_multiplier": 2.0,
            },
        },
        {
            "customer_id": "demo-008",
            "expected_monthly_volume_chf": 10_000_000,
            "expected_transaction_count_monthly": 65,
            "expected_counterparty_regions": ["United States", "European Union", "United Kingdom", "Singapore"],
            "expected_products": ["crypto exchange monitoring", "custody", "FX"],
            "expected_activity_description": "Crypto exchange operating, custody, and institutional settlement flows.",
            "allowed_risk_band": "medium_to_high",
            "last_kyc_refresh_at": "2025-12-31",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 2_500_000,
                "new_region_monthly_count": 2,
                "volume_spike_multiplier": 2.0,
            },
        },
        {
            "customer_id": "demo-009",
            "expected_monthly_volume_chf": 15_000_000,
            "expected_transaction_count_monthly": 80,
            "expected_counterparty_regions": ["United States", "European Union", "United Kingdom"],
            "expected_products": ["corporate banking", "FX", "treasury"],
            "expected_activity_description": "Large-cap technology treasury and operating flows.",
            "allowed_risk_band": "low_to_medium",
            "last_kyc_refresh_at": "2026-06-01",
            "transaction_monitoring_thresholds": {
                "single_payment_chf": 5_000_000,
                "new_region_monthly_count": 3,
                "volume_spike_multiplier": 2.5,
            },
        },
    ]


def simulated_transactions() -> list[dict[str, Any]]:
    rows = [
        ("demo-009", "2026-06-19T10:12:00Z", 4_800_000, "outbound", "Anthropic PBC", "United States", "SWIFT", "AI infrastructure partnership settlement", ["alert-046", "alert-047"]),
        ("demo-009", "2026-06-19T11:44:00Z", 6_200_000, "outbound", "Blackstone Data Center Partners", "United States", "SWIFT", "Data-center capacity prepayment", ["alert-046", "alert-048"]),
        ("demo-009", "2026-06-19T14:05:00Z", 3_100_000, "outbound", "Cloud TPU Hardware Vendor", "Taiwan", "SWIFT", "AI chip supply-chain payment", ["alert-046", "alert-048"]),
        ("demo-009", "2026-06-20T07:15:00Z", 2_400_000, "inbound", "Enterprise Cloud Customer", "United Kingdom", "SWIFT", "Cloud-services receivable", ["alert-047"]),
        ("demo-003", "2025-05-28T15:22:00Z", 2_750_000, "outbound", "Digital Asset Custody Provider", "United States", "WIRE", "Custody onboarding reserve transfer", ["alert-010", "alert-014"]),
        ("demo-003", "2025-05-29T09:20:00Z", 1_950_000, "outbound", "Crypto Treasury Execution Desk", "United States", "WIRE", "Bitcoin treasury execution support", ["alert-009", "alert-015"]),
        ("demo-003", "2025-06-03T16:40:00Z", 980_000, "inbound", "Retail Operations Account", "Canada", "SWIFT", "Inventory treasury sweep", []),
        ("demo-003", "2025-06-10T12:11:00Z", 1_250_000, "outbound", "Collateral Management Agent", "United States", "WIRE", "Digital asset collateral operations", ["alert-013"]),
        ("demo-008", "2026-02-09T08:31:00Z", 750_000, "outbound", "AU Launch Vendor Pty Ltd", "Australia", "SWIFT", "Country-domain launch support", ["alert-043", "alert-044"]),
        ("demo-008", "2026-02-10T10:35:00Z", 520_000, "outbound", "Australian Compliance Counsel", "Australia", "SWIFT", "Market-entry legal review", ["alert-044", "alert-045"]),
        ("demo-008", "2026-02-12T13:01:00Z", 460_000, "inbound", "Institutional Client AU", "Australia", "SWIFT", "Pilot exchange settlement", ["alert-042"]),
        ("demo-002", "2026-05-26T08:05:00Z", 240_000, "outbound", "Spain Marketing Vendor", "Spain", "SEPA", "Campaign pause and regulatory communications", ["alert-007", "alert-008"]),
        ("demo-002", "2026-05-26T12:42:00Z", 310_000, "outbound", "EU Legal Counsel", "Spain", "SEPA", "Market-access legal advice", ["alert-007", "alert-008"]),
        ("demo-002", "2026-05-27T09:09:00Z", 95_000, "inbound", "Event Market Liquidity Partner", "United States", "ACH", "Liquidity adjustment", ["alert-006"]),
        ("demo-006", "2022-04-06T09:00:00Z", 85_000, "outbound", "Moscow OTC Broker", "Russia", "SWIFT", "Post-sanctions attempted settlement", ["alert-034", "alert-036"]),
        ("demo-006", "2022-04-06T10:30:00Z", 120_000, "outbound", "High Risk VASP Cluster", "Russia", "SWIFT", "Exchange liquidity movement", ["alert-033"]),
        ("demo-006", "2022-04-07T11:45:00Z", 42_000, "inbound", "Baltic Payment Processor", "Estonia", "SEPA", "Legacy exchange settlement", []),
        ("demo-007", "2023-04-25T13:17:00Z", 6_500_000, "outbound", "Singapore Tobacco Distributor", "Singapore", "SWIFT", "Trade settlement", ["alert-037"]),
        ("demo-007", "2023-04-26T09:55:00Z", 1_800_000, "outbound", "DPRK Exposure Review Escrow", "North Korea", "SWIFT", "Synthetic sanctions-review placeholder", ["alert-038", "alert-040"]),
        ("demo-007", "2023-04-27T15:08:00Z", 3_200_000, "inbound", "UK Operating Entity", "United Kingdom", "SWIFT", "Intercompany treasury movement", []),
        ("demo-001", "2025-06-02T09:18:00Z", 4_400_000, "outbound", "Bitstamp Europe SA", "Luxembourg", "SWIFT", "Acquisition-close treasury support", ["alert-001", "alert-005"]),
        ("demo-001", "2025-06-04T15:33:00Z", 1_350_000, "outbound", "Bitstamp UK Ltd", "United Kingdom", "SWIFT", "Integration operating account funding", ["alert-003", "alert-004"]),
        ("demo-004", "2025-06-30T10:04:00Z", 890_000, "outbound", "Backed Assets Issuance", "Bermuda", "SWIFT", "Tokenized equities program settlement", ["alert-017", "alert-018"]),
        ("demo-005", "2026-06-18T11:27:00Z", 620_000, "inbound", "Stablecoin Payment Network Participant", "Singapore", "SWIFT", "Circle Payments Network pilot settlement", ["alert-022", "alert-025"]),
    ]
    transactions = []
    for index, row in enumerate(rows, start=1):
        (
            customer_id,
            booked_at,
            amount_chf,
            direction,
            counterparty_name,
            counterparty_country,
            payment_rail,
            purpose,
            related_public_signal_ids,
        ) = row
        transactions.append(
            {
                "transaction_id": f"tx-{index:03d}",
                "customer_id": customer_id,
                "booked_at": booked_at,
                "amount_chf": amount_chf,
                "direction": direction,
                "counterparty_name": counterparty_name,
                "counterparty_country": counterparty_country,
                "payment_rail": payment_rail,
                "purpose": purpose,
                "related_public_signal_ids": related_public_signal_ids,
            }
        )
    return transactions


def build_internal_signals(
    activity_baselines: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    by_customer = defaultdict(list)
    for transaction in transactions:
        by_customer[transaction["customer_id"]].append(transaction)
    baseline_by_customer = {item["customer_id"]: item for item in activity_baselines}

    def signal(
        internal_signal_id: str,
        customer_id: str,
        signal_type: str,
        severity: str,
        confidence: float,
        summary: str,
        tx_ids: list[str],
        baseline_comparison: str,
        recommended_action: str,
    ) -> dict[str, Any]:
        return {
            "internal_signal_id": internal_signal_id,
            "customer_id": customer_id,
            "signal_type": signal_type,
            "severity": severity,
            "confidence": confidence,
            "summary": summary,
            "supporting_transaction_ids": tx_ids,
            "baseline_comparison": baseline_comparison,
            "recommended_action": recommended_action,
            "created_at": generated_at,
        }

    google_total = sum(tx["amount_chf"] for tx in by_customer["demo-009"])
    google_expected = baseline_by_customer["demo-009"]["expected_monthly_volume_chf"]

    signals = [
        signal(
            "internal-001",
            "demo-009",
            "transaction_volume_spike",
            "medium",
            0.82,
            "Alphabet has several large AI infrastructure-related treasury movements inside the same window as fresh public AI chip coverage.",
            ["tx-001", "tx-002", "tx-003", "tx-004"],
            f"Observed CHF {google_total:,} in AI infrastructure-linked payments versus CHF {google_expected:,} expected monthly volume.",
            "Add to RM call brief and ask whether treasury, FX, operating-account, or financing needs are changing with the AI infrastructure buildout.",
        ),
        signal(
            "internal-002",
            "demo-003",
            "activity_profile_mismatch",
            "high",
            0.86,
            "GameStop has treasury movements to digital-asset and collateral counterparties after a baseline that expected retail operating flows.",
            ["tx-005", "tx-006", "tx-008"],
            "Digital-asset counterparties are outside the prior retail treasury activity description.",
            "Route to KYC refresh and document whether crypto treasury activity changes the risk profile or service opportunity.",
        ),
        signal(
            "internal-003",
            "demo-008",
            "new_counterparty_region",
            "medium",
            0.81,
            "Coinbase has synthetic Australia-linked counterparties after the coinbase.au domain signal.",
            ["tx-009", "tx-010", "tx-011"],
            "Australia was not in expected counterparty regions for the activity baseline.",
            "Ask RM to confirm whether Australia is active launch activity, pre-launch planning, or defensive registration.",
        ),
        signal(
            "internal-004",
            "demo-006",
            "screening_review_required",
            "high",
            0.88,
            "Garantex has post-sanctions synthetic Russia/VASP-linked payments requiring enhanced review.",
            ["tx-015", "tx-016"],
            "Russia-linked counterparties and VASP cluster activity exceed the expected Estonia-only activity baseline.",
            "Escalate to compliance for sanctions and AML review. Treat as a review trigger, not a final determination.",
        ),
        signal(
            "internal-005",
            "demo-007",
            "screening_review_required",
            "high",
            0.84,
            "BAT has a synthetic North Korea exposure review placeholder following public OFAC settlement evidence.",
            ["tx-019"],
            "North Korea is outside the expected regions and should be treated as a sanctions-review scenario.",
            "Escalate to compliance and document that this is synthetic internal context for the demo.",
        ),
        signal(
            "internal-006",
            "demo-002",
            "new_counterparty_region",
            "medium",
            0.79,
            "Polymarket has Spain-linked payments after public reporting of market-access blocking and gambling-license review.",
            ["tx-012", "tx-013"],
            "Spain is outside the expected counterparty regions in the activity baseline.",
            "Ask RM to confirm whether Spanish exposure has been halted, remediated, or requires KYC update.",
        ),
        signal(
            "internal-007",
            "demo-001",
            "linked_entity_flow",
            "medium",
            0.78,
            "Robinhood has post-acquisition flows to Bitstamp entities that align with the public ownership/control alert.",
            ["tx-021", "tx-022"],
            "Bitstamp entity flows were not part of the pre-acquisition activity profile.",
            "Request updated corporate structure and operating-account map for the newly acquired entities.",
        ),
    ]
    return signals


def build_fused_alerts(
    alerts: list[dict[str, Any]],
    material_alerts: list[dict[str, Any]],
    internal_signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts_by_id = {alert["alert_id"]: alert for alert in alerts}
    material_by_id = {alert["alert_id"]: alert for alert in material_alerts}
    internal_by_customer = defaultdict(list)
    for signal in internal_signals:
        internal_by_customer[signal["customer_id"]].append(signal)

    fusion_targets = {
        "alert-046": ["internal-001"],
        "alert-047": ["internal-001"],
        "alert-048": ["internal-001"],
        "alert-013": ["internal-002"],
        "alert-014": ["internal-002"],
        "alert-043": ["internal-003"],
        "alert-045": ["internal-003"],
        "alert-034": ["internal-004"],
        "alert-036": ["internal-004"],
        "alert-038": ["internal-005"],
        "alert-040": ["internal-005"],
        "alert-007": ["internal-006"],
        "alert-008": ["internal-006"],
        "alert-005": ["internal-007"],
    }

    signals_by_id = {signal["internal_signal_id"]: signal for signal in internal_signals}
    fused = []
    for alert_id, signal_ids in fusion_targets.items():
        alert = material_by_id.get(alert_id) or alerts_by_id.get(alert_id)
        if not alert:
            continue
        attached = [signals_by_id[item] for item in signal_ids if item in signals_by_id]
        if not attached:
            attached = internal_by_customer.get(alert["customer_id"], [])[:1]
        public_score = alert.get("material_score") or 100
        internal_boost = min(30, round(sum(signal["confidence"] for signal in attached) * 15))
        fused.append(
            {
                "fused_alert_id": f"fused-{len(fused) + 1:03d}",
                "alert_id": alert_id,
                "customer_id": alert["customer_id"],
                "fusion_type": "public_plus_internal",
                "public_signal_type": alert["signal_type"],
                "public_title": alert["title"],
                "internal_signal_ids": [signal["internal_signal_id"] for signal in attached],
                "internal_signal_summaries": [signal["summary"] for signal in attached],
                "fusion_rationale": (
                    "Public evidence created the KYC drift alert; synthetic internal-bank activity "
                    "adds behavioral context for RM/compliance triage."
                ),
                "fused_score": public_score + internal_boost,
                "recommended_workflow": "Human review required before KYC update, escalation, or customer outreach.",
            }
        )
    return fused


def entity_resolution_review() -> list[dict[str, Any]]:
    return [
        {
            "review_id": "entity-review-001",
            "customer_id": "demo-006",
            "source_family": "OpenSanctions candidate",
            "candidate_name": "Garantex Europe OU",
            "candidate_identifiers": ["OFAC program: RUSSIA-EO14024", "jurisdiction: Estonia/Russia"],
            "match_score": 0.94,
            "match_status": "review_required_high_confidence",
            "match_reason": "Legal name and OFAC regulator source align with the synthetic baseline entity and aliases.",
            "recommended_action": "Escalate as candidate sanctions-screening review. Do not treat as final legal determination without compliance validation.",
        },
        {
            "review_id": "entity-review-002",
            "customer_id": "demo-007",
            "source_family": "OFAC / sanctions settlement candidate",
            "candidate_name": "British American Tobacco p.l.c.",
            "candidate_identifiers": ["OFAC settlement", "North Korea / DPRK exposure"],
            "match_score": 0.90,
            "match_status": "review_required_high_confidence",
            "match_reason": "Official Treasury source names BAT and related subsidiary activity.",
            "recommended_action": "Escalate for sanctioned-country business exposure review and update customer risk memo.",
        },
        {
            "review_id": "entity-review-003",
            "customer_id": "demo-008",
            "source_family": "RDAP / registry candidate",
            "candidate_name": "coinbase.au",
            "candidate_identifiers": ["domain: coinbase.au", "eligibility: COINBASE trademark owner"],
            "match_score": 0.78,
            "match_status": "review_required_medium_confidence",
            "match_reason": "RDAP links the country-code domain to Coinbase identity data, but active local operations are not proven.",
            "recommended_action": "Ask RM whether the domain is defensive, pre-launch, or active Australia market activity.",
        },
        {
            "review_id": "entity-review-004",
            "customer_id": "demo-009",
            "source_family": "GLEIF/registry placeholder",
            "candidate_name": "Alphabet Inc.",
            "candidate_identifiers": ["ticker: GOOGL", "ticker: GOOG", "US public company"],
            "match_score": 0.86,
            "match_status": "accepted_for_demo_registry_context",
            "match_reason": "Public company identity is strong; LEI or SEC CIK connector should replace this placeholder in production.",
            "recommended_action": "Use as registry-hardening placeholder and add GLEIF/SEC identifier enrichment later.",
        },
        {
            "review_id": "entity-review-005",
            "customer_id": "demo-002",
            "source_family": "weak-name-collision test",
            "candidate_name": "Poly Market Services Ltd",
            "candidate_identifiers": ["name-only", "unknown jurisdiction"],
            "match_score": 0.41,
            "match_status": "rejected_too_weak",
            "match_reason": "Name similarity is insufficient without jurisdiction, URL, management, or identifier overlap.",
            "recommended_action": "Suppress as false-positive entity match and retain for evaluation.",
        },
    ]


def layer2_signal_playbook() -> list[dict[str, Any]]:
    return [
        {
            "signal_id": "playbook-001",
            "signal": "Sudden spike in negative news about a corporate client",
            "expected_flag": "High Reputational Risk",
            "recommended_action": "Trigger enhanced due diligence; escalate to compliance review.",
            "layer_2_detection_logic": "Count adverse-media items over the last 24 hours and compare with the customer's prior 30-day media baseline. Escalate when the spike is material and source quality is B or better.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "The current Alphabet example is a business-model and scale signal, not adverse media.",
            },
            "expected_outcome": "Risk alert only when negative-news volume and severity are both above threshold.",
        },
        {
            "signal_id": "playbook-002",
            "signal": "High-value cross-border transfers inconsistent with historical behaviour",
            "expected_flag": "Behavioural Anomaly - Potential Money Mule",
            "recommended_action": "Monitor transactions; flag for AML analyst review.",
            "layer_2_detection_logic": "Compare payment size, rail, counterparty country, and payment purpose against the onboarded activity profile and transaction-monitoring thresholds.",
            "alphabet_demo_mapping": {
                "status": "observed",
                "context": "Synthetic Alphabet transactions include AI infrastructure payments, including a Taiwan supply-chain payment, inside the same window as the public AI chip signal.",
                "supporting_internal_signal_ids": ["internal-001"],
            },
            "expected_outcome": "RM review plus AML analyst handoff if payments are unexplained or cross into higher-risk regions.",
        },
        {
            "signal_id": "playbook-003",
            "signal": "Multiple linked entities, low activity, sudden large flows",
            "expected_flag": "Structuring / Layering Risk",
            "recommended_action": "Trigger AML investigation.",
            "layer_2_detection_logic": "Detect clusters of related entities with shared counterparties, common payment references, or synchronized transfers after a low-activity baseline.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "No linked-entity layering pattern is simulated for Alphabet; Robinhood/Bitstamp is the current linked-entity demo case.",
            },
            "expected_outcome": "Compliance investigation queue, not automatic customer reclassification.",
        },
        {
            "signal_id": "playbook-004",
            "signal": "Legal entity name change",
            "expected_flag": "Entity Identity Change - Re-KYC Required",
            "recommended_action": "Trigger KYC refresh; re-evaluate risk category.",
            "layer_2_detection_logic": "Compare registry, LEI, SEC, Companies House, or ZEFIX legal-name fields with the onboarded KYC record.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "No Alphabet legal-name change is present in the current public evidence.",
            },
            "expected_outcome": "KYC refresh task with registry source attached.",
        },
        {
            "signal_id": "playbook-005",
            "signal": "Domain switch or significant website content change",
            "expected_flag": "Business Activity Change Signal",
            "recommended_action": "Re-analyse website content; compare vs. original onboarding data.",
            "layer_2_detection_logic": "Diff known domains, product pages, terms, and country pages against stored onboarding snapshots. Rank changes mentioning regulated products, digital assets, payment rails, or jurisdictions.",
            "alphabet_demo_mapping": {
                "status": "watch",
                "context": "Alphabet is not a domain-switch case, but Google Cloud TPU product language should be monitored against the onboarded technology-treasury profile.",
            },
            "expected_outcome": "RM confirmation on whether the change is cosmetic, defensive, or a material business activity change.",
        },
        {
            "signal_id": "playbook-006",
            "signal": "Public pivot (e.g. SaaS startup -> crypto trading)",
            "expected_flag": "Material Business Model Change",
            "recommended_action": "Update risk classification; escalate for compliance review.",
            "layer_2_detection_logic": "Classify public evidence into business areas and compare it with the baseline business model, known products, and expected counterparties.",
            "alphabet_demo_mapping": {
                "status": "observed_partial",
                "context": "Alphabet is not pivoting into crypto, but the public AI chip/commercial silicon signal extends the onboarded cloud and advertising profile into a more infrastructure-intensive activity area.",
                "supporting_alert_ids": ["alert-046", "alert-048"],
            },
            "expected_outcome": "Update the KYC activity narrative and ask whether treasury, FX, data-center, or supply-chain needs are changing.",
        },
        {
            "signal_id": "playbook-007",
            "signal": "Jurisdiction move or change of legal form (e.g. GmbH -> offshore)",
            "expected_flag": "Structural Risk Change",
            "recommended_action": "Trigger enhanced due diligence; re-check beneficial ownership.",
            "layer_2_detection_logic": "Compare registry domicile, legal form, branch records, and tax-residence indicators with the current KYC profile.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "No Alphabet jurisdiction move or legal-form change is present in the current evidence.",
            },
            "expected_outcome": "Enhanced due diligence if the new structure increases opacity or jurisdictional risk.",
        },
        {
            "signal_id": "playbook-008",
            "signal": "New shareholders or beneficial owners appear",
            "expected_flag": "Ownership Change - KYC Drift",
            "recommended_action": "Full ownership verification; re-screen against sanctions/PEP lists.",
            "layer_2_detection_logic": "Monitor registry filings, beneficial-owner registers where available, SEC ownership disclosures, and credible transaction announcements.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "No new Alphabet beneficial-owner signal is present in the current evidence.",
            },
            "expected_outcome": "Ownership verification task and screening refresh.",
        },
        {
            "signal_id": "playbook-009",
            "signal": "Large funding round or rapid geographic expansion",
            "expected_flag": "Scale Risk Change",
            "recommended_action": "Reassess transaction monitoring thresholds; update activity profile.",
            "layer_2_detection_logic": "Detect funding, capital expenditure, partnership, hiring, product availability, and region-expansion signals; compare expected volume thresholds with observed internal activity.",
            "alphabet_demo_mapping": {
                "status": "observed",
                "context": "The Alphabet case combines public AI infrastructure expansion coverage with synthetic high-value AI infrastructure-linked treasury activity.",
                "supporting_alert_ids": ["alert-046", "alert-047", "alert-048"],
                "supporting_internal_signal_ids": ["internal-001"],
            },
            "expected_outcome": "Reassess monthly-volume expectations and route commercial opportunities to the RM while keeping compliance review available.",
        },
        {
            "signal_id": "playbook-010",
            "signal": "Previously dormant company begins high transaction volume",
            "expected_flag": "Dormancy Break - Suspicious Activation",
            "recommended_action": "Trigger AML review; validate business legitimacy.",
            "layer_2_detection_logic": "Compare recent transaction count and value against the dormant or low-volume baseline, then require a business-purpose explanation before changing the baseline.",
            "alphabet_demo_mapping": {
                "status": "not_observed",
                "context": "Alphabet is a high-activity public company, not a dormant-company activation case.",
            },
            "expected_outcome": "AML review if activation cannot be explained by public, customer-provided, or internal business context.",
        },
    ]


def expanded_kyc_profiles(
    generated_at: str,
    internal_signals: list[dict[str, Any]],
    fused_alerts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alphabet_signals = [signal for signal in internal_signals if signal["customer_id"] == "demo-009"]
    alphabet_fused = [alert for alert in fused_alerts if alert["customer_id"] == "demo-009"]
    return [
        {
            "profile_id": "kyc-demo-009-layer2",
            "customer_id": "demo-009",
            "legal_name": "Alphabet Inc.",
            "profile_type": "simulated_internal_bank_kyc",
            "generated_at": generated_at,
            "important_demo_notice": "This is a synthetic bank-side profile for the hackathon demo. It uses public sources for context and simulated internal activity for Layer 2; it is not AMINA customer data.",
            "onboarding_assumption": {
                "relationship_start_date": "2026-06-01",
                "relationship_manager": "Mara Keller",
                "relationship_scope": "Corporate treasury, FX, operating account, and strategic technology-sector relationship monitoring.",
                "bank_products": ["corporate banking", "FX", "treasury", "cash management"],
            },
            "research_sources": [
                {
                    "source_name": "Alphabet Investor Relations",
                    "source_url": "https://abc.xyz/investor/",
                    "how_used": "Confirms Alphabet is a public company with investor reporting, SEC filings, governance, and financial disclosures available for ongoing monitoring.",
                },
                {
                    "source_name": "Google Cloud TPU documentation",
                    "source_url": "https://docs.cloud.google.com/tpu/docs/intro-to-tpu",
                    "how_used": "Contextualizes TPUs as Google-designed machine-learning accelerators that can be consumed through Google Cloud services.",
                },
                {
                    "source_name": "The Times / Wall Street Journal syndicated article",
                    "source_url": "https://www.thetimes.com/business/wsj/article/google-is-using-nvidias-playbook-to-build-a-rival-ai-chip-business-rkbzvb9jn",
                    "how_used": "Layer 1 public signal for AI infrastructure, custom silicon, and possible commercial expansion beyond the original treasury baseline.",
                },
            ],
            "baseline_kyc_profile": {
                "expected_business_model": [
                    "Public large-cap technology holding company.",
                    "Core activity expected around search, advertising, software, cloud services, subscriptions, devices, and technology investments.",
                    "Bank relationship expected to support treasury, operating flows, vendor payments, and FX rather than regulated financial intermediation.",
                ],
                "expected_activity_description": "Large-cap technology treasury and operating flows with mostly predictable high-quality counterparties.",
                "expected_transaction_profile": {
                    "expected_monthly_volume_chf": 15_000_000,
                    "expected_transaction_count_monthly": 80,
                    "typical_single_payment_chf": {
                        "p50": 150_000,
                        "p95": 2_500_000,
                        "review_threshold": 5_000_000,
                    },
                    "expected_counterparty_regions": ["United States", "European Union", "United Kingdom"],
                    "expected_payment_rails": ["SWIFT", "ACH", "SEPA", "wire"],
                    "expected_products": ["corporate banking", "FX", "treasury"],
                },
                "initial_risk_rating": "low_to_medium",
                "risk_rating_rationale": [
                    "Public company with strong public reporting and governance visibility.",
                    "Technology sector creates strategic scale and cyber concentration risks, but not inherently high AML risk under the baseline.",
                    "Cross-border treasury flows are expected, but new regions or new activity classes should be reviewed.",
                ],
            },
            "layer_1_public_signal_context": [
                {
                    "alert_id": "alert-046",
                    "signal_type": "business_activity_change",
                    "why_it_matters_against_kyc": "AI infrastructure and custom silicon activity is adjacent to the baseline cloud profile but may change counterparty regions, capex intensity, and strategic banking needs.",
                },
                {
                    "alert_id": "alert-047",
                    "signal_type": "commercial_opportunity",
                    "why_it_matters_against_kyc": "A credible AI infrastructure buildout may create treasury, FX, liquidity, or financing conversations for the RM.",
                },
                {
                    "alert_id": "alert-048",
                    "signal_type": "new_product",
                    "why_it_matters_against_kyc": "Google Cloud TPUs and AI chips should be recorded as part of the current activity narrative if confirmed by the client.",
                },
            ],
            "layer_2_internal_context": {
                "internal_signal_ids": [signal["internal_signal_id"] for signal in alphabet_signals],
                "fused_alert_ids": [alert["fused_alert_id"] for alert in alphabet_fused],
                "monitoring_observation": "Synthetic AI infrastructure-linked transactions total CHF 16.5m in the demo window, slightly above the expected monthly activity baseline of CHF 15.0m.",
                "contextual_decision": "Do not auto-escalate as AML solely from public news. Use Layer 2 to focus RM questions on volume expectations, new counterparties, and whether AI infrastructure activity should be added to KYC.",
            },
            "layer_2_highlight_flags": [
                {
                    "signal": "High-value cross-border transfers inconsistent with historical behaviour",
                    "expected_flag": "Behavioural Anomaly - Potential Money Mule",
                    "current_status": "observed_as_review_trigger",
                    "evidence": "Synthetic payments include CHF 6.2m to a US data-center counterparty and CHF 3.1m to a Taiwan AI chip supply-chain counterparty.",
                    "recommended_action": "Monitor transactions; ask RM to confirm business purpose and route to AML analyst review if unexplained.",
                },
                {
                    "signal": "Public pivot or material business-model expansion",
                    "expected_flag": "Material Business Model Change",
                    "current_status": "observed_partial",
                    "evidence": "Public AI chip and TPU signal expands the baseline cloud/technology profile toward more infrastructure and silicon activity.",
                    "recommended_action": "Update activity narrative after client confirmation; reassess risk rating only if products, counterparties, or jurisdictions materially change.",
                },
                {
                    "signal": "Large funding round or rapid geographic expansion",
                    "expected_flag": "Scale Risk Change",
                    "current_status": "observed_as_scale_signal",
                    "evidence": "Layer 1 public signal plus Layer 2 synthetic treasury activity imply higher infrastructure scale, even without a funding round.",
                    "recommended_action": "Reassess transaction monitoring thresholds and prepare a commercial RM follow-up.",
                },
                {
                    "signal": "Domain switch or significant website content change",
                    "expected_flag": "Business Activity Change Signal",
                    "current_status": "watch",
                    "evidence": "No domain switch is detected for Alphabet, but Google Cloud TPU product pages should be monitored for changes in product availability and commercial positioning.",
                    "recommended_action": "Keep page-diff monitoring active; compare future product language against onboarding data.",
                },
            ],
            "expected_outcome": {
                "rm_tldr": "Alphabet is still a low-to-medium-risk public technology client, but fresh AI infrastructure evidence plus synthetic treasury activity makes the KYC activity narrative and monitoring thresholds worth reviewing.",
                "recommended_next_step": "Add to RM call brief, validate whether AI infrastructure activity changes expected transaction volume, and update KYC only after human confirmation.",
                "compliance_position": "Assistive triage only. No final AML, sanctions, or legal conclusion is made by the system.",
            },
        }
    ]


def alphabet_layer2_case_study(profile: dict[str, Any], playbook: list[dict[str, Any]]) -> str:
    baseline = profile["baseline_kyc_profile"]
    tx_profile = baseline["expected_transaction_profile"]
    lines = [
        "# Alphabet Layer 2 KYC Case Study",
        "",
        "## Demo Notice",
        "",
        profile["important_demo_notice"],
        "",
        "## Simulated Internal Bank Intelligence",
        "",
        f"- Customer: {profile['legal_name']} ({profile['customer_id']})",
        f"- Relationship start: {profile['onboarding_assumption']['relationship_start_date']}",
        f"- RM: {profile['onboarding_assumption']['relationship_manager']}",
        f"- Initial risk rating: {baseline['initial_risk_rating']}",
        f"- Expected monthly volume: CHF {tx_profile['expected_monthly_volume_chf']:,}",
        f"- Expected monthly transaction count: {tx_profile['expected_transaction_count_monthly']}",
        f"- Expected regions: {', '.join(tx_profile['expected_counterparty_regions'])}",
        f"- Review threshold: CHF {tx_profile['typical_single_payment_chf']['review_threshold']:,} single payment",
        "",
        "## Expected Business Model",
        "",
    ]
    lines.extend(f"- {item}" for item in baseline["expected_business_model"])
    lines.extend(
        [
            "",
            "## Layer 1 Narrowing Logic",
            "",
        ]
    )
    for item in profile["layer_1_public_signal_context"]:
        lines.append(f"- {item['alert_id']} ({item['signal_type']}): {item['why_it_matters_against_kyc']}")
    lines.extend(
        [
            "",
            "## Layer 2 Highlight Flags",
            "",
            "| Signal | Expected Flag | Current Status | Recommended Action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in profile["layer_2_highlight_flags"]:
        lines.append(
            f"| {item['signal']} | {item['expected_flag']} | {item['current_status']} | {item['recommended_action']} |"
        )
    lines.extend(
        [
            "",
            "## Full Signal Playbook",
            "",
            "| Signal | Expected Flag | Recommended Action | Alphabet Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in playbook:
        mapping = item["alphabet_demo_mapping"]
        lines.append(
            f"| {item['signal']} | {item['expected_flag']} | {item['recommended_action']} | {mapping['status']}: {mapping['context']} |"
        )
    lines.extend(
        [
            "",
            "## Expected Outcome",
            "",
            f"- RM TLDR: {profile['expected_outcome']['rm_tldr']}",
            f"- Next step: {profile['expected_outcome']['recommended_next_step']}",
            f"- Compliance position: {profile['expected_outcome']['compliance_position']}",
            "",
            "## Public Research Sources",
            "",
        ]
    )
    for source in profile["research_sources"]:
        lines.append(f"- {source['source_name']}: {source['source_url']}")
    lines.append("")
    return "\n".join(lines)


def cost_trace(
    baselines: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    facts: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
    internal_signals: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    run_id = f"cost-{generated_at.replace(':', '').replace('-', '').replace('Z', '')}"
    customer_count = len(baselines)
    document_count = len(documents)
    rows = [
        ("source_discovery", "rule_and_http", 0, 0, 0.00, "Catalog, API, and page discovery; no LLM reasoning required."),
        ("evidence_ranking", "deterministic_rules", 0, 0, 0.00, "Visible-text extraction and sentence scoring are deterministic."),
        ("fact_extraction", "deterministic_rules", 0, 0, 0.00, f"Generated {len(facts)} facts using typed rule extractors."),
        ("material_filtering", "deterministic_rules", 0, 0, 0.00, f"Scored {len(alerts)} alerts using source quality, freshness, severity, and keywords."),
        ("internal_monitoring", "deterministic_rules", 0, 0, 0.00, f"Generated {len(internal_signals)} synthetic internal monitoring signals."),
        ("human_review_summary", "not_invoked", 0, 0, 0.00, "LLM escalation layer is documented but not invoked in this demo run."),
    ]
    return [
        {
            "run_id": run_id,
            "generated_at": generated_at,
            "stage": stage,
            "customer_count": customer_count,
            "document_count": document_count,
            "model_used": model_used,
            "estimated_tokens_in": tokens_in,
            "estimated_tokens_out": tokens_out,
            "estimated_cost_usd": cost,
            "notes": notes,
            "cost_per_1000_customers_usd": round((cost / max(customer_count, 1)) * 1000, 4),
        }
        for stage, model_used, tokens_in, tokens_out, cost, notes in rows
    ]


def evaluation_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "eval-001",
            "customer_id": "demo-009",
            "expected_signal_type": "business_activity_change",
            "expected_category": "mixed",
            "expected_outcome": "true_positive_public_plus_internal",
            "evidence_document_ids": ["doc-010"],
            "should_alert": True,
            "reason": "Fresh Google AI chip coverage plus internal AI infrastructure payments should create a notification.",
        },
        {
            "case_id": "eval-002",
            "customer_id": "demo-003",
            "expected_signal_type": "treasury_policy_change",
            "expected_category": "mixed",
            "expected_outcome": "true_positive_stale_but_auditable",
            "evidence_document_ids": ["doc-001", "doc-002"],
            "should_alert": True,
            "reason": "GameStop Bitcoin treasury evidence should remain in full workspace, but not in the 24-hour TLDR queue.",
        },
        {
            "case_id": "eval-003",
            "customer_id": "demo-008",
            "expected_signal_type": "domain_registration",
            "expected_category": "mixed",
            "expected_outcome": "true_positive_requires_confirmation",
            "evidence_document_ids": ["doc-022"],
            "should_alert": True,
            "reason": "coinbase.au is a country-code domain signal requiring RM confirmation.",
        },
        {
            "case_id": "eval-004",
            "customer_id": "demo-006",
            "expected_signal_type": "jurisdiction_restriction",
            "expected_category": "risk",
            "expected_outcome": "true_positive_high_risk_context",
            "evidence_document_ids": ["doc-020"],
            "should_alert": True,
            "reason": "Official OFAC source should produce high-risk review signal.",
        },
        {
            "case_id": "eval-005",
            "customer_id": "demo-007",
            "expected_signal_type": "regulatory_scrutiny",
            "expected_category": "risk",
            "expected_outcome": "true_positive_sanctioned_country_business",
            "evidence_document_ids": ["doc-021"],
            "should_alert": True,
            "reason": "Official Treasury source should trigger sanctioned-country business review.",
        },
        {
            "case_id": "eval-006",
            "customer_id": "demo-002",
            "expected_signal_type": "entity_resolution",
            "expected_category": "suppression",
            "expected_outcome": "false_positive_rejected",
            "evidence_document_ids": [],
            "should_alert": False,
            "reason": "Weak Poly Market Services Ltd name-only match should be rejected.",
        },
        {
            "case_id": "eval-007",
            "customer_id": "demo-005",
            "expected_signal_type": "new_product",
            "expected_category": "suppression",
            "expected_outcome": "undated_product_page_suppressed_from_tldr",
            "evidence_document_ids": ["doc-011", "doc-012", "doc-019"],
            "should_alert": False,
            "reason": "Undated Circle product pages should stay out of strict 24-hour notification feed.",
        },
        {
            "case_id": "eval-008",
            "customer_id": "demo-004",
            "expected_signal_type": "new_product",
            "expected_category": "opportunity",
            "expected_outcome": "stale_signal_not_in_tldr",
            "evidence_document_ids": ["doc-017"],
            "should_alert": True,
            "reason": "Kraken xStocks is a valid workspace alert but stale for today's TLDR feed.",
        },
        {
            "case_id": "eval-009",
            "customer_id": "demo-008",
            "expected_signal_type": "new_counterparty_region",
            "expected_category": "internal_context",
            "expected_outcome": "public_internal_fusion",
            "evidence_document_ids": ["doc-022"],
            "should_alert": True,
            "reason": "Australia RDAP plus Australia counterparties should strengthen KYC update workflow.",
        },
        {
            "case_id": "eval-010",
            "customer_id": "demo-001",
            "expected_signal_type": "ownership_change",
            "expected_category": "ownership_control",
            "expected_outcome": "true_positive_ownership_drift",
            "evidence_document_ids": ["doc-014", "doc-015"],
            "should_alert": True,
            "reason": "Robinhood/Bitstamp acquisition should create ownership/control drift.",
        },
        {
            "case_id": "eval-011",
            "customer_id": "demo-009",
            "expected_signal_type": "regulatory_scrutiny",
            "expected_category": "risk",
            "expected_outcome": "not_triggered_without_regulatory_terms",
            "evidence_document_ids": ["doc-010"],
            "should_alert": False,
            "reason": "Google AI chip story should not become a regulatory alert without regulator, penalty, or investigation terms.",
        },
        {
            "case_id": "eval-012",
            "customer_id": "demo-002",
            "expected_signal_type": "jurisdiction_restriction",
            "expected_category": "risk",
            "expected_outcome": "stale_risk_workspace_only",
            "evidence_document_ids": ["doc-007", "doc-008", "doc-009"],
            "should_alert": True,
            "reason": "Polymarket Spain blocking should remain a workspace risk signal and not appear as same-day news.",
        },
    ]


def report_text(
    generated_at: str,
    baselines: list[dict[str, Any]],
    transactions: list[dict[str, Any]],
    internal_signals: list[dict[str, Any]],
    fused_alerts: list[dict[str, Any]],
    entity_reviews: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    eval_cases: list[dict[str, Any]],
    kyc_profiles: list[dict[str, Any]],
    playbook: list[dict[str, Any]],
) -> str:
    signal_counts = Counter(signal["signal_type"] for signal in internal_signals)
    review_counts = Counter(item["match_status"] for item in entity_reviews)
    total_cost = sum(row["estimated_cost_usd"] for row in cost_rows)
    public_plus_internal = [item for item in fused_alerts if item["fusion_type"] == "public_plus_internal"]
    true_cases = sum(1 for item in eval_cases if item["should_alert"])
    suppress_cases = len(eval_cases) - true_cases
    observed_playbook_items = sum(
        1 for item in playbook if item["alphabet_demo_mapping"]["status"] in {"observed", "observed_partial"}
    )

    lines = [
        "# Challenge Readiness Report",
        "",
        f"- Generated at: {generated_at}",
        f"- Internal activity baselines: {len(baselines)}",
        f"- Synthetic transactions: {len(transactions)}",
        f"- Internal monitoring signals: {len(internal_signals)}",
        f"- Public + internal fused alerts: {len(public_plus_internal)}",
        f"- Entity-resolution reviews: {len(entity_reviews)}",
        f"- Evaluation cases: {len(eval_cases)}",
        f"- Expanded Layer 2 KYC profiles: {len(kyc_profiles)}",
        f"- Layer 2 signal playbook items: {len(playbook)}",
        f"- Estimated AI cost for this run: USD {total_cost:.2f}",
        "",
        "## What Is Now Covered",
        "",
        "- Layer 1 public intelligence remains in `data_02`, `data_03`, and `data_06`.",
        "- Layer 2 simulated bank intelligence now lives in `data_07`.",
        "- Alphabet now has an expanded simulated KYC profile with expected business model, transaction volumes, regions, thresholds, and RM outcomes.",
        "- The bank-side playbook maps each challenge signal to an expected flag, detection logic, and recommended action.",
        "- Transaction anomalies, new counterparty regions, screening review triggers, and linked-entity flows are represented.",
        "- Public alerts can be fused with synthetic internal monitoring signals.",
        "- Entity-resolution review includes accepted, review-required, and rejected-too-weak examples.",
        "- Cost trace shows the current demo is rule-first and does not invoke LLM reasoning by default.",
        "",
        "## Internal Signal Mix",
        "",
    ]
    for signal_type, count in sorted(signal_counts.items()):
        lines.append(f"- {signal_type}: {count}")

    lines.extend(
        [
            "",
            "## Expanded Alphabet KYC Case",
            "",
            f"- Signal playbook items mapped to Alphabet as observed or partially observed: {observed_playbook_items}",
            "- The demo uses public AI infrastructure evidence to narrow the RM question, then Layer 2 synthetic transactions to decide what should be checked internally.",
            "- Outcome: update the activity narrative and monitoring thresholds only after RM/client confirmation.",
        ]
    )

    lines.extend(["", "## Entity Resolution Outcomes", ""])
    for status, count in sorted(review_counts.items()):
        lines.append(f"- {status}: {count}")

    lines.extend(
        [
            "",
            "## Evaluation Set",
            "",
            f"- Positive or should-alert cases: {true_cases}",
            f"- Suppression / should-not-alert cases: {suppress_cases}",
            "",
            "## Demo Talking Points",
            "",
            "1. SignalWatch does not only scrape public news; it can combine public intelligence with internal-bank activity context.",
            "2. The current pipeline is cost-efficient because discovery, extraction, filtering, and internal monitoring are deterministic by default.",
            "3. High-risk outputs remain human-in-the-loop and should not be treated as final legal, AML, or sanctions determinations.",
            "4. The system keeps suppressed, stale, and weak-match cases for audit instead of silently deleting them.",
            "",
            "## Remaining Honest Gaps",
            "",
            "- Review actions are still browser-local in the dashboard; production needs server-side audit persistence.",
            "- Sanctions and registry connectors are represented through specs and candidate examples, not full live-provider automation.",
            "- Simulated transactions are synthetic and should never be represented as AMINA production data.",
            "- RBAC is specified but not enforced by a backend API in this static prototype.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    generated_at = now_utc()
    baselines = load_json("data_01/baseline_snapshots.json", [])
    documents = load_json("data_02/documents.json", [])
    facts = load_json("data_03/facts.json", [])
    alerts = load_json("data_03/alerts.json", [])
    material_alerts = load_json("data_06/material_alerts.json", [])

    activity_baselines = customer_activity_baselines()
    transactions = simulated_transactions()
    internal_signals = build_internal_signals(activity_baselines, transactions, generated_at)
    fused_alerts = build_fused_alerts(alerts, material_alerts, internal_signals)
    entity_reviews = entity_resolution_review()
    playbook = layer2_signal_playbook()
    kyc_profiles = expanded_kyc_profiles(generated_at, internal_signals, fused_alerts)
    costs = cost_trace(baselines, documents, facts, alerts, internal_signals, generated_at)
    eval_cases = evaluation_cases()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUT_DIR / "customer_activity_baselines.json", activity_baselines)
    write_json(OUTPUT_DIR / "simulated_transactions.json", transactions)
    write_json(OUTPUT_DIR / "internal_monitoring_signals.json", internal_signals)
    write_json(OUTPUT_DIR / "public_internal_fused_alerts.json", fused_alerts)
    write_json(OUTPUT_DIR / "entity_resolution_review.json", entity_reviews)
    write_json(OUTPUT_DIR / "layer2_signal_playbook.json", playbook)
    write_json(OUTPUT_DIR / "expanded_kyc_profiles.json", kyc_profiles)
    write_json(OUTPUT_DIR / "cost_trace.json", costs)
    write_json(OUTPUT_DIR / "evaluation_cases.json", eval_cases)
    (OUTPUT_DIR / "alphabet_layer2_case_study.md").write_text(
        alphabet_layer2_case_study(kyc_profiles[0], playbook),
        encoding="utf-8",
        newline="\n",
    )
    (OUTPUT_DIR / "challenge_readiness_report.md").write_text(
        report_text(
            generated_at,
            activity_baselines,
            transactions,
            internal_signals,
            fused_alerts,
            entity_reviews,
            costs,
            eval_cases,
            kyc_profiles,
            playbook,
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        "Challenge gap outputs complete: "
        f"{len(activity_baselines)} internal baselines, "
        f"{len(transactions)} transactions, "
        f"{len(internal_signals)} internal signals, "
        f"{len(fused_alerts)} fused alerts, "
        f"{len(kyc_profiles)} expanded KYC profiles, "
        f"{len(eval_cases)} evaluation cases."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
