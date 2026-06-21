from __future__ import annotations

import json
import hashlib
import hmac
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .security import EncryptionManager, verify_password


DEFAULT_RELATIONSHIP_MANAGERS = (
    ("rm-mara-keller", "Mara Keller", "Europe/Zurich", ["demo-001", "demo-009"]),
    ("rm-alex-meier", "Alex Meier", "Europe/Zurich", ["demo-002"]),
    ("rm-jonas-frei", "Jonas Frei", "Europe/Zurich", ["demo-003"]),
    ("rm-nina-schmid", "Nina Schmid", "Europe/Zurich", ["demo-004"]),
    ("rm-rafael-costa", "Rafael Costa", "Europe/Zurich", ["demo-005"]),
    ("rm-lea-baumann", "Lea Baumann", "Europe/Zurich", ["demo-006"]),
    ("rm-sofia-weber", "Sofia Weber", "Europe/Zurich", ["demo-007"]),
    ("rm-daniel-roth", "Daniel Roth", "Europe/Zurich", ["demo-008"]),
)

DEFAULT_PREFERENCES: dict[str, Any] = {
    "lookback_hours": 24,
    "minimum_material_score": 100,
    "minimum_confidence": 0.70,
    "categories": ["risk", "ownership_control", "mixed", "opportunity"],
    "severities": ["critical", "high", "medium", "low"],
    "signal_types": [],
    "require_source_url": True,
    "include_undated_collected": False,
    "include_collected_evidence": False,
}

