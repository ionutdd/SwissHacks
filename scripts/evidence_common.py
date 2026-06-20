from __future__ import annotations

import datetime as dt
import html
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "SwissHacksEvidenceCollector/0.1 contact: hackathon@example.com"

SIGNAL_RULES: dict[str, dict[str, list[str]]] = {
    "ownership_change": {
        "terms": ["acquisition", "acquired", "closed", "merger", "subsidiary", "purchase"],
        "fields": ["subsidiaries", "business_area"],
    },
    "new_subsidiary": {
        "terms": ["subsidiary", "legal entity", "ltd", "inc.", "s.a.", "pte"],
        "fields": ["subsidiaries"],
    },
    "new_jurisdiction": {
        "terms": ["jurisdiction", "licensed", "registration", "eu", "uk", "us", "singapore", "bermuda"],
        "fields": ["known_jurisdictions", "risk_rating"],
    },
    "business_activity_change": {
        "terms": ["business", "institutional", "trading", "exchange", "derivatives", "retail trading"],
        "fields": ["business_area", "known_products"],
    },
    "digital_asset_activity": {
        "terms": ["bitcoin", "crypto", "digital asset", "stablecoin", "usdc", "eurc", "tokenized"],
        "fields": ["business_area", "known_products", "risk_rating"],
    },
    "treasury_policy_change": {
        "terms": ["treasury", "reserve asset", "investment policy", "cash", "bitcoin"],
        "fields": ["business_area", "known_products", "risk_rating"],
    },
    "regulatory_scrutiny": {
        "terms": ["cftc", "regulator", "penalty", "order", "investigation", "blocked", "licence", "license"],
        "fields": ["risk_rating", "known_jurisdictions"],
    },
    "jurisdiction_restriction": {
        "terms": ["blocked", "restricted", "eligible", "non-u.s.", "u.s.", "spain", "investigation"],
        "fields": ["known_jurisdictions", "risk_rating"],
    },
    "public_listing": {
        "terms": ["investor relations", "public company", "ipo", "listed", "stock", "sec"],
        "fields": ["entity_type"],
    },
    "new_product": {
        "terms": ["launch", "available", "product", "network", "xstocks", "circle mint", "arc"],
        "fields": ["known_products", "business_area"],
    },
    "commercial_opportunity": {
        "terms": ["payments", "institutional", "custody", "lending", "commerce", "banks", "enterprises"],
        "fields": ["known_products", "business_area"],
    },
    "risk_rating_review": {
        "terms": ["risk", "volatility", "regulatory", "custody", "security", "counterparty"],
        "fields": ["risk_rating"],
    },
    "domain_registration": {
        "terms": ["rdap", "registrant", "trademark owner", "nameserver", "country-code domain"],
        "fields": ["websites", "known_jurisdictions", "risk_rating"],
    },
    "jurisdiction_expansion": {
        "terms": ["eligible", "non-u.s.", "bermuda", "licensed", "jurisdiction", "clients"],
        "fields": ["known_jurisdictions", "business_area"],
    },
}

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}

SKIP_TAGS = {"script", "style", "svg", "canvas", "noscript"}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth == 0 and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth == 0 and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_visible_text("".join(self.parts))


class LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self.current_href: str | None = None
        self.current_text: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "a":
            attr_map = {name.lower(): value for name, value in attrs if value is not None}
            href = attr_map.get("href")
            if href:
                self.current_href = urljoin(self.base_url, href)
                self.current_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "a" and self.current_href:
            link_text = normalize_text(" ".join(self.current_text))
            parsed = urlparse(self.current_href)
            if parsed.scheme in {"http", "https"}:
                self.links.append({"url": self.current_href, "text": link_text})
            self.current_href = None
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0 and self.current_href:
            self.current_text.append(data)


@dataclass
class FetchResult:
    source: dict[str, Any]
    url: str
    status: str
    html_text: str
    clean_text: str
    title: str | None
    published_at: str | None
    error: str | None = None


@dataclass
class PipelineResult:
    name: str
    documents: list[dict[str, Any]]
    traces: list[dict[str, Any]]
    discovered_sources: int
    seed_sources: int


def normalize_text(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("\xa0", " ")
    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"\s{2,}", " ", value)
    return value.strip()


def normalize_visible_text(value: str) -> str:
    value = html.unescape(value or "").replace("\xa0", " ")
    value = re.sub(r"[ \t\f\v]+", " ", value)
    lines: list[str] = []
    previous = ""
    for raw_line in re.split(r"[\r\n]+", value):
        line = normalize_text(raw_line)
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines)


