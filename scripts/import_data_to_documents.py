#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure the repository root is on sys.path so `server` package imports work
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.document_store import DocumentStore
from server.security import EncryptionManager


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import pipeline output JSON files into the SignalWatch document DB.")
    parser.add_argument("--data-root", type=Path, default=Path("."))
    parser.add_argument("--document-db", type=Path, default=Path("runtime/signalwatch.documents.json"))
    parser.add_argument("--key-file", type=Path, default=None)
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    document_db = args.document_db.resolve()
    key_file = args.key_file.resolve() if args.key_file else document_db.with_name("signalwatch.key")

    encryption = EncryptionManager.load_or_create(key_file)
    documents = DocumentStore(document_db, encryption)
    documents.initialize()

    mapping_collections = {
        "customers": data_root / "data_01" / "baseline_snapshots.json",
        "evidence_documents": data_root / "data_02" / "documents.json",
        "collection_trace": data_root / "data_02" / "collection_trace.json",
        "facts": data_root / "data_03" / "facts.json",
        "alerts": data_root / "data_03" / "alerts.json",
        "material_alerts": data_root / "data_06" / "material_alerts.json",
        "noise_suppression": data_root / "data_06" / "noise_suppression.json",
    }

    mapping_documents = {
        "page_watch_state": data_root / "data_02" / "page_watch_state.json",
        "ai_analysis": data_root / "data_03" / "ai_evidence_analysis.json",
        "refresh_summary": data_root / "data_06" / "refresh_summary.json",
    }

    for collection, path in mapping_collections.items():
        if path.is_file():
            try:
                value = load_json(path)
                # Handle baseline snapshots mapping: if it's an object of customers, convert to list
                if collection == "customers" and isinstance(value, dict):
                    # baseline_snapshots.json can be either list or dict keyed by id
                    customers = list(value.values())
                    documents.replace_collection(collection, customers)
                else:
                    documents.replace_collection(collection, value)
                print(f"Imported collection {collection} from {path}")
            except Exception as error:
                print(f"Failed to import {collection} from {path}: {error}")

    for name, path in mapping_documents.items():
        if path.is_file():
            try:
                value = load_json(path)
                documents.replace_document(name, value)
                print(f"Imported document {name} from {path}")
            except Exception as error:
                print(f"Failed to import document {name} from {path}: {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