ALLOWED_CATEGORIES = {"risk", "ownership_control", "mixed", "opportunity"}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_preferences(value: dict[str, Any], customer_ids: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Preferences must be a JSON object.")
    merged = {**DEFAULT_PREFERENCES, **value}

    try:
        merged["lookback_hours"] = int(merged["lookback_hours"])
        merged["minimum_material_score"] = int(merged["minimum_material_score"])
        merged["minimum_confidence"] = float(merged["minimum_confidence"])
    except (TypeError, ValueError) as error:
        raise ValueError("Lookback, score, and confidence must be numeric.") from error

    if not 1 <= merged["lookback_hours"] <= 720:
        raise ValueError("Lookback hours must be between 1 and 720.")
    if not 0 <= merged["minimum_material_score"] <= 500:
        raise ValueError("Minimum material score must be between 0 and 500.")
    if not 0 <= merged["minimum_confidence"] <= 1:
        raise ValueError("Minimum confidence must be between 0 and 1.")

    for key, allowed in (("categories", ALLOWED_CATEGORIES), ("severities", ALLOWED_SEVERITIES)):
        items = merged.get(key)
        if not isinstance(items, list) or not items:
            raise ValueError(f"{key.replace('_', ' ').title()} must contain at least one value.")
        normalized = list(dict.fromkeys(str(item) for item in items))
        unknown = set(normalized) - allowed
        if unknown:
            raise ValueError(f"Unsupported {key}: {', '.join(sorted(unknown))}.")
        merged[key] = normalized

    signal_types = merged.get("signal_types", [])
    if not isinstance(signal_types, list):
        raise ValueError("Signal types must be a list.")
    merged["signal_types"] = list(dict.fromkeys(str(item).strip() for item in signal_types if str(item).strip()))

    watchlist = merged.get("watchlist_customer_ids", [])
    if not isinstance(watchlist, list):
        raise ValueError("Watchlist customer IDs must be a list.")
    watchlist = list(dict.fromkeys(str(item).strip() for item in watchlist if str(item).strip()))
    if customer_ids is not None:
        unknown_customers = set(watchlist) - customer_ids
        if unknown_customers:
            raise ValueError(f"Unknown watchlist customers: {', '.join(sorted(unknown_customers))}.")
    merged["watchlist_customer_ids"] = watchlist

    for key in ("require_source_url", "include_undated_collected", "include_collected_evidence"):
        if not isinstance(merged.get(key), bool):
            raise ValueError(f"{key.replace('_', ' ').title()} must be true or false.")
    return merged


class SignalWatchStore:
    def __init__(self, database_path: Path | str, encryption: EncryptionManager | None = None):
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption = encryption

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA secure_delete = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS relationship_managers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    rm_id TEXT PRIMARY KEY REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    config_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rm_portfolios (
                    rm_id TEXT NOT NULL REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    customer_id TEXT NOT NULL,
                    PRIMARY KEY (rm_id, customer_id)
                );
                CREATE TABLE IF NOT EXISTS refresh_jobs (
                    id TEXT PRIMARY KEY,
                    rm_id TEXT NOT NULL REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    trigger_type TEXT NOT NULL,
                    schedule_key TEXT UNIQUE,
                    retrieve INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    scheduled_for TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    worker_pid INTEGER,
                    summary_json TEXT,
                    error TEXT
                );
                CREATE INDEX IF NOT EXISTS refresh_jobs_rm_created_idx
                    ON refresh_jobs(rm_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS notifications (
                    rm_id TEXT NOT NULL REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    alert_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    PRIMARY KEY (rm_id, alert_id)
                );
                CREATE TABLE IF NOT EXISTS review_actions (
                    id TEXT PRIMARY KEY,
                    rm_id TEXT NOT NULL REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    alert_id TEXT NOT NULL,
                    notification_key TEXT,
                    customer_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS review_actions_rm_created_idx
                    ON review_actions(rm_id, created_at);
                CREATE TRIGGER IF NOT EXISTS review_actions_no_update
                    BEFORE UPDATE ON review_actions BEGIN
                        SELECT RAISE(ABORT, 'review actions are append-only');
                    END;
                CREATE TRIGGER IF NOT EXISTS review_actions_no_delete
                    BEFORE DELETE ON review_actions BEGIN
                        SELECT RAISE(ABORT, 'review actions are append-only');
                    END;
                CREATE TABLE IF NOT EXISTS app_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    rm_id TEXT REFERENCES relationship_managers(id) ON DELETE SET NULL,
                    password_hash TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    failed_attempts INTEGER NOT NULL DEFAULT 0,
                    locked_until TEXT,
                    last_login_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_digest TEXT NOT NULL UNIQUE,
                    csrf_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    idle_expires_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    revoked_at TEXT
                );
                CREATE INDEX IF NOT EXISTS sessions_token_idx ON sessions(token_digest);
                CREATE TABLE IF NOT EXISTS approval_requests (
                    id TEXT PRIMARY KEY,
                    rm_id TEXT NOT NULL REFERENCES relationship_managers(id) ON DELETE CASCADE,
                    alert_id TEXT NOT NULL,
                    requested_action TEXT NOT NULL,
                    payload_ciphertext TEXT NOT NULL,
                    status TEXT NOT NULL,
                    maker_user_id TEXT NOT NULL REFERENCES users(id),
                    checker_user_id TEXT REFERENCES users(id),
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decision_note_ciphertext TEXT
                );
                CREATE INDEX IF NOT EXISTS approvals_status_idx ON approval_requests(status, created_at);
                CREATE TRIGGER IF NOT EXISTS approval_requests_no_delete
                    BEFORE DELETE ON approval_requests BEGIN
                        SELECT RAISE(ABORT, 'approval requests are immutable');
                    END;
                CREATE TRIGGER IF NOT EXISTS approval_requests_decided_no_update
                    BEFORE UPDATE ON approval_requests WHEN OLD.status != 'pending' BEGIN
                        SELECT RAISE(ABORT, 'decided approvals are immutable');
                    END;
                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    actor_user_id TEXT REFERENCES users(id),
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    payload_ciphertext TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                    BEFORE UPDATE ON audit_events BEGIN
                        SELECT RAISE(ABORT, 'audit events are append-only');
                    END;
                CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                    BEFORE DELETE ON audit_events BEGIN
                        SELECT RAISE(ABORT, 'audit events are append-only');
                    END;
                CREATE TABLE IF NOT EXISTS model_cost_events (
                    id TEXT PRIMARY KEY,
                    job_id TEXT REFERENCES refresh_jobs(id) ON DELETE SET NULL,
                    rm_id TEXT REFERENCES relationship_managers(id) ON DELETE SET NULL,
                    stage TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    tokens_in INTEGER NOT NULL DEFAULT 0,
                    tokens_out INTEGER NOT NULL DEFAULT 0,
                    estimated_cost_usd REAL NOT NULL DEFAULT 0,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    metadata_ciphertext TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS model_cost_created_idx ON model_cost_events(created_at DESC);
                """
            )
        self._seed_relationship_managers()
        if self.encryption:
            self._encrypt_existing_state()

    def _encrypt_existing_state(self) -> None:
        changed = False
        with self.connection() as connection:
            notification_rows = connection.execute(
                "SELECT rm_id, alert_id, payload_json FROM notifications"
            ).fetchall()
            for row in notification_rows:
                if not row["payload_json"].startswith("swenc:"):
                    changed = True
                    value = json.loads(row["payload_json"])
                    connection.execute(
                        "UPDATE notifications SET payload_json = ? WHERE rm_id = ? AND alert_id = ?",
                        (
                            self._protect_json(value, f"notification:{row['rm_id']}:{row['alert_id']}"),
                            row["rm_id"],
                            row["alert_id"],
                        ),
                    )
            job_rows = connection.execute(
                "SELECT id, summary_json, error FROM refresh_jobs"
            ).fetchall()
            for row in job_rows:
                if row["summary_json"] and not row["summary_json"].startswith("swenc:"):
                    changed = True
                    connection.execute(
                        "UPDATE refresh_jobs SET summary_json = ? WHERE id = ?",
                        (self._protect_json(json.loads(row["summary_json"]), f"job:{row['id']}:summary"), row["id"]),
                    )
                if row["error"] and not row["error"].startswith("swenc:"):
                    changed = True
                    connection.execute(
                        "UPDATE refresh_jobs SET error = ? WHERE id = ?",
                        (
                            self._protect_text(
                                self._unprotect_text(row["error"], f"job:{row['id']}:error"),
                                f"job:{row['id']}:error",
                            ),
                            row["id"],
                        ),
                    )
            action_rows = connection.execute("SELECT id, note FROM review_actions").fetchall()
            if any(row["note"] and not row["note"].startswith("swenc:") for row in action_rows):
                changed = True
                connection.execute("DROP TRIGGER IF EXISTS review_actions_no_update")
                for row in action_rows:
                    if row["note"] and not row["note"].startswith("swenc:"):
                        connection.execute(
                            "UPDATE review_actions SET note = ? WHERE id = ?",
                            (
                                self._protect_text(
                                    self._unprotect_text(row["note"], f"action:{row['id']}:note"),
                                    f"action:{row['id']}:note",
                                ),
                                row["id"],
                            ),
                        )
                connection.execute(
                    """
                    CREATE TRIGGER review_actions_no_update
                    BEFORE UPDATE ON review_actions BEGIN
                        SELECT RAISE(ABORT, 'review actions are append-only');
                    END
                    """
                )
        if changed:
            connection = sqlite3.connect(self.database_path, isolation_level=None, timeout=30)
            try:
                connection.execute("PRAGMA secure_delete = ON")
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                connection.execute("VACUUM")
            finally:
                connection.close()

    def _protect_json(self, value: Any, associated_data: str) -> str:
        if self.encryption:
            return self.encryption.encrypt_json(value, associated_data)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    def _unprotect_json(self, value: str | None, associated_data: str, fallback: Any = None) -> Any:
        if not value:
            return fallback
        if self.encryption and value.startswith("swenc:"):
            return self.encryption.decrypt_json(value, associated_data)
        return json.loads(value)

    def _protect_text(self, value: str, associated_data: str) -> str:
        return self._protect_json({"value": value}, associated_data)

    def _unprotect_text(self, value: str | None, associated_data: str) -> str:
        if value and not value.startswith("swenc:") and not value.lstrip().startswith("{"):
            return value
        payload = self._unprotect_json(value, associated_data, {"value": ""})
        return str(payload.get("value", ""))

    def _seed_relationship_managers(self) -> None:
        now = utc_now()
        with self.connection() as connection:
            for rm_id, name, timezone_name, watchlist in DEFAULT_RELATIONSHIP_MANAGERS:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO relationship_managers
                        (id, name, timezone, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, 1, ?, ?)
                    """,
                    (rm_id, name, timezone_name, now, now),
                )
                preferences = {**DEFAULT_PREFERENCES, "watchlist_customer_ids": watchlist}
                connection.execute(
                    """
                    INSERT OR IGNORE INTO notification_preferences (rm_id, config_json, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (rm_id, json.dumps(preferences, separators=(",", ":")), now),
                )
                for customer_id in watchlist:
                    connection.execute(
                        "INSERT OR IGNORE INTO rm_portfolios (rm_id, customer_id) VALUES (?, ?)",
                        (rm_id, customer_id),
                    )

    def relationship_managers(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM relationship_managers ORDER BY name"
            ).fetchall()
        return [dict(row) | {"enabled": bool(row["enabled"])} for row in rows]

    def relationship_manager(self, rm_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM relationship_managers WHERE id = ?", (rm_id,)
            ).fetchone()
        return (dict(row) | {"enabled": bool(row["enabled"])}) if row else None

    def portfolio_customer_ids(self, rm_id: str) -> set[str]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT customer_id FROM rm_portfolios WHERE rm_id = ?", (rm_id,)
            ).fetchall()
        return {row["customer_id"] for row in rows}

    def update_relationship_manager(self, rm_id: str, timezone_name: str, enabled: bool = True) -> dict[str, Any]:
        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown timezone: {timezone_name}.") from error
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE relationship_managers SET timezone = ?, enabled = ?, updated_at = ? WHERE id = ?",
                (timezone_name, int(enabled), utc_now(), rm_id),
            )
            if not cursor.rowcount:
                raise KeyError(rm_id)
        return self.relationship_manager(rm_id) or {}

    def preferences(self, rm_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT config_json FROM notification_preferences WHERE rm_id = ?", (rm_id,)
            ).fetchone()
        if not row:
            raise KeyError(rm_id)
        return json.loads(row["config_json"])

    def update_preferences(
        self, rm_id: str, value: dict[str, Any], customer_ids: set[str] | None = None
    ) -> dict[str, Any]:
        current = self.preferences(rm_id)
        preferences = validate_preferences({**current, **value}, customer_ids)
        with self.connection() as connection:
            connection.execute(
                "UPDATE notification_preferences SET config_json = ?, updated_at = ? WHERE rm_id = ?",
                (json.dumps(preferences, separators=(",", ":")), utc_now(), rm_id),
            )
        return preferences

    def create_job(
        self,
        rm_id: str,
        trigger_type: str,
        retrieve: bool = True,
        schedule_key: str | None = None,
        scheduled_for: str | None = None,
    ) -> dict[str, Any] | None:
        job_id = f"job-{uuid.uuid4().hex}"
        now = utc_now()
        try:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO refresh_jobs
                        (id, rm_id, trigger_type, schedule_key, retrieve, status, created_at, scheduled_for)
                    VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)
                    """,
                    (job_id, rm_id, trigger_type, schedule_key, int(retrieve), now, scheduled_for),
                )
        except sqlite3.IntegrityError:
            return None
        return self.job(job_id)

    def job(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM refresh_jobs WHERE id = ?", (job_id,)).fetchone()
        return self._job_payload(row) if row else None

    def jobs(self, rm_id: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
        query = "SELECT * FROM refresh_jobs"
        params: list[Any] = []
        if rm_id:
            query += " WHERE rm_id = ?"
            params.append(rm_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._job_payload(row) for row in rows]

    def _job_payload(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["retrieve"] = bool(payload["retrieve"])
        payload["summary"] = self._unprotect_json(
            payload.pop("summary_json"), f"job:{payload['id']}:summary", None
        )
        if payload.get("error"):
            payload["error"] = self._unprotect_text(payload["error"], f"job:{payload['id']}:error")
        return payload

    def queued_jobs(self, limit: int) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM refresh_jobs WHERE status = 'queued' ORDER BY created_at LIMIT ?", (limit,)
            ).fetchall()
        return [self._job_payload(row) for row in rows]

    def recover_interrupted_jobs(self) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE refresh_jobs
                SET status = 'queued', started_at = NULL, worker_pid = NULL,
                    error = NULL
                WHERE status = 'running' AND completed_at IS NULL
                """
            )

    def mark_job_running(self, job_id: str, worker_pid: int) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE refresh_jobs SET status = 'running', started_at = ?, worker_pid = ? WHERE id = ?",
                (utc_now(), worker_pid, job_id),
            )

    def complete_job(self, job_id: str, summary: dict[str, Any]) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE refresh_jobs
                SET status = 'completed', completed_at = ?, summary_json = ?, error = NULL
                WHERE id = ?
                """,
                (utc_now(), self._protect_json(summary, f"job:{job_id}:summary"), job_id),
            )

    def fail_job(self, job_id: str, error: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE refresh_jobs SET status = 'failed', completed_at = ?, error = ? WHERE id = ?",
                (utc_now(), self._protect_text(error[-4000:], f"job:{job_id}:error"), job_id),
            )

    def replace_notifications(self, rm_id: str, alerts: list[dict[str, Any]]) -> None:
        now = utc_now()
        with self.connection() as connection:
            connection.execute("UPDATE notifications SET active = 0 WHERE rm_id = ?", (rm_id,))
            for rank, alert in enumerate(alerts, start=1):
                connection.execute(
                    """
                    INSERT INTO notifications
                        (rm_id, alert_id, payload_json, rank, active, first_seen_at, last_seen_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    ON CONFLICT(rm_id, alert_id) DO UPDATE SET
                        payload_json = excluded.payload_json,
                        rank = excluded.rank,
                        active = 1,
                        last_seen_at = excluded.last_seen_at
                    """,
                    (
                        rm_id,
                        alert["alert_id"],
                        self._protect_json(alert, f"notification:{rm_id}:{alert['alert_id']}"),
                        rank,
                        now,
                        now,
                    ),
                )

    def notifications(self, rm_id: str, active_only: bool = True) -> list[dict[str, Any]]:
        query = "SELECT alert_id, payload_json FROM notifications WHERE rm_id = ?"
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY rank"
        with self.connection() as connection:
            rows = connection.execute(query, (rm_id,)).fetchall()
        return [
            self._unprotect_json(row["payload_json"], f"notification:{rm_id}:{row['alert_id']}", {})
            for row in rows
        ]

    def add_action(self, rm_id: str, value: dict[str, Any]) -> dict[str, Any]:
        allowed_actions = {
            "acknowledged",
            "escalated",
            "customer_update_requested",
            "added_to_call_brief",
            "dismissed",
        }
        action = str(value.get("action", ""))
        if action not in allowed_actions:
            raise ValueError("Unsupported review action.")
        alert_id = str(value.get("alert_id", "")).strip()
        customer_id = str(value.get("customer_id", "")).strip()
        if not alert_id or not customer_id:
            raise ValueError("Alert ID and customer ID are required.")
        record = {
            "id": str(value.get("id") or f"action-{uuid.uuid4().hex}"),
            "rm_id": rm_id,
            "alert_id": alert_id,
            "notification_key": value.get("notification_key"),
            "customer_id": customer_id,
            "action": action,
            "note": str(value.get("note", ""))[:2000],
            "created_by": str(value.get("created_by") or rm_id),
            "created_at": str(value.get("created_at") or utc_now()),
        }
        stored_record = {
            **record,
            "note": self._protect_text(record["note"], f"action:{record['id']}:note"),
        }
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO review_actions
                    (id, rm_id, alert_id, notification_key, customer_id, action, note, created_by, created_at)
                VALUES (:id, :rm_id, :alert_id, :notification_key, :customer_id, :action, :note, :created_by, :created_at)
                """,
                stored_record,
            )
        return record

    def actions(self, rm_id: str) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM review_actions WHERE rm_id = ? ORDER BY created_at", (rm_id,)
            ).fetchall()
        actions: list[dict[str, Any]] = []
        for row in rows:
            action = dict(row)
            action["note"] = self._unprotect_text(action["note"], f"action:{action['id']}:note")
            actions.append(action)
        return actions

    def create_user(
        self,
        username: str,
        display_name: str,
        role: str,
        password_hash: str,
        rm_id: str | None = None,
    ) -> dict[str, Any]:
        username = username.strip().lower()
        if not username or not display_name.strip():
            raise ValueError("Username and display name are required.")
        if role not in {"admin", "compliance", "rm", "auditor"}:
            raise ValueError("Role must be admin, compliance, rm, or auditor.")
        if role == "rm" and not rm_id:
            raise ValueError("RM users must be assigned to a relationship manager.")
        if rm_id and not self.relationship_manager(rm_id):
            raise ValueError("Assigned relationship manager does not exist.")
        user_id = f"user-{uuid.uuid4().hex}"
        now = utc_now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO users
                    (id, username, display_name, role, rm_id, password_hash, active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (user_id, username, display_name.strip(), role, rm_id, password_hash, now, now),
            )
        return self.user(user_id) or {}

    def user(self, user_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self._public_user(row) if row else None

    def users(self) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM users ORDER BY username").fetchall()
        return [self._public_user(row) for row in rows]

    @staticmethod
    def _public_user(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload.pop("password_hash", None)
        payload.pop("failed_attempts", None)
        payload.pop("locked_until", None)
        payload["active"] = bool(payload["active"])
        return payload

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        username = username.strip().lower()
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not row:
            # Keep nonexistent-user requests on the same expensive Argon2 path.
            verify_password(
                "$argon2id$v=19$m=65536,t=3,p=4$mJMMAID84Bik237VDO182g$imLZ3rPq6voZWKK+MZTVESD7QkECTF/qYHHwXEykqU4",
                password,
            )
            return None
        user = dict(row)
        if not user["active"]:
            return None
        now = datetime.now(timezone.utc)
        locked_until = user.get("locked_until")
        if locked_until and datetime.fromisoformat(locked_until.replace("Z", "+00:00")) > now:
            return None
        valid, replacement_hash = verify_password(user["password_hash"], password)
        with self.connection() as connection:
            if not valid:
                attempts = int(user.get("failed_attempts") or 0) + 1
                lock = (now + timedelta(minutes=15)).replace(microsecond=0).isoformat().replace("+00:00", "Z") if attempts >= 5 else None
                connection.execute(
                    "UPDATE users SET failed_attempts = ?, locked_until = ?, updated_at = ? WHERE id = ?",
                    (attempts, lock, utc_now(), user["id"]),
                )
                return None
            connection.execute(
                """
                UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL,
                    last_login_at = ?, updated_at = ? WHERE id = ?
                """,
                (replacement_hash or user["password_hash"], utc_now(), utc_now(), user["id"]),
            )
        return self.user(user["id"])

    def create_session(self, user_id: str, token_digest: str, csrf_digest: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        session_id = f"session-{uuid.uuid4().hex}"
        record = {
            "id": session_id,
            "user_id": user_id,
            "token_digest": token_digest,
            "csrf_digest": csrf_digest,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now + timedelta(hours=8)).isoformat().replace("+00:00", "Z"),
            "idle_expires_at": (now + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
            "last_seen_at": now.isoformat().replace("+00:00", "Z"),
        }
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions
                    (id, user_id, token_digest, csrf_digest, created_at, expires_at, idle_expires_at, last_seen_at)
                VALUES (:id, :user_id, :token_digest, :csrf_digest, :created_at, :expires_at, :idle_expires_at, :last_seen_at)
                """,
                record,
            )
        return record

    def authenticated_session(self, token_digest: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT s.*, u.username, u.display_name, u.role, u.rm_id, u.active
                FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_digest = ? AND s.revoked_at IS NULL
                """,
                (token_digest,),
            ).fetchone()
        if not row or not row["active"]:
            return None
        payload = dict(row)
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        idle_expires = datetime.fromisoformat(payload["idle_expires_at"].replace("Z", "+00:00"))
        if expires <= now or idle_expires <= now:
            self.revoke_session(payload["id"])
            return None
        now_text = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        idle_text = (now + timedelta(minutes=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        with self.connection() as connection:
            connection.execute(
                "UPDATE sessions SET last_seen_at = ?, idle_expires_at = ? WHERE id = ?",
                (now_text, idle_text, payload["id"]),
            )
        payload["user"] = {
            "id": payload["user_id"],
            "username": payload["username"],
            "display_name": payload["display_name"],
            "role": payload["role"],
            "rm_id": payload["rm_id"],
        }
        return payload

    def rotate_session_csrf(self, session_id: str, csrf_digest: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE sessions SET csrf_digest = ? WHERE id = ?", (csrf_digest, session_id))

    def revoke_session(self, session_id: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", (utc_now(), session_id))

    def create_approval(self, rm_id: str, alert_id: str, requested_action: str, payload: dict[str, Any], maker_user_id: str) -> dict[str, Any]:
        approval_id = f"approval-{uuid.uuid4().hex}"
        now = utc_now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO approval_requests
                    (id, rm_id, alert_id, requested_action, payload_ciphertext, status, maker_user_id, created_at)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
                """,
                (
                    approval_id,
                    rm_id,
                    alert_id,
                    requested_action,
                    self._protect_json(payload, f"approval:{approval_id}:payload"),
                    maker_user_id,
                    now,
                ),
            )
        return self.approval(approval_id) or {}

    def approval(self, approval_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM approval_requests WHERE id = ?", (approval_id,)).fetchone()
        return self._approval_payload(row) if row else None

    def approvals(self, rm_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM approval_requests"
        params: list[Any] = []
        if rm_id:
            query += " WHERE rm_id = ?"
            params.append(rm_id)
        query += " ORDER BY created_at DESC"
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._approval_payload(row) for row in rows]

    def _approval_payload(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["payload"] = self._unprotect_json(
            payload.pop("payload_ciphertext"), f"approval:{payload['id']}:payload", {}
        )
        payload["decision_note"] = self._unprotect_text(
            payload.pop("decision_note_ciphertext"), f"approval:{payload['id']}:decision"
        ) if payload.get("decision_note_ciphertext") else ""
        return payload

    def decide_approval(self, approval_id: str, checker_user_id: str, decision: str, note: str = "") -> dict[str, Any]:
        if decision not in {"approved", "rejected"}:
            raise ValueError("Decision must be approved or rejected.")
        approval = self.approval(approval_id)
        if not approval:
            raise KeyError(approval_id)
        if approval["status"] != "pending":
            raise ValueError("Approval has already been decided.")
        if approval["maker_user_id"] == checker_user_id:
            raise ValueError("Maker-checker control forbids approving your own request.")
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE approval_requests SET status = ?, checker_user_id = ?, decided_at = ?,
                    decision_note_ciphertext = ? WHERE id = ? AND status = 'pending'
                """,
                (
                    decision,
                    checker_user_id,
                    utc_now(),
                    self._protect_text(note[:2000], f"approval:{approval_id}:decision"),
                    approval_id,
                ),
            )
        return self.approval(approval_id) or {}

    def append_audit(self, actor_user_id: str | None, action: str, entity_type: str, entity_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        event_id = f"audit-{uuid.uuid4().hex}"
        created_at = utc_now()
        ciphertext = self._protect_json(payload, f"audit:{event_id}:payload")
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous = connection.execute("SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1").fetchone()
            previous_hash = previous["event_hash"] if previous else "0" * 64
            canonical = "|".join(
                [previous_hash, event_id, created_at, actor_user_id or "system", action, entity_type, entity_id, ciphertext]
            ).encode("utf-8")
            key = self.encryption.derive("audit-chain-v1") if self.encryption else b"signalwatch-test-audit-key"
            event_hash = hmac.new(key, canonical, hashlib.sha256).hexdigest()
            connection.execute(
                """
                INSERT INTO audit_events
                    (id, created_at, actor_user_id, action, entity_type, entity_id,
                     payload_ciphertext, previous_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, created_at, actor_user_id, action, entity_type, entity_id, ciphertext, previous_hash, event_hash),
            )
        return {"id": event_id, "created_at": created_at, "event_hash": event_hash}

    def audit_events(self, limit: int = 200) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM audit_events ORDER BY sequence DESC LIMIT ?", (limit,)).fetchall()
        events: list[dict[str, Any]] = []
        for row in rows:
            event = dict(row)
            event["payload"] = self._unprotect_json(
                event.pop("payload_ciphertext"), f"audit:{event['id']}:payload", {}
            )
            events.append(event)
        return events

    def verify_audit_chain(self) -> dict[str, Any]:
        with self.connection() as connection:
            rows = connection.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        previous_hash = "0" * 64
        key = self.encryption.derive("audit-chain-v1") if self.encryption else b"signalwatch-test-audit-key"
        for row in rows:
            canonical = "|".join(
                [
                    previous_hash,
                    row["id"],
                    row["created_at"],
                    row["actor_user_id"] or "system",
                    row["action"],
                    row["entity_type"],
                    row["entity_id"],
                    row["payload_ciphertext"],
                ]
            ).encode("utf-8")
            expected = hmac.new(key, canonical, hashlib.sha256).hexdigest()
            if row["previous_hash"] != previous_hash or not hmac.compare_digest(expected, row["event_hash"]):
                return {"valid": False, "events_checked": row["sequence"] - 1, "broken_at": row["id"]}
            previous_hash = row["event_hash"]
        return {"valid": True, "events_checked": len(rows), "head_hash": previous_hash}

    def record_cost_event(
        self,
        job_id: str | None,
        rm_id: str | None,
        stage: str,
        model_name: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        estimated_cost_usd: float = 0,
        duration_ms: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event_id = f"cost-{uuid.uuid4().hex}"
        created_at = utc_now()
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO model_cost_events
                    (id, job_id, rm_id, stage, model_name, tokens_in, tokens_out,
                     estimated_cost_usd, duration_ms, metadata_ciphertext, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    job_id,
                    rm_id,
                    stage,
                    model_name,
                    max(0, int(tokens_in)),
                    max(0, int(tokens_out)),
                    max(0, float(estimated_cost_usd)),
                    max(0, int(duration_ms)),
                    self._protect_json(metadata or {}, f"cost:{event_id}:metadata"),
                    created_at,
                ),
            )
        return {"id": event_id, "created_at": created_at}

    def cost_summary(self) -> dict[str, Any]:
        with self.connection() as connection:
            totals = connection.execute(
                """
                SELECT COUNT(*) AS event_count, COALESCE(SUM(tokens_in), 0) AS tokens_in,
                       COALESCE(SUM(tokens_out), 0) AS tokens_out,
                       COALESCE(SUM(estimated_cost_usd), 0) AS estimated_cost_usd,
                       COALESCE(SUM(duration_ms), 0) AS duration_ms
                FROM model_cost_events
                """
            ).fetchone()
            by_stage = connection.execute(
                """
                SELECT stage, COUNT(*) AS executions, SUM(tokens_in) AS tokens_in,
                       SUM(tokens_out) AS tokens_out, SUM(estimated_cost_usd) AS estimated_cost_usd,
                       SUM(duration_ms) AS duration_ms
                FROM model_cost_events GROUP BY stage ORDER BY stage
                """
            ).fetchall()
        return {**dict(totals), "by_stage": [dict(row) for row in by_stage]}

    def metadata(self, key: str) -> str | None:
        with self.connection() as connection:
            row = connection.execute("SELECT value FROM app_metadata WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set_metadata(self, key: str, value: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO app_metadata (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
