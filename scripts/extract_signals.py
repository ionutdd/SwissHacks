import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


SIGNAL_ALIASES = {
    "jurisdiction_expansion": "new_jurisdiction",
    "commercial_expansion": "commercial_opportunity",
}

FACT_FIELD_MAP = {
    "ownership_change": ["subsidiaries", "business_area", "risk_rating"],
    "new_subsidiary": ["subsidiaries", "known_jurisdictions", "risk_rating"],
    "new_jurisdiction": ["known_jurisdictions", "risk_rating"],
    "business_activity_change": ["business_area", "known_products", "risk_rating"],
    "digital_asset_activity": ["business_area", "known_products", "risk_rating"],
    "treasury_policy_change": ["business_area", "known_products", "risk_rating"],
    "regulatory_scrutiny": ["risk_rating", "business_area"],
    "jurisdiction_restriction": ["known_jurisdictions", "risk_rating"],
    "new_product": ["known_products", "business_area"],
    "public_listing": ["entity_type", "known_products"],
    "commercial_opportunity": ["known_products", "business_area"],
    "domain_registration": ["websites", "known_jurisdictions", "risk_rating"],
    "risk_rating_review": ["risk_rating", "known_products", "business_area"],
}

SOURCE_QUALITY_FACT_BASE = {
    "A": 0.85,
    "B": 0.72,
    "C": 0.55,
    "D": 0.35,
}

SOURCE_QUALITY_ALERT_SCORE = {
    "A": 0.95,
    "B": 0.80,
    "C": 0.55,
    "D": 0.30,
}

SOURCE_TYPES_OFFICIAL = {
    "company_newsroom",
    "official_blog",
    "product_page",
    "investor_relations",
    "regulator",
    "sec_filing",
    "domain_rdap",
}

SCALAR_FIELDS = {"risk_rating", "entity_type", "domicile"}

CORPORATE_SUFFIXES = (
    "inc",
    "incorporated",
    "corp",
    "corporation",
    "llc",
    "ltd",
    "limited",
    "s.a",
    "sa",
    "pte",
    "plc",
    "group",
)

JURISDICTION_PATTERNS = [
    ("United States", [r"\bUnited States\b", r"\bU\.S\.\b", r"\bUS\b"]),
    ("United Kingdom", [r"\bUnited Kingdom\b", r"\bUK\b"]),
    ("European Union", [r"\bEuropean Union\b", r"\bEU\b"]),
    ("Luxembourg", [r"\bLuxembourg\b"]),
    ("British Virgin Islands", [r"\bBritish Virgin Islands\b", r"\bBVI\b"]),
    ("Singapore", [r"\bSingapore\b"]),
    ("Bermuda", [r"\bBermuda\b"]),
    ("Jersey", [r"\bJersey\b"]),
    ("Australia", [r"\bAustralia\b", r"\b\.au\b", r"\bauDA\b"]),
    ("Spain", [r"\bSpain\b", r"\bEspa(?:n|ñ)a\b"]),
    ("Russia", [r"\bRussia\b", r"\bRussian Federation\b", r"\bMoscow\b", r"\bSt\. Petersburg\b"]),
    ("North Korea", [r"\bNorth Korea\b", r"\bDPRK\b", r"\bDemocratic People's Republic of Korea\b"]),
]

RECOMMENDED_ACTIONS = {
    "regulatory_scrutiny": (
        "Escalate to compliance for enhanced due diligence and confirm whether "
        "the customer has licensing or market-access changes."
    ),
    "jurisdiction_restriction": (
        "Ask RM to confirm operating jurisdictions and route to compliance if "
        "customer activity includes restricted markets."
    ),
    "ownership_change": (
        "Request updated corporate structure and beneficial ownership information "
        "before the next review."
    ),
    "new_subsidiary": (
        "Request customer confirmation and update KYC jurisdiction and entity "
        "structure fields."
    ),
    "new_jurisdiction": (
        "Request customer confirmation and update KYC jurisdiction and entity "
        "structure fields."
    ),
    "business_activity_change": (
        "Review the updated business activity and determine whether the current "
        "KYC risk rating still fits."
    ),
    "digital_asset_activity": (
        "Review custody, trading, and lending suitability; assess digital-asset "
        "risk impact."
    ),
    "treasury_policy_change": (
        "Review custody, trading, and lending suitability; assess digital-asset "
        "risk impact."
    ),
    "risk_rating_review": (
        "Route to compliance for risk-rating review and document whether the "
        "baseline should be updated."
    ),
    "new_product": (
        "Add to RM call brief for custody, payments, FX, lending, or treasury "
        "discussion."
    ),
    "commercial_opportunity": (
        "Add to RM call brief for custody, payments, FX, lending, or treasury "
        "discussion."
    ),
    "domain_registration": (
        "Ask the RM to confirm whether the country-code domain is defensive, "
        "pre-launch, or tied to active local market activity."
    ),
    "public_listing": (
        "Refresh the company profile and add public filing monitoring to the "
        "customer watchlist."
    ),
}


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def clean_spaces(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))


def normalized_signal_types(document):
    signals = set()
    for signal_type in document.get("expected_signal_types") or []:
        signals.add(SIGNAL_ALIASES.get(signal_type, signal_type))
    return signals


def document_text(document):
    parts = [
        document.get("title"),
        document.get("evidence_excerpt"),
        document.get("raw_text"),
    ]
    return clean_spaces(" ".join(part for part in parts if part))


def lower_document_text(document):
    return document_text(document).lower()


def has_any(text, terms):
    return any(term.lower() in text for term in terms)


def normalize_match_value(value):
    normalized = clean_spaces(value).lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    tokens = [
        token
        for token in normalized.split()
        if token not in CORPORATE_SUFFIXES and token != "the"
    ]
    return " ".join(tokens)


def split_values(value):
    if value is None:
        return []
    if isinstance(value, list):
        candidates = value
    else:
        candidates = re.split(r";|\|", str(value))
    return [clean_spaces(candidate) for candidate in candidates if clean_spaces(candidate)]


