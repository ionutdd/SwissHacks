#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ALLOWED_SIGNAL_FIELDS: dict[str, set[str]] = {
    "ownership_change": {"subsidiaries", "business_area", "risk_rating"},
    "new_subsidiary": {"subsidiaries", "known_jurisdictions", "risk_rating"},
    "new_jurisdiction": {"known_jurisdictions", "risk_rating"},
    "business_activity_change": {"business_area", "known_products", "risk_rating"},
    "digital_asset_activity": {"business_area", "known_products", "risk_rating"},
    "treasury_policy_change": {"business_area", "known_products", "risk_rating"},
    "regulatory_scrutiny": {"risk_rating", "business_area"},
    "jurisdiction_restriction": {"known_jurisdictions", "risk_rating"},
    "new_product": {"known_products", "business_area"},
    "public_listing": {"entity_type", "known_products"},
    "commercial_opportunity": {"known_products", "business_area"},
    "domain_registration": {"websites", "known_jurisdictions", "risk_rating"},
    "risk_rating_review": {"risk_rating", "known_products", "business_area"},
}

ALLOWED_SIGNAL_TYPES = sorted(ALLOWED_SIGNAL_FIELDS)
ALLOWED_KYC_FIELDS = sorted({field for fields in ALLOWED_SIGNAL_FIELDS.values() for field in fields})
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ENV_KEYS = ("APERTUS_API_KEY", "APERTUS_BASE_URL", "APERTUS_MODEL")
MAX_TEXT_CHARS = 7000
ANALYSIS_VERSION = "ai-evidence-analysis-v1"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SignalWatch/0.1"
SIGNAL_TYPE_ALIASES = {
    "adverse_media": "regulatory_scrutiny",
    "negative_news": "regulatory_scrutiny",
    "legal_risk": "regulatory_scrutiny",
    "regulatory_action": "regulatory_scrutiny",
    "sanctions_exposure": "jurisdiction_restriction",
    "sanctioned_country_exposure": "jurisdiction_restriction",
    "jurisdiction_expansion": "new_jurisdiction",
    "geographic_expansion": "new_jurisdiction",
    "country_expansion": "new_jurisdiction",
    "market_entry": "new_jurisdiction",
    "new_market": "new_jurisdiction",
    "business_model_change": "business_activity_change",
    "business_pivot": "business_activity_change",
    "product_launch": "new_product",
    "new_service": "new_product",
    "funding_round": "commercial_opportunity",
    "commercial_expansion": "commercial_opportunity",
    "domain_switch": "domain_registration",
    "website_change": "business_activity_change",
    "kyc_refresh": "risk_rating_review",
    "risk_reclassification": "risk_rating_review",
}
FIELD_ALIASES = {
    "jurisdiction": "known_jurisdictions",
    "jurisdictions": "known_jurisdictions",
    "countries": "known_jurisdictions",
    "country": "known_jurisdictions",
    "products": "known_products",
    "product": "known_products",
    "services": "known_products",
    "service": "known_products",
    "business_model": "business_area",
    "business_activity": "business_area",
    "activity": "business_area",
    "risk": "risk_rating",
    "risk_level": "risk_rating",
    "rating": "risk_rating",
    "legal_entities": "subsidiaries",
    "legal_entity": "subsidiaries",
    "entities": "subsidiaries",
    "domain": "websites",
    "website": "websites",
    "entity": "entity_type",
}


class ApertusConfigError(RuntimeError):
    pass


