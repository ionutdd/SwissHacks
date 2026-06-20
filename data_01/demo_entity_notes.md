# Demo Entity Handoff

Generated for Subtask 01: Demo Entities And Baselines.

## Top 3 Stories

1. **Polymarket**: high-risk prediction-market customer with regulatory/gambling-law signals and crypto settlement exposure.
2. **Robinhood**: ownership/control and jurisdiction drift after closing the Bitstamp acquisition.
3. **GameStop**: non-crypto public company suddenly adds bitcoin to treasury, creating custody/lending opportunity and risk review.

## Backup / Secondary Stories

- **Kraken**: strong ownership/control and product-line drift through NinjaTrader, derivatives, and tokenized equities.
- **Circle**: strong commercial opportunity story around stablecoin infrastructure, public-company filings, and payment-network expansion.

## Why These Entities

These entities cover the required demo mix:

- Risk drift: Polymarket.
- Opportunity drift: GameStop and Circle.
- Ownership/control drift: Robinhood and Kraken.
- New jurisdiction or subsidiary exposure: Robinhood through Bitstamp.
- Digital asset activity: GameStop, Circle, Kraken, Polymarket.
- Public-company filings: Robinhood, GameStop, Circle.
- Crypto-native evidence: Kraken, Circle, Polymarket.

## Entity Notes

### demo-001: Robinhood Markets, Inc.

Drift story: Robinhood closed the Bitstamp acquisition after the baseline, adding a global crypto exchange, institutional crypto services, licenses, and new jurisdiction exposure.

Category: ownership/control, jurisdiction, business activity, digital asset activity.

Why it works:

- Clear official announcement.
- Strong before/after KYC story.
- Easy for judges to understand.
- AMINA relevance is direct: crypto trading, institutional services, staking/lending, jurisdiction expansion.

Best sources for teammate 2:

- Robinhood official acquisition-close announcement: https://robinhood.com/us/en/newsroom/robinhood-completes-acquisition-of-bitstamp/
- Robinhood investor relations.
- Bitstamp about/legal/license pages.
- Reputable news coverage of the acquisition.

Expected fields to change:

- `subsidiaries`
- `known_jurisdictions`
- `business_area`
- `risk_rating`

### demo-002: Blockratize, Inc. d/b/a Polymarket

Drift story: Polymarket has post-baseline regulatory and gambling-law signals, plus a regulated-exchange acquisition path back into the US market.

Category: risk, adverse media, regulatory scrutiny, sensitive business activity.

Why it works:

- Very strong risk narrative.
- CFTC enforcement history is official and easy to explain.
- Prediction markets map naturally to gambling/betting sensitivity.
- Crypto settlement creates digital-asset exposure.

Best sources for teammate 2:

- CFTC enforcement page: https://www.cftc.gov/PressRoom/PressReleases/8478-22
- Axios on QCEX acquisition and US return: https://www.axios.com/2025/07/21/prediction-market-polymarket-us
- Polymarket website and announcements.
- Gaming regulator lists or complaints where accessible.
- Reputable media on jurisdiction blocks or state gambling-law disputes.

Expected fields to change:

- `risk_rating`
- `business_area`
- `known_jurisdictions`
- `investors`
- `subsidiaries`

### demo-003: GameStop Corp.

Drift story: GameStop moved from a non-crypto retail baseline into a bitcoin treasury strategy after the last review.

Category: opportunity, digital asset activity, treasury policy, risk review.

Why it works:

- This maps exactly to the prompt idea: "if they suddenly have a bunch of bitcoins".
- The company is public, so teammate 2 can use filings and investor relations.
- The story creates both opportunity and risk: custody/lending vs volatility and policy change.

Best sources for teammate 2:

- GameStop investor relations: https://news.gamestop.com
- SEC filings after March 2025.
- Investopedia coverage: https://www.investopedia.com/gamestop-stock-slips-on-disclosure-of-500-million-bitcoin-buy-11743013
- Annual report risk-factor changes.

Expected fields to change:

- `business_area`
- `known_products`
- `known_wallets`
- `risk_rating`

