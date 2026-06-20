# AMINA KYC Drift Early Warning Specs

This folder turns `InitialPrompt.md` into a buildable specification package for a SwissHacks 2026 prototype.

## Spec Index

- [01 Product Spec](01-product-spec.md): problem, users, goals, MVP scope, success metrics.
- [02 Signal Taxonomy Spec](02-signal-taxonomy-spec.md): risk signals, opportunity signals, scoring, alert rules.
- [03 Data Ingestion Spec](03-data-ingestion-spec.md): sources, connector design, entity resolution, evidence model.
- [04 RM Workflow Spec](04-rm-workflow-spec.md): relationship manager dashboard, alert lifecycle, review/audit states.
- [05 Hackathon Demo Spec](05-hackathon-demo-spec.md): prototype scope, demo entities, scenarios, evaluation rubric.
- [06 Team Workstreams Spec](06-team-workstreams-spec.md): data-first four-person task split, interfaces, dependencies, and integration plan.
- [Subtask 01 Specs](subtask-01-demo-entities-baselines/README.md): detailed specs for demo entity selection and synthetic KYC baselines.
- [Subtask 02 Specs](subtask-02-evidence-source-collection/README.md): detailed specs for public evidence collection and normalized source documents.

## Product Thesis

Relationship managers currently maintain KYC knowledge as periodic snapshots. The prototype should convert that static snapshot into a continuously monitored customer profile that flags:

1. **Risk profile drift**: new facts that may increase financial-crime, sanctions, AML, reputational, or regulatory risk.
2. **Commercial opportunity drift**: new facts that suggest the customer may need more AMINA services.

The key product principle is evidence-first alerting. The system should never ask an RM to trust a black-box model. Every alert must show the source, timestamp, extracted fact, changed field, confidence, severity, and suggested next action.

## AMINA Context From Public Sources

Public AMINA pages position the bank as bridging traditional and digital asset finance. AMINA corporate pages describe business banking, crypto custody, trading, foreign exchange, lending, staking, deposits, stablecoin rewards, and investments as relevant service areas.

Useful public references:

- AMINA about page: https://aminagroup.com/about-us/
- AMINA corporates page: https://aminagroup.com/corporates/
- AMINA corporate banking: https://aminagroup.com/corporates/banking/
- AMINA corporate custody: https://aminagroup.com/corporates/custody/
- AMINA corporate lending: https://aminagroup.com/corporates/lending/
- AMINA corporate trading: https://aminagroup.com/corporates/trading/
- AMINA corporate staking: https://aminagroup.com/corporates/staking/
- AMINA corporate investments: https://aminagroup.com/corporates/investments/
- AMINA regulatory disclosure: https://aminagroup.com/regulatory-disclosure/
- FINMA AML supervision context: https://www.finma.ch/en/supervision/cross-sector-issues/combating-money-laundering/
- FINMA banking supervision context: https://www.finma.ch/en/supervision/banks-and-securities-firms/
- Swiss SECO sanctions entry point: https://www.seco.admin.ch/seco/en/home/Aussenwirtschaftspolitik_Wirtschaftliche_Zusammenarbeit/Wirtschaftsbeziehungen/exportkontrollen-und-sanktionen/sanktionen-embargos.html
- UN Security Council Consolidated List: https://www.un.org/securitycouncil/content/un-sc-consolidated-list
- OFAC Sanctions List Service: https://ofac.treasury.gov/sanctions-list-service

## Prototype Name

Working name: **SignalWatch for AMINA**.

One-line pitch: **An AI copilot that continuously compares public signals against AMINA's last-known KYC snapshot and gives relationship managers evidence-backed alerts for risk changes and service opportunities.**
