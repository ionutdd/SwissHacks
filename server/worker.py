from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .document_store import DocumentStore
from .notification_engine import evaluate_alerts
from .security import EncryptionManager
from .store import SignalWatchStore, utc_now


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class RetrievalLock:
    def __init__(self, path: Path, timeout_seconds: int = 1800):
        self.path = path
        self.timeout_seconds = timeout_seconds
        self.acquired = False

    def __enter__(self) -> "RetrievalLock":
        deadline = time.monotonic() + self.timeout_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        while time.monotonic() < deadline:
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
                os.close(descriptor)
                self.acquired = True
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                    if age > self.timeout_seconds:
                        self.path.unlink(missing_ok=True)
                        continue
                except FileNotFoundError:
                    continue
                time.sleep(1)
        raise TimeoutError("Timed out waiting for the evidence retrieval lock.")

    def __exit__(self, *_args: object) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)


def materialize_pipeline_inputs(documents: DocumentStore, workspace: Path) -> dict[str, Path]:
    paths = {
        "baseline": workspace / "input" / "baseline_snapshots.json",
        "catalog": workspace / "input" / "source_catalog.json",
        "documents": workspace / "data" / "documents.json",
        "data02": workspace / "data",
        "data03": workspace / "signals",
        "data06": workspace / "material",
        "alerts": workspace / "signals" / "alerts.json",
        "ai_analysis": workspace / "signals" / "ai_evidence_analysis.json",
    }
    write_json(paths["baseline"], documents.collection("customers"))
    write_json(paths["catalog"], documents.document("source_catalog") or {})
    write_json(paths["documents"], documents.collection("evidence_documents"))
    page_watch_state = documents.document("page_watch_state")
    if page_watch_state:
        write_json(paths["data02"] / "page_watch_state.json", page_watch_state)
    ai_analysis = documents.document("ai_analysis")
    if ai_analysis:
        write_json(paths["ai_analysis"], ai_analysis)
    return paths


def import_pipeline_outputs(documents: DocumentStore, paths: dict[str, Path]) -> None:
    collection_files = {
        "evidence_documents": paths["documents"],
        "collection_trace": paths["data02"] / "collection_trace.json",
        "facts": paths["data03"] / "facts.json",
        "alerts": paths["alerts"],
        "material_alerts": paths["data06"] / "material_alerts.json",
        "noise_suppression": paths["data06"] / "noise_suppression.json",
    }
    document_files = {
        "page_watch_state": paths["data02"] / "page_watch_state.json",
        "ai_analysis": paths["ai_analysis"],
        "refresh_summary": paths["data06"] / "refresh_summary.json",
    }
    for collection, path in collection_files.items():
        if path.is_file():
            documents.replace_collection(collection, load_json(path))
    for collection, path in document_files.items():
        if path.is_file():
            documents.replace_document(collection, load_json(path))


def run_retrieval_if_needed(
    store: SignalWatchStore,
    documents: DocumentStore,
    root: Path,
    job_id: str,
    ai_mode: str,
) -> dict[str, Any]:
    lock_path = store.database_path.parent / "retrieval.lock"
    with RetrievalLock(lock_path):
        last_retrieval = parse_utc(store.metadata("last_retrieval_at"))
        now = datetime.now(timezone.utc)
        if last_retrieval and now - last_retrieval < timedelta(minutes=10):
            return {"retrieval": "shared", "last_retrieval_at": last_retrieval.isoformat()}

        preferences = [store.preferences(item["id"]) for item in store.relationship_managers() if item["enabled"]]
        lookback_hours = max((item["lookback_hours"] for item in preferences), default=24)
        job_directory = store.database_path.parent / "jobs" / job_id
        job_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pipeline-", dir=job_directory) as temporary_directory:
            paths = materialize_pipeline_inputs(documents, Path(temporary_directory))
            command = [
                sys.executable,
                "scripts/run_material_signal_refresh.py",
                "--baseline",
                str(paths["baseline"]),
                "--catalog",
                str(paths["catalog"]),
                "--documents",
                str(paths["documents"]),
                "--data02-dir",
                str(paths["data02"]),
                "--data03-dir",
                str(paths["data03"]),
                "--output-dir",
                str(paths["data06"]),
                "--alerts",
                str(paths["alerts"]),
                "--ai-analysis-output",
                str(paths["ai_analysis"]),
                "--lookback-hours",
                str(lookback_hours),
                "--all-notification-customers",
                "--ai-mode",
                ai_mode,
            ]
            completed = subprocess.run(
                command,
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,
            )
            if not completed.returncode:
                import_pipeline_outputs(documents, paths)
        log_dir = store.database_path.parent / "jobs" / job_id
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"
        log_file.write_text(
            completed.stdout + ("\nSTDERR\n" + completed.stderr if completed.stderr else ""),
            encoding="utf-8",
        )
        if completed.returncode:
            raise RuntimeError(f"Evidence pipeline failed with exit code {completed.returncode}. See explicit log file with extra details at: {log_file.absolute()}")
        completed_at = utc_now()
        store.set_metadata("last_retrieval_at", completed_at)
        return {"retrieval": "completed", "last_retrieval_at": completed_at}


