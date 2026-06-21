from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.document_store import DocumentStore


COLLECTION_FILES = {
    "customers": "data_01/baseline_snapshots.json",
    "source_catalog": "data_02/source_catalog.json",
    "evidence_documents": "data_02/documents.json",
    "collection_trace": "data_02/collection_trace.json",
    "page_watch_state": "data_02/page_watch_state.json",
    "facts": "data_03/facts.json",
    "alerts": "data_03/alerts.json",
    "ai_analysis": "data_03/ai_evidence_analysis.json",
    "material_alerts": "data_06/material_alerts.json",
    "noise_suppression": "data_06/noise_suppression.json",
    "refresh_summary": "data_06/refresh_summary.json",
    "activity_baselines": "data_07/customer_activity_baselines.json",
    "simulated_transactions": "data_07/simulated_transactions.json",
    "internal_signals": "data_07/internal_monitoring_signals.json",
    "fused_alerts": "data_07/public_internal_fused_alerts.json",
    "entity_resolution_reviews": "data_07/entity_resolution_review.json",
    "signal_playbook": "data_07/layer2_signal_playbook.json",
    "expanded_kyc_profiles": "data_07/expanded_kyc_profiles.json",
    "cost_trace": "data_07/cost_trace.json",
    "evaluation_cases": "data_07/evaluation_cases.json",
    "curated_founder_investor_sources": "data_08/curated_founder_investor_sources.json",
    "founder_investor": "data_08/founder_investor_intelligence.json",
    "curated_public_kyc_sources": "data_09/curated_public_kyc_sources.json",
    "public_kyc": "data_09/public_kyc_profiles.json",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def import_legacy_data(source_root: Path, destination: Path) -> dict[str, int]:
    destination.unlink(missing_ok=True)
    store = DocumentStore(destination)
    store.initialize()
    counts: dict[str, int] = {}
    for collection, relative_path in COLLECTION_FILES.items():
        path = source_root / relative_path
        if not path.is_file():
            continue
        value = load_json(path)
        if isinstance(value, list):
            store.replace_collection(collection, value)
            counts[collection] = len(value)
        elif isinstance(value, dict):
            store.replace_document(collection, value)
            counts[collection] = 1
        else:
            store.replace_document(collection, {"value": value})
            counts[collection] = 1

    artifacts: list[dict[str, Any]] = []
    for data_directory in sorted(source_root.glob("data_[0-9][0-9]")):
        for path in sorted(data_directory.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source_root).as_posix()
            if relative in COLLECTION_FILES.values():
                continue
            if path.suffix.lower() == ".json":
                artifacts.append({"path": relative, "media_type": "application/json", "payload": load_json(path)})
            elif path.suffix.lower() == ".md":
                artifacts.append({"path": relative, "media_type": "text/markdown", "content": path.read_text(encoding="utf-8")})
    store.replace_collection("artifacts", artifacts)
    counts["artifacts"] = len(artifacts)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy generated files into the TinyDB document store.")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "storage" / "signalwatch.seed.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts = import_legacy_data(args.source_root.resolve(), args.output.resolve())
    print(f"Imported {sum(counts.values())} documents across {len(counts)} collections into {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