### demo-004: Payward, Inc. d/b/a Kraken

Drift story: Kraken moved beyond a crypto-exchange baseline with NinjaTrader acquisition, derivatives expansion, and tokenized-equity products.

Category: ownership/control, business activity, product expansion, jurisdiction expansion.

Why it works:

- Strong AMINA strategic relevance.
- Product drift is easy to classify.
- Good for showing that the system catches opportunity and risk together.

Best sources for teammate 2:

- Kraken blog: https://blog.kraken.com
- Kraken xStocks announcement: https://blog.kraken.com/product/xstocks/tokenized-equities-now-available
- NinjaTrader website.
- Reuters or other reputable coverage of NinjaTrader acquisition.
- WSJ coverage of tokenized equities: https://www.wsj.com/finance/currencies/kraken-crypto-exchange-stock-tokens-e4fc1bb9

Expected fields to change:

- `subsidiaries`
- `business_area`
- `known_products`
- `known_jurisdictions`
- `risk_rating`

### demo-005: Circle Internet Group, Inc.

Drift story: Circle expanded from stablecoin issuer baseline into public-company status, tokenized money-market products, payment-network expansion, and new infrastructure products.

Category: commercial opportunity, stablecoin infrastructure, public listing, product expansion.

Why it works:

- Stablecoins are highly relevant to AMINA.
- Public-company filings create scalable monitoring data.
- Clear commercial map: payments, FX, custody, tokenized assets, stablecoin rewards.

Best sources for teammate 2:

- Circle investor relations: https://investor.circle.com
- Circle Mint: https://www.circle.com/circle-mint
- SEC filings for CRCL.
- Circle product announcements for Circle Payments Network and Arc.
- Reputable IPO coverage.

Expected fields to change:

- `entity_type`
- `business_area`
- `known_products`
- `known_jurisdictions`
- `risk_rating`

## Candidate Scores

| Entity | Public Evidence | Drift Clarity | AMINA Relevance | Source Quality | Automation Potential | Demo Simplicity | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Polymarket | 5 | 5 | 5 | 4 | 4 | 5 | accept |
| Robinhood | 5 | 5 | 5 | 5 | 5 | 5 | accept |
| GameStop | 5 | 5 | 5 | 4 | 5 | 5 | accept |
| Kraken | 4 | 4 | 5 | 4 | 4 | 4 | accept |
| Circle | 5 | 4 | 5 | 5 | 5 | 4 | accept |

## Notes For Teammate 2

Start with the top 3 stories before collecting secondary evidence.

Priority order:

1. Robinhood official Bitstamp announcement.
2. CFTC Polymarket enforcement page plus one newer Polymarket regulatory/gambling source.
3. GameStop investor relations or SEC source for bitcoin purchase.
4. Kraken source for NinjaTrader or xStocks.
5. Circle investor relations or SEC source.

For each source, capture:

- URL.
- Source type.
- Source quality.
- Published date.
- Collected date.
- Exact evidence excerpt.
- Expected signal type.

## Notes For Teammate 3

Expected signal types to support first:

- `ownership_change`
- `new_subsidiary`
- `new_jurisdiction`
- `business_activity_change`
- `digital_asset_activity`
- `treasury_policy_change`
- `regulatory_scrutiny`
- `commercial_opportunity`

Priority fields to compare:

- `known_jurisdictions`
- `business_area`
- `risk_rating`
- `known_products`
- `subsidiaries`
- `investors`

## Notes For Teammate 4

Recommended demo order:

1. Open dashboard and show five monitored entities.
2. Open Polymarket high-risk alert.
3. Open Robinhood ownership/jurisdiction alert.
4. Open GameStop opportunity alert.
5. Generate RM call brief showing one compliance action and one commercial follow-up.

Keep UI plain. The evidence and reasoning should do the selling.

## Known Caveats

- Baselines are synthetic and designed for demonstration, not real AMINA customer files.
- Some suggested sources may require teammate 2 to replace a news source with a more official filing if available.
- Do not infer wallet ownership unless a company directly publishes a wallet or filing.
- Treat regulatory items as review triggers, not final legal conclusions.

