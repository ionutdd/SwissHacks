from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import secrets
import ssl
import subprocess
import sys
import threading
import time
from http.cookies import SimpleCookie
from datetime import datetime, time as datetime_time, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit
from zoneinfo import ZoneInfo

from .document_store import DocumentStore
from .security import EncryptionManager, mask_sensitive, new_csrf_token, new_session_token
from .store import SignalWatchStore, utc_now


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = ROOT / "runtime" / "signalwatch.db"
DEFAULT_DOCUMENT_SEED = ROOT / "storage" / "signalwatch.seed.json"
SCHEDULE_HOURS = (7, 13)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def schedule_payload(manager: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    zone = ZoneInfo(manager["timezone"])
    local_now = now.astimezone(zone)
    candidates: list[datetime] = []
    for day_offset in (0, 1):
        local_date = local_now.date() + timedelta(days=day_offset)
        for hour in SCHEDULE_HOURS:
            candidate = datetime.combine(local_date, datetime_time(hour=hour), tzinfo=zone)
            if candidate > local_now:
                candidates.append(candidate)
    next_run = min(candidates)
    return {
        "local_datetime": local_now.replace(microsecond=0).isoformat(),
        "next_run_at": next_run.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "next_run_local": next_run.replace(microsecond=0).isoformat(),
        "schedule_local_hours": list(SCHEDULE_HOURS),
    }


def due_schedule_slots(manager: dict[str, Any], now: datetime | None = None) -> list[dict[str, str]]:
    now = now or datetime.now(timezone.utc)
    zone = ZoneInfo(manager["timezone"])
    local_now = now.astimezone(zone)
    due: list[dict[str, str]] = []
    for hour in SCHEDULE_HOURS:
        local_slot = datetime.combine(local_now.date(), datetime_time(hour=hour), tzinfo=zone)
        lateness = local_now - local_slot
        if timedelta(0) <= lateness < timedelta(hours=6):
            due.append(
                {
                    "schedule_key": f"{manager['id']}:{local_slot.date().isoformat()}:{hour:02d}",
                    "scheduled_for": local_slot.astimezone(timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                }
            )
    return due


def seed_existing_notifications(store: SignalWatchStore, documents: DocumentStore) -> None:
    if store.metadata("existing_notifications_seeded"):
        return
    material_alerts = documents.collection("material_alerts")
    for manager in store.relationship_managers():
        watchlist = set(store.preferences(manager["id"])["watchlist_customer_ids"])
        matching = [alert for alert in material_alerts if alert.get("customer_id") in watchlist]
        store.replace_notifications(manager["id"], matching)
    store.set_metadata("existing_notifications_seeded", utc_now())


class Scheduler:
    def __init__(self, store: SignalWatchStore, poll_seconds: int = 20):
        self.store = store
        self.poll_seconds = poll_seconds
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, name="signalwatch-scheduler", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=5)

    def tick(self, now: datetime | None = None) -> None:
        for manager in self.store.relationship_managers():
            if not manager["enabled"]:
                continue
            for slot in due_schedule_slots(manager, now):
                job = self.store.create_job(
                    manager["id"],
                    "scheduled",
                    retrieve=True,
                    schedule_key=slot["schedule_key"],
                    scheduled_for=slot["scheduled_for"],
                )
                if job:
                    self.store.append_audit(
                        None,
                        "refresh.scheduled",
                        "refresh_job",
                        job["id"],
                        {"rm_id": manager["id"], "scheduled_for": slot["scheduled_for"]},
                    )

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as error:
                print(f"Scheduler tick failed: {error}", file=sys.stderr)
            self.stop_event.wait(self.poll_seconds)


class WorkerManager:
    def __init__(
        self,
        store: SignalWatchStore,
        documents: DocumentStore,
        key_file: Path,
        root: Path,
        ai_mode: str = "off",
        max_workers: int = 2,
        poll_seconds: int = 2,
    ):
        self.store = store
        self.documents = documents
        self.key_file = key_file
        self.root = root
        self.ai_mode = ai_mode
        self.max_workers = max(1, max_workers)
        self.poll_seconds = poll_seconds
        self.stop_event = threading.Event()
        self.processes: dict[str, tuple[subprocess.Popen[str], Any]] = {}
        self.thread = threading.Thread(target=self._run, name="signalwatch-worker-manager", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=5)
        for process, log_handle in self.processes.values():
            if process.poll() is None:
                process.terminate()
            log_handle.close()

    def _reap(self) -> None:
        for job_id, (process, log_handle) in list(self.processes.items()):
            if process.poll() is None:
                continue
            log_handle.close()
            if process.returncode and self.store.job(job_id) and self.store.job(job_id)["status"] == "running":
                self.store.fail_job(job_id, f"Worker exited with code {process.returncode}.")
            del self.processes[job_id]

    def _start_queued(self) -> None:
        capacity = self.max_workers - len(self.processes)
        if capacity <= 0:
            return
        for job in self.store.queued_jobs(capacity):
            log_path = self.store.database_path.parent / "jobs" / job["id"] / "worker.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = log_path.open("a", encoding="utf-8")
            self.store.mark_job_running(job["id"], 0)
            command = [
                sys.executable,
                "-m",
                "server.worker",
                "--database",
                str(self.store.database_path),
                "--root",
                str(self.root),
                "--document-database",
                str(self.documents.path),
                "--key-file",
                str(self.key_file),
                "--ai-mode",
                self.ai_mode,
                "--job-id",
                job["id"],
            ]
            try:
                process = subprocess.Popen(
                    command,
                    cwd=self.root,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
            except Exception as error:
                log_handle.close()
                self.store.fail_job(job["id"], f"Could not start worker: {error}")
                continue
            self.processes[job["id"]] = (process, log_handle)

    def _run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self._reap()
                self._start_queued()
            except Exception as error:
                print(f"Worker manager tick failed: {error}", file=sys.stderr)
            self.stop_event.wait(self.poll_seconds)


class SignalWatchHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        store: SignalWatchStore,
        root: Path,
        documents: DocumentStore,
        encryption: EncryptionManager,
        cookie_secure: bool,
        scheduler: Scheduler,
        workers: WorkerManager,
    ):
        super().__init__(address, SignalWatchHandler)
        self.store = store
        self.root = root
        self.documents = documents
        self.encryption = encryption
        self.cookie_secure = cookie_secure
        self.scheduler = scheduler
        self.workers = workers
        self.login_attempts: dict[str, list[float]] = {}
        self.login_attempt_lock = threading.Lock()

    def allow_login_attempt(self, address: str) -> bool:
        cutoff = time.monotonic() - 300
        with self.login_attempt_lock:
            attempts = [item for item in self.login_attempts.get(address, []) if item >= cutoff]
            if len(attempts) >= 10:
                self.login_attempts[address] = attempts
                return False
            attempts.append(time.monotonic())
            self.login_attempts[address] = attempts
            return True


class SignalWatchHandler(BaseHTTPRequestHandler):
    server: SignalWatchHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format_string: str, *args: object) -> None:
        print(f"{self.address_string()} [{self.log_date_time_string()}] {format_string % args}")

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        if self.server.cookie_secure:
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' https://cdn.amcharts.com; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )
        super().end_headers()

    def send_json(
        self,
        value: Any,
        status: HTTPStatus = HTTPStatus.OK,
        headers: dict[str, str] | None = None,
    ) -> None:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for name, header_value in (headers or {}).items():
            self.send_header(name, header_value)
        self.end_headers()
        self.wfile.write(payload)

    def send_error_json(self, status: HTTPStatus, message: str) -> None:
        self.send_json({"error": message}, status)

    def read_json(self) -> dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length header.") from error
        if content_length <= 0 or content_length > 1_000_000:
            raise ValueError("Request body must be between 1 byte and 1 MB.")
        try:
            value = json.loads(self.rfile.read(content_length))
        except json.JSONDecodeError as error:
            raise ValueError("Request body is not valid JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Request body must be a JSON object.")
        return value

    def session_token(self) -> str | None:
        authorization = self.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            return authorization.removeprefix("Bearer ").strip()
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        morsel = cookie.get("signalwatch_session")
        return morsel.value if morsel else None

    def authenticate(self, require_csrf: bool = False) -> dict[str, Any] | None:
        token = self.session_token()
        if not token:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "Authentication required.")
            return None
        digest = self.server.encryption.token_digest(token)
        session = self.server.store.authenticated_session(digest)
        if not session:
            self.send_error_json(HTTPStatus.UNAUTHORIZED, "Session is invalid or expired.")
            return None
        if require_csrf:
            csrf = self.headers.get("X-CSRF-Token", "")
            csrf_digest = self.server.encryption.token_digest(csrf, "csrf-token") if csrf else ""
            if not csrf or not secrets.compare_digest(csrf_digest, session["csrf_digest"]):
                self.send_error_json(HTTPStatus.FORBIDDEN, "CSRF validation failed.")
                return None
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                self.send_error_json(HTTPStatus.FORBIDDEN, "Cross-origin state change rejected.")
                return None
        return session

    @staticmethod
    def can_access_rm(user: dict[str, Any], rm_id: str) -> bool:
        return user["role"] in {"admin", "compliance", "auditor"} or (
            user["role"] == "rm" and user.get("rm_id") == rm_id
        )

    def require_roles(self, session: dict[str, Any], *roles: str) -> bool:
        if session["user"]["role"] in roles:
            return True
        self.send_error_json(HTTPStatus.FORBIDDEN, "Your role does not permit this operation.")
        return False

    def session_cookie(self, token: str, max_age: int = 28800) -> str:
        parts = [
            f"signalwatch_session={token}",
            "Path=/",
            "HttpOnly",
            "SameSite=Strict",
            f"Max-Age={max_age}",
        ]
        if self.server.cookie_secure:
            parts.append("Secure")
        return "; ".join(parts)

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/api/health":
            self.send_json({"status": "ok", "time": utc_now()})
            return
        if parsed.path.startswith("/dashboard/") or parsed.path == "/dashboard":
            self.serve_dashboard(parsed.path)
            return
        if parsed.path in {"", "/"}:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/dashboard/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        session = self.authenticate()
        if not session:
            return
        user = session["user"]
        if parsed.path == "/api/auth/me":
            csrf = new_csrf_token()
            self.server.store.rotate_session_csrf(
                session["id"], self.server.encryption.token_digest(csrf, "csrf-token")
            )
            self.send_json({"user": user, "csrf_token": csrf})
            return
        if parsed.path == "/api/relation-managers":
            managers = [
                self.manager_payload(item)
                for item in self.server.store.relationship_managers()
                if self.can_access_rm(user, item["id"])
            ]
            self.send_json({"relationship_managers": managers})
            return
        if parsed.path == "/api/bootstrap":
            query = parse_qs(parsed.query)
            rm_id = query.get("rm_id", [""])[0]
            self.bootstrap(rm_id, session)
            return
        match = re.fullmatch(r"/api/relation-managers/([^/]+)/jobs", parsed.path)
        if match:
            rm_id = unquote(match.group(1))
            if not self.server.store.relationship_manager(rm_id) or not self.can_access_rm(user, rm_id):
                self.send_error_json(HTTPStatus.NOT_FOUND, "Relationship manager not found.")
                return
            self.send_json({"jobs": self.server.store.jobs(rm_id)})
            return
        if parsed.path == "/api/approvals":
            if user["role"] == "rm":
                approvals = self.server.store.approvals(user.get("rm_id"))
            else:
                approvals = self.server.store.approvals()
            self.send_json({"approvals": approvals})
            return
        if parsed.path == "/api/audit":
            if not self.require_roles(session, "admin", "compliance", "auditor"):
                return
            self.send_json(
                {
                    "verification": self.server.store.verify_audit_chain(),
                    "events": self.server.store.audit_events(),
                }
            )
            return
        if parsed.path == "/api/costs":
            if not self.require_roles(session, "admin", "compliance", "auditor"):
                return
            self.send_json({"costs": self.server.store.cost_summary()})
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Not found.")

    def do_PUT(self) -> None:
        parsed = urlsplit(self.path)
        session = self.authenticate(require_csrf=True)
        if not session:
            return
        if not self.require_roles(session, "admin", "compliance", "rm"):
            return
        match = re.fullmatch(r"/api/relation-managers/([^/]+)/preferences", parsed.path)
        if not match:
            self.send_error_json(HTTPStatus.NOT_FOUND, "Not found.")
            return
        rm_id = unquote(match.group(1))
        if not self.server.store.relationship_manager(rm_id) or not self.can_access_rm(session["user"], rm_id):
            self.send_error_json(HTTPStatus.NOT_FOUND, "Relationship manager not found.")
            return
        try:
            body = self.read_json()
            customers = self.server.documents.collection("customers")
            customer_ids = {item["customer_id"] for item in customers}
            if session["user"]["role"] == "rm":
                customer_ids &= self.server.store.portfolio_customer_ids(rm_id)
            timezone_name = str(body.pop("timezone", self.server.store.relationship_manager(rm_id)["timezone"])).strip()
            manager = self.server.store.update_relationship_manager(rm_id, timezone_name)
            preferences = self.server.store.update_preferences(rm_id, body, customer_ids)
            job = self.server.store.create_job(rm_id, "preferences", retrieve=True)
        except (ValueError, KeyError) as error:
            self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
            return
        self.server.store.append_audit(
            session["user"]["id"],
            "notification_preferences.updated",
            "relationship_manager",
            rm_id,
            {"preferences": preferences, "refresh_job_id": job["id"] if job else None},
        )
        self.send_json(
            {"relationship_manager": self.manager_payload(manager), "preferences": preferences, "job": job}
        )

    def do_POST(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/api/auth/login":
            if not self.server.allow_login_attempt(self.client_address[0]):
                self.send_error_json(HTTPStatus.TOO_MANY_REQUESTS, "Too many login attempts. Try again later.")
                return
            try:
                body = self.read_json()
            except ValueError as error:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
                return
            username = str(body.get("username", ""))[:200]
            password = str(body.get("password", ""))
            user = self.server.store.authenticate_user(username, password)
            if not user:
                self.server.store.append_audit(
                    None, "authentication.failed", "user", username.lower(), {"remote": self.client_address[0]}
                )
                self.send_error_json(HTTPStatus.UNAUTHORIZED, "Invalid username or password.")
                return
            token = new_session_token()
            csrf = new_csrf_token()
            session_record = self.server.store.create_session(
                user["id"],
                self.server.encryption.token_digest(token),
                self.server.encryption.token_digest(csrf, "csrf-token"),
            )
            self.server.store.append_audit(
                user["id"], "authentication.succeeded", "session", session_record["id"], {"remote": self.client_address[0]}
            )
            self.send_json(
                {"user": user, "csrf_token": csrf},
                headers={"Set-Cookie": self.session_cookie(token)},
            )
            return

        session = self.authenticate(require_csrf=True)
        if not session:
            return
        user = session["user"]
        if parsed.path == "/api/auth/logout":
            self.server.store.revoke_session(session["id"])
            self.server.store.append_audit(user["id"], "authentication.logged_out", "session", session["id"], {})
            self.send_json(
                {"logged_out": True},
                headers={"Set-Cookie": self.session_cookie("", max_age=0)},
            )
            return
        match = re.fullmatch(r"/api/relation-managers/([^/]+)/refresh", parsed.path)
        if match:
            rm_id = unquote(match.group(1))
            if not self.require_roles(session, "admin", "compliance", "rm"):
                return
            if not self.server.store.relationship_manager(rm_id) or not self.can_access_rm(user, rm_id):
                self.send_error_json(HTTPStatus.NOT_FOUND, "Relationship manager not found.")
                return
            if self.headers.get("Content-Length", "0") not in {"", "0"}:
                try:
                    self.read_json()
                except ValueError as error:
                    self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
                    return
            job = self.server.store.create_job(rm_id, "manual", retrieve=True)
            self.server.store.append_audit(
                user["id"], "refresh.requested", "refresh_job", job["id"], {"rm_id": rm_id}
            )
            self.send_json({"job": job}, HTTPStatus.ACCEPTED)
            return
        match = re.fullmatch(r"/api/relation-managers/([^/]+)/actions", parsed.path)
        if match:
            rm_id = unquote(match.group(1))
            if not self.require_roles(session, "admin", "compliance", "rm"):
                return
            if not self.server.store.relationship_manager(rm_id) or not self.can_access_rm(user, rm_id):
                self.send_error_json(HTTPStatus.NOT_FOUND, "Relationship manager not found.")
                return
            try:
                action_payload = self.read_json()
            except ValueError as error:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
                return
            requested_action = str(action_payload.get("action", ""))
            if requested_action in {"escalated", "dismissed", "customer_update_requested"}:
                approval = self.server.store.create_approval(
                    rm_id,
                    str(action_payload.get("alert_id", "")),
                    requested_action,
                    action_payload,
                    user["id"],
                )
                self.server.store.append_audit(
                    user["id"],
                    "approval.requested",
                    "approval",
                    approval["id"],
                    {"rm_id": rm_id, "alert_id": approval["alert_id"], "requested_action": requested_action},
                )
                self.send_json({"approval": approval}, HTTPStatus.ACCEPTED)
                return
            try:
                action = self.server.store.add_action(rm_id, action_payload)
            except ValueError as error:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
                return
            self.server.store.append_audit(
                user["id"], "review_action.recorded", "alert", action["alert_id"], {"action": action["action"], "rm_id": rm_id}
            )
            self.send_json({"action": action}, HTTPStatus.CREATED)
            return
        match = re.fullmatch(r"/api/approvals/([^/]+)/decision", parsed.path)
        if match:
            if not self.require_roles(session, "admin", "compliance"):
                return
            approval_id = unquote(match.group(1))
            try:
                body = self.read_json()
                approval = self.server.store.decide_approval(
                    approval_id,
                    user["id"],
                    str(body.get("decision", "")),
                    str(body.get("note", "")),
                )
                action = None
                if approval["status"] == "approved":
                    action_payload = {**approval["payload"], "created_by": user["display_name"]}
                    action = self.server.store.add_action(approval["rm_id"], action_payload)
            except KeyError:
                self.send_error_json(HTTPStatus.NOT_FOUND, "Approval not found.")
                return
            except ValueError as error:
                self.send_error_json(HTTPStatus.BAD_REQUEST, str(error))
                return
            self.server.store.append_audit(
                user["id"],
                f"approval.{approval['status']}",
                "approval",
                approval_id,
                {"alert_id": approval["alert_id"], "action_id": action["id"] if action else None},
            )
            self.send_json({"approval": approval, "action": action})
            return
        self.send_error_json(HTTPStatus.NOT_FOUND, "Not found.")

    def do_DELETE(self) -> None:
        session = self.authenticate(require_csrf=True)
        if not session:
            return
        self.send_error_json(HTTPStatus.METHOD_NOT_ALLOWED, "Banking audit records cannot be deleted.")

    def manager_payload(self, manager: dict[str, Any]) -> dict[str, Any]:
        payload = dict(manager)
        payload["portfolio_customer_ids"] = sorted(self.server.store.portfolio_customer_ids(manager["id"]))
        payload.update(schedule_payload(manager))
        payload["preferences"] = self.server.store.preferences(manager["id"])
        latest_jobs = self.server.store.jobs(manager["id"], limit=1)
        payload["latest_job"] = latest_jobs[0] if latest_jobs else None
        return payload

    def bootstrap(self, rm_id: str, session: dict[str, Any]) -> None:
        user = session["user"]
        managers = [
            item for item in self.server.store.relationship_managers() if self.can_access_rm(user, item["id"])
        ]
        if not rm_id and managers:
            rm_id = user.get("rm_id") or managers[0]["id"]
        manager = self.server.store.relationship_manager(rm_id)
        if not manager or not self.can_access_rm(user, rm_id):
            self.send_error_json(HTTPStatus.NOT_FOUND, "Relationship manager not found.")
            return
        allowed_customer_ids = (
            self.server.store.portfolio_customer_ids(rm_id)
            if user["role"] == "rm"
            else {item["customer_id"] for item in self.server.documents.collection("customers")}
        )
        customers = [
            item for item in self.server.documents.collection("customers") if item.get("customer_id") in allowed_customer_ids
        ]
        documents = [
            item
            for item in self.server.documents.collection("evidence_documents")
            if item.get("customer_id") in allowed_customer_ids
        ]
        document_ids = {item.get("document_id") for item in documents}
        facts = [
            item for item in self.server.documents.collection("facts") if item.get("customer_id") in allowed_customer_ids
        ]
        alerts = [
            item for item in self.server.documents.collection("alerts") if item.get("customer_id") in allowed_customer_ids
        ]
        noise = [
            item
            for item in self.server.documents.collection("noise_suppression")
            if item.get("customer_id") in allowed_customer_ids
        ]
        ai_analysis = self.server.documents.document("ai_analysis", {"analyses": []})
        if isinstance(ai_analysis, dict):
            ai_analysis = {
                **ai_analysis,
                "analyses": [
                    item for item in ai_analysis.get("analyses", []) if item.get("document_id") in document_ids
                ],
            }
        internal_signals = [
            item for item in self.server.documents.collection("internal_signals") if item.get("customer_id") in allowed_customer_ids
        ]
        fused_alerts = [
            item for item in self.server.documents.collection("fused_alerts") if item.get("customer_id") in allowed_customer_ids
        ]
        expanded_profiles = [
            item
            for item in self.server.documents.collection("expanded_kyc_profiles")
            if item.get("customer_id") in allowed_customer_ids
        ]
        founder_investor = self.server.documents.document("founder_investor", {"customers": []})
        public_kyc = self.server.documents.document("public_kyc", {"customers": []})
        if isinstance(founder_investor, dict):
            founder_investor = {
                **founder_investor,
                "customers": [
                    item for item in founder_investor.get("customers", []) if item.get("customer_id") in allowed_customer_ids
                ],
            }
        if isinstance(public_kyc, dict):
            public_kyc = {
                **public_kyc,
                "customers": [
                    item for item in public_kyc.get("customers", []) if item.get("customer_id") in allowed_customer_ids
                ],
            }
        if user["role"] not in {"admin", "compliance"}:
            internal_signals = mask_sensitive(internal_signals)
            fused_alerts = mask_sensitive(fused_alerts)
            expanded_profiles = mask_sensitive(expanded_profiles)
        jobs = self.server.store.jobs(rm_id)
        completed_summary = next((job["summary"] for job in jobs if job["status"] == "completed"), None)
        payload = {
            "relationshipManagers": [self.manager_payload(item) for item in managers],
            "currentRelationshipManager": self.manager_payload(manager),
            "authenticatedUser": user,
            "preferences": self.server.store.preferences(rm_id),
            "customers": customers,
            "documents": documents,
            "facts": facts,
            "alerts": alerts,
            "aiAnalysis": ai_analysis,
            "materialAlerts": [
                item
                for item in self.server.store.notifications(rm_id)
                if item.get("customer_id") in allowed_customer_ids
            ],
            "noiseSuppression": noise,
            "refreshSummary": completed_summary or self.server.documents.document("refresh_summary", {}),
            "internalSignals": internal_signals,
            "fusedAlerts": fused_alerts,
            "expandedKycProfiles": expanded_profiles,
            "layer2SignalPlaybook": self.server.documents.collection("signal_playbook"),
            "founderInvestor": founder_investor,
            "publicKyc": public_kyc,
            "actions": self.server.store.actions(rm_id),
            "approvals": self.server.store.approvals(rm_id),
            "costSummary": self.server.store.cost_summary(),
            "jobs": jobs,
        }
        self.send_json(payload)

    def serve_dashboard(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"/dashboard", "/dashboard/"} else request_path.removeprefix("/dashboard/")
        dashboard_root = (self.server.root / "dashboard").resolve()
        file_path = (dashboard_root / unquote(relative)).resolve()
        try:
            file_path.relative_to(dashboard_root)
        except ValueError:
            self.send_error_json(HTTPStatus.FORBIDDEN, "Forbidden.")
            return
        if not file_path.is_file():
            self.send_error_json(HTTPStatus.NOT_FOUND, "Asset not found.")
            return
        payload = file_path.read_bytes()
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(payload)


def build_server(
    host: str,
    port: int,
    database: Path,
    max_workers: int,
    document_database: Path | None = None,
    key_file: Path | None = None,
    cookie_secure: bool = False,
    ai_mode: str = "off",
) -> SignalWatchHTTPServer:
    key_file = key_file or database.with_name("signalwatch.key")
    encryption = EncryptionManager.load_or_create(key_file)
    store = SignalWatchStore(database, encryption)
    store.initialize()
    store.recover_interrupted_jobs()
    documents = DocumentStore(
        document_database or database.with_name("signalwatch.documents.json"), encryption
    )
    documents.initialize(DEFAULT_DOCUMENT_SEED)
    seed_existing_notifications(store, documents)
    scheduler = Scheduler(store)
    workers = WorkerManager(store, documents, key_file, ROOT, ai_mode=ai_mode, max_workers=max_workers)
    return SignalWatchHTTPServer(
        (host, port), store, ROOT, documents, encryption, cookie_secure, scheduler, workers
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SignalWatch application server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--document-database", type=Path, default=None)
    parser.add_argument("--key-file", type=Path, default=None)
    parser.add_argument("--secure-cookie", action="store_true", help="Require HTTPS for the session cookie.")
    parser.add_argument("--tls-cert", type=Path, help="PEM certificate chain for HTTPS.")
    parser.add_argument("--tls-key", type=Path, help="PEM private key for HTTPS.")
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 2))
    parser.add_argument("--ai-mode", choices=["off", "mock", "live"], default="off")
    args = parser.parse_args()
    if bool(args.tls_cert) != bool(args.tls_key):
        raise ValueError("--tls-cert and --tls-key must be provided together.")
    if args.host not in {"127.0.0.1", "localhost", "::1"} and not args.tls_cert:
        raise ValueError("Non-loopback binding requires --tls-cert and --tls-key.")
    server = build_server(
        args.host,
        args.port,
        args.database,
        args.workers,
        args.document_database,
        args.key_file,
        args.secure_cookie or bool(args.tls_cert),
        args.ai_mode,
    )
    scheme = "http"
    if args.tls_cert and args.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.tls_cert, args.tls_key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        scheme = "https"
    server.scheduler.start()
    server.workers.start()
    print(f"SignalWatch listening on {scheme}://{args.host}:{args.port}/dashboard/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.scheduler.stop()
        server.workers.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
