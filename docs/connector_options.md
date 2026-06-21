# Connector Options

These sources can support an MVP without pretending that a free feed is a complete production AML/KYC service.

## Sanctions

- [US Treasury OFAC Sanctions List Service](https://ofac.treasury.gov/sanctions-list-service): official downloadable SDN and consolidated non-SDN data. Poll on the controlled schedule, retain source version/hash, and screen aliases with human review.
- [UN Security Council Consolidated List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list): official XML, HTML, and PDF formats for listed individuals and entities.
- [EU consolidated financial sanctions dataset](https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en): official EU data portal dataset.
- [Swiss SECO sanctions search](https://www.seco.admin.ch/seco/en/home/Aussenwirtschaftspolitik_Wirtschaftliche_Zusammenarbeit/Wirtschaftsbeziehungen/exportkontrollen-und-sanktionen/sanktionen-embargos/sanktionsmassnahmen/suche_sanktionsadressaten.html): authoritative Swiss sanctions source for a Switzerland-focused deployment.

Use direct official feeds as the free baseline. They do not provide a complete PEP/adverse-media risk product, entity-resolution guarantees, or regulatory liability transfer.

## Entity And KYC Enrichment

- [GLEIF API](https://www.gleif.org/en/lei-data/gleif-api): public LEI and legal-entity reference data, useful for identifiers, legal names, relationships, and registration context.
- [UK Companies House API](https://developer.company-information.service.gov.uk/developer-guidelines): company/officer/filing data with an API key; official guidance currently documents 600 requests per five-minute window.
- [Swiss Zefix Public REST API](https://www.zefix.admin.ch/ZefixPublicREST/swagger-ui/index.html): official Swiss commercial-register interface.
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces): official US issuer submissions and company facts. Follow SEC fair-access and user-agent guidance.

These sources enrich KYC but do not replace customer-provided documentation, beneficial-owner verification, or a regulated onboarding decision.

## Adverse Media

- [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/): useful for broad multilingual news discovery. Treat results as leads, preserve the original publisher link, deduplicate, and apply source-quality controls.
- Publisher/company/regulator RSS feeds: inexpensive and explainable, but coverage must be curated and monitored for feed failures.

## Licensing Caveat

[OpenSanctions licensing](https://www.opensanctions.org/licensing/) states that free use is for non-commercial users and businesses need a data license. It can be evaluated during development, but it should not be presented as a free production option for a bank.

## Suggested Production Path

1. Start with OFAC, UN, EU, SECO, GLEIF, Zefix, Companies House, SEC, and GDELT connectors.
2. Store source snapshots, retrieval timestamps, hashes, licensing metadata, and parser versions in the document database.
3. Run deterministic exact/alias matching first; send uncertain matches to human review rather than auto-blocking.
4. Benchmark false positives and operational workload before selecting a commercial PEP/adverse-media provider.
5. Keep internal AML transaction monitoring inside the bank boundary; send only minimized derived signals to the public-intelligence layer.
