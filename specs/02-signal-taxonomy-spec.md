# Signal Taxonomy Spec

## Signal Definition

A signal is a new, external, evidence-backed fact that may change AMINA's understanding of a customer compared with the last KYC snapshot.

Each signal must answer:

- What changed?
- Which customer or related party does it affect?
- Which KYC field changed?
- Why does this matter?
- What source proves it?
- What should the RM or compliance team do next?

## Signal Object

```json
{
  "signal_id": "sig-001",
  "customer_id": "demo-001",
  "signal_type": "new_high_risk_jurisdiction_exposure",
  "category": "risk",
  "title": "New subsidiary incorporated in high-risk jurisdiction",
  "summary": "Public registry data indicates a new subsidiary in Jurisdiction X.",
  "changed_fields": ["subsidiaries", "known_jurisdictions"],
  "evidence": [
    {
      "source_name": "Company registry",
      "source_url": "https://example-registry.test/company/123",
      "published_at": "2026-05-20",
      "collected_at": "2026-06-19",
      "source_type": "registry",
      "excerpt": "Subsidiary Example X Ltd registered on 2026-05-20."
    }
  ],
  "confidence": 0.84,
  "severity": "high",
  "recommended_action": "Compliance review and RM customer update request",
  "status": "new"
}
```

## Risk Signal Categories

### 1. Jurisdiction And Domicile Drift

Detect changes involving:

- Company domicile.
- Founder, director, UBO, or investor residency.
- New subsidiaries, branches, or operating entities.
- New markets, shipping destinations, counterparties, or supplier footprints.
- Exposure to sanctioned, embargoed, high-corruption, conflict, or high-AML-risk jurisdictions.

Example triggers:

- New office or subsidiary in a sanctioned or sensitive jurisdiction.
- Job postings for local country managers in newly entered countries.
- Website adds country-specific pages or supported currencies.
- Founder publicly relocates to a higher-risk jurisdiction.

### 2. Business Activity Drift

Detect changes in what the customer does.

Sensitive sectors to flag:

- Adult content.
- Gambling and betting.
- Arms, defense, or dual-use goods.
- Precious metals, gems, diamonds, mining, or high-value commodities.
- Unlicensed money transmission or VASP activity.
- Mixers, tumblers, privacy-enhancing crypto services, darknet exposure.
- High-risk DeFi, OTC brokerage, token issuance, or yield products.
- Shell-company formation or nominee-heavy structures.

Example triggers:

- New product page for gambling, adult, defense, or money-transfer services.
- Press release announcing a defense contract.
- GitHub or docs release for a mixer-like protocol.
- Terms of service add token issuance, custodial wallet, or exchange functionality.

### 3. Ownership And Control Drift

Detect changes to:

- Cap table.
- Investors.
- UBOs.
- Directors and officers.
- Senior management.
- Board members.
- M&A events.
- Significant creditors or strategic partners.

Example triggers:

- New funding round led by an unknown or high-risk investor.
- Director resignation after enforcement news.
- New investor tied to sanctioned persons or adverse media.
- Merger with an entity operating in a prohibited sector.

### 4. Crypto Exposure Drift

Detect new or changed digital-asset activity.

Example triggers:

- Customer launches or acquires a token.
- Public wallet begins interacting with sanctioned addresses, mixers, bridges, high-risk DeFi protocols, or gambling platforms.
- Customer announces treasury allocation to BTC, ETH, stablecoins, or other assets.
- Customer begins staking, lending, borrowing, or market-making activity.
- Customer adds crypto payments or custody to its own product.

Important constraint: wallet-level monitoring requires known wallet addresses, public attribution, or a licensed blockchain analytics provider. The prototype should not claim attribution from weak wallet-name matching alone.

### 5. Adverse Media And Enforcement Drift

Detect:

- Criminal allegations.
- Regulatory enforcement.
- Civil litigation with fraud, sanctions, corruption, insolvency, or consumer-harm allegations.
- Data breaches.
- Market-manipulation allegations.
- Bankruptcy or liquidation indicators.
- Executive misconduct.

Example triggers:

- New article links customer to corruption investigation.
- Regulator publishes enforcement action.
- Court docket shows fraud complaint.
- Security breach affects customer funds.

### 6. Financial And Operational Anomaly Drift

Detect signs that the stated business no longer matches observed behavior.

Example triggers:

- Large funding round with no hiring, product, or operating expansion.
- Sudden layoffs after claiming rapid growth.
- Repeated office closures or unexplained dormant status.
- Domain, website, and social channels go inactive while transaction volumes increase.
- New shell subsidiaries with unclear business purpose.

## Opportunity Signal Categories

### 1. Growth And Funding

Relevant AMINA products:

- Corporate banking.
- Deposits.
- Lending.
- FX.
- Investments.
- Custody.

Example triggers:

- Funding round.
- Revenue milestone.
- Hiring surge.
- New CFO, treasury, or finance role.
- Acquisition or market expansion.

### 2. Treasury And Liquidity Needs

Relevant AMINA products:

- Deposits.
- Stablecoin rewards.
- Lending against traditional or digital assets.
- FX and trading.

Example triggers:

- Company raises cash and needs treasury management.
- Company announces large stablecoin balances.
- Company expands payroll or vendors across currencies.
- Company holds assets that could support secured borrowing.

### 3. Digital Asset Activity

Relevant AMINA products:

- Custody.
- Off-exchange custody.
- Staking.
- Trading.
- Investment products.

Example triggers:

- Company adds ETH, SOL, BTC, or stablecoin treasury exposure.
- Company launches validator, staking, or token infrastructure.
- Company needs institutional custody for reserves.
- Company engages in large trading or OTC activity.

### 4. International Expansion

Relevant AMINA products:

- Multi-currency banking.
- FX.
- Corporate accounts.
- Cross-border payment support.

Example triggers:

- New subsidiaries.
- Localized websites.
- Country-specific hiring.
- New suppliers or ecommerce channels.

## Scoring

### Severity

- **Critical**: sanctions hit, credible criminal enforcement, direct prohibited activity, or confirmed high-risk crypto exposure. Immediate compliance review.
- **High**: material high-risk jurisdiction, ownership, sector, or adverse media drift. Compliance review and RM contact.
- **Medium**: plausible risk drift or strategic opportunity with moderate confidence. RM review.
- **Low**: weak signal, low-impact change, or opportunity-only update. Add to customer brief.

### Confidence

Confidence should combine:

- Entity match confidence.
- Source quality.
- Recency.
- Number of corroborating sources.
- Extracted-fact clarity.
- Whether the fact directly contradicts baseline KYC data.

### Source Quality

- **A**: official registry, regulator, sanctions list, court filing, company-owned site.
- **B**: reputable news outlet, exchange filing, verified social account, job board controlled by company.
- **C**: third-party database, scraped marketplace, non-verified social post.
- **D**: forum, repost, weak match, unverifiable claim.

## Alert Suppression Rules

- Suppress duplicate alerts for the same underlying event unless new evidence increases severity.
- Suppress low-confidence social-only alerts unless corroborated.
- Suppress opportunity alerts when a risk alert is critical for the same customer, but keep them visible in the customer timeline.
- Reopen a dismissed alert only if material new evidence appears.

## Acceptance Criteria

- The prototype supports at least 8 risk signal types and 5 opportunity signal types.
- Every signal maps to at least one KYC field.
- Every signal has a severity and confidence score.
- Every high or critical signal includes a recommended next action.
- The taxonomy can produce both a compliance queue and an RM opportunity queue.