def array_contains(existing_values, candidate):
    normalized_candidate = normalize_match_value(candidate)
    if not normalized_candidate:
        return False
    for existing in existing_values or []:
        normalized_existing = normalize_match_value(existing)
        if (
            normalized_candidate == normalized_existing
            or normalized_candidate in normalized_existing
            or normalized_existing in normalized_candidate
        ):
            return True
    return False


def extract_jurisdictions(text):
    jurisdictions = []
    for display, patterns in JURISDICTION_PATTERNS:
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            jurisdictions.append(display)
    return jurisdictions


def source_quality_base(document):
    return SOURCE_QUALITY_FACT_BASE.get(document.get("source_quality"), 0.35)


def mentions_entity_in_title_and_excerpt(document, baseline):
    title = (document.get("title") or "").lower()
    excerpt = (document.get("evidence_excerpt") or "").lower()
    aliases = [baseline.get("legal_name", "")]
    aliases.extend(baseline.get("aliases") or [])
    aliases = [alias.lower() for alias in aliases if alias]
    return any(alias in title for alias in aliases) and any(alias in excerpt for alias in aliases)


def extraction_confidence(document, baseline, direct=True, ambiguous=False, derived=False):
    confidence = source_quality_base(document)
    if mentions_entity_in_title_and_excerpt(document, baseline):
        confidence += 0.05
    if direct:
        confidence += 0.05
    if document.get("source_type") == "reputable_news":
        confidence -= 0.10
    if ambiguous:
        confidence -= 0.15
    if derived:
        confidence -= 0.06
    if not document.get("published_at"):
        confidence -= 0.03
    return round(clamp(confidence), 2)


def make_fact(
    document,
    baseline,
    fact_type,
    obj,
    value,
    jurisdiction=None,
    fields=None,
    direct=True,
    ambiguous=False,
    derived=False,
):
    return {
        "customer_id": document["customer_id"],
        "document_id": document["document_id"],
        "fact_type": fact_type,
        "subject": baseline["legal_name"],
        "object": clean_spaces(obj),
        "value": clean_spaces(value),
        "jurisdiction": jurisdiction,
        "effective_date": document.get("published_at"),
        "baseline_fields_targeted": fields or FACT_FIELD_MAP[fact_type],
        "evidence_excerpt": clean_spaces(document.get("evidence_excerpt")),
        "source_quality": document.get("source_quality"),
        "source_type": document.get("source_type"),
        "source_name": document.get("source_name"),
        "source_url": document.get("source_url"),
        "extraction_method": "rule",
        "extraction_confidence": extraction_confidence(
            document,
            baseline,
            direct=direct,
            ambiguous=ambiguous,
            derived=derived,
        ),
    }


def extract_ownership_change(document, baseline):
    text = lower_document_text(document)
    if not has_any(text, ["acquisition", "acquire", "entered into an agreement to acquire"]):
        return []

    if "bitstamp" in text:
        return [
            make_fact(
                document,
                baseline,
                "ownership_change",
                "Bitstamp Ltd.",
                "Robinhood closed its acquisition of Bitstamp Ltd., a global cryptocurrency exchange.",
            )
        ]
    if "ninjatrader" in text:
        return [
            make_fact(
                document,
                baseline,
                "ownership_change",
                "NinjaTrader",
                "Kraken entered into an agreement to acquire NinjaTrader for $1.5 billion.",
            )
        ]

    match = re.search(r"acquire\s+([A-Z][A-Za-z0-9&.,'\-\s]{2,80})", document_text(document))
    if match:
        target = clean_spaces(match.group(1)).rstrip(".")
        return [
            make_fact(
                document,
                baseline,
                "ownership_change",
                target,
                f"{baseline['legal_name']} announced an acquisition involving {target}.",
                ambiguous=True,
            )
        ]
    return []


def extract_new_subsidiary(document, baseline):
    text = lower_document_text(document)
    if "bitstamp legal entities" not in text and "bitstamp europe" not in text:
        return []

    entities = [
        "Bitstamp Europe S.A.",
        "Bitstamp UK Ltd.",
        "Bitstamp Ltd.",
        "Bitstamp Global Ltd.",
        "Bitstamp Asia Pte Ltd",
    ]
    return [
        make_fact(
            document,
            baseline,
            "new_subsidiary",
            "; ".join(entities),
            "Bitstamp disclosures list regulated legal entities serving clients by residency.",
            jurisdiction="Luxembourg; United Kingdom; British Virgin Islands; Singapore",
        )
    ]


def extract_new_jurisdiction(document, baseline):
    text = document_text(document)
    lower_text = text.lower()
    jurisdictions = extract_jurisdictions(text)

    if "bitstamp" in lower_text and jurisdictions:
        selected = [
            jurisdiction
            for jurisdiction in jurisdictions
            if jurisdiction
            in {"Luxembourg", "United Kingdom", "British Virgin Islands", "Singapore"}
        ]
        if selected:
            return [
                make_fact(
                    document,
                    baseline,
                    "new_jurisdiction",
                    "; ".join(selected),
                    "Bitstamp legal entity disclosures add licensed crypto-asset service jurisdictions.",
                    jurisdiction="; ".join(selected),
                )
            ]

    if "xstocks" in lower_text or "bermuda" in lower_text or "jersey" in lower_text:
        selected = [
            jurisdiction
            for jurisdiction in jurisdictions
            if jurisdiction in {"Jersey", "Bermuda"}
        ]
        if "non-u.s" in lower_text:
            selected.append("non-U.S. clients")
        if selected:
            return [
                make_fact(
                    document,
                    baseline,
                    "new_jurisdiction",
                    "; ".join(dict.fromkeys(selected)),
                    "xStocks evidence references Jersey issuance, Bermuda digital-asset licensing, or non-U.S. eligibility.",
                    jurisdiction="; ".join(dict.fromkeys(selected)),
                )
            ]

    if "garantex" in lower_text and "russia" in lower_text:
        return [
            make_fact(
                document,
                baseline,
                "new_jurisdiction",
                "Russia",
                "Treasury evidence says the majority of Garantex operations are carried out in Moscow and St. Petersburg, Russia.",
                jurisdiction="Russia",
            )
        ]

    if "british american tobacco" in lower_text and ("north korea" in lower_text or "dprk" in lower_text):
        return [
            make_fact(
                document,
                baseline,
                "new_jurisdiction",
                "North Korea",
                "OFAC evidence describes North Korea joint-venture profits and exports to the North Korean Embassy in Singapore.",
                jurisdiction="North Korea",
            )
        ]

    if (
        document.get("source_type") == "domain_rdap"
        and "coinbase.au" in lower_text
        and has_any(lower_text, ["registrant name coinbase", "eligibility name coinbase", "trademark owner"])
    ):
        return [
            make_fact(
                document,
                baseline,
                "new_jurisdiction",
                "Australia",
                "RDAP evidence ties the coinbase.au country-code domain to Coinbase identity data.",
                jurisdiction="Australia",
                fields=["known_jurisdictions", "risk_rating"],
            )
        ]

    return []