class ApertusAPIError(RuntimeError):
    def __init__(self, message: str, diagnostics: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics or {}


class ModelValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ApertusConfig:
    api_key: str
    base_url: str
    model: str

    @property
    def chat_completions_url(self) -> str:
        base = self.base_url.strip().rstrip("/")
        base = re.sub(r"(/chat/completions)+$", "/chat/completions", base)
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def unquote_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_local_env(env_path: str | Path = ".env") -> dict[str, str]:
    path = Path(env_path)
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^\$env:([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match:
            continue
        key = match.group(1).strip()
        value = unquote_env_value(match.group(2))
        loaded[key] = value
        os.environ.setdefault(key, value)
    return loaded


def load_apertus_config(env_path: str | Path = ".env") -> ApertusConfig:
    load_local_env(env_path)
    values = {key: os.environ.get(key, "").strip() for key in ENV_KEYS}
    missing = [key for key, value in values.items() if not value]
    if missing:
        missing_display = ", ".join(missing)
        raise ApertusConfigError(
            f"Missing Apertus API configuration: {missing_display}. "
            "Set them in .env using APERTUS_API_KEY=, APERTUS_BASE_URL=, APERTUS_MODEL=."
        )
    return ApertusConfig(
        api_key=values["APERTUS_API_KEY"],
        base_url=values["APERTUS_BASE_URL"],
        model=values["APERTUS_MODEL"],
    )


def apertus_user_agent() -> str:
    return os.environ.get("APERTUS_USER_AGENT", DEFAULT_USER_AGENT).strip() or DEFAULT_USER_AGENT


def clean_spaces(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_for_quote(value: str) -> str:
    value = html.unescape(value or "")
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\xa0": " ",
    }
    for before, after in replacements.items():
        value = value.replace(before, after)
    return clean_spaces(value).lower()


def document_text(document: dict[str, Any]) -> str:
    parts = [
        document.get("title"),
        document.get("evidence_excerpt"),
        document.get("raw_text"),
    ]
    return clean_spaces(" ".join(str(part) for part in parts if part))


def quote_in_document(quote: str, document: dict[str, Any]) -> bool:
    normalized_quote = normalize_for_quote(quote)
    normalized_text = normalize_for_quote(document_text(document))
    return bool(normalized_quote and normalized_quote in normalized_text)


def normalize_identifier(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_spaces(value).lower()).strip("_")


def normalize_signal_type(value: Any, document: dict[str, Any], warnings: list[str]) -> str:
    signal_type = normalize_identifier(value)
    signal_type = SIGNAL_TYPE_ALIASES.get(signal_type, signal_type)
    if signal_type in ALLOWED_SIGNAL_FIELDS:
        return signal_type

    expected = [item for item in document.get("expected_signal_types") or [] if item in ALLOWED_SIGNAL_FIELDS]
    fallback = expected[0] if expected else "business_activity_change"
    warnings.append(f"Unsupported Apertus signal_type '{clean_spaces(value) or '<empty>'}' mapped to '{fallback}'.")
    return fallback


def normalize_changed_fields(value: Any, signal_type: str, document: dict[str, Any], warnings: list[str]) -> list[str]:
    raw_fields = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for field in raw_fields:
        mapped = FIELD_ALIASES.get(normalize_identifier(field), normalize_identifier(field))
        if mapped in ALLOWED_SIGNAL_FIELDS[signal_type]:
            normalized.append(mapped)
        elif mapped in ALLOWED_KYC_FIELDS:
            warnings.append(f"Apertus field '{clean_spaces(field)}' is not supported for {signal_type}; ignored.")

    if not normalized:
        for field in document.get("baseline_fields_targeted") or []:
            mapped = FIELD_ALIASES.get(normalize_identifier(field), normalize_identifier(field))
            if mapped in ALLOWED_SIGNAL_FIELDS[signal_type]:
                normalized.append(mapped)

    if not normalized:
        normalized.append(sorted(ALLOWED_SIGNAL_FIELDS[signal_type])[0])
        warnings.append(f"Missing supported changed_kyc_fields; inferred '{normalized[0]}' for {signal_type}.")

    return sorted(dict.fromkeys(normalized))


def normalize_severity(value: Any, warnings: list[str]) -> str:
    severity = clean_spaces(value).lower()
    if severity in ALLOWED_SEVERITIES:
        return severity
    warnings.append(f"Unsupported severity_suggestion '{severity or '<empty>'}' normalized to 'medium'.")
    return "medium"


def normalize_confidence(value: Any, warnings: list[str]) -> float:
    original = value
    if isinstance(value, str):
        text = value.strip().replace("%", "")
        try:
            value = float(text)
            if value > 1:
                value = value / 100
        except ValueError:
            value = 0.7
            warnings.append(f"Unsupported confidence '{clean_spaces(original)}' normalized to 0.7.")
    elif not isinstance(value, (int, float)):
        value = 0.7
        warnings.append("Missing confidence normalized to 0.7.")

    value = float(value)
    if value < 0 or value > 1:
        warnings.append(f"Out-of-range confidence '{original}' clamped into 0..1.")
    return round(max(0.0, min(1.0, value)), 2)


def source_supported_quote(candidate_quote: str, document: dict[str, Any], warnings: list[str]) -> str:
    quote = clean_spaces(candidate_quote)
    if quote and quote_in_document(quote, document):
        return quote

    excerpt = clean_spaces(document.get("evidence_excerpt"))
    if excerpt:
        warnings.append("Apertus evidence quote was not exact; replaced with collected source excerpt.")
        return excerpt[:500]

    text = document_text(document)
    sentences = [clean_spaces(item) for item in re.split(r"(?<=[.!?])\s+", text) if clean_spaces(item)]
    if sentences:
        warnings.append("Apertus evidence quote was not exact; replaced with first source sentence.")
        return sentences[0][:500]

    warnings.append("Apertus evidence quote was not exact and source text was empty; using title as evidence quote.")
    return clean_spaces(document.get("title"))[:500]


def coerce_bool_default_true(value: Any, field_name: str, warnings: list[str]) -> bool:
    try:
        return coerce_bool(value, field_name)
    except ModelValidationError:
        warnings.append(f"{field_name} was not boolean; normalized to true.")
        return True


def baseline_for_prompt(baseline: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "customer_id",
        "legal_name",
        "aliases",
        "entity_type",
        "domicile",
        "business_area",
        "risk_rating",
        "known_jurisdictions",
        "known_products",
        "subsidiaries",
        "websites",
        "last_reviewed_at",
        "expected_drift_types",
    ]
    return {key: baseline.get(key) for key in keys if key in baseline}


def document_for_prompt(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": document.get("document_id"),
        "source_url": document.get("source_url"),
        "source_name": document.get("source_name"),
        "source_type": document.get("source_type"),
        "source_quality": document.get("source_quality"),
        "title": document.get("title"),
        "published_at": document.get("published_at"),
        "evidence_excerpt": document.get("evidence_excerpt"),
        "article_text": document_text(document)[:MAX_TEXT_CHARS],
    }


def build_messages(document: dict[str, Any], baseline: dict[str, Any]) -> list[dict[str, str]]:
    schema = {
        "relevant": True,
        "entity_match": True,
        "signal_candidates": [
            {
                "signal_type": "one allowed signal type",
                "changed_kyc_fields": ["one or more allowed KYC fields"],
                "severity_suggestion": "low|medium|high|critical",
                "confidence": 0.0,
                "claim": "short factual claim",
                "reason": "why this differs from the baseline",
                "verbatim_evidence": "exact short quote from the supplied document only",
                "effective_date": "YYYY-MM-DD or null",
                "needs_human_review": True,
            }
        ],
        "no_signal_reason": "required when signal_candidates is empty",
    }
    payload = {
        "customer": {
            "legal_name": baseline.get("legal_name"),
            "aliases": baseline.get("aliases") or [],
        },
        "baseline_kyc": baseline_for_prompt(baseline),
        "document": document_for_prompt(document),
        "allowed_signal_types": ALLOWED_SIGNAL_TYPES,
        "allowed_kyc_fields_by_signal_type": {
            key: sorted(value) for key, value in ALLOWED_SIGNAL_FIELDS.items()
        },
        "required_output_schema": schema,
    }
    return [
        {
            "role": "system",
            "content": (
                "You are an evidence-analysis component for a bank KYC drift prototype. "
                "Use only the supplied document and baseline. Do not use outside knowledge. "
                "Return every supported signal candidate that is directly supported by the document, up to 4 candidates. "
                "Set effective_date to null unless a date is explicitly present in the supplied document metadata or text. "
                "Return strict JSON only. Do not update KYC data. If evidence is weak, return no candidates."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
        },
    ]


def prompt_char_count(messages: list[dict[str, str]]) -> int:
    return sum(len(message.get("content", "")) for message in messages)


def response_headers_to_dict(headers: Any) -> dict[str, str]:
    useful: dict[str, str] = {}
    for key, value in getattr(headers, "items", lambda: [])():
        key_text = str(key)
        if key_text.lower() in {
            "content-type",
            "content-length",
            "date",
            "server",
            "x-request-id",
            "request-id",
            "retry-after",
        }:
            useful[key_text] = str(value)
    return useful


def request_diagnostics(
    *,
    config: ApertusConfig,
    messages: list[dict[str, str]],
    timeout: int,
    request_payload: dict[str, Any],
    document_text_length: int | None = None,
) -> dict[str, Any]:
    return {
        "request_url": config.chat_completions_url,
        "model": config.model,
        "timeout_seconds": timeout,
        "request_user_agent": apertus_user_agent(),
        "prompt_char_count": prompt_char_count(messages),
        "request_payload_char_count": len(json.dumps(request_payload, ensure_ascii=False)),
        "document_text_char_count": document_text_length,
    }


def call_apertus_openai_compatible(
    messages: list[dict[str, str]],
    config: ApertusConfig,
    timeout: int = 45,
    document_text_length: int | None = None,
) -> str:
    request_payload = {
        "model": config.model,
        "messages": messages,
        "temperature": 0,
    }
    diagnostics = request_diagnostics(
        config=config,
        messages=messages,
        timeout=timeout,
        request_payload=request_payload,
        document_text_length=document_text_length,
    )
    request = Request(
        config.chat_completions_url,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": apertus_user_agent(),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except OSError:
            body = "<could not read HTTPError response body>"
        raise ApertusAPIError(
            "Apertus API request failed with HTTPError.",
            {
                **diagnostics,
                "http_status_code": exc.code,
                "http_reason": exc.reason,
                "response_body_text": body,
                "response_headers": response_headers_to_dict(exc.headers),
            },
        ) from exc
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise ApertusAPIError(
            f"Apertus API request failed: {type(exc).__name__}",
            {
                **diagnostics,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        ) from exc

    try:
        return response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ApertusAPIError(
            "Apertus API response did not match OpenAI-compatible chat format.",
            {
                **diagnostics,
                "response_shape_error": type(exc).__name__,
            },
        ) from exc


def parse_json_object(raw_output: str) -> dict[str, Any]:
    text = clean_spaces(raw_output)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        payload = parse_first_json_object(text)
    if not isinstance(payload, dict):
        raise ModelValidationError("Model output must be a JSON object.")
    return payload


def parse_first_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    if start < 0:
        raise ModelValidationError("Model output is not valid JSON: no JSON object found.")

    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        character = text[index]
        if in_string:
            if escape:
                escape = False
            elif character == "\\":
                escape = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : index + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as exc:
                    raise ModelValidationError(f"Model output is not valid JSON: {exc.msg}") from exc

    raise ModelValidationError("Model output is not valid JSON: incomplete JSON object.")


def coerce_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes"}:
            return True
        if normalized in {"false", "no"}:
            return False
    raise ModelValidationError(f"{field_name} must be boolean.")


def validate_candidate(candidate: Any, document: dict[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ModelValidationError(f"signal_candidates[{index}] must be an object.")

    warnings: list[str] = []
    signal_type = normalize_signal_type(candidate.get("signal_type"), document, warnings)
    normalized_fields = normalize_changed_fields(candidate.get("changed_kyc_fields"), signal_type, document, warnings)
    severity = normalize_severity(candidate.get("severity_suggestion"), warnings)
    confidence = normalize_confidence(candidate.get("confidence"), warnings)

    claim = clean_spaces(candidate.get("claim")) or clean_spaces(document.get("title")) or f"{signal_type} signal detected"
    reason = clean_spaces(candidate.get("reason")) or "Apertus identified this as different from the supplied baseline."
    evidence = source_supported_quote(clean_spaces(candidate.get("verbatim_evidence")), document, warnings)

    effective_date = candidate.get("effective_date")
    effective_date_source = "null"
    if effective_date is not None:
        effective_date = clean_spaces(effective_date)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", effective_date):
            effective_date = None
            effective_date_source = "invalid_model_date_normalized_to_null"
            warnings.append(f"Apertus effective_date was not YYYY-MM-DD; normalized to null.")
        else:
            if effective_date == document.get("published_at"):
                effective_date_source = "document_published_at"
            elif effective_date in document_text(document):
                effective_date_source = "document_text"
            else:
                effective_date = None
                effective_date_source = "model_supplied_date_not_in_source_normalized_to_null"
                warnings.append("Apertus effective_date was not present in source text; normalized to null.")

    needs_human_review = coerce_bool_default_true(
        candidate.get("needs_human_review"),
        f"{signal_type} needs_human_review",
        warnings,
    )
    if not needs_human_review:
        warnings.append(f"Apertus set needs_human_review to false; forced to true for model-derived evidence.")

    return {
        "signal_type": signal_type,
        "changed_kyc_fields": sorted(dict.fromkeys(normalized_fields)),
        "severity_suggestion": severity,
        "confidence": confidence,
        "claim": claim,
        "reason": reason,
        "verbatim_evidence": evidence,
        "effective_date": effective_date,
        "effective_date_source": effective_date_source,
        "needs_human_review": True,
        "validator_warnings": warnings,
    }


def validate_model_output(raw_output: str, document: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    payload = parse_json_object(raw_output)
    errors: list[str] = []

    raw_candidates = (
        payload.get("signal_candidates")
        or payload.get("signals")
        or payload.get("candidates")
        or payload.get("signal_candidate")
        or []
    )
    if isinstance(raw_candidates, dict):
        raw_candidates = [raw_candidates]
    if not isinstance(raw_candidates, list):
        raw_candidates = []
        errors.append("Model omitted a usable signal_candidates list; normalized to empty list.")

    if "relevant" in payload:
        try:
            relevant = coerce_bool(payload.get("relevant"), "relevant")
        except ModelValidationError:
            relevant = bool(raw_candidates)
            errors.append("Model relevant flag was not boolean; inferred from signal_candidates.")
    else:
        relevant = bool(raw_candidates)
        errors.append("Model omitted relevant; inferred from non-empty signal_candidates.")

    if "entity_match" in payload:
        try:
            entity_match = coerce_bool(payload.get("entity_match"), "entity_match")
        except ModelValidationError:
            entity_match = bool(raw_candidates)
            errors.append("Model entity_match flag was not boolean; inferred from signal_candidates.")
    else:
        entity_match = bool(raw_candidates)
        errors.append("Model omitted entity_match; inferred from non-empty signal_candidates.")

    candidates: list[dict[str, Any]] = []
    if relevant and entity_match:
        for index, candidate in enumerate(raw_candidates):
            try:
                candidates.append(validate_candidate(candidate, document, index))
            except ModelValidationError as exc:
                errors.append(str(exc))

    no_signal_reason = clean_spaces(payload.get("no_signal_reason"))
    if not candidates and not no_signal_reason:
        no_signal_reason = "Model returned no supported signal candidates."

    return {
        "relevant": relevant,
        "entity_match": entity_match,
        "signal_candidates": candidates,
        "no_signal_reason": no_signal_reason if not candidates else None,
    }, errors


def base_record(
    document: dict[str, Any],
    generated_at: str,
    mode: str,
    model: str | None,
) -> dict[str, Any]:
    return {
        "analysis_id": f"ai-{document.get('document_id', 'unknown')}",
        "analysis_version": ANALYSIS_VERSION,
        "document_id": document.get("document_id"),
        "customer_id": document.get("customer_id"),
        "source_url": document.get("source_url"),
        "source_name": document.get("source_name"),
        "title": document.get("title"),
        "published_at": document.get("published_at"),
        "generated_at": generated_at,
        "mode": mode,
        "model": model,
        "detection_method": "rule_fallback",
        "raw_model_output": None,
        "validated_analysis": None,
        "api_diagnostics": None,
        "validation_errors": [],
        "validation_warnings": [],
        "status": "pending",
    }


def mock_no_signal_output() -> str:
    return json.dumps(
        {
            "relevant": False,
            "entity_match": False,
            "signal_candidates": [],
            "no_signal_reason": "Mock mode fixture: no AI call was made, so deterministic rules should be used.",
        }
    )


def analyze_document(
    document: dict[str, Any],
    baseline: dict[str, Any],
    *,
    mode: str,
    generated_at: str,
    config: ApertusConfig | None = None,
    client: Callable[[list[dict[str, str]], ApertusConfig], str] | None = None,
) -> dict[str, Any]:
    model = config.model if config else None
    record = base_record(document, generated_at, mode, model)

    if mode == "off":
        record["status"] = "skipped_ai_disabled"
        return record

    messages = build_messages(document, baseline)
    if mode == "mock":
        raw_output = mock_no_signal_output()
    else:
        if config is None:
            raise ApertusConfigError("Apertus config is required for live mode.")
        try:
            raw_output = (
                client(messages, config)
                if client
                else call_apertus_openai_compatible(
                    messages,
                    config,
                    document_text_length=len(document_text(document)),
                )
            )
        except Exception as exc:
            record["status"] = "api_error"
            record["validation_errors"] = [f"{type(exc).__name__}: {exc}"]
            if isinstance(exc, ApertusAPIError):
                record["api_diagnostics"] = exc.diagnostics
            return record

    record["raw_model_output"] = raw_output
    try:
        validated, validation_warnings = validate_model_output(raw_output, document)
    except ModelValidationError as exc:
        record["status"] = "invalid_model_output"
        record["validation_errors"] = [str(exc)]
        return record

    record["validated_analysis"] = validated
    record["validation_errors"] = []
    record["validation_warnings"] = validation_warnings
    if validated["signal_candidates"]:
        record["status"] = "validated"
        record["detection_method"] = "ai_validated"
    else:
        record["status"] = "mock_fixture_no_signal" if mode == "mock" else "no_signal"
    return record


def analyze_documents(
    documents: list[dict[str, Any]],
    baselines: list[dict[str, Any]],
    *,
    mode: str,
    config: ApertusConfig | None = None,
    client: Callable[[list[dict[str, str]], ApertusConfig], str] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = generated_at or now_utc()
    baselines_by_customer = {baseline["customer_id"]: baseline for baseline in baselines}
    analyses: list[dict[str, Any]] = []

    for document in documents:
        baseline = baselines_by_customer.get(document.get("customer_id"))
        if not baseline:
            record = base_record(document, generated, mode, config.model if config else None)
            record["status"] = "skipped_missing_baseline"
            analyses.append(record)
            continue
        analyses.append(
            analyze_document(
                document,
                baseline,
                mode=mode,
                generated_at=generated,
                config=config,
                client=client,
            )
        )

    return {
        "generated_at": generated,
        "analysis_version": ANALYSIS_VERSION,
        "mode": mode,
        "model": config.model if config else None,
        "allowed_signal_types": ALLOWED_SIGNAL_TYPES,
        "allowed_kyc_fields": ALLOWED_KYC_FIELDS,
        "analyses": analyses,
    }


def load_validated_candidates_by_document(artifact: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    candidates_by_document: dict[str, list[dict[str, Any]]] = {}
    for record in artifact.get("analyses") or []:
        if record.get("status") != "validated":
            continue
        analysis = record.get("validated_analysis") or {}
        candidates = analysis.get("signal_candidates") or []
        if not candidates:
            continue
        document_id = record.get("document_id")
        if not document_id:
            continue
        enriched = []
        for candidate in candidates:
            enriched.append(
                {
                    **candidate,
                    "analysis_id": record.get("analysis_id"),
                    "model": record.get("model"),
                    "generated_at": record.get("generated_at"),
                    "source_url": record.get("source_url"),
                    "source_name": record.get("source_name"),
                    "validator_warnings": candidate.get("validator_warnings", []) + record.get("validation_warnings", []),
                    "detection_method": "ai_validated",
                }
            )
        candidates_by_document[str(document_id)] = enriched
    return candidates_by_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze collected evidence with Apertus before rule extraction.")
    parser.add_argument("--baselines", default="data_01/baseline_snapshots.json")
    parser.add_argument("--documents", default="data_02/documents.json")
    parser.add_argument("--output", default="data_03/ai_evidence_analysis.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument(
        "--mode",
        choices=["off", "mock", "live"],
        default="off",
        help="off writes disabled records, mock writes no-signal fixture records, live calls Apertus.",
    )
    parser.add_argument("--smoke-test", action="store_true", help="Call Apertus with a tiny prompt and print diagnostics.")
    parser.add_argument("--timeout-seconds", type=int, default=45)
    return parser.parse_args()


def smoke_test(env_file: str | Path, timeout: int) -> int:
    config = load_apertus_config(env_file)
    print(f"APERTUS_BASE_URL={config.base_url}")
    print(f"APERTUS_MODEL={config.model}")
    print(f"Resolved chat completions URL={config.chat_completions_url}")
    messages = [
        {
            "role": "system",
            "content": "Return a tiny plain text response.",
        },
        {
            "role": "user",
            "content": "Reply with: Apertus smoke test OK",
        },
    ]
    try:
        content = call_apertus_openai_compatible(messages, config, timeout=timeout, document_text_length=0)
    except ApertusAPIError as exc:
        print("Smoke test failed.")
        print(str(exc))
        print(json.dumps(exc.diagnostics, ensure_ascii=False, indent=2))
        return 1
    print("Smoke test response:")
    print(content)
    return 0


def main() -> int:
    args = parse_args()
    if args.smoke_test:
        return smoke_test(args.env_file, args.timeout_seconds)

    baselines = load_json(args.baselines)
    documents = load_json(args.documents)
    config = None
    if args.mode == "live":
        config = load_apertus_config(args.env_file)

    artifact = analyze_documents(documents, baselines, mode=args.mode, config=config)
    write_json(args.output, artifact)
    status_counts: dict[str, int] = {}
    for record in artifact["analyses"]:
        status = record["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    print(
        "AI evidence analysis complete: "
        f"{len(artifact['analyses'])} document(s), mode={args.mode}, statuses={status_counts}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
