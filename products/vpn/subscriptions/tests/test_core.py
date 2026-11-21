import hashlib
import hmac
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from wexum_vpn_billing import (
    BillingEngine, ConflictError, NotFoundError, Plan, SecurityError, TestHmacAdapter,
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
        self.order = self.engine.create_order("tenant_A", "account_A", PLAN, "sandbox-test", now=NOW)

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
        second = self.engine.create_order("tenant_B", "account_B", PLAN, "sandbox-test", now=NOW)
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
