# Alphabet Layer 2 KYC Case Study

## Demo Notice

This is a synthetic bank-side profile for the hackathon demo. It uses public sources for context and simulated internal activity for Layer 2; it is not AMINA customer data.

## Simulated Internal Bank Intelligence

- Customer: Alphabet Inc. (demo-009)
- Relationship start: 2026-06-01
- RM: Mara Keller
- Initial risk rating: low_to_medium
- Expected monthly volume: CHF 15,000,000
- Expected monthly transaction count: 80
- Expected regions: United States, European Union, United Kingdom
- Review threshold: CHF 5,000,000 single payment

## Expected Business Model

- Public large-cap technology holding company.
- Core activity expected around search, advertising, software, cloud services, subscriptions, devices, and technology investments.
- Bank relationship expected to support treasury, operating flows, vendor payments, and FX rather than regulated financial intermediation.

## Layer 1 Narrowing Logic

- alert-046 (business_activity_change): AI infrastructure and custom silicon activity is adjacent to the baseline cloud profile but may change counterparty regions, capex intensity, and strategic banking needs.
- alert-047 (commercial_opportunity): A credible AI infrastructure buildout may create treasury, FX, liquidity, or financing conversations for the RM.
- alert-048 (new_product): Google Cloud TPUs and AI chips should be recorded as part of the current activity narrative if confirmed by the client.

## Layer 2 Highlight Flags

| Signal | Expected Flag | Current Status | Recommended Action |
| --- | --- | --- | --- |
| High-value cross-border transfers inconsistent with historical behaviour | Behavioural Anomaly - Potential Money Mule | observed_as_review_trigger | Monitor transactions; ask RM to confirm business purpose and route to AML analyst review if unexplained. |
| Public pivot or material business-model expansion | Material Business Model Change | observed_partial | Update activity narrative after client confirmation; reassess risk rating only if products, counterparties, or jurisdictions materially change. |
| Large funding round or rapid geographic expansion | Scale Risk Change | observed_as_scale_signal | Reassess transaction monitoring thresholds and prepare a commercial RM follow-up. |
| Domain switch or significant website content change | Business Activity Change Signal | watch | Keep page-diff monitoring active; compare future product language against onboarding data. |

## Full Signal Playbook

| Signal | Expected Flag | Recommended Action | Alphabet Status |
| --- | --- | --- | --- |
| Sudden spike in negative news about a corporate client | High Reputational Risk | Trigger enhanced due diligence; escalate to compliance review. | not_observed: The current Alphabet example is a business-model and scale signal, not adverse media. |
| High-value cross-border transfers inconsistent with historical behaviour | Behavioural Anomaly - Potential Money Mule | Monitor transactions; flag for AML analyst review. | observed: Synthetic Alphabet transactions include AI infrastructure payments, including a Taiwan supply-chain payment, inside the same window as the public AI chip signal. |
| Multiple linked entities, low activity, sudden large flows | Structuring / Layering Risk | Trigger AML investigation. | not_observed: No linked-entity layering pattern is simulated for Alphabet; Robinhood/Bitstamp is the current linked-entity demo case. |
| Legal entity name change | Entity Identity Change - Re-KYC Required | Trigger KYC refresh; re-evaluate risk category. | not_observed: No Alphabet legal-name change is present in the current public evidence. |
| Domain switch or significant website content change | Business Activity Change Signal | Re-analyse website content; compare vs. original onboarding data. | watch: Alphabet is not a domain-switch case, but Google Cloud TPU product language should be monitored against the onboarded technology-treasury profile. |
| Public pivot (e.g. SaaS startup -> crypto trading) | Material Business Model Change | Update risk classification; escalate for compliance review. | observed_partial: Alphabet is not pivoting into crypto, but the public AI chip/commercial silicon signal extends the onboarded cloud and advertising profile into a more infrastructure-intensive activity area. |
| Jurisdiction move or change of legal form (e.g. GmbH -> offshore) | Structural Risk Change | Trigger enhanced due diligence; re-check beneficial ownership. | not_observed: No Alphabet jurisdiction move or legal-form change is present in the current evidence. |
| New shareholders or beneficial owners appear | Ownership Change - KYC Drift | Full ownership verification; re-screen against sanctions/PEP lists. | not_observed: No new Alphabet beneficial-owner signal is present in the current evidence. |
| Large funding round or rapid geographic expansion | Scale Risk Change | Reassess transaction monitoring thresholds; update activity profile. | observed: The Alphabet case combines public AI infrastructure expansion coverage with synthetic high-value AI infrastructure-linked treasury activity. |
| Previously dormant company begins high transaction volume | Dormancy Break - Suspicious Activation | Trigger AML review; validate business legitimacy. | not_observed: Alphabet is a high-activity public company, not a dormant-company activation case. |

## Expected Outcome

- RM TLDR: Alphabet is still a low-to-medium-risk public technology client, but fresh AI infrastructure evidence plus synthetic treasury activity makes the KYC activity narrative and monitoring thresholds worth reviewing.
- Next step: Add to RM call brief, validate whether AI infrastructure activity changes expected transaction volume, and update KYC only after human confirmation.
- Compliance position: Assistive triage only. No final AML, sanctions, or legal conclusion is made by the system.

## Public Research Sources

- Alphabet Investor Relations: https://abc.xyz/investor/
- Google Cloud TPU documentation: https://docs.cloud.google.com/tpu/docs/intro-to-tpu
- The Times / Wall Street Journal syndicated article: https://www.thetimes.com/business/wsj/article/google-is-using-nvidias-playbook-to-build-a-rival-ai-chip-business-rkbzvb9jn