def extract_business_activity_change(document, baseline):
    text = lower_document_text(document)
    facts = []
    if has_any(text, ["event-based binary options", "prediction market", "apuestas", "gambling licence", "licencia de juego"]):
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "event-based binary options and gambling-market exposure",
                "Polymarket evidence describes event-based binary options, prediction markets, or gambling-license exposure.",
            )
        )
    elif "global cryptocurrency exchange" in text:
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "global cryptocurrency exchange",
                "The Bitstamp acquisition adds a global cryptocurrency exchange to Robinhood's business profile.",
            )
        )
    elif "futures trading platform" in text:
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "U.S. futures and multi-asset professional trading",
                "The NinjaTrader acquisition expands Kraken toward U.S. futures and multi-asset professional trading.",
            )
        )
    elif "garantex" in text and "virtual currency exchange" in text:
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "Russia-linked virtual currency exchange with AML/CFT deficiencies",
                "Treasury evidence describes Garantex as a Russia-linked virtual currency exchange with AML/CFT deficiencies and illicit transaction exposure.",
                jurisdiction="Russia",
            )
        )
    elif "british american tobacco" in text and "north korea" in text:
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "North Korea tobacco joint-venture and export exposure",
                "OFAC evidence describes BAT-related North Korea joint-venture profits and tobacco exports involving U.S. financial institutions.",
                jurisdiction="North Korea",
            )
        )
    elif document.get("source_type") == "domain_rdap" and "coinbase.au" in text and "trademark owner" in text:
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "Australia country-code domain monitoring signal",
                "RDAP evidence links coinbase.au to Coinbase identity data, creating a market-entry or defensive-domain review item.",
                jurisdiction="Australia",
                fields=["business_area", "known_products", "risk_rating"],
            )
        )
    elif has_any(text, ["google", "alphabet"]) and has_any(
        text,
        ["tpu", "tensor processing unit", "ai chip", "ai infrastructure", "google cloud"],
    ):
        facts.append(
            make_fact(
                document,
                baseline,
                "business_activity_change",
                "AI infrastructure and custom silicon expansion",
                "Fresh evidence describes Google's expansion of AI infrastructure, TPUs, or AI chip commercialization.",
                fields=["business_area", "known_products", "risk_rating"],
            )
        )
    return facts


def extract_digital_asset_activity(document, baseline):
    text = lower_document_text(document)
    title = (document.get("title") or "").lower()

    if "purchased 4,710 bitcoin" in text or "purchase of bitcoin" in title:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "4,710 Bitcoin purchase",
                "GameStop announced that it purchased 4,710 Bitcoin.",
            )
        ]
    if "treasury reserve asset" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "Bitcoin treasury reserve asset",
                "GameStop approved Bitcoin as a treasury reserve asset.",
            )
        ]
    if "pledged portion of its digital assets as collateral" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "digital assets pledged as collateral",
                "GameStop pledged part of its digital assets as collateral in a covered-call strategy.",
            )
        ]
    if "bitcoin and other crypto" in text and "regulatory uncertainty" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "Bitcoin and other crypto-currencies",
                "GameStop disclosed regulatory and legal uncertainty around Bitcoin and other crypto-currencies.",
            )
        ]
    if "xstocks" in text or "tokenized u.s. stocks" in text or "tokenized equities" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "tokenized U.S. stocks and ETFs",
                "Kraken evidence describes tokenized U.S. stocks and ETFs through xStocks.",
            )
        ]
    if "circle payments network" in text or "stablecoins like usdc and eurc" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "USDC/EURC stablecoin payments",
                "Circle Payments Network enables payments with 24/7 settlement via stablecoins like USDC and EURC.",
            )
        ]
    if "usdc" in text and "global payments" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "USDC global payments",
                "USDC enables near-instant, low-cost global payments and 24/7 liquidity.",
            )
        ]
    if "circle mint" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "USDC/EURC access and redemption",
                "Circle Mint gives distributors access to and redemption of USDC and EURC.",
            )
        ]
    if "crypto-assets services" in text:
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "crypto-asset services",
                "Bitstamp legal entities provide crypto-asset services based on client residency.",
            )
        ]
    if "garantex" in text and ("virtual currency exchange" in text or "virtual currencies" in text):
        return [
            make_fact(
                document,
                baseline,
                "digital_asset_activity",
                "sanctioned Russia-linked virtual currency exchange",
                "Treasury evidence links Garantex virtual currency exchange activity to illicit actors, darknet markets, ransomware, and Russian financial-services sanctions exposure.",
                jurisdiction="Russia",
            )
        ]
    return []


def extract_treasury_policy_change(document, baseline):
    text = lower_document_text(document)
    title = (document.get("title") or "").lower()
    if "treasury reserve asset" in text:
        return [
            make_fact(
                document,
                baseline,
                "treasury_policy_change",
                "Bitcoin treasury reserve asset",
                "GameStop's board approved Bitcoin as a treasury reserve asset.",
            )
        ]
    if "purchased 4,710 bitcoin" in text or "purchase of bitcoin" in title:
        return [
            make_fact(
                document,
                baseline,
                "treasury_policy_change",
                "4,710 Bitcoin purchase",
                "GameStop purchased 4,710 Bitcoin after its baseline review.",
            )
        ]
    if "covered-call strategy" in text:
        return [
            make_fact(
                document,
                baseline,
                "treasury_policy_change",
                "digital assets collateral and covered-call strategy",
                "GameStop used digital assets as collateral in connection with a covered-call strategy.",
            )
        ]
    return []


