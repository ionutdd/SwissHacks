# Entity Selection Spec

## Selection Goal

Pick demo entities where public evidence can show a meaningful change from an older KYC baseline.

The best entities are not just famous. The best entities have clear, source-backed changes that map to AMINA's business:

- Crypto custody.
- Trading and FX.
- Lending.
- Staking.
- Deposits.
- Stablecoin rewards.
- Corporate banking.
- Investments.
- AML, sanctions, adverse media, ownership, jurisdiction, or business activity risk.

## Selection Criteria

Score each candidate from 1 to 5.

| Criterion | What Good Looks Like |
| --- | --- |
| Public evidence availability | Sources are accessible without login or paid access. |
| Drift clarity | The change can be explained in one sentence. |
| AMINA relevance | The story maps to risk, compliance, or AMINA services. |
| Source quality | Evidence comes from official pages, filings, registries, or reputable news. |
| Automation potential | A future system could monitor the source repeatedly. |
| Demo simplicity | A judge can understand the story quickly. |

Prefer candidates scoring at least 4 in drift clarity, AMINA relevance, and source quality.

## Good Entity Types

### Web3 Or Crypto Companies

Good for:

- Crypto exposure drift.
- Custody/staking/trading opportunities.
- Token launch or treasury signals.
- Regulatory or adverse media risk.

Source ideas:

- Company blog.
- Token documentation.
- GitHub.
- Governance forum.
- Block explorer for publicly attributed wallets.
- News articles.

### Fintech Or Payments Companies

Good for:

- Money movement risk.
- Jurisdiction expansion.
- Banking and FX opportunities.
- Licensing or enforcement changes.

Source ideas:

- Product pages.
- Terms of service.
- Regulatory filings.
- Careers pages.
- News.

### Public Companies With Filings

Good for:

- Ownership/control changes.
- Subsidiaries.
- Risk factors.
- Treasury activity.
- Litigation or enforcement.

Source ideas:

- SEC EDGAR.
- Annual reports.
- Investor relations.
- Press releases.
- News.

### Fast-Growing Startups

Good for:

- Funding opportunity.
- Hiring expansion.
- New markets.
- Product drift.

Source ideas:

- Careers page.
- Press releases.
- LinkedIn company page if accessible.
- Crunchbase-like pages if available.
- News.

## Bad Entity Choices

Avoid entities where:

- The name is too ambiguous.
- Evidence is only from rumors.
- Evidence sits behind login walls.
- The public story is interesting but not relevant to AMINA.
- The change is too technical to explain quickly.
- The entity has no clear baseline-to-current drift.

## Candidate Scoring Template

```markdown
## Candidate: [Entity Name]

- Public evidence availability: 1-5
- Drift clarity: 1-5
- AMINA relevance: 1-5
- Source quality: 1-5
- Automation potential: 1-5
- Demo simplicity: 1-5

Expected drift story:

Likely source URLs:

Expected category:
- risk / opportunity / ownership / mixed

Decision:
- accept / reject / backup
```

## Minimum Final Mix

Final selection must include:

- 1 risk drift entity.
- 1 opportunity drift entity.
- 1 ownership/control, jurisdiction, or subsidiary drift entity.

Nice to have:

- 1 crypto-native entity.
- 1 public company with filings.
- 1 startup-like company with careers/news evidence.