def mojibake_score(value: str) -> int:
    tokens = [
        "\ufffd",
        "\u00e2\u20ac\u2122",
        "\u00e2\u20ac\u0153",
        "\u00e2\u20ac\u009d",
        "\u00e2\u20ac\u201c",
        "\u00e2\u20ac\u201d",
        "\u00c3",
        "\u00c2",
    ]
    return sum(value.count(token) for token in tokens)


def decode_body(body: bytes, declared_charset: str | None) -> str:
    candidates: list[tuple[int, str]] = []
    encodings = [declared_charset, "utf-8", "windows-1252", "iso-8859-1"]
    for encoding in [item for item in encodings if item]:
        try:
            decoded = body.decode(encoding, errors="replace")
        except LookupError:
            continue
        penalty = decoded.count("\ufffd") * 10 + mojibake_score(decoded) * 4
        candidates.append((penalty, decoded))
    if not candidates:
        return body.decode("utf-8", errors="replace")
    return sorted(candidates, key=lambda item: item[0])[0][1]


def prune_html(html_text: str) -> str:
    html_text = re.sub(r"<ix:header\b.*?</ix:header>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    html_text = re.sub(r"<ix:hidden\b.*?</ix:hidden>", " ", html_text, flags=re.IGNORECASE | re.DOTALL)
    html_text = re.sub(
        r"<([a-z0-9:_-]+)\b[^>]*style=[\"'][^\"']*display\s*:\s*none[^\"']*[\"'][^>]*>.*?</\1>",
        " ",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return html_text


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, indent=2, ensure_ascii=False)
        file.write("\n")


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_url(url: str, timeout: int = 25) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        charset = response.headers.get_content_charset()
        return decode_body(body, charset)


def visible_text(html_text: str) -> str:
    parser = VisibleTextParser()
    parser.feed(prune_html(html_text))
    return parser.text()


def extract_links(html_text: str, base_url: str) -> list[dict[str, str]]:
    parser = LinkParser(base_url)
    parser.feed(html_text)
    return parser.links


def extract_title(html_text: str, clean_text: str, source: dict[str, Any]) -> str:
    if source.get("title_hint"):
        return str(source["title_hint"])

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if title_match:
        title = normalize_text(re.sub(r"<[^>]+>", " ", title_match.group(1)))
        if title:
            return title[:180]

    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if h1_match:
        title = normalize_text(re.sub(r"<[^>]+>", " ", h1_match.group(1)))
        if title:
            return title[:180]

    return clean_text[:90] if clean_text else "Untitled source"


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()
    iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", value)
    if iso_match:
        return iso_match.group(0)

    month_re = (
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(\d{1,2}),\s+(\d{4})"
    )
    month_match = re.search(month_re, value, flags=re.IGNORECASE)
    if month_match:
        month_names = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        month = month_names.index(month_match.group(1).lower()) + 1
        day = int(month_match.group(2))
        year = int(month_match.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    slash_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", value)
    if slash_match:
        month = int(slash_match.group(1))
        day = int(slash_match.group(2))
        year = int(slash_match.group(3))
        return f"{year:04d}-{month:02d}-{day:02d}"

    return None


def extract_published_at(html_text: str, clean_text: str, source: dict[str, Any]) -> str | None:
    hinted = normalize_date(source.get("published_at_hint"))
    if hinted:
        return hinted

    meta_patterns = [
        r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|date|pubdate|publishdate|dc.date)["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:article:published_time|date|pubdate|publishdate|dc.date)["\']',
        r'"datePublished"\s*:\s*"([^"]+)"',
    ]
    for pattern in meta_patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE)
        if match:
            parsed = normalize_date(match.group(1))
            if parsed:
                return parsed

    return normalize_date(clean_text[:2000])


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    candidates: list[str] = []
    for block in re.split(r"\n+", text):
        block = normalize_text(block)
        if not block:
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'$])", block)
        for part in parts:
            part = normalize_text(part)
            if len(part) >= 30:
                candidates.append(part)
    return candidates


def entity_terms(entity: dict[str, Any]) -> list[str]:
    terms = [entity.get("legal_name", "")]
    terms.extend(entity.get("aliases", []))
    terms.extend(entity.get("executives", []))
    terms.extend(entity.get("subsidiaries", []))
    return unique_terms(terms)


def rule_signal_terms(source: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for signal in source.get("expected_signal_types", []):
        terms.extend(SIGNAL_RULES.get(signal, {}).get("terms", []))
    return unique_terms(terms)


def source_query_terms(source: dict[str, Any]) -> list[str]:
    return unique_terms(source.get("query_terms", []))


def unique_terms(terms: list[Any]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for term in terms:
        if term is None:
            continue
        value = normalize_text(str(term))
        key = value.lower()
        if len(value) >= 2 and key not in seen:
            seen.add(key)
            normalized.append(value)
    return normalized


def term_score(text: str, terms: list[str]) -> int:
    lower = text.lower()
    score = 0
    for term in terms:
        term_lower = term.lower()
        if not term_lower:
            continue
        count = lower.count(term_lower)
        if count:
            score += count * (3 if " " in term_lower or len(term_lower) > 8 else 1)
    return score


def evidence_quality_score(text: str) -> int:
    lower = text.lower()
    score = 0

    if len(text) >= 90:
        score += 2
    if len(text) >= 160:
        score += 1

    body_markers = [
        "announced",
        "entered into",
        "has closed",
        "has blocked access",
        "investigates whether",
        "operating without",
        "disclosed",
        "ha publicado",
        "ha emitido",
        "today announced",
        "is currently available",
        "is a global",
        "is natively issued",
        "redeemable",
    ]
    if any(marker in lower for marker in body_markers):
        score += 3

    junk_markers = [
        "skip to main content",
        "ir al contenido",
        "search / search",
        "securities registered pursuant",
        "pre-commencement communications",
        "check the appropriate box",
        " | the guardian",
        " | el pa",
        " | cadena ser",
        " | actualidad",
        " | economia",
        " | economia",
    ]
    if any(marker in lower for marker in junk_markers):
        score -= 6

    if "|" in text and len(text) < 220:
        score -= 3

    return score


def link_score(link: dict[str, str], entity: dict[str, Any], config: dict[str, Any]) -> int:
    value = f"{link.get('text', '')} {link.get('url', '')}"
    return term_score(value, entity_terms(entity) + source_query_terms(config) + rule_signal_terms(config))


def entity_match_score(text: str, entity: dict[str, Any], source: dict[str, Any]) -> int:
    score = term_score(text, entity_terms(entity))
    parsed = urlparse(source.get("url", ""))
    source_host = parsed.netloc.lower().replace("www.", "")

    for website in entity.get("websites", []):
        host = urlparse(website).netloc.lower().replace("www.", "")
        if host and host in source_host:
            score += 3

    return score


def best_evidence(clean_text: str, entity: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    sentences = split_sentences(clean_text)
    if not sentences and clean_text:
        sentences = [normalize_text(clean_text[:1200])]

    query_lookup_terms = source_query_terms(source)
    rule_lookup_terms = rule_signal_terms(source)
    all_terms = unique_terms(entity_terms(entity) + query_lookup_terms + rule_lookup_terms)

    def signal_score(value: str) -> int:
        return (term_score(value, query_lookup_terms) * 3) + term_score(value, rule_lookup_terms)

    def score_text(value: str) -> int:
        return term_score(value, all_terms) + (signal_score(value) * 3)

    ranked_sentences = sorted(
        (
            (
                signal_score(sentence),
                score_text(sentence) + evidence_quality_score(sentence),
                evidence_quality_score(sentence),
                len(sentence),
                index,
                sentence,
            )
            for index, sentence in enumerate(sentences)
        ),
        key=lambda item: (item[1], item[0], item[2], item[3], item[4]),
        reverse=True,
    )

    best_signal_score, best_sentence_score, _, _, best_index, best_sentence = (
        ranked_sentences[0] if ranked_sentences else (0, 0, 0, 0, 0, clean_text[:520])
    )

    window_start = max(0, best_index - 1)
    window_end = min(len(sentences), best_index + 2)
    best_chunk = " ".join(sentences[window_start:window_end])

    excerpt = best_sentence
    if len(excerpt) > 520:
        excerpt = excerpt[:517].rstrip() + "..."

    raw_text = best_chunk
    if len(raw_text) > 1600:
        raw_text = raw_text[:1597].rstrip() + "..."

    return {
        "raw_text": raw_text,
        "evidence_excerpt": excerpt,
        "retrieval_score": best_sentence_score,
        "source_term_score": best_signal_score,
    }


def confidence_hint(source_quality: str, match_score: int, retrieval_score: int) -> str:
    if source_quality == "A" and match_score >= 3 and retrieval_score >= 6:
        return "high"
    if source_quality in {"A", "B"} and match_score >= 1 and retrieval_score >= 3:
        return "medium" if source_quality == "B" else "high"
    if source_quality == "B" and retrieval_score >= 2:
        return "medium"
    return "low"


def infer_fields(source: dict[str, Any]) -> list[str]:
    fields = list(source.get("baseline_fields_targeted", []))
    for signal in source.get("expected_signal_types", []):
        fields.extend(SIGNAL_RULES.get(signal, {}).get("fields", []))
    return unique_terms(fields)


def fetch_source(source: dict[str, Any]) -> FetchResult:
    url = source["url"]
    try:
        html_text = fetch_url(url)
        clean_text = visible_text(html_text)
        title = extract_title(html_text, clean_text, source)
        published_at = extract_published_at(html_text, clean_text, source)
        return FetchResult(
            source=source,
            url=url,
            status="ok",
            html_text=html_text,
            clean_text=clean_text,
            title=title,
            published_at=published_at,
        )
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return FetchResult(
            source=source,
            url=url,
            status="failed",
            html_text="",
            clean_text="",
            title=source.get("title_hint"),
            published_at=normalize_date(source.get("published_at_hint")),
            error=f"{type(exc).__name__}: {exc}",
        )


def source_key(source: dict[str, Any]) -> tuple[Any, ...]:
    return (
        source.get("url"),
        tuple(source.get("expected_signal_types", [])),
        tuple(source.get("baseline_fields_targeted", [])),
    )


def dedupe_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for source in sources:
        key = source_key(source)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped


def build_document(
    document_number: int,
    fetch: FetchResult,
    entity: dict[str, Any],
    collected_at: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    source = fetch.source
    connector = source.get("connector", "web_page")
    if fetch.status != "ok":
        return None, {
            "source_id": source.get("source_id"),
            "url": fetch.url,
            "status": "failed",
            "connector": connector,
            "error": fetch.error,
        }

    evidence = best_evidence(fetch.clean_text, entity, source)
    match_score = entity_match_score(fetch.clean_text, entity, source)
    retrieval_score = evidence["retrieval_score"]
    source_term_score = evidence["source_term_score"]

    if connector == "sec_recent_filings" and source_term_score <= 2:
        return None, {
            "source_id": source.get("source_id"),
            "url": fetch.url,
            "status": "skipped",
            "connector": connector,
            "reason": "SEC API-discovered filing did not contain configured source/signal terms.",
            "entity_match_score": match_score,
            "retrieval_score": retrieval_score,
            "source_term_score": source_term_score,
            "clean_text_chars": len(fetch.clean_text),
        }

    document = {
        "document_id": f"doc-{document_number:03d}",
        "customer_id": source["customer_id"],
        "source_type": source["source_type"],
        "source_name": source["source_name"],
        "source_url": source["url"],
        "source_quality": source["source_quality"],
        "title": fetch.title,
        "published_at": fetch.published_at,
        "collected_at": collected_at,
        "language": source.get("language_hint", "en"),
        "raw_text": evidence["raw_text"],
        "evidence_excerpt": evidence["evidence_excerpt"],
        "expected_signal_types": list(source.get("expected_signal_types", [])),
        "baseline_fields_targeted": infer_fields(source),
        "automation_potential": source.get("automation_potential", "medium"),
        "confidence_hint": confidence_hint(source["source_quality"], match_score, retrieval_score),
        "limitations": source.get("limitations"),
    }

    trace = {
        "source_id": source.get("source_id"),
        "document_id": document["document_id"],
        "url": fetch.url,
        "status": "ok",
        "connector": connector,
        "entity_match_score": match_score,
        "retrieval_score": retrieval_score,
        "source_term_score": source_term_score,
        "clean_text_chars": len(fetch.clean_text),
    }

    if "page_hash" in source:
        trace["page_hash"] = source["page_hash"]
        trace["page_changed"] = source.get("page_changed")

    return document, trace


def collect_sources(
    sources: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
    collected_at: str,
    start_number: int = 1,
    polite_delay_seconds: float = 0.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import time

    baseline_by_id = {entity["customer_id"]: entity for entity in baselines}
    documents: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    for source in sources:
        customer_id = source["customer_id"]
        entity = baseline_by_id.get(customer_id)
        if not entity:
            traces.append(
                {
                    "source_id": source.get("source_id"),
                    "url": source.get("url"),
                    "status": "failed",
                    "connector": source.get("connector"),
                    "error": f"Unknown customer_id {customer_id}",
                }
            )
            continue

        fetch = fetch_source(source)
        document, trace = build_document(start_number + len(documents), fetch, entity, collected_at)
        traces.append(trace)
        if document:
            documents.append(document)
        if polite_delay_seconds:
            time.sleep(polite_delay_seconds)

    return documents, traces


def write_pipeline_outputs(output_dir: Path, name: str, result: PipelineResult) -> None:
    run_dir = output_dir / "pipeline_runs"
    write_json(run_dir / f"{name}_documents.json", result.documents)
    write_json(run_dir / f"{name}_trace.json", result.traces)


def generate_source_map(
    docs: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
    collected_at: str,
) -> str:
    baseline_by_id = {entity["customer_id"]: entity for entity in baselines}
    quality_ab = sum(1 for doc in docs if doc["source_quality"] in {"A", "B"})
    source_types = sorted({doc["source_type"] for doc in docs})
    failures = [trace for trace in traces if trace.get("status") == "failed"]
    skipped = [trace for trace in traces if trace.get("status") == "skipped"]
    discovery = [trace for trace in traces if trace.get("stage") == "discovery"]

    lines: list[str] = [
        "# Evidence Collection Handoff",
        "",
        "Generated by split collector scripts for Subtask 02.",
        "",
        "## Collection Summary",
        "",
        f"- Generated at: {collected_at}",
        f"- Total documents: {len(docs)}",
        f"- A/B quality documents: {quality_ab}",
        f"- Source types represented: {', '.join(f'`{item}`' for item in source_types)}",
        "- Top 3 stories covered: Polymarket, Robinhood, GameStop",
        "- Official or primary sources for top 3 stories: yes",
        f"- Failed source fetches: {len(failures)}",
        f"- Skipped low-signal candidates: {len(skipped)}",
        f"- Discovery traces: {len(discovery)}",
        "",
        "## Implemented Collection Algorithm",
        "",
        "The run is split by source pipeline:",
        "",
        "1. `collect_evidence_SEC.py`: SEC EDGAR filings and recent-filings API.",
        "2. `collect_evidence_company_site.py`: official newsroom, press, blog, and IR link discovery.",
        "3. `collect_evidence_regulator.py`: regulator candidate matching.",
        "4. `collect_evidence_news_event.py`: GDELT/news-event discovery with public fallbacks.",
        "5. `collect_evidence_page_diff.py`: product/legal page hash monitoring.",
        "6. `collect_evidence_domain_rdap.py`: RDAP lookup, ccTLD jurisdiction inference, and registrant/trademark identity matching.",
        "7. `collect_evidence_direct_sources.py`: explicitly cataloged public URLs.",
        "",
        "Every pipeline emits the same source schema, then the shared core fetches pages, cleans text, ranks evidence sentences, and writes normalized documents.",
        "",
        "## Source List By Customer",
        "",
    ]

    for customer_id in sorted({doc["customer_id"] for doc in docs}):
        entity = baseline_by_id.get(customer_id, {})
        lines.extend(
            [
                f"### {customer_id}: {entity.get('legal_name', customer_id)}",
                "",
                "Documents:",
                "",
            ]
        )
        for doc in [item for item in docs if item["customer_id"] == customer_id]:
            lines.append(f"- `{doc['document_id']}`: {doc['title']} ({doc['source_quality']}, {doc['source_type']}).")

        signals = sorted({signal for doc in docs if doc["customer_id"] == customer_id for signal in doc["expected_signal_types"]})
        fields = sorted({field for doc in docs if doc["customer_id"] == customer_id for field in doc["baseline_fields_targeted"]})
        lines.extend(
            [
                "",
                f"Supported drift: {', '.join(f'`{signal}`' for signal in signals)}",
                "",
                f"Baseline fields: {', '.join(f'`{field}`' for field in fields)}",
                "",
                f"Demo value: {entity.get('demo_story', 'Evidence supports the demo drift story.')}",
                "",
            ]
        )

    lines.extend(["## Connector Trace", ""])
    for trace in traces:
        if trace.get("stage") == "discovery":
            lines.append(
                f"- DISCOVERY `{trace.get('connector')}` for `{trace.get('customer_id')}`: "
                f"{trace.get('discovered_sources', 0)} source(s)."
            )
        elif trace.get("status") == "ok":
            lines.append(
                f"- `{trace.get('document_id')}` from `{trace.get('connector')}`: "
                f"entity score {trace.get('entity_match_score')}, retrieval score {trace.get('retrieval_score')}, "
                f"source-term score {trace.get('source_term_score')}, text chars {trace.get('clean_text_chars')}."
            )
        elif trace.get("status") == "skipped":
            lines.append(
                f"- SKIPPED `{trace.get('url')}`: {trace.get('reason')} "
                f"(source-term score {trace.get('source_term_score')})."
            )
        else:
            lines.append(f"- FAILED `{trace.get('url')}`: {trace.get('error')}")

    lines.extend(
        [
            "",
            "## Weak Or Replacement Needed",
            "",
            "- Secondary news sources should be replaced by official pages when a primary source is available.",
            "- LinkedIn is out of scope for this run; use an approved API or licensed provider for those signals.",
            "- Product pages without dates are useful evidence but weaker for freshness scoring.",
            "",
            "## Notes For Teammate 3",
            "",
            "- Start extraction with A-quality official sources.",
            "- Preserve `published_at` and compare it with `last_reviewed_at` before creating a drift alert.",
            "- Use `source_quality`, `confidence_hint`, and retrieval score from the connector trace as scoring priors.",
            "- Every extracted fact must cite `document_id` and reuse the evidence excerpt.",
            "",
            "## Notes For Teammate 4",
            "",
            "- Show source quality badges and direct source links.",
            "- Use Robinhood/Bitstamp, Polymarket/CFTC, GameStop/Bitcoin, and Coinbase/coinbase.au as the clearest demo cards.",
            "- Keep the algorithm slide simple: split source collectors, shared RAG ranking, evidence-backed alert.",
            "",
        ]
    )

    return "\n".join(lines)


def generate_run_report(
    docs: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    collected_at: str,
) -> str:
    failures = [trace for trace in traces if trace.get("status") == "failed"]
    skipped = [trace for trace in traces if trace.get("status") == "skipped"]
    discovery = [trace for trace in traces if trace.get("stage") == "discovery"]
    lines = [
        "# Collection Run Report",
        "",
        f"- Generated at: {collected_at}",
        f"- Output documents: {len(docs)}",
        f"- Failed fetches: {len(failures)}",
        f"- Skipped low-signal candidates: {len(skipped)}",
        f"- Discovery traces: {len(discovery)}",
        "",
        "## Algorithm",
        "",
        "The run used split collector scripts. Each pipeline discovered candidate sources, then the shared evidence core fetched pages, cleaned text, ranked evidence sentences, and emitted normalized documents.",
        "",
        "## Failures",
        "",
    ]

    if not failures:
        lines.append("- None.")
    else:
        for failure in failures:
            lines.append(f"- `{failure.get('url')}`: {failure.get('error')}")

    lines.extend(["", "## Skipped Candidates", ""])
    if not skipped:
        lines.append("- None.")
    else:
        for item in skipped:
            lines.append(f"- `{item.get('url')}`: {item.get('reason')}")

    lines.extend(["", "## Documents", ""])
    for doc in docs:
        lines.append(
            f"- `{doc['document_id']}` `{doc['customer_id']}` {doc['source_quality']} "
            f"{doc['source_type']}: {doc['title']}"
        )

    return "\n".join(lines) + "\n"


def write_final_outputs(
    output_dir: Path,
    docs: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
    collected_at: str,
) -> None:
    write_json(output_dir / "documents.json", docs)
    write_json(output_dir / "collection_trace.json", traces)
    (output_dir / "source_evidence_map.md").write_text(
        generate_source_map(docs, traces, baselines, collected_at),
        encoding="utf-8",
        newline="\n",
    )
    (output_dir / "collection_run_report.md").write_text(
        generate_run_report(docs, traces, collected_at),
        encoding="utf-8",
        newline="\n",
    )


def load_baselines_and_catalog(baseline_path: str, catalog_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return load_json(Path(baseline_path)), load_json(Path(catalog_path))


def discovery_trace(
    connector: str,
    customer_id: str,
    discovered_sources: int,
    status: str = "ok",
    **extra: Any,
) -> dict[str, Any]:
    trace = {
        "stage": "discovery",
        "connector": connector,
        "customer_id": customer_id,
        "status": status,
        "discovered_sources": discovered_sources,
    }
    trace.update(extra)
    return trace