def extract_regulatory_scrutiny(document, baseline):
    text = lower_document_text(document)
    if "garantex" in text and ("ofac" in text or "sanctioned" in text):
        return [
            make_fact(
                document,
                baseline,
                "regulatory_scrutiny",
                "OFAC sanctions on Garantex",
                "Treasury sanctioned Garantex and described illicit transaction exposure, AML/CFT deficiencies, and Russia financial-services sanctions risk.",
                jurisdiction="Russia",
            )
        ]
    if "british american tobacco" in text and ("ofac" in text or "settlement" in text) and "north korea" in text:
        return [
            make_fact(
                document,
                baseline,
                "regulatory_scrutiny",
                "$508 million OFAC settlement for North Korea sanctions violations",
                "OFAC announced a $508 million settlement with British American Tobacco for apparent violations of U.S. sanctions on North Korea and WMD proliferators.",
                jurisdiction="North Korea",
            )
        ]
    if "cftc" in text and ("penalty" in text or "order" in text):
        return [
            make_fact(
                document,
                baseline,
                "regulatory_scrutiny",
                "CFTC Polymarket order and $1.4 million penalty",
                "The CFTC ordered Polymarket's operator to pay a $1.4 million penalty for off-exchange event-based binary options and registration failures.",
                jurisdiction="United States",
            )
        ]
    if has_any(text, ["blocked access", "bloqueo", "expediente sancionador", "gambling licence", "licencia de juego", "sin licencia"]):
        return [
            make_fact(
                document,
                baseline,
                "regulatory_scrutiny",
                "Spanish gambling-license investigation",
                "Spanish authorities opened or reported a gambling-license investigation involving Polymarket.",
                jurisdiction="Spain",
            )
        ]
    return []


def extract_jurisdiction_restriction(document, baseline):
    text = lower_document_text(document)
    if "garantex" in text and ("russia" in text or "russian federation" in text) and ("sanction" in text or "e.o. 14024" in text):
        return [
            make_fact(
                document,
                baseline,
                "jurisdiction_restriction",
                "Russia sanctions and virtual-currency evasion exposure",
                "Treasury designated Garantex for operating in the Russian Federation financial-services sector and highlighted virtual-currency sanctions-evasion risk.",
                jurisdiction="Russia",
            )
        ]
    if "british american tobacco" in text and ("north korea" in text or "dprk" in text):
        return [
            make_fact(
                document,
                baseline,
                "jurisdiction_restriction",
                "North Korea sanctions exposure",
                "OFAC evidence describes North Korea-related business and payments touching the U.S. financial system.",
                jurisdiction="North Korea",
            )
        ]
    if has_any(text, ["blocked access", "bloqueo", "sin licencia", "without a gambling licence"]):
        return [
            make_fact(
                document,
                baseline,
                "jurisdiction_restriction",
                "Spain market-access block",
                "Spain blocked access or reported enforcement related to operating without a gambling license.",
                jurisdiction="Spain",
            )
        ]
    return []


def extract_new_product(document, baseline):
    text = lower_document_text(document)
    title = (document.get("title") or "").lower()
    if "circle payments network" in text or "circle payments network" in title:
        return [
            make_fact(
                document,
                baseline,
                "new_product",
                "Circle Payments Network",
                "Circle Payments Network enables 24/7 real-time settlement with stablecoins.",
            )
        ]
    if "circle mint" in text or "circle mint" in title:
        return [
            make_fact(
                document,
                baseline,
                "new_product",
                "Circle Mint",
                "Circle Mint gives distributors access to and redemption of USDC and EURC.",
            )
        ]
    if "usdc" in title or ("usdc" in text and "global payments" in text):
        return [
            make_fact(
                document,
                baseline,
                "new_product",
                "USDC global payments",
                "USDC enables 24/7 liquidity and near-instant global payments.",
            )
        ]
    if "xstocks" in text or "tokenized u.s. stocks" in text or "tokenized equities" in text:
        return [
            make_fact(
                document,
                baseline,
                "new_product",
                "xStocks tokenized equities",
                "Kraken evidence describes tokenized U.S. stocks and ETFs through xStocks.",
            )
        ]
    if has_any(text, ["google", "alphabet"]) and has_any(text, ["tpu", "tensor processing unit", "ai chip"]):
        return [
            make_fact(
                document,
                baseline,
                "new_product",
                "Google Cloud TPUs and AI chips",
                "Fresh evidence describes Google expanding Tensor Processing Units or AI chip offerings for AI infrastructure customers.",
            )
        ]
    return []


def extract_public_listing(document, baseline):
    text = lower_document_text(document)
    if "investor relations" in text and "circle internet group" in text:
        return [
            make_fact(
                document,
                baseline,
                "public_listing",
                "Circle Investor Relations profile",
                "Circle maintains investor-relations materials describing its public-company profile and stablecoin network.",
                direct=False,
                derived=True,
            )
        ]
    return []


