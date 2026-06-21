from __future__ import annotations

import json
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import extract_signals
from ai_evidence_analysis import (
    ApertusAPIError,
    ApertusConfig,
    ModelText,
    analyze_document,
    call_apertus_openai_compatible,
    load_validated_candidates_by_document,
)


CONFIG = ApertusConfig(
    api_key="test-key",
    base_url="https://example.invalid/v1",
    model="apertus-test",
)

DOCUMENT = {
    "document_id": "doc-test",
    "customer_id": "cust-1",
    "source_type": "product_page",
    "source_name": "Circle",
    "source_url": "https://example.invalid/cpn",
    "source_quality": "A",
    "title": "Circle Payments Network",
    "published_at": "2026-06-20",
    "collected_at": "2026-06-20T10:00:00Z",
    "raw_text": (
        "Circle Payments Network (CPN) is a global network of partners, including banks, "
        "payment service providers, virtual asset service providers, and enterprises, "
        "who enable payments with 24/7 real-time settlement via stablecoins like USDC and EURC."
    ),
    "evidence_excerpt": "Circle Payments Network (CPN) is a global network of partners, including banks.",
    "expected_signal_types": ["new_product"],
    "baseline_fields_targeted": ["known_products", "business_area"],
}

BASELINE = {
    "customer_id": "cust-1",
    "legal_name": "Circle Internet Group, Inc.",
    "aliases": ["Circle"],
    "entity_type": "public_company",
    "business_area": ["financial technology"],
    "risk_rating": "medium",
    "known_products": [],
    "known_jurisdictions": ["United States"],
    "last_reviewed_at": "2026-01-01",
}


def valid_output() -> str:
    return json.dumps(
        {
            "relevant": True,
            "entity_match": True,
            "signal_candidates": [
                {
                    "signal_type": "new_product",
                    "changed_kyc_fields": ["known_products"],
                    "severity_suggestion": "medium",
                    "confidence": 0.86,
                    "claim": "Circle Payments Network enables stablecoin settlement.",
                    "reason": "The baseline does not list Circle Payments Network as a known product.",
                    "verbatim_evidence": "Circle Payments Network (CPN) is a global network of partners",
                    "effective_date": "2026-06-20",
                    "needs_human_review": True,
                }
            ],
            "no_signal_reason": "",
        }
    )


class AiEvidenceAnalysisTests(unittest.TestCase):
    def test_chat_completions_url_appended_once(self) -> None:
        cases = [
            ("https://api.publicai.co", "https://api.publicai.co/v1/chat/completions"),
            ("https://api.publicai.co/v1", "https://api.publicai.co/v1/chat/completions"),
            ("https://api.publicai.co/v1/", "https://api.publicai.co/v1/chat/completions"),
            ("https://api.publicai.co/v1/chat/completions", "https://api.publicai.co/v1/chat/completions"),
            ("https://api.publicai.co/v1/chat/completions/", "https://api.publicai.co/v1/chat/completions"),
        ]
        for base_url, expected in cases:
            config = ApertusConfig(api_key="test-key", base_url=base_url, model="apertus-test")
            self.assertEqual(config.chat_completions_url, expected)

    def test_http_error_diagnostics_are_structured_and_secret_free(self) -> None:
        error = HTTPError(
            CONFIG.chat_completions_url,
            400,
            "Bad Request",
            {"Content-Type": "application/json", "X-Request-Id": "req-test"},
            BytesIO(b'{"error":"bad request"}'),
        )
        messages = [{"role": "user", "content": "hello"}]

        with patch("ai_evidence_analysis.urlopen", side_effect=error):
            with self.assertRaises(ApertusAPIError) as raised:
                call_apertus_openai_compatible(messages, CONFIG, timeout=12, document_text_length=34)

        diagnostics = raised.exception.diagnostics
        self.assertEqual(diagnostics["request_url"], CONFIG.chat_completions_url)
        self.assertEqual(diagnostics["http_status_code"], 400)
        self.assertEqual(diagnostics["model"], CONFIG.model)
        self.assertEqual(diagnostics["timeout_seconds"], 12)
        self.assertEqual(diagnostics["document_text_char_count"], 34)
        self.assertIn("bad request", diagnostics["response_body_text"])
        self.assertNotIn(CONFIG.api_key, json.dumps(diagnostics))

    def test_valid_ai_result(self) -> None:
        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=lambda _messages, _config: valid_output(),
        )

        self.assertEqual(record["status"], "validated")
        self.assertEqual(record["detection_method"], "ai_validated")
        self.assertEqual(record["validated_analysis"]["signal_candidates"][0]["signal_type"], "new_product")

    def test_live_model_usage_is_preserved_for_cost_telemetry(self) -> None:
        output = ModelText(
            valid_output(),
            {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1500},
        )
        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=lambda _messages, _config: output,
        )
        self.assertEqual(record["model_usage"]["prompt_tokens"], 1200)
        self.assertEqual(record["model_usage"]["completion_tokens"], 300)

    def test_malformed_json(self) -> None:
        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=lambda _messages, _config: "{not json",
        )

        self.assertEqual(record["status"], "invalid_model_output")
        self.assertIn("not valid JSON", record["validation_errors"][0])

    def test_unsupported_signal_type_is_accommodated(self) -> None:
        payload = json.loads(valid_output())
        payload["signal_candidates"][0]["signal_type"] = "product_launch"
        payload["signal_candidates"][0]["changed_kyc_fields"] = ["product"]
        payload["no_signal_reason"] = ""

        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=lambda _messages, _config: json.dumps(payload),
        )

        self.assertEqual(record["status"], "validated")
        candidate = record["validated_analysis"]["signal_candidates"][0]
        self.assertEqual(candidate["signal_type"], "new_product")
        self.assertEqual(candidate["changed_kyc_fields"], ["known_products"])

    def test_quote_not_present_is_replaced_with_source_excerpt(self) -> None:
        payload = json.loads(valid_output())
        payload["signal_candidates"][0]["verbatim_evidence"] = "This quote is not in the source text."
        payload["no_signal_reason"] = "Candidate rejected by validator."

        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=lambda _messages, _config: json.dumps(payload),
        )

        self.assertEqual(record["status"], "validated")
        candidate = record["validated_analysis"]["signal_candidates"][0]
        self.assertEqual(candidate["verbatim_evidence"], DOCUMENT["evidence_excerpt"])
        self.assertIn("not exact", candidate["validator_warnings"][0])

    def test_api_failure_triggers_rule_fallback(self) -> None:
        def failing_client(_messages, _config):
            raise ApertusAPIError("boom")

        record = analyze_document(
            DOCUMENT,
            BASELINE,
            mode="live",
            generated_at="2026-06-20T10:00:00Z",
            config=CONFIG,
            client=failing_client,
        )
        self.assertEqual(record["status"], "api_error")

        artifact = {"analyses": [record]}
        ai_candidates = load_validated_candidates_by_document(artifact)
        facts, skipped = extract_signals.extract_facts(
            [DOCUMENT],
            {"cust-1": BASELINE},
            ai_candidates_by_document=ai_candidates,
        )

        self.assertEqual(skipped, 0)
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0]["detection_method"], "rule_fallback")
        self.assertEqual(facts[0]["fact_type"], "new_product")


if __name__ == "__main__":
    unittest.main()
