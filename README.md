# SignalWatch

SignalWatch is a static hackathon prototype for evidence-backed KYC drift monitoring.

## Local Environment

Copy the tracked template and fill values locally:

```powershell
Copy-Item .env.example .env
```

`.env` is intentionally ignored by Git. It is the only place for local Apertus credentials:

```text
APERTUS_API_KEY=
APERTUS_BASE_URL=
APERTUS_MODEL=
```

`APERTUS_BASE_URL` may be an OpenAI-compatible `/v1` base URL or a full `/chat/completions` endpoint. API keys must not be committed, placed in JSON outputs, documentation examples, or frontend code.

## Run The Pipeline

Deterministic-only mode:

```powershell
python scripts/run_material_signal_refresh.py --skip-collection --ai-mode off --lookback-hours 24
```

Offline/mock AI mode, with no API calls:

```powershell
python scripts/run_material_signal_refresh.py --skip-collection --ai-mode mock --lookback-hours 24
```

Apertus AI-enriched mode:

```powershell
python scripts/run_material_signal_refresh.py --skip-collection --ai-mode live --lookback-hours 24
```

The AI stage writes `data_03/ai_evidence_analysis.json`. Every collected document is sent to Apertus in live mode. Validated AI candidates are preferred per signal type, and deterministic rule fallback still fills supported signals that Apertus did not return. If AI is disabled, returns no candidates, fails, times out, or produces invalid JSON, deterministic rule fallback still generates facts and alerts.

The default notification window is 24 hours and uses strict `published_at_only` freshness. The TLDR notification queue is limited to the focused demo watchlist: Coinbase, GameStop, Kraken, and Alphabet. The full Customer workspace still shows all alerts. Use `--include-collected-evidence` only when you intentionally want newly crawled undated/old pages to appear as operational refresh items.

Smoke-test Apertus without exposing the API key:

```powershell
python scripts/ai_evidence_analysis.py --smoke-test
```

## Dashboard

Start a local static server:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

Open:

```text
http://127.0.0.1:8000/dashboard/
```

Alert details show detection method, model name when AI was used, exact evidence quote, source links, and a human-review badge for AI-derived signals.

## Tests

```powershell
python -m unittest discover -s tests
```

The tests use mocked model responses and never make a real Apertus API call.

## Git Safety Check

Verify `.env` is ignored:

```powershell
git check-ignore -v .env
```