def extract_commercial_opportunity(document, baseline):
    text = lower_document_text(document)
    if "purchased 4,710 bitcoin" in text or "treasury reserve asset" in text:
        return [
            make_fact(
                document,
                baseline,
                "commercial_opportunity",
                "Bitcoin custody and treasury services opportunity",
                "GameStop's Bitcoin treasury activity creates a custody, trading, lending, or treasury-services conversation.",
                fields=["known_products", "business_area"],
                derived=True,
            )
        ]
    if "circle payments network" in text:
        return [
            make_fact(
                document,
                baseline,
                "commercial_opportunity",
                "Circle Payments Network payments opportunity",
                "Circle Payments Network creates an institutional payments, FX, and stablecoin settlement opportunity.",
                fields=["known_products", "business_area"],
                derived=True,
            )
        ]
    if "circle mint" in text:
        return [
            make_fact(
                document,
                baseline,
                "commercial_opportunity",
                "Circle Mint distribution opportunity",
                "Circle Mint creates an RM opportunity around USDC/EURC access, redemption, and distribution.",
                fields=["known_products", "business_area"],
                derived=True,
            )
        ]
    if "usdc" in text and "global payments" in text:
        return [
            make_fact(
                document,
                baseline,
                "commercial_opportunity",
                "USDC liquidity and payments opportunity",
                "USDC payment and liquidity evidence creates an RM opportunity for stablecoin settlement and treasury services.",
                fields=["known_products", "business_area"],
                derived=True,
            )
        ]
    if has_any(text, ["google", "alphabet"]) and has_any(
        text,
        ["tpu", "tensor processing unit", "ai chip", "ai infrastructure", "google cloud"],
    ):
        return [
            make_fact(
                document,
                baseline,
                "commercial_opportunity",
                "AI infrastructure and cloud banking opportunity",
                "Google's AI infrastructure expansion creates an RM conversation around corporate treasury, liquidity, FX, financing, and operating-account needs.",
                fields=["known_products", "business_area"],
                derived=True,
            )
        ]
    return []


def extract_domain_registration(document, baseline):
    text = lower_document_text(document)
    if document.get("source_type") != "domain_rdap":
        return []
    if "coinbase.au" not in text:
        return []
    if not has_any(text, ["registrant name coinbase", "eligibility name coinbase", "trademark owner"]):
        return []

    return [
        make_fact(
            document,
            baseline,
            "domain_registration",
            "https://coinbase.au",
            "RDAP ties coinbase.au to Coinbase, Inc. through registrant and COINBASE trademark-owner eligibility data.",
            jurisdiction="Australia",
            fields=["websites", "known_jurisdictions", "risk_rating"],
        )
    ]


def extract_risk_rating_review(document, baseline):
    text = lower_document_text(document)
    if document.get("source_type") == "domain_rdap" and "coinbase.au" in text and "trademark owner" in text:
        return [
            make_fact(
                document,
                baseline,
                "risk_rating_review",
                "country-code domain expansion review",
                "The coinbase.au RDAP record should be reviewed to confirm whether the domain is defensive, pre-launch, or active local market evidence.",
                jurisdiction="Australia",
                fields=["risk_rating", "known_jurisdictions", "business_area"],
            )
        ]
    if "garantex" in text and has_any(text, ["illicit actors", "darknet markets", "ransomware", "aml/cft deficiencies"]):
        return [
            make_fact(
                document,
                baseline,
                "risk_rating_review",
                "Garantex illicit finance and AML/CFT risk",
                "Treasury evidence associates Garantex with illicit actors, darknet markets, ransomware proceeds, and AML/CFT deficiencies.",
                jurisdiction="Russia",
            )
        ]
    if "british american tobacco" in text and has_any(text, ["north korea", "dprk", "wmd", "designated north korean banks"]):
        return [
            make_fact(
                document,
                baseline,
                "risk_rating_review",
                "North Korea sanctions and WMD-proliferator risk",
                "OFAC evidence describes apparent North Korea and WMD sanctions violations involving BAT, intermediaries, and U.S. financial institutions.",
                jurisdiction="North Korea",
            )
        ]
    if "regulatory uncertainty" in text or "increased regulatory scrutiny" in text:
        return [
            make_fact(
                document,
                baseline,
                "risk_rating_review",
                "digital-asset regulatory uncertainty",
                "GameStop disclosed regulatory uncertainty and potential increased scrutiny around Bitcoin and crypto-currencies.",
            )
        ]
    if "covered-call strategy" in text and "digital assets" in text:
        return [
            make_fact(
                document,
                baseline,
                "risk_rating_review",
                "digital assets collateral strategy",
                "GameStop's use of digital assets as collateral calls for risk-rating review.",
                derived=True,
            )
        ]
    return []


EXTRACTORS = {
    "ownership_change": extract_ownership_change,
    "new_subsidiary": extract_new_subsidiary,
    "new_jurisdiction": extract_new_jurisdiction,
    "business_activity_change": extract_business_activity_change,
    "digital_asset_activity": extract_digital_asset_activity,
    "treasury_policy_change": extract_treasury_policy_change,
    "regulatory_scrutiny": extract_regulatory_scrutiny,
    "jurisdiction_restriction": extract_jurisdiction_restriction,
    "new_product": extract_new_product,
    "public_listing": extract_public_listing,
    "commercial_opportunity": extract_commercial_opportunity,
    "domain_registration": extract_domain_registration,
    "risk_rating_review": extract_risk_rating_review,
}


def extract_facts(documents, baselines_by_customer):
    facts = []
    low_confidence_skipped = 0
    for document in documents:
        baseline = baselines_by_customer.get(document.get("customer_id"))
        if not baseline:
            continue
        expected_signals = normalized_signal_types(document)
        for fact_type, extractor in EXTRACTORS.items():
            if fact_type not in expected_signals:
                continue
            for fact in extractor(document, baseline):
                if not fact.get("evidence_excerpt") or fact["extraction_confidence"] < 0.45:
                    low_confidence_skipped += 1
                    continue
                facts.append(fact)

    for index, fact in enumerate(facts, start=1):
        facts[index - 1] = {"fact_id": f"fact-{index:03d}", **fact}
    return facts, low_confidence_skipped


def values_for_field(fact, field):
    fact_type = fact["fact_type"]
    if field == "known_jurisdictions":
        return split_values(fact.get("jurisdiction") or fact.get("object"))
    if field == "subsidiaries":
        return split_values(fact.get("object"))
    if field == "known_products":
        return split_values(fact.get("object"))
    if field == "business_area":
        if fact_type == "regulatory_scrutiny":
            return [fact.get("object")]
        return split_values(fact.get("object"))
    if field == "risk_rating":
        return [f"Review due to {fact.get('object')}"]
    if field == "entity_type":
        return [fact.get("object")]
    return split_values(fact.get("object"))