def execute_job(
    database_path: Path,
    root: Path,
    job_id: str,
    document_database_path: Path | None = None,
    key_file: Path | None = None,
    ai_mode: str = "off",
) -> dict[str, Any]:
    encryption = EncryptionManager.load_or_create(key_file or database_path.with_name("signalwatch.key"))
    store = SignalWatchStore(database_path, encryption)
    store.initialize()
    documents = DocumentStore(
        document_database_path or database_path.with_name("signalwatch.documents.json"), encryption
    )
    documents.initialize(root / "storage" / "signalwatch.seed.json")
    job = store.job(job_id)
    if not job:
        raise KeyError(f"Unknown refresh job: {job_id}")
    store.mark_job_running(job_id, os.getpid())
    store.append_audit(None, "refresh.started", "refresh_job", job_id, {"rm_id": job["rm_id"], "worker_pid": os.getpid()})
    retrieval_summary: dict[str, Any] = {"retrieval": "skipped"}
    retrieval_started = time.perf_counter()
    if job["retrieve"]:
        retrieval_summary = run_retrieval_if_needed(store, documents, root, job_id, ai_mode)
    retrieval_duration_ms = round((time.perf_counter() - retrieval_started) * 1000)
    store.record_cost_event(
        job_id,
        job["rm_id"],
        "evidence_retrieval",
        "http_and_rules",
        duration_ms=retrieval_duration_ms,
        metadata=retrieval_summary,
    )

    alerts = documents.collection("alerts")
    preferences = store.preferences(job["rm_id"])
    classification_started = time.perf_counter()
    notifications, summary = evaluate_alerts(alerts, preferences)
    classification_duration_ms = round((time.perf_counter() - classification_started) * 1000)
    store.record_cost_event(
        job_id,
        job["rm_id"],
        "notification_classification",
        "deterministic_rules",
        duration_ms=classification_duration_ms,
        metadata={"alerts_evaluated": len(alerts), "notifications_created": len(notifications)},
    )
    ai_analysis = documents.document("ai_analysis", {}) if retrieval_summary.get("retrieval") == "completed" else {}
    usage_records = [
        item.get("model_usage", {})
        for item in (ai_analysis.get("analyses", []) if isinstance(ai_analysis, dict) else [])
        if item.get("model_usage")
    ]
    tokens_in = sum(int(item.get("prompt_tokens") or 0) for item in usage_records)
    tokens_out = sum(int(item.get("completion_tokens") or 0) for item in usage_records)
    input_rate = float(os.getenv("SIGNALWATCH_MODEL_INPUT_USD_PER_1M", "0"))
    output_rate = float(os.getenv("SIGNALWATCH_MODEL_OUTPUT_USD_PER_1M", "0"))
    estimated_cost = ((tokens_in * input_rate) + (tokens_out * output_rate)) / 1_000_000
    store.record_cost_event(
        job_id,
        job["rm_id"],
        "llm_reasoning",
        str(ai_analysis.get("model") or ("not_invoked" if ai_mode == "off" else ai_mode)),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        estimated_cost_usd=estimated_cost,
        metadata={
            "ai_mode": ai_mode,
            "model_calls_with_usage": len(usage_records),
            "input_rate_usd_per_million": input_rate,
            "output_rate_usd_per_million": output_rate,
        },
    )
    store.replace_notifications(job["rm_id"], notifications)
    summary = {**summary, **retrieval_summary, "rm_id": job["rm_id"]}
    store.complete_job(job_id, summary)
    store.append_audit(
        None,
        "refresh.completed",
        "refresh_job",
        job_id,
        {"rm_id": job["rm_id"], "summary": summary},
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute one isolated SignalWatch RM refresh job.")
    parser.add_argument("--database", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--document-database", required=True)
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--ai-mode", choices=["off", "mock", "live"], default="off")
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    encryption = EncryptionManager.load_or_create(Path(args.key_file))
    store = SignalWatchStore(Path(args.database), encryption)
    try:
        summary = execute_job(
            Path(args.database),
            Path(args.root),
            args.job_id,
            Path(args.document_database),
            Path(args.key_file),
            args.ai_mode,
        )
        print(json.dumps(summary))
        return 0
    except Exception as error:
        store.fail_job(args.job_id, f"{type(error).__name__}: {error}")
        store.append_audit(
            None,
            "refresh.failed",
            "refresh_job",
            args.job_id,
            {"error_type": type(error).__name__, "message": str(error)},
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
