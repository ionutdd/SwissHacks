# SignalWatch

SignalWatch is a server-backed application for evidence-backed KYC drift monitoring. It combines a persistent RM console, a scheduled evidence pipeline, and configurable per-RM notification policies.

## Local Environment

Install the application dependency:

```powershell
python -m pip install -r requirements.txt
```

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

## Dashboard

Create the first users. Passwords are prompted securely and must be at least 14 characters with mixed character classes:

```powershell
python -m server.manage_users create --username admin --display-name "Security Admin" --role admin
python -m server.manage_users create --username mara --display-name "Mara Keller" --role rm --rm-id rm-mara-keller
python -m server.manage_users create --username checker --display-name "Compliance Checker" --role compliance
```

Start the application server:

```powershell
python -m server.app --host 127.0.0.1 --port 8000 --workers 4
```

Open:

```text
http://127.0.0.1:8000/dashboard/
```

The schema-free extracted data lives in the TinyDB document database at `runtime/signalwatch.documents.json`, initialized from `storage/signalwatch.seed.json`. Named collections hold customers, public evidence, facts, alerts, internal signals, KYC enrichment, provenance, and evaluation artifacts without forcing those sources into one rigid schema.

Structured application state remains in SQLite at `runtime/signalwatch.db`: relationship managers, notification preferences, jobs, active notification assignments, and review actions. Worker logs are written below `runtime/jobs/`. Pipeline files exist only inside a temporary job workspace; successful outputs are imported into TinyDB and the workspace is deleted.

Each enabled relationship manager has an IANA timezone. The in-process scheduler creates retrieval jobs at 07:00 and 13:00 in that timezone, and a bounded subprocess pool executes them. Closely timed RM jobs share a retrieval completed within the previous ten minutes, while notification qualification remains independent for every RM.

Use **Notification settings** in the dashboard to configure:

- RM timezone and watchlist
- lookback window, minimum material score, and minimum confidence
- included categories, severities, and signal types
- source URL and evidence freshness requirements

Saving a policy immediately queues a full retrieval and classification worker and shows its live status in the Notifications tab. **Run refresh now** does the same manually. The server must remain running for automatic 07:00 and 13:00 scheduling.

The 07:00 and 13:00 local-RM schedule is intentional controlled monitoring for a bank; this project does not claim continuous market-data streaming.

## Security And Governance

- Passwords use Argon2id with a unique 128-bit salt, 64 MiB memory cost, and no reversible password storage.
- Browser authentication uses 384-bit opaque session tokens in `HttpOnly`, `SameSite=Strict` cookies. Only keyed token digests are stored server-side.
- State-changing APIs require a session-bound CSRF token and same-origin validation. Sessions have an eight-hour absolute lifetime and a 30-minute idle timeout.
- Runtime TinyDB documents and sensitive SQLite fields use AES-256-GCM authenticated encryption with fresh 96-bit nonces and context-bound associated data.
- RM users are restricted to their assigned portfolio. Compliance/admin roles can work across portfolios; auditors are read-only. Internal fields are masked for roles without sensitive-data clearance.
- Review actions are append-only. Escalation, dismissal, and customer-update actions require a different compliance/admin user to approve or reject them.
- Security and workflow events are append-only and HMAC hash-chained. The Governance tab verifies the chain and shows its current head.
- Every worker records measured stage duration, input/output tokens reported by a live model, configured token rates, and estimated cost. Zero model usage is recorded explicitly when no LLM is invoked.

For production HTTPS, provide a certificate and key; this also forces the `Secure` cookie flag:

```powershell
python -m server.app --host 0.0.0.0 --port 8443 --secure-cookie `
  --tls-cert .\certs\server.pem --tls-key .\certs\server-key.pem
```

`SIGNALWATCH_DATA_KEY` can supply a URL-safe base64 32-byte data key from a secrets manager. Without it, a local key is generated at `runtime/signalwatch.key` with restricted filesystem permissions. Production deployments should inject this key from KMS/HSM-backed secret management and never copy it into source control.

For live Apertus telemetry, start with `--ai-mode live` and configure the actual contracted rates:

```text
SIGNALWATCH_MODEL_INPUT_USD_PER_1M=
SIGNALWATCH_MODEL_OUTPUT_USD_PER_1M=
```

Free and low-cost connector options, including licensing limits, are documented in [docs/connector_options.md](docs/connector_options.md).

Alert details show both levels of provenance: whether the source document was reviewed by Apertus, and whether the final signal was extracted by AI or deterministic fallback. Details also show the model name, exact evidence quote, source links, and a human-review badge for model-derived signals.

Material scores use deterministic controls plus Apertus severity suggestions when available. Sanctions, OFAC, DPRK/North Korea, ransomware, regulatory scrutiny, ownership/control drift, jurisdiction drift, and human-review-required signals receive explicit business-impact weighting so critical compliance alerts rank above lower-risk product or opportunity alerts.

Alert details and RM briefs also show public-source KYC and founder/investor collections, including source links, verification status, KYC questions, advisory-vs-equity classification, and disclosed or missing ownership percentage.

## Remaining Challenge Gaps

The MVP covers scheduled public intelligence, KYC drift, simulated internal context, explainable alert scoring, source citations, human review actions, and per-RM notification policies. Before a regulated production deployment it still needs:

- enterprise SSO and managed KMS/HSM integration
- formal retention rules and stronger public/internal deployment isolation
- external WORM/SIEM audit export for regulator-grade retention
- direct production connectors for sanctions, registries, AML transactions, and adverse-media providers
- production observability, retries/dead-letter handling, backups, and high-availability deployment

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