def materiality_for_fact(fact):
    fact_type = fact["fact_type"]
    obj = (fact.get("object") or "").lower()
    if fact_type in {"regulatory_scrutiny", "jurisdiction_restriction"}:
        return "high"
    if fact_type == "ownership_change":
        return "high"
    if fact_type == "treasury_policy_change" and "bitcoin" in obj:
        return "high"
    if fact_type == "risk_rating_review":
        return "high"
    if fact_type == "domain_registration":
        return "medium"
    if fact_type in {"new_subsidiary", "new_jurisdiction", "business_activity_change", "digital_asset_activity", "new_product"}:
        return "medium"
    if fact_type in {"commercial_opportunity", "public_listing"}:
        return "low"
    return "medium"


def compare_fact_to_baseline(fact, baseline):
    changed_fields = []
    baseline_value = {}
    new_value = {}
    reasons = []

    for field in fact.get("baseline_fields_targeted") or FACT_FIELD_MAP[fact["fact_type"]]:
        existing = baseline.get(field)
        candidates = values_for_field(fact, field)
        if field in SCALAR_FIELDS:
            changed_fields.append(field)
            baseline_value[field] = existing
            new_value[field] = candidates[0] if candidates else fact.get("value")
            reasons.append(f"{field} requires review due to {fact['object']}.")
            continue

        existing_values = existing if isinstance(existing, list) else []
        new_candidates = [
            candidate
            for candidate in candidates
            if candidate and not array_contains(existing_values, candidate)
        ]
        if new_candidates:
            changed_fields.append(field)
            baseline_value[field] = existing_values
            new_value[field] = new_candidates
            reasons.append(
                f"{', '.join(new_candidates)} is not listed in baseline {field}."
            )

    fact_date = parse_iso_date(fact.get("effective_date"))
    baseline_date = parse_iso_date(baseline.get("last_reviewed_at"))
    predates_baseline = bool(fact_date and baseline_date and fact_date <= baseline_date)
    allow_undated = not fact_date and fact.get("source_quality") in {"A", "B"}
    is_new_information = bool(changed_fields) and (not predates_baseline or allow_undated)

    if predates_baseline:
        reasons.append(
            "The evidence date is before or on the baseline review date, so it is kept as context unless corroborated by newer evidence."
        )
    if allow_undated:
        reasons.append(
            "The source is undated, but source quality is high enough for a review alert."
        )

    return {
        "fact_id": fact["fact_id"],
        "customer_id": fact["customer_id"],
        "is_new_information": is_new_information,
        "changed_fields": sorted(set(changed_fields)),
        "baseline_value": baseline_value,
        "new_value": new_value,
        "materiality": materiality_for_fact(fact),
        "comparison_reason": " ".join(reasons) if reasons else "No material baseline difference found.",
        "predates_baseline": predates_baseline,
    }


def alert_group_key(fact):
    return (
        fact["customer_id"],
        fact["fact_type"],
        normalize_match_value(fact.get("object")),
    )


def category_for_alert(facts):
    fact_type = facts[0]["fact_type"]
    customer_id = facts[0]["customer_id"]
    if fact_type in {"regulatory_scrutiny", "jurisdiction_restriction", "risk_rating_review"}:
        return "risk"
    if fact_type in {"ownership_change", "new_subsidiary"}:
        return "ownership_control"
    if fact_type in {"commercial_opportunity"}:
        return "opportunity"
    if fact_type == "new_product" and customer_id == "demo-005":
        return "opportunity"
    if fact_type in {"new_product"}:
        return "opportunity"
    if fact_type == "public_listing":
        return "opportunity"
    if fact_type in {"treasury_policy_change", "digital_asset_activity", "business_activity_change", "new_jurisdiction", "domain_registration"}:
        return "mixed"
    return "mixed"


def severity_for_alert(fact_type, materiality, category, object_value):
    object_value = (object_value or "").lower()
    if materiality == "high":
        return "high"
    if fact_type == "new_jurisdiction" and has_any(object_value, ["bermuda", "british virgin islands", "russia", "north korea"]):
        return "high"
    if fact_type == "digital_asset_activity" and has_any(object_value, ["sanctioned", "ransomware", "darknet"]):
        return "high"
    if fact_type == "digital_asset_activity" and has_any(object_value, ["bitcoin", "collateral"]):
        return "medium"
    if category == "opportunity":
        return "medium"
    if materiality == "low":
        return "low"
    return "medium"


def average(values):
    return sum(values) / len(values) if values else 0.0


def alert_confidence(facts, comparison, documents_by_id):
    avg_fact_confidence = average([fact["extraction_confidence"] for fact in facts])
    source_quality_score = average(
        [SOURCE_QUALITY_ALERT_SCORE.get(fact.get("source_quality"), 0.30) for fact in facts]
    )
    changed_fields = set(comparison["changed_fields"])
    comparison_clarity = 0.75 if changed_fields <= {"risk_rating"} else 0.95

    document_ids = {fact["document_id"] for fact in facts}
    if len(document_ids) >= 2:
        corroboration = 1.0
    else:
        document = documents_by_id[next(iter(document_ids))]
        corroboration = 0.85 if document.get("source_type") in SOURCE_TYPES_OFFICIAL else 0.65

    confidence = (
        0.45 * avg_fact_confidence
        + 0.25 * source_quality_score
        + 0.20 * comparison_clarity
        + 0.10 * corroboration
    )
    return round(clamp(confidence), 2)


def title_for_alert(customer_name, fact_type, object_value):
    templates = {
        "ownership_change": f"{customer_name} has ownership/control drift involving {object_value}",
        "new_subsidiary": f"{customer_name} has new legal entities to review",
        "new_jurisdiction": f"{customer_name} has new jurisdiction exposure: {object_value}",
        "business_activity_change": f"{customer_name} business activity changed: {object_value}",
        "digital_asset_activity": f"{customer_name} has new digital-asset activity: {object_value}",
        "treasury_policy_change": f"{customer_name} treasury activity changed: {object_value}",
        "regulatory_scrutiny": f"{customer_name} faces regulatory scrutiny: {object_value}",
        "jurisdiction_restriction": f"{customer_name} has jurisdiction restriction signal: {object_value}",
        "new_product": f"{customer_name} product signal: {object_value}",
        "commercial_opportunity": f"{customer_name} commercial opportunity: {object_value}",
        "domain_registration": f"{customer_name} has country-domain registration signal: {object_value}",
        "risk_rating_review": f"{customer_name} risk rating should be reviewed",
        "public_listing": f"{customer_name} public-company profile should be refreshed",
    }
    return templates.get(fact_type, f"{customer_name} signal: {object_value}")


