import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from wexum_vpn_billing import (
    BillingEngine, BillingError, ConflictError, NotFoundError, Plan, SecurityError, TestHmacAdapter,
)


SECRET = b"synthetic-fixture-key-not-for-real-payments"
NOW = 1_800_000_000
PLAN = Plan("monthly", "KZT", 179000)


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.db"
        self.engine = BillingEngine(self.path, {"sandbox-test": TestHmacAdapter(SECRET)}, allow_test_adapters=True)
        self.order = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test", now=NOW, request_id="initial-checkout")

    def send(self, kind="paid", *, event_id="evt1", transaction_id="txn1", order_id=None,
             occurred_at=NOW, period_end=NOW+2592000, amount=PLAN.amount_minor, currency="KZT",
             now=NOW, secret=SECRET, **overrides):
        payload = dict(event_id=event_id, order_id=order_id or self.order, transaction_id=transaction_id,
                       kind=kind, occurred_at=occurred_at,
                       period_end=period_end if kind in ("paid", "renewed") else None,
                       amount_minor=amount, currency=currency)
        if kind in ("cancelled", "resumed", "payment_failed"):
            payload["transaction_id"] = ""
        payload.update(overrides)
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ts = str(now)
        signature = hmac.new(secret, ts.encode()+b"."+body, hashlib.sha256).hexdigest()
        headers = {"X-Test-Timestamp": ts, "X-Test-Signature": signature}
        return self.engine.accept_webhook("sandbox-test", body, headers, now=now)

    def snapshot(self, now=NOW):
        return self.engine.snapshot("tenant_A", "account_A", self.order, now=now)

    def test_storage_open_failure_is_sanitized_and_fail_closed(self):
        missing_parent = Path(self.tmp.name) / "missing-parent" / "billing.db"
        with self.assertRaisesRegex(BillingError, "^billing storage unavailable$") as caught:
            BillingEngine(missing_parent, {"sandbox-test": TestHmacAdapter(SECRET)}, allow_test_adapters=True)
        self.assertIsNone(caught.exception.__cause__)
        self.assertFalse(missing_parent.exists())

    def test_storage_outage_after_initialization_is_sanitized(self):
        self.path.unlink()
        self.path.mkdir()
        with self.assertRaisesRegex(BillingError, "^billing storage unavailable$") as caught:
            self.engine.snapshot("tenant_A", "account_A", self.order, now=NOW)
        self.assertIsNone(caught.exception.__cause__)

    def test_no_client_activation(self):
        self.assertFalse(self.snapshot().eligible)
        self.assertEqual(self.snapshot().state, "pending")
        with self.assertRaises(SecurityError):
            self.engine.accept_webhook("not-approved", b"{}", {}, now=NOW)

    def test_verified_payment_and_expiry(self):
        self.assertTrue(self.send().changed)
        self.assertEqual(self.snapshot().state, "active")
        self.assertFalse(self.snapshot(NOW+2592000).eligible)
        self.assertEqual(self.snapshot(NOW+2592000).state, "expired")

    def test_same_event_exactly_once(self):
        self.send()
        result = self.send()
        self.assertTrue(result.duplicate_event)
        self.assertFalse(result.changed)
        self.assertEqual(self.snapshot().revision, 1)

    def test_event_collision_rejected_without_mutation(self):
        self.send()
        with self.assertRaises(ConflictError):
            self.send(event_id="evt1", transaction_id="txn2")
        self.assertEqual(self.snapshot().revision, 1)

    def test_same_transaction_other_event_does_not_extend(self):
        self.send()
        result = self.send(event_id="evt2")
        self.assertFalse(result.changed)
        self.assertEqual(self.snapshot().access_until, NOW+2592000)

    def test_transaction_reuse_across_accounts_rejected(self):
        second = self.engine.create_order("tenant_B", "account_B", PLAN, "sandbox-test", now=NOW, request_id="secondary-checkout")
        self.send()
        with self.assertRaises(ConflictError):
            self.send(event_id="evt2", order_id=second)
        self.assertFalse(self.engine.snapshot("tenant_B", "account_B", second, now=NOW).eligible)

    def test_refund_revokes_and_no_resurrection(self):
        self.send()
        self.send("refunded", event_id="refund1")
        self.assertEqual(self.snapshot().state, "revoked")
        self.assertFalse(self.snapshot().eligible)
        self.send("renewed", event_id="late-paid", occurred_at=NOW-10)
        self.assertFalse(self.snapshot().eligible)

    def test_refund_before_paid_still_rejects_access(self):
        self.send("chargeback", event_id="back1")
        self.send(event_id="evt-late")
        self.assertEqual(self.snapshot().state, "revoked")

    def test_refund_old_period_does_not_revoke_new_period(self):
        self.send()
        self.send("renewed", event_id="evt2", transaction_id="txn2", period_end=NOW+5000000)
        self.send("refunded", event_id="refund1")
        self.assertTrue(self.snapshot().eligible)
        self.assertEqual(self.snapshot().access_until, NOW+5000000)

    def test_cancel_preserves_access_and_resume(self):
        self.send()
        self.send("cancelled", event_id="cancel1", occurred_at=NOW+10)
        self.assertEqual(self.snapshot().state, "cancellation_scheduled")
        self.send("resumed", event_id="resume1", occurred_at=NOW+20)
        self.assertEqual(self.snapshot().state, "active")
        self.send("cancelled", event_id="cancel-late", occurred_at=NOW+5)
        self.assertEqual(self.snapshot().state, "active")

    def test_failed_payment_does_not_grant_or_remove_access(self):
        self.send("payment_failed")
        self.assertFalse(self.snapshot().eligible)
        self.send(event_id="paid2")
        self.send("payment_failed", event_id="fail2")
        self.assertTrue(self.snapshot().eligible)

    def test_wrong_tenant_or_account_fails_closed(self):
        self.send()
        for tenant, account in [("tenant_B", "account_A"), ("tenant_A", "account_B")]:
            with self.assertRaises(NotFoundError):
                self.engine.snapshot(tenant, account, self.order, now=NOW)

    def test_price_currency_and_binding_mismatch(self):
        for kwargs in ({"amount":1}, {"currency":"USD"}, {"order_id":"not_created"}):
            with self.assertRaises(SecurityError):
                self.send(**kwargs)
        self.assertEqual(self.snapshot().revision, 0)

    def test_unsigned_and_wrong_signature(self):
        with self.assertRaises(SecurityError):
            self.send(secret=b"invalid-but-long-enough-test-key-123456789")
        self.assertFalse(self.snapshot().eligible)

    def test_duplicate_case_insensitive_signature_headers_fail_closed(self):
        body = self._payload()
        headers = self._headers()
        # Different HTTP stacks may choose the first or last case variant.
        for duplicate in (
            {"x-test-signature": headers["X-Test-Signature"]},
            {"x-test-signature": "0" * 64},
            {"x-test-timestamp": str(NOW)},
            {"x-test-timestamp": str(NOW + 1)},
        ):
            with self.subTest(duplicate=duplicate):
                with self.assertRaises(SecurityError):
                    self.engine.accept_webhook(
                        "sandbox-test", body, {**headers, **duplicate}, now=NOW
                    )
        self.assertEqual(self.snapshot().revision, 0)
        self.assertFalse(self.snapshot().eligible)

    def test_signature_headers_reject_non_string_values(self):
        body = self._payload()
        headers = self._headers()
        for invalid in ({**headers, "X-Test-Signature": None},
                        {**headers, 123: "irrelevant"}):
            with self.assertRaises(SecurityError):
                self.engine.accept_webhook("sandbox-test", body, invalid, now=NOW)
        self.assertEqual(self.snapshot().revision, 0)

    def test_signature_headers_reject_non_mapping_containers(self):
        body = self._payload()
        for invalid in (None, [], [("X-Test-Timestamp", str(NOW))], "headers"):
            with self.subTest(container=type(invalid).__name__):
                with self.assertRaisesRegex(SecurityError, "^invalid test signature headers$"):
                    self.engine.accept_webhook("sandbox-test", body, invalid, now=NOW)
        self.assertEqual(self.snapshot().revision, 0)
        self.assertFalse(self.snapshot().eligible)

    def test_unhashable_webhook_provider_rejected_without_ledger_mutation(self):
        body = self._payload()
        headers = self._headers()
        for provider in (None, [], {}, 123):
            with self.subTest(provider=type(provider).__name__):
                with self.assertRaisesRegex(SecurityError, "^unknown provider$"):
                    self.engine.accept_webhook(provider, body, headers, now=NOW)
        self.assertEqual(self.snapshot().revision, 0)
        self.assertFalse(self.snapshot().eligible)

    def test_old_signature_time(self):
        payload = dict(event_id="evt1", order_id=self.order, transaction_id="txn1", kind="paid",
                       occurred_at=NOW, period_end=NOW+300, currency="KZT", amount_minor=179000)
        body = json.dumps(payload).encode()
        stamp = str(NOW-301)
        sig = hmac.new(SECRET, stamp.encode()+b"."+body, hashlib.sha256).hexdigest()
        with self.assertRaises(SecurityError):
            self.engine.accept_webhook("sandbox-test", body, {"X-Test-Timestamp":stamp,"X-Test-Signature":sig}, now=NOW)

    def test_malformed_signed_json_and_duplicate_keys(self):
        for body in [b"{", b'{"event_id":"a","event_id":"b"}', b"[]"]:
            ts = str(NOW)
            sig = hmac.new(SECRET, ts.encode()+b"."+body, hashlib.sha256).hexdigest()
            with self.assertRaises(SecurityError):
                self.engine.accept_webhook("sandbox-test", body, {"x-test-timestamp":ts,"x-test-signature":sig}, now=NOW)

    def test_deeply_nested_signed_json_fails_closed(self):
        # A correctly signed but deeply nested payload must not leak RecursionError.
        body = b"[" * 1200 + b"0" + b"]" * 1200
        timestamp = str(NOW)
        signature = hmac.new(
            SECRET, timestamp.encode("ascii") + b"." + body, hashlib.sha256
        ).hexdigest()
        headers = {"X-Test-Timestamp": timestamp, "X-Test-Signature": signature}
        with self.assertRaisesRegex(SecurityError, "^invalid webhook JSON$"):
            self.engine.accept_webhook("sandbox-test", body, headers, now=NOW)
        self.assertEqual(self.snapshot().revision, 0)
        self.assertFalse(self.snapshot().eligible)

    def test_test_webhook_header_bounds_reject_before_ledger_write(self):
        body = self._payload()
        valid = self._headers()
        invalid_headers = [
            {**valid, **{f"X-Extra-{i}": "v" for i in range(31)}},
            {**valid, "X-Long-Name-" + "a" * 120: "v"},
            {**valid, "X-Extra": "v" * 257},
            {**valid, "X-Unicode-é": "v"},
        ]
        for headers in invalid_headers:
            with self.subTest(headers=list(headers)[-1]):
                with self.assertRaises(SecurityError):
                    self.engine.accept_webhook("sandbox-test", body, headers, now=NOW)
                self.assertEqual(self.snapshot().revision, 0)
                self.assertFalse(self.snapshot().eligible)

    def test_forbidden_live_adapter(self):
        class NotApproved:
            name = "live"
            test_only = False
        with self.assertRaises(SecurityError):
            BillingEngine(self.path, {"live":NotApproved()})
        with self.assertRaises(SecurityError):
            BillingEngine(self.path, {"sandbox-test":TestHmacAdapter(SECRET)})

    def test_concurrent_duplicate_event_is_one_revision(self):
        errors = []
        outcomes = []
        barrier = threading.Barrier(6)
        def worker():
            try:
                barrier.wait(timeout=3)
                outcomes.append(self.send())
            except Exception as exc:
                errors.append(exc)
        workers = [threading.Thread(target=worker) for _ in range(6)]
        for worker in workers: worker.start()
        for worker in workers: worker.join(timeout=6)
        self.assertFalse(errors, errors)
        self.assertEqual(sum(not o.duplicate_event for o in outcomes), 1)
        self.assertEqual(self.snapshot().revision, 1)

    def test_conflicting_period_for_existing_receipt_rolls_back(self):
        self.send()
        with self.assertRaises(ConflictError):
            self.send(event_id="evt-other", period_end=NOW+9999999)
        self.assertEqual(self.snapshot().revision, 1)
        self.assertEqual(self.snapshot().access_until, NOW+2592000)

    def test_expired_cancelled_period_stays_expired(self):
        self.send()
        self.send("cancelled", event_id="cancel1")
        self.assertEqual(self.snapshot(now=NOW+2592000).state, "expired")

    def test_recovery_after_chargeback_and_distinct_new_purchase(self):
        self.send()
        self.send("chargeback", event_id="charge1")
        self.assertFalse(self.snapshot().eligible)
        self.send("renewed", event_id="new-purchase", transaction_id="txn2", period_end=NOW+2592001)
        self.assertTrue(self.snapshot().eligible)

    def test_stored_sqlite_does_not_contain_raw_webhook(self):
        self.send()
        data = self.path.read_bytes()
        self.assertNotIn(b'"event_id":', data)
        self.assertNotIn(SECRET, data)

    def test_input_validation_rejects_bool_and_sql_fragments(self):
        with self.assertRaises(SecurityError):
            Plan("demo", "KZT", True)
        with self.assertRaises(SecurityError):
            self.engine.create_order("tenant_A;DROP TABLE orders", "account_A", PLAN, "sandbox-test", now=NOW, request_id="bad-tenant")
        with self.assertRaises(SecurityError):
            self.send(event_id="evt-bool", amount_minor=True)
        self.assertFalse(self.snapshot().eligible)

    def test_two_different_event_ids_for_same_receipt_concurrently(self):
        results = []
        errors = []
        barrier = threading.Barrier(2)
        def worker(event_id):
            try:
                barrier.wait(timeout=3)
                results.append(self.send(event_id=event_id))
            except Exception as exc:
                errors.append(exc)
        threads = [threading.Thread(target=worker, args=(name,)) for name in ("evtA", "evtB")]
        for t in threads: t.start()
        for t in threads: t.join(timeout=6)
        self.assertFalse(errors, errors)
        self.assertEqual(sum(result.changed for result in results), 1)
        self.assertEqual(self.snapshot().access_until, NOW+2592000)

    def test_ephemeral_database_path_is_rejected_before_open(self):
        # A new SQLite connection is opened per operation; :memory: would
        # silently discard the schema and every billing event on close.
        for bad in (":memory:", "", None, 42):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(SecurityError, "durable billing database path required"):
                    BillingEngine(bad, {"sandbox-test": TestHmacAdapter(SECRET)},
                                  allow_test_adapters=True)
        self.assertFalse(self.snapshot().eligible)

    def test_concurrent_conflicting_checkout_terms_create_only_one_order(self):
        # Two authenticated retries with the same scoped key but different
        # server-approved terms must never produce two durable orders.
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def worker(plan):
            try:
                barrier.wait(timeout=5)
                results.append(self.engine.create_order(
                    "tenant_A", "account_A", plan, "sandbox-test",
                    now=NOW, request_id="conflicting-concurrent-checkout"))
            except Exception as exc:
                errors.append(exc)

        plans = (PLAN, Plan("annual", "KZT", 500000))
        threads = [threading.Thread(target=worker, args=(plan,)) for plan in plans]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=8)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ConflictError)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM order_requests WHERE order_id=?",
                (results[0],)).fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)
        self.assertFalse(self.snapshot().eligible)

    def test_order_retry_returns_same_order(self):
        original = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                            now=NOW + 1, request_id="checkout-retry")
        retry = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                         now=NOW + 100, request_id="checkout-retry")
        self.assertEqual(original, retry)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)

    def test_order_retry_conflicting_plan_is_rejected(self):
        self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test", now=NOW,
                                 request_id="conflicting-request")
        with self.assertRaises(ConflictError):
            self.engine.create_order("tenant_A", "account_A", Plan("annual", "KZT", 500000),
                                     "sandbox-test", now=NOW, request_id="conflicting-request")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)

    def test_same_order_request_key_scoped_to_tenant_and_account(self):
        order1 = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test", now=NOW,
                                          request_id="same-key")
        order2 = self.engine.create_order("tenant_B", "account_A", PLAN, "sandbox-test", now=NOW,
                                          request_id="same-key")
        order3 = self.engine.create_order("tenant_A", "account_B", PLAN, "sandbox-test", now=NOW,
                                          request_id="same-key")
        self.assertEqual(len({order1, order2, order3}), 3)

    def test_order_retry_survives_database_restart(self):
        order = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                         now=NOW, request_id="persistent-key")
        new_engine = BillingEngine(self.path, {"sandbox-test": TestHmacAdapter(SECRET)},
                                   allow_test_adapters=True)
        self.assertEqual(new_engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                                  now=NOW + 100, request_id="persistent-key"), order)

    def test_concurrent_same_order_key_creates_one_order(self):
        barrier = threading.Barrier(8)
        results = []
        errors = []
        def worker():
            try:
                barrier.wait(timeout=5)
                results.append(self.engine.create_order("tenant_A", "account_A", PLAN,
                                                        "sandbox-test", now=NOW,
                                                        request_id="concurrent-order"))
            except Exception as exc:
                errors.append(exc)
        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=8)
        self.assertFalse(errors, errors)
        self.assertEqual(len(results), 8)
        self.assertEqual(len(set(results)), 1)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)

    def test_event_insert_failure_rolls_back_payment_and_allows_retry(self):
        # A transaction row is written before the event ledger insert.
        # If the latter fails, the whole payment must roll back atomically.
        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TRIGGER reject_event BEFORE INSERT ON events "
                "BEGIN SELECT RAISE(ABORT, 'injected event failure'); END"
            )
        with self.assertRaisesRegex(BillingError, "^billing storage unavailable$") as caught:
            self.send()
        self.assertIsNone(caught.exception.__cause__)
        self.assertEqual(self.snapshot().revision, 0)
        self.assertFalse(self.snapshot().eligible)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
            db.execute("DROP TRIGGER reject_event")
        self.assertTrue(self.send().changed)
        self.assertEqual(self.snapshot().revision, 1)
        self.assertTrue(self.snapshot().eligible)

    def test_order_request_insert_failure_rolls_back(self):
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TRIGGER reject_request BEFORE INSERT ON order_requests "
                       "BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        with self.assertRaisesRegex(BillingError, "^billing storage unavailable$") as caught:
            self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                     now=NOW, request_id="fault-injection")
        self.assertIsNone(caught.exception.__cause__)
        with sqlite3.connect(self.path) as db:
            db.execute("DROP TRIGGER reject_request")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 1)
        self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                 now=NOW, request_id="fault-injection")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 2)

    def test_order_request_invalid_or_missing_key_is_denied(self):
        for bad in ("", "with spaces", "A" * 129, None):
            with self.subTest(key=bad):
                with self.assertRaises(SecurityError):
                    self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test",
                                             now=NOW, request_id=bad)

    def test_restart_preserves_ledger(self):
        self.send()
        restarted = BillingEngine(self.path, {"sandbox-test":TestHmacAdapter(SECRET)}, allow_test_adapters=True)
        self.assertTrue(restarted.snapshot("tenant_A", "account_A", self.order, now=NOW).eligible)
        self.assertTrue(restarted.accept_webhook("sandbox-test", self._payload(), self._headers(), now=NOW).duplicate_event)

    def _payload(self):
        return json.dumps(dict(event_id="evt1", order_id=self.order, transaction_id="txn1", kind="paid",
                               occurred_at=NOW, period_end=NOW+2592000, amount_minor=179000, currency="KZT"),
                          sort_keys=True, separators=(",", ":")).encode()

    def _headers(self):
        body = self._payload()
        return {"X-Test-Timestamp":str(NOW), "X-Test-Signature":hmac.new(SECRET, str(NOW).encode()+b"."+body, hashlib.sha256).hexdigest()}


if __name__ == "__main__":
    unittest.main()
