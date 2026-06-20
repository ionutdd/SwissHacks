# Entity Source Plan

Use this as the practical collection guide for `data_02/source_catalog.json` and `data_02/documents.json`.

## Priority 1: Polymarket

Customer ID: `demo-002`

Demo purpose: high-risk regulatory/gambling-law drift.

Collect at least 3 documents:

1. CFTC enforcement source.
   - URL: https://www.cftc.gov/PressRoom/PressReleases/8478-22
   - Source type: `regulator`
   - Source quality: `A`
   - Expected signal types: `regulatory_scrutiny`, `business_activity_change`
   - Target fields: `risk_rating`, `business_area`

2. QCEX/QCX acquisition or US return source.
   - Suggested URL: https://www.axios.com/2025/07/21/prediction-market-polymarket-us
   - Source type: `reputable_news`
   - Source quality: `B`
   - Expected signal types: `ownership_change`, `jurisdiction_restriction`, `business_activity_change`
   - Target fields: `subsidiaries`, `known_jurisdictions`, `business_area`

3. Gaming/jurisdiction restriction source.
   - Search for official regulator pages first.
   - Use reputable news if official source is hard to access.
   - Expected signal types: `jurisdiction_restriction`, `regulatory_scrutiny`
   - Target fields: `known_jurisdictions`, `risk_rating`

## Priority 2: Robinhood

Customer ID: `demo-001`

Demo purpose: ownership/control, jurisdiction, and business-line drift.

Collect at least 3 documents:

1. Robinhood official Bitstamp acquisition-close announcement.
   - URL: https://robinhood.com/us/en/newsroom/robinhood-completes-acquisition-of-bitstamp/
   - Source type: `company_newsroom`
   - Source quality: `A`
   - Expected signal types: `ownership_change`, `new_subsidiary`, `business_activity_change`
   - Target fields: `subsidiaries`, `business_area`, `known_products`

2. Bitstamp jurisdiction/license/company profile source.
   - Prefer Bitstamp official legal/about page.
   - Source type: `product_page` or `company_newsroom`
   - Source quality: `A`
   - Expected signal types: `new_jurisdiction`
   - Target fields: `known_jurisdictions`, `risk_rating`

3. Robinhood investor relations or SEC filing.
   - Source type: `investor_relations` or `sec_filing`
   - Source quality: `A`
   - Expected signal types: `ownership_change`, `business_activity_change`
   - Target fields: `subsidiaries`, `business_area`

## Priority 3: GameStop

Customer ID: `demo-003`

Demo purpose: sudden crypto treasury exposure and AMINA custody/lending opportunity.

Collect at least 3 documents:

1. GameStop investor-relations or press release for bitcoin purchase.
   - Suggested starting URL: https://news.gamestop.com
   - Source type: `investor_relations`
   - Source quality: `A`
   - Expected signal types: `digital_asset_activity`, `treasury_policy_change`
   - Target fields: `business_area`, `known_products`, `risk_rating`

2. SEC filing or annual report risk-factor source.
   - Source type: `sec_filing`
   - Source quality: `A`
   - Expected signal types: `treasury_policy_change`, `digital_asset_activity`
   - Target fields: `risk_rating`, `known_products`

3. Reputable news corroboration.
   - Suggested URL: https://www.investopedia.com/gamestop-stock-slips-on-disclosure-of-500-million-bitcoin-buy-11743013
   - Source type: `reputable_news`
   - Source quality: `B`
   - Expected signal types: `digital_asset_activity`, `commercial_opportunity`
   - Target fields: `known_products`, `risk_rating`

## Priority 4: Kraken

Customer ID: `demo-004`

Demo purpose: product-line and ownership/control drift.

Collect at least 3 documents:

1. Kraken or NinjaTrader acquisition source.
   - Prefer Kraken official blog or press page.
   - Source type: `official_blog` or `company_newsroom`
   - Source quality: `A`
   - Expected signal types: `ownership_change`, `business_activity_change`
   - Target fields: `subsidiaries`, `business_area`

2. xStocks/tokenized equities source.
   - Suggested URL: https://blog.kraken.com/product/xstocks/tokenized-equities-now-available
   - Source type: `official_blog`
   - Source quality: `A`
   - Expected signal types: `new_product`, `digital_asset_activity`
   - Target fields: `business_area`, `known_products`

3. Reputable news source on tokenized equities or derivatives expansion.
   - Use a free source if WSJ is paywalled.
   - Source type: `reputable_news`
   - Source quality: `B`
   - Expected signal types: `new_product`, `jurisdiction_expansion`
   - Target fields: `known_jurisdictions`, `business_area`

## Priority 5: Circle

Customer ID: `demo-005`

Demo purpose: stablecoin and payments commercial opportunity.

Collect at least 3 documents:

1. Circle investor relations or SEC filing for public listing / IPO.
   - Suggested URL: https://investor.circle.com
   - Source type: `investor_relations` or `sec_filing`
   - Source quality: `A`
   - Expected signal types: `public_listing`, `commercial_opportunity`
   - Target fields: `entity_type`, `known_products`

2. Circle product page for Circle Mint, payments, USDC, EURC, USYC, or Arc.
   - Suggested URL: https://www.circle.com/circle-mint
   - Source type: `product_page`
   - Source quality: `A`
   - Expected signal types: `new_product`, `digital_asset_activity`
   - Target fields: `business_area`, `known_products`

3. Reputable news or filing source for product expansion.
   - Source type: `reputable_news` or `sec_filing`
   - Source quality: `A` or `B`
   - Expected signal types: `commercial_opportunity`, `new_product`
   - Target fields: `known_products`, `business_area`

## Minimum Collection Mix

Target by entity:

| Entity | Minimum Documents | Must Include Official Source |
| --- | ---: | --- |
| Polymarket | 3 | yes |
| Robinhood | 3 | yes |
| GameStop | 3 | yes |
| Kraken | 3 | yes |
| Circle | 3 | yes |

Total minimum: 15 documents.