def display_object_for_alert(fact_type, fallback_object, comparison):
    field_priority = {
        "new_jurisdiction": "known_jurisdictions",
        "new_subsidiary": "subsidiaries",
        "ownership_change": "subsidiaries",
        "new_product": "known_products",
        "commercial_opportunity": "known_products",
        "digital_asset_activity": "known_products",
        "treasury_policy_change": "known_products",
        "business_activity_change": "business_area",
        "domain_registration": "websites",
    }
    field = field_priority.get(fact_type)
    if not field:
        return fallback_object
    value = comparison["new_value"].get(field)
    if isinstance(value, list) and value:
        return "; ".join(value)
    if isinstance(value, str) and value:
        return value
    return fallback_object


def summary_for_alert(facts, comparison):
    primary = facts[0]
    document_count = len({fact["document_id"] for fact in facts})
    evidence_word = "document" if document_count == 1 else "documents"
    return (
        f"{document_count} evidence {evidence_word} support {primary['fact_type']} "
        f"for {primary['object']}. {comparison['comparison_reason']}"
    )


def build_evidence(facts, documents_by_id):
    evidence = []
    seen = set()
    for fact in facts:
        document_id = fact["document_id"]
        if document_id in seen:
            continue
        seen.add(document_id)
        document = documents_by_id[document_id]
        evidence.append(
            {
                "document_id": document_id,
                "source_name": document.get("source_name"),
                "source_url": document.get("source_url"),
                "published_at": document.get("published_at"),
                "collected_at": document.get("collected_at"),
                "source_type": document.get("source_type"),
                "source_quality": document.get("source_quality"),
                "title": document.get("title"),
                "excerpt": document.get("evidence_excerpt"),
            }
        )
    return evidence


def merge_comparisons(comparisons):
    changed_fields = sorted({field for comparison in comparisons for field in comparison["changed_fields"]})
    baseline_value = {}
    new_value = defaultdict(list)
    reasons = []
    materiality_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    materiality = "low"

    for comparison in comparisons:
        for field, value in comparison["baseline_value"].items():
            baseline_value.setdefault(field, value)
        for field, value in comparison["new_value"].items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                if item not in new_value[field]:
                    new_value[field].append(item)
        if comparison["comparison_reason"]:
            reasons.append(comparison["comparison_reason"])
        if materiality_order[comparison["materiality"]] > materiality_order[materiality]:
            materiality = comparison["materiality"]

    return {
        "changed_fields": changed_fields,
        "baseline_value": baseline_value,
        "new_value": dict(new_value),
        "materiality": materiality,
        "comparison_reason": " ".join(dict.fromkeys(reasons)),
    }


def create_alerts(facts, comparisons_by_fact_id, baselines_by_customer, documents_by_id, created_at):
    grouped = defaultdict(list)
    pre_baseline_context = 0
    for fact in facts:
        comparison = comparisons_by_fact_id[fact["fact_id"]]
        if not comparison["is_new_information"]:
            if comparison["predates_baseline"]:
                pre_baseline_context += 1
            continue
        grouped[alert_group_key(fact)].append(fact)

    alerts = []
    for group_facts in grouped.values():
        baseline = baselines_by_customer[group_facts[0]["customer_id"]]
        merged_comparison = merge_comparisons(
            [comparisons_by_fact_id[fact["fact_id"]] for fact in group_facts]
        )
        category = category_for_alert(group_facts)
        fact_type = group_facts[0]["fact_type"]
        object_value = display_object_for_alert(
            fact_type,
            group_facts[0]["object"],
            merged_comparison,
        )
        severity = severity_for_alert(
            fact_type,
            merged_comparison["materiality"],
            category,
            object_value,
        )
        alerts.append(
            {
                "customer_id": group_facts[0]["customer_id"],
                "category": category,
                "signal_type": fact_type,
                "title": title_for_alert(baseline["legal_name"], fact_type, object_value),
                "summary": summary_for_alert(group_facts, merged_comparison),
                "changed_fields": merged_comparison["changed_fields"],
                "baseline_value": merged_comparison["baseline_value"],
                "new_value": merged_comparison["new_value"],
                "severity": severity,
                "confidence": alert_confidence(group_facts, merged_comparison, documents_by_id),
                "recommended_action": RECOMMENDED_ACTIONS[fact_type],
                "evidence_document_ids": sorted({fact["document_id"] for fact in group_facts}),
                "fact_ids": [fact["fact_id"] for fact in group_facts],
                "evidence": build_evidence(group_facts, documents_by_id),
                "comparison_reason": merged_comparison["comparison_reason"],
                "status": "new",
                "created_at": created_at,
            }
        )

    alerts.sort(
        key=lambda alert: (
            alert["customer_id"],
            alert["signal_type"],
            ",".join(alert["evidence_document_ids"]),
            alert["title"],
        )
    )
    for index, alert in enumerate(alerts, start=1):
        alerts[index - 1] = {"alert_id": f"alert-{index:03d}", **alert}

    duplicate_facts_clustered = sum(len(group_facts) - 1 for group_facts in grouped.values())
    return alerts, {
        "pre_baseline_context": pre_baseline_context,
        "duplicate_facts_clustered": duplicate_facts_clustered,
    }


