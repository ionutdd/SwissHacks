# Subtask 02: Evidence And Source Collection

Owner: Teammate 2

Mission: collect public evidence for the demo entities and normalize it into a clean `documents.json` file that the extraction/scoring teammate can use.

This is a critical subtask. The prototype wins or loses on evidence quality. A simple dashboard with strong sources is more convincing than a polished dashboard with vague claims.

## Files In This Folder

- [01-task-brief.md](01-task-brief.md): what teammate 2 owns and must deliver.
- [02-source-collection-spec.md](02-source-collection-spec.md): source types, collection workflow, quality rules.
- [03-document-schema-spec.md](03-document-schema-spec.md): required `documents.json` structure.
- [04-entity-source-plan.md](04-entity-source-plan.md): source plan for each selected demo entity.
- [05-output-checklist.md](05-output-checklist.md): final checklist before handoff to teammates 3 and 4.
- [06-connector-algorithms-spec.md](06-connector-algorithms-spec.md): runnable source connector algorithms.

## Required Inputs

Teammate 2 starts from:

- `data_01/baseline_snapshots.json`
- `data_01/demo_entity_notes.md`

## Required Outputs

Teammate 2 should produce:

- `scripts/evidence_common.py`
- `scripts/collect_evidence.py`
- `scripts/collect_evidence_SEC.py`
- `scripts/collect_evidence_company_site.py`
- `scripts/collect_evidence_regulator.py`
- `scripts/collect_evidence_news_event.py`
- `scripts/collect_evidence_page_diff.py`
- `scripts/collect_evidence_direct_sources.py`
- `data_02/source_catalog.json`
- `data_02/documents.json`
- `data_02/source_evidence_map.md`
- `data_02/collection_trace.json`
- `data_02/collection_run_report.md`
- `data_02/page_watch_state.json`
- `data_02/pipeline_runs/`

## Runnable Algorithm

Run:

```powershell
python scripts\collect_evidence.py --baseline data_01\baseline_snapshots.json --catalog data_02\source_catalog.json --output-dir data_02
```

The collector loads the baseline watchlist, runs the split source collectors, fetches public source pages, cleans text, ranks evidence chunks with a lightweight RAG-style lexical retrieval step, and writes normalized documents.

Run one isolated pipeline:

```powershell
python scripts\collect_evidence_SEC.py
python scripts\collect_evidence_company_site.py
python scripts\collect_evidence_regulator.py
python scripts\collect_evidence_news_event.py
python scripts\collect_evidence_page_diff.py
python scripts\collect_evidence_direct_sources.py
```

## Handoff Contract

Teammate 2 hands off to:

- Teammate 3, who extracts facts and scores alerts from `documents.json`.
- Teammate 4, who displays source excerpts and links in the UI.

## Definition Of Done

- At least 15 source documents are collected.
- Every document has URL, source type, source quality, timestamp, title, and evidence excerpt.
- At least 8 documents come from A or B quality sources.
- At least 4 source types are represented.
- Every top 3 demo story has at least 2 supporting documents.
- No high-risk demo claim depends only on social media or a weak source.
