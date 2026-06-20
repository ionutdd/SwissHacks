# Task Brief

## Objective

Build the extraction and scoring layer for the KYC drift prototype.

Task 2 gives us normalized source documents. Task 3 turns those documents into:

1. Structured facts.
2. Baseline differences.
3. Risk/opportunity classifications.
4. Prioritized alerts with evidence links.

## What Task 3 Is About

Task 3 is not about collecting more data and not about UI polish.

It is about answering:

- What fact does this evidence prove?
- Is that fact new compared with the last KYC review?
- Does it create risk, opportunity, or both?
- How severe is it?
- How confident are we?
- What should the RM or compliance team do next?

## What To Build

Create a deterministic signal engine that can run on:

- `data_01/baseline_snapshots.json`
- `data_02/documents.json`

The engine should output:

- `data_03/facts.json`
- `data_03/alerts.json`
- optional run report for debugging and demo explanation.

## Priority Signal Stories

Support these first:

1. **Polymarket risk drift**
   - Regulatory scrutiny.
   - Gambling/license jurisdiction restriction.
   - Sensitive business activity.

2. **Robinhood ownership and jurisdiction drift**
   - Bitstamp acquisition.
   - New subsidiary/legal entities.
   - New jurisdictions and crypto licensing exposure.

3. **GameStop crypto treasury drift**
   - Bitcoin treasury reserve policy.
   - Bitcoin purchase.
   - Digital-asset risk review and AMINA custody/lending opportunity.

4. **Kraken product and ownership drift**
   - NinjaTrader acquisition.
   - Tokenized equities/xStocks product.
   - Jurisdiction/legal disclosure.

5. **Circle commercial opportunity drift**
   - Stablecoin/payments products.
   - Circle Mint, CPN, USDC.
   - Public-company/institutional payments opportunity.

## What Not To Do

- Do not invent facts from weak hints.
- Do not produce alerts without evidence.
- Do not create legal conclusions beyond what the source says.
- Do not infer wallet ownership.
- Do not overbuild an LLM agent if deterministic rules cover the demo.
- Do not make UI decisions beyond the alert shape teammate 4 needs.

## Implementation Recommendation

For the hackathon, use deterministic rules and phrase matching first.

Recommended flow:

1. Load baselines and documents.
2. For each document, use `expected_signal_types` and evidence text to extract candidate facts.
3. Normalize fact values into simple fields: subject, object, jurisdiction, product, amount, event type.
4. Compare extracted facts with baseline arrays and scalar fields.
5. Create one alert per material customer/event cluster.
6. Score severity and confidence.
7. Attach recommended actions and evidence links.

LLM-assisted extraction can be added later, but only if it outputs strict JSON and cites source excerpts.