def report_lines(documents, facts, alerts, skipped, suppression_stats):
    category_counts = Counter(alert["category"] for alert in alerts)
    severity_counts = Counter(alert["severity"] for alert in alerts)
    top_alerts = sorted(
        alerts,
        key=lambda alert: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}[alert["severity"]],
            alert["confidence"],
        ),
        reverse=True,
    )[:3]

    lines = [
        "# Signal Extraction Handoff",
        "",
        "## Run Summary",
        "",
        f"- Documents processed: {len(documents)}",
        f"- Facts generated: {len(facts)}",
        f"- Alerts generated: {len(alerts)}",
        f"- Risk alerts: {category_counts.get('risk', 0)}",
        f"- Opportunity alerts: {category_counts.get('opportunity', 0)}",
        f"- Ownership/control alerts: {category_counts.get('ownership_control', 0)}",
        f"- Mixed alerts: {category_counts.get('mixed', 0)}",
        "",
        "## Severity Counts",
        "",
    ]
    for severity in ["critical", "high", "medium", "low"]:
        lines.append(f"- {severity}: {severity_counts.get(severity, 0)}")

    lines.extend(["", "## Top Demo Alerts", ""])
    for index, alert in enumerate(top_alerts, start=1):
        lines.append(
            f"{index}. {alert['customer_id']} - {alert['title']} - "
            f"{alert['severity']} severity, {alert['confidence']} confidence"
        )

    lines.extend(
        [
            "",
            "## Suppressed Or Skipped",
            "",
            f"- Low-confidence facts skipped: {skipped}",
            f"- Pre-baseline context facts not alerted: {suppression_stats['pre_baseline_context']}",
            f"- Duplicate facts clustered into shared alerts: {suppression_stats['duplicate_facts_clustered']}",
            "",
            "## Notes For Teammate 4",
            "",
            "- `alerts.json` includes an `evidence` list with source URL, title, published date, and excerpt.",
            "- `changed_fields`, `baseline_value`, and `new_value` are already shaped for before/after UI display.",
            "- `fact_ids` can be used to drill into `facts.json` for extraction details.",
        ]
    )
    return "\n".join(lines) + "\n"


def validate_outputs(facts, alerts, documents_by_id):
    fact_ids = {fact["fact_id"] for fact in facts}
    document_ids = set(documents_by_id)
    errors = []
    required_fact_fields = {
        "fact_id",
        "customer_id",
        "document_id",
        "fact_type",
        "subject",
        "baseline_fields_targeted",
        "evidence_excerpt",
        "source_quality",
        "extraction_confidence",
    }
    required_alert_fields = {
        "alert_id",
        "customer_id",
        "category",
        "signal_type",
        "title",
        "summary",
        "changed_fields",
        "baseline_value",
        "new_value",
        "severity",
        "confidence",
        "recommended_action",
        "evidence_document_ids",
        "fact_ids",
        "status",
        "created_at",
    }

    for fact in facts:
        missing = required_fact_fields - set(fact)
        if missing:
            errors.append(f"{fact.get('fact_id', '<missing>')} missing fact fields: {sorted(missing)}")
        if fact.get("document_id") not in document_ids:
            errors.append(f"{fact.get('fact_id')} references unknown document {fact.get('document_id')}")
        if not (fact.get("value") or fact.get("object")):
            errors.append(f"{fact.get('fact_id')} has neither value nor object")

    for alert in alerts:
        missing = required_alert_fields - set(alert)
        if missing:
            errors.append(f"{alert.get('alert_id', '<missing>')} missing alert fields: {sorted(missing)}")
        if not alert.get("fact_ids"):
            errors.append(f"{alert.get('alert_id')} has no fact IDs")
        if not alert.get("evidence_document_ids"):
            errors.append(f"{alert.get('alert_id')} has no evidence documents")
        for fact_id in alert.get("fact_ids") or []:
            if fact_id not in fact_ids:
                errors.append(f"{alert.get('alert_id')} references unknown fact {fact_id}")
        for document_id in alert.get("evidence_document_ids") or []:
            if document_id not in document_ids:
                errors.append(f"{alert.get('alert_id')} references unknown document {document_id}")

    category_counts = Counter(alert["category"] for alert in alerts)
    if len(alerts) < 8:
        errors.append("Fewer than 8 alerts generated")
    if category_counts.get("risk", 0) < 3:
        errors.append("Fewer than 3 risk alerts generated")
    if category_counts.get("opportunity", 0) < 3:
        errors.append("Fewer than 3 opportunity alerts generated")
    if category_counts.get("ownership_control", 0) < 1:
        errors.append("No ownership/control alert generated")
    return errors


def parse_args():
    parser = argparse.ArgumentParser(description="Extract facts and scored alerts from evidence documents.")
    parser.add_argument("--baselines", default="data_01/baseline_snapshots.json")
    parser.add_argument("--documents", default="data_02/documents.json")
    parser.add_argument("--output-dir", default="data_03")
    parser.add_argument("--created-at", default="2026-06-20T00:00:00Z")
    parser.add_argument("--skip-validation", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    baselines = load_json(args.baselines)
    documents = load_json(args.documents)
    baselines_by_customer = {baseline["customer_id"]: baseline for baseline in baselines}
    documents_by_id = {document["document_id"]: document for document in documents}

    facts, low_confidence_skipped = extract_facts(documents, baselines_by_customer)
    comparisons_by_fact_id = {
        fact["fact_id"]: compare_fact_to_baseline(
            fact,
            baselines_by_customer[fact["customer_id"]],
        )
        for fact in facts
    }
    alerts, suppression_stats = create_alerts(
        facts,
        comparisons_by_fact_id,
        baselines_by_customer,
        documents_by_id,
        args.created_at,
    )

    output_dir = Path(args.output_dir)
    write_json(output_dir / "facts.json", facts)
    write_json(output_dir / "alerts.json", alerts)
    (output_dir / "signal_run_report.md").write_text(
        report_lines(documents, facts, alerts, low_confidence_skipped, suppression_stats),
        encoding="utf-8",
        newline="\n",
    )

    errors = [] if args.skip_validation else validate_outputs(facts, alerts, documents_by_id)
    if errors:
        print("Signal extraction completed with validation errors:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    category_counts = Counter(alert["category"] for alert in alerts)
    print(
        "Signal extraction complete: "
        f"{len(documents)} documents, {len(facts)} facts, {len(alerts)} alerts "
        f"({category_counts.get('risk', 0)} risk, "
        f"{category_counts.get('opportunity', 0)} opportunity, "
        f"{category_counts.get('ownership_control', 0)} ownership/control)."
    )


if __name__ == "__main__":
    main()
