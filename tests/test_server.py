from __future__ import annotations

import json
import threading
import unittest
from http.cookiejar import CookieJar
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen


ROOT = Path(__file__).resolve().parents[1]

from server.app import build_server, due_schedule_slots, schedule_payload
from server.document_store import DocumentStore
from server.notification_engine import evaluate_alerts
from server.security import EncryptionManager, hash_password
from server.store import DEFAULT_PREFERENCES, SignalWatchStore, validate_preferences
from server.worker import execute_job


class NotificationEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.alerts = DocumentStore(ROOT / "storage" / "signalwatch.seed.json").collection("alerts")
        cls.now = datetime(2026, 6, 20, 14, 37, 31, tzinfo=timezone.utc)

    def test_default_demo_policy_selects_alphabet_material_alerts(self) -> None:
        preferences = {
            **DEFAULT_PREFERENCES,
            "watchlist_customer_ids": ["demo-009"],
        }
        alerts, summary = evaluate_alerts(self.alerts, preferences, self.now)
        self.assertEqual([item["alert_id"] for item in alerts], ["alert-061", "alert-063", "alert-062"])
        self.assertEqual(summary["material_alerts"], 3)

    def test_custom_threshold_and_category_change_qualification(self) -> None:
        preferences = {
            **DEFAULT_PREFERENCES,
            "watchlist_customer_ids": ["demo-009"],
            "minimum_material_score": 120,
            "categories": ["opportunity"],
        }
        alerts, _summary = evaluate_alerts(self.alerts, preferences, self.now)
        self.assertEqual([item["alert_id"] for item in alerts], ["alert-063", "alert-062"])

    def test_preference_validation_rejects_unknown_customers(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown watchlist"):
            validate_preferences(
                {**DEFAULT_PREFERENCES, "watchlist_customer_ids": ["missing"]},
                {"demo-001"},
            )


class ScheduleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = {"id": "rm-test", "timezone": "Europe/Zurich"}

    def test_next_run_uses_rm_timezone(self) -> None:
        now = datetime(2026, 6, 21, 4, 0, tzinfo=timezone.utc)
        payload = schedule_payload(self.manager, now)
        self.assertEqual(payload["next_run_at"], "2026-06-21T05:00:00Z")
        self.assertIn("07:00:00+02:00", payload["next_run_local"])

    def test_due_slots_include_local_morning_and_lunch(self) -> None:
        morning = due_schedule_slots(self.manager, datetime(2026, 6, 21, 5, 1, tzinfo=timezone.utc))
        lunch = due_schedule_slots(self.manager, datetime(2026, 6, 21, 11, 1, tzinfo=timezone.utc))
        self.assertEqual(morning[0]["schedule_key"], "rm-test:2026-06-21:07")
        self.assertEqual(lunch[-1]["schedule_key"], "rm-test:2026-06-21:13")


class StoreAndWorkerTests(unittest.TestCase):
    def test_document_store_keeps_schema_free_collections(self) -> None:
        store = DocumentStore(ROOT / "storage" / "signalwatch.seed.json")
        self.assertEqual(len(store.collection("customers")), 9)
        self.assertEqual(len(store.collection("alerts")), 63)
        self.assertIn("customers", store.document("founder_investor"))

    def test_preferences_actions_and_jobs_are_persistent(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "signalwatch.db"
            store = SignalWatchStore(path)
            store.initialize()
            store.update_preferences("rm-mara-keller", {"lookback_hours": 48})
            action = store.add_action(
                "rm-mara-keller",
                {"alert_id": "alert-061", "customer_id": "demo-009", "action": "acknowledged"},
            )
            reopened = SignalWatchStore(path)
            reopened.initialize()
            self.assertEqual(reopened.preferences("rm-mara-keller")["lookback_hours"], 48)
            self.assertEqual(reopened.actions("rm-mara-keller")[0]["id"], action["id"])

    def test_classification_worker_writes_rm_notifications(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "signalwatch.db"
            key_file = Path(directory) / "signalwatch.key"
            encryption = EncryptionManager.load_or_create(key_file)
            store = SignalWatchStore(path, encryption)
            store.initialize()
            store.update_preferences(
                "rm-mara-keller",
                {
                    "lookback_hours": 720,
                    "minimum_material_score": 100,
                    "watchlist_customer_ids": ["demo-009"],
                    "include_collected_evidence": True,
                },
            )
            job = store.create_job("rm-mara-keller", "test", retrieve=False)
            summary = execute_job(path, ROOT, job["id"], key_file=key_file)
            self.assertEqual(store.job(job["id"])["status"], "completed")
            self.assertEqual(summary["rm_id"], "rm-mara-keller")
            self.assertGreater(len(store.notifications("rm-mara-keller")), 0)
            self.assertEqual(store.cost_summary()["event_count"], 3)
            self.assertTrue(store.verify_audit_chain()["valid"])


class SecurityAndGovernanceTests(unittest.TestCase):
    def test_runtime_documents_are_encrypted_and_authenticated(self) -> None:
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            encryption = EncryptionManager.load_or_create(directory / "signalwatch.key")
            store = DocumentStore(directory / "documents.json", encryption)
            store.initialize(ROOT / "storage" / "signalwatch.seed.json")
            raw = store.path.read_text(encoding="utf-8")
            self.assertNotIn("Robinhood Markets", raw)
            self.assertIn("swenc:v1:", raw)
            self.assertEqual(len(store.collection("alerts")), 63)

    def test_argon2_uses_unique_salts(self) -> None:
        first = hash_password("Correct-Horse-Battery-42!")
        second = hash_password("Correct-Horse-Battery-42!")
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("$argon2id$"))

    def test_existing_plaintext_application_state_is_encrypted_on_upgrade(self) -> None:
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            database = directory / "state.db"
            plaintext_store = SignalWatchStore(database)
            plaintext_store.initialize()
            plaintext_store.replace_notifications(
                "rm-mara-keller",
                [{"alert_id": "alert-secret", "customer_id": "demo-009", "title": "Sensitive alert title"}],
            )
            plaintext_store.add_action(
                "rm-mara-keller",
                {
                    "alert_id": "alert-secret",
                    "customer_id": "demo-009",
                    "action": "acknowledged",
                    "note": "Sensitive analyst note",
                },
            )
            encryption = EncryptionManager.load_or_create(directory / "signalwatch.key")
            encrypted_store = SignalWatchStore(database, encryption)
            encrypted_store.initialize()
            raw = database.read_bytes()
            self.assertNotIn(b"Sensitive alert title", raw)
            self.assertNotIn(b"Sensitive analyst note", raw)
            self.assertEqual(encrypted_store.notifications("rm-mara-keller")[0]["title"], "Sensitive alert title")
            self.assertEqual(encrypted_store.actions("rm-mara-keller")[0]["note"], "Sensitive analyst note")

    def test_maker_checker_audit_chain_and_cost_telemetry(self) -> None:
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            encryption = EncryptionManager.load_or_create(directory / "signalwatch.key")
            store = SignalWatchStore(directory / "state.db", encryption)
            store.initialize()
            maker = store.create_user(
                "maker", "RM Maker", "rm", hash_password("Maker-Password-Secure-42!"), "rm-mara-keller"
            )
            checker = store.create_user(
                "checker", "Compliance Checker", "compliance", hash_password("Checker-Password-Strong-42!"), None
            )
            approval = store.create_approval(
                "rm-mara-keller",
                "alert-061",
                "escalated",
                {"alert_id": "alert-061", "customer_id": "demo-009", "action": "escalated"},
                maker["id"],
            )
            with self.assertRaisesRegex(ValueError, "own request"):
                store.decide_approval(approval["id"], maker["id"], "approved")
            decided = store.decide_approval(approval["id"], checker["id"], "approved")
            self.assertEqual(decided["status"], "approved")

            store.append_audit(maker["id"], "approval.requested", "approval", approval["id"], {})
            store.append_audit(checker["id"], "approval.approved", "approval", approval["id"], {})
            self.assertTrue(store.verify_audit_chain()["valid"])
            with store.connection() as connection:
                with self.assertRaises(Exception):
                    connection.execute("UPDATE audit_events SET action = 'tampered'")

            store.record_cost_event(None, "rm-mara-keller", "llm_reasoning", "not_invoked", duration_ms=12)
            summary = store.cost_summary()
            self.assertEqual(summary["event_count"], 1)
            self.assertEqual(summary["duration_ms"], 12)


class HttpServerTests(unittest.TestCase):
    def test_bootstrap_and_preference_api(self) -> None:
        with TemporaryDirectory() as directory:
            server = build_server("127.0.0.1", 0, Path(directory) / "signalwatch.db", 1)
            server.store.create_user(
                "mara",
                "Mara Keller",
                "rm",
                hash_password("Correct-Horse-Battery-42!"),
                "rm-mara-keller",
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            opener = build_opener(HTTPCookieProcessor(CookieJar()))
            try:
                login = Request(
                    f"{base}/api/auth/login",
                    data=json.dumps({"username": "mara", "password": "Correct-Horse-Battery-42!"}).encode("utf-8"),
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                authentication = json.load(opener.open(login))
                csrf = authentication["csrf_token"]
                bootstrap = json.load(opener.open(f"{base}/api/bootstrap?rm_id=rm-mara-keller"))
                self.assertEqual(len(bootstrap["customers"]), 2)
                self.assertEqual(len(bootstrap["materialAlerts"]), 3)
                self.assertIn("[REDACTED]", json.dumps(bootstrap["internalSignals"]))

                preferences = bootstrap["preferences"] | {"lookback_hours": 36, "timezone": "Europe/Bucharest"}
                request = Request(
                    f"{base}/api/relation-managers/rm-mara-keller/preferences",
                    data=json.dumps(preferences).encode("utf-8"),
                    method="PUT",
                    headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
                )
                missing_csrf = Request(
                    f"{base}/api/relation-managers/rm-mara-keller/preferences",
                    data=json.dumps(preferences).encode("utf-8"),
                    method="PUT",
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as csrf_denied:
                    opener.open(missing_csrf)
                self.assertEqual(csrf_denied.exception.code, 403)
                updated = json.load(opener.open(request))
                self.assertEqual(updated["preferences"]["lookback_hours"], 36)
                self.assertEqual(updated["relationship_manager"]["timezone"], "Europe/Bucharest")
                self.assertTrue(updated["job"]["retrieve"])
                self.assertEqual(opener.open(f"{base}/dashboard/").status, 200)
                with self.assertRaises(HTTPError) as denied:
                    opener.open(f"{base}/api/bootstrap?rm_id=rm-alex-meier")
                self.assertEqual(denied.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
