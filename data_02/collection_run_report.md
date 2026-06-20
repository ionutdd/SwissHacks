# Collection Run Report

- Generated at: 2026-06-20T05:31:39Z
- Output documents: 21
- Failed fetches: 1
- Skipped low-signal candidates: 5
- Discovery traces: 12

## Algorithm

The run used split collector scripts. Each pipeline discovered candidate sources, then the shared evidence core fetched pages, cleaned text, ranked evidence sentences, and emitted normalized documents.

## Failures

- `https://www.axios.com/2025/07/21/prediction-market-polymarket-us`: HTTPError: HTTP Error 403: Forbidden

## Skipped Candidates

- `None`: News API query unavailable; using configured fallbacks. URLError: <urlopen error [WinError 10060] A connection attempt failed because the connected party did not properly respond after a period of time, or established connection failed because connected host has failed to respond>
- `None`: News API query unavailable; using configured fallbacks. HTTPError: HTTP Error 429: Too Many Requests
- `https://www.sec.gov/Archives/edgar/data/1783879/000178387926000071/hood-20260616.htm`: SEC API-discovered filing did not contain configured source/signal terms.
- `https://www.sec.gov/Archives/edgar/data/1326380/000132638026000020/gme-20260602.htm`: SEC API-discovered filing did not contain configured source/signal terms.
- `https://www.sec.gov/Archives/edgar/data/1876042/000187604226000192/crcl-20260612.htm`: SEC API-discovered filing did not contain configured source/signal terms.

## Documents

- `doc-001` `demo-003` A sec_filing: GameStop Announces Purchase of Bitcoin
- `doc-002` `demo-003` A sec_filing: GameStop Form 10-K for fiscal year 2024
- `doc-003` `demo-003` A sec_filing: GameStop Form 10-Q for quarter ended May 3, 2025
- `doc-004` `demo-003` A sec_filing: GameStop Corp. 10-Q filed 2026-06-11
- `doc-005` `demo-004` A company_newsroom: Kraken to Acquire NinjaTrader: Introducing the Next Era of Professional Trading Kraken has entered into an agreement to acquire NinjaTrader, the leading U.S. retail futures trading platform, for $1.5 billion, subject to certain purchase price adjustments.
- `doc-006` `demo-002` A regulator: CFTC Orders Event-Based Binary Options Markets Operator to Pay $1.4 Million Penalty
- `doc-007` `demo-002` B reputable_news: Spain blocks access to Polymarket and Kalshi as it launches gambling licence investigation | Spain | The Guardian
- `doc-008` `demo-002` B reputable_news: Consumo ordena el bloqueo de Polymarket y Kalshi en España por operar sin licencia de juego | Economía | EL PAÍS
- `doc-009` `demo-002` B reputable_news: El futuro de Polymarket tras el bloqueo del Gobierno: "Es ilegal, no tiene licencia y no hay posibilidad de que la consiga" | Actualidad | Cadena SER
- `doc-010` `demo-005` A product_page: Circle Payments Network
- `doc-011` `demo-005` A product_page: USDC | Powering global finance. Issued by Circle.
- `doc-012` `demo-004` A product_page: xStocks Risk Disclosure
- `doc-013` `demo-001` A company_newsroom: Robinhood Completes Acquisition of Bitstamp
- `doc-014` `demo-001` A company_newsroom: Robinhood Completes Acquisition of Bitstamp
- `doc-015` `demo-001` A company_newsroom: Bitstamp legal entity and licensing disclosures
- `doc-016` `demo-004` A official_blog: From Wall Street to your wallet: Tokenized equities now available on Kraken
- `doc-017` `demo-005` A investor_relations: Circle Investor Relations
- `doc-018` `demo-005` A product_page: Circle Mint
- `doc-019` `demo-006` A regulator: Treasury Sanctions Russia-Based Hydra and Ransomware-Enabling Virtual Currency Exchange Garantex
- `doc-020` `demo-007` A regulator: Treasury Announces $508 Million Settlement with British American Tobacco
- `doc-021` `demo-008` A domain_rdap: RDAP record for coinbase.au
