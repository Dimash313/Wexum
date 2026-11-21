"""Isolated, durable subscription accounting; deliberately no payment execution."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
import sqlite3
from typing import Iterator, Mapping, Protocol


class BillingError(ValueError):
    """A rejected billing request without exposing provider payloads."""


class SecurityError(BillingError):
    """Untrusted, invalid, or mismatched authority input."""


class ConflictError(BillingError):
    """A receipt/event identifier attempted to change its meaning."""


class NotFoundError(BillingError):
    """Missing order or order outside the authenticated tenant/account."""


_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_REF = re.compile(r"[a-zA-Z0-9_.-]{1,128}\Z")
_KINDS = frozenset({"paid", "renewed", "refunded", "chargeback", "cancelled", "resumed", "payment_failed"})
_PAYMENT_KINDS = frozenset({"paid", "renewed"})
_REFUND_KINDS = frozenset({"refunded", "chargeback"})
_FIELDS = frozenset({"event_id", "order_id", "transaction_id", "kind", "occurred_at", "period_end", "currency", "amount_minor"})


def _identifier(value: object, pattern: re.Pattern[str] = _ID) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise SecurityError("invalid opaque identifier")
    return value


def _int(value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > 10**12:
        raise SecurityError("invalid integer field")
    return value


@dataclass(frozen=True)
class Plan:
    code: str
    currency: str
    amount_minor: int

    def __post_init__(self) -> None:
        _identifier(self.code)
        if not isinstance(self.currency, str) or not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise SecurityError("invalid ISO currency code")
        _int(self.amount_minor, minimum=1)


@dataclass(frozen=True)
class VerifiedEvent:
    provider: str
    event_id: str
    order_id: str
    transaction_id: str
    kind: str
    occurred_at: int
    period_end: int | None
    currency: str
    amount_minor: int


@dataclass(frozen=True)
class Snapshot:
    order_id: str
    tenant_id: str
    account_id: str
    plan_code: str
    state: str
    access_until: int | None
    eligible: bool
    revision: int


@dataclass(frozen=True)
class WebhookResult:
    duplicate_event: bool
    changed: bool


class ProviderAdapter(Protocol):
    name: str
    test_only: bool

    def verify(self, body: bytes, headers: Mapping[str, str], received_at: int) -> VerifiedEvent: ...


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SecurityError("duplicate JSON key")
        result[key] = value
    return result


class TestHmacAdapter:
    """TEST FIXTURE ONLY. Not a payment gateway or production webhook protocol."""

    name = "sandbox-test"
    test_only = True

    def __init__(self, secret: bytes) -> None:
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise SecurityError("test secret must be at least 32 bytes")
        self._secret = secret

    def verify(self, body: bytes, headers: Mapping[str, str], received_at: int) -> VerifiedEvent:
        if not isinstance(body, bytes) or len(body) > 16_384:
            raise SecurityError("invalid webhook size")
        received_at = _int(received_at)
        if not isinstance(headers, Mapping):
            raise SecurityError("invalid test signature headers")
        if len(headers) > 32:
            raise SecurityError("invalid test signature headers")
        normalized: dict[str, str] = {}
        for key, value in headers.items():
            if (not isinstance(key, str) or not isinstance(value, str)
                    or len(key) > 128 or len(value) > 256
                    or not key.isascii()):
                raise SecurityError("invalid test signature headers")
            folded = key.lower()
            if folded in normalized:
                raise SecurityError("ambiguous test signature headers")
            normalized[folded] = value
        timestamp = normalized.get("x-test-timestamp", "")
        signature = normalized.get("x-test-signature", "")
        if not re.fullmatch(r"[0-9]{1,12}", timestamp) or not re.fullmatch(r"[0-9a-f]{64}", signature):
            raise SecurityError("missing or invalid test signature")
        if abs(received_at - int(timestamp)) > 300:
            raise SecurityError("test signature timestamp expired")
        expected = hmac.new(self._secret, timestamp.encode("ascii") + b"." + body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise SecurityError("invalid test signature")
        try:
            document = json.loads(body, object_pairs_hook=_unique_json_pairs)
        except (ValueError, UnicodeDecodeError, TypeError, RecursionError):
            raise SecurityError("invalid webhook JSON") from None
        if not isinstance(document, dict) or set(document) != _FIELDS:
            raise SecurityError("invalid event fields")
        kind = document["kind"]
        if not isinstance(kind, str) or kind not in _KINDS:
            raise SecurityError("unsupported billing event")
        event_id = _identifier(document["event_id"], _REF)
        order_id = _identifier(document["order_id"])
        transaction_id = document["transaction_id"]
        if kind in _PAYMENT_KINDS | _REFUND_KINDS:
            transaction_id = _identifier(transaction_id, _REF)
        elif transaction_id != "":
            raise SecurityError("unexpected transaction for status event")
        occurred_at = _int(document["occurred_at"])
        if occurred_at > received_at + 300:
            raise SecurityError("future event time")
        period_end = document["period_end"]
        if kind in _PAYMENT_KINDS:
            period_end = _int(period_end, minimum=occurred_at + 1)
        elif period_end is not None:
            raise SecurityError("unexpected period for status/refund event")
        amount = _int(document["amount_minor"], minimum=1)
        currency = document["currency"]
        if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
            raise SecurityError("invalid event currency")
        return VerifiedEvent(self.name, event_id, order_id, transaction_id, kind, occurred_at, period_end, currency, amount)


class BillingEngine:
    """Trusted server-side boundary. Caller must authenticate order creation."""

    def __init__(self, db_path: str | Path, adapters: Mapping[str, ProviderAdapter], *, allow_test_adapters: bool = False) -> None:
        self._path = str(db_path)
        if not adapters:
            raise SecurityError("no approved billing adapters configured")
        for name, adapter in adapters.items():
            _identifier(name, _REF)
            if name != adapter.name or not adapter.test_only or not allow_test_adapters:
                raise SecurityError("live/unauthorized provider adapters are disabled")
        self._adapters = dict(adapters)
        with self._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL, account_id TEXT NOT NULL,
                    plan_code TEXT NOT NULL, provider TEXT NOT NULL,
                    currency TEXT NOT NULL, amount_minor INTEGER NOT NULL,
                    cancel_at_end INTEGER NOT NULL DEFAULT 0,
                    schedule_at INTEGER NOT NULL DEFAULT -1,
                    schedule_event_id TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS order_requests (
                    request_digest TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL UNIQUE REFERENCES orders(order_id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    provider TEXT NOT NULL, event_id TEXT NOT NULL,
                    order_id TEXT NOT NULL REFERENCES orders(order_id),
                    digest TEXT NOT NULL,
                    PRIMARY KEY (provider, event_id)
                );
                CREATE TABLE IF NOT EXISTS transactions (
                    provider TEXT NOT NULL, transaction_id TEXT NOT NULL,
                    order_id TEXT NOT NULL REFERENCES orders(order_id),
                    period_end INTEGER, refunded INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (provider, transaction_id)
                );
                CREATE INDEX IF NOT EXISTS transactions_order_idx ON transactions(order_id);
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        try:
            db = sqlite3.connect(self._path, timeout=5, isolation_level=None)
        except sqlite3.Error:
            raise BillingError("billing storage unavailable") from None
        db.row_factory = sqlite3.Row
        try:
            try:
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA busy_timeout=5000")
                yield db
            except sqlite3.Error:
                raise BillingError("billing storage unavailable") from None
        finally:
            db.close()

    def create_order(self, tenant_id: str, account_id: str, plan: Plan, provider: str,
                     *, now: int, request_id: str) -> str:
        """A trusted, authorized server must supply a stable checkout request ID.

        Repeating the same tenant/account/request ID returns one persisted order;
        changing its plan, price or provider is rejected, even after restart.
        """
        _identifier(tenant_id)
        _identifier(account_id)
        _identifier(request_id, _REF)
        _int(now)
        if not isinstance(plan, Plan) or not isinstance(provider, str) or provider not in self._adapters:
            raise SecurityError("unknown plan or provider")
        request_digest = hashlib.sha256(
            json.dumps([tenant_id, account_id, request_id], separators=(",", ":")).encode("ascii")
        ).hexdigest()
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                previous = db.execute("""
                    SELECT orders.* FROM order_requests
                    JOIN orders ON orders.order_id = order_requests.order_id
                    WHERE order_requests.request_digest=?
                """, (request_digest,)).fetchone()
                if previous is not None:
                    if (previous["tenant_id"] != tenant_id or previous["account_id"] != account_id
                            or previous["plan_code"] != plan.code or previous["provider"] != provider
                            or previous["currency"] != plan.currency or previous["amount_minor"] != plan.amount_minor):
                        raise ConflictError("checkout request reused with different order terms")
                    db.commit()
                    return previous["order_id"]
                order_id = secrets.token_hex(16)
                db.execute("INSERT INTO orders(order_id, tenant_id, account_id, plan_code, provider, currency, amount_minor, created_at) VALUES(?,?,?,?,?,?,?,?)",
                           (order_id, tenant_id, account_id, plan.code, provider, plan.currency, plan.amount_minor, now))
                db.execute("INSERT INTO order_requests(request_digest, order_id) VALUES(?,?)",
                           (request_digest, order_id))
                db.commit()
                return order_id
            except BaseException:
                db.rollback()
                raise

    def accept_webhook(self, provider: str, body: bytes, headers: Mapping[str, str], *, now: int) -> WebhookResult:
        _int(now)
        if not isinstance(provider, str):
            raise SecurityError("unknown provider")
        adapter = self._adapters.get(provider)
        if adapter is None:
            raise SecurityError("unknown provider")
        event = adapter.verify(body, headers, now)
        if event.provider != provider:
            raise SecurityError("provider identity mismatch")
        digest = hashlib.sha256(body).hexdigest()  # Never store raw webhook payloads.
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                result = self._apply(db, event, digest)
                db.commit()
                return result
            except BaseException:
                db.rollback()
                raise

    @staticmethod
    def _apply(db: sqlite3.Connection, event: VerifiedEvent, digest: str) -> WebhookResult:
        prior = db.execute("SELECT digest, order_id FROM events WHERE provider=? AND event_id=?",
                           (event.provider, event.event_id)).fetchone()
        if prior:
            if prior["digest"] != digest or prior["order_id"] != event.order_id:
                raise ConflictError("event identifier collision")
            return WebhookResult(duplicate_event=True, changed=False)
        order = db.execute("SELECT * FROM orders WHERE order_id=?", (event.order_id,)).fetchone()
        if order is None or order["provider"] != event.provider:
            raise SecurityError("unknown provider order binding")
        if event.currency != order["currency"] or event.amount_minor != order["amount_minor"]:
            raise SecurityError("price/currency does not match server order")

        changed = False
        if event.kind in _PAYMENT_KINDS | _REFUND_KINDS:
            txn = db.execute("SELECT * FROM transactions WHERE provider=? AND transaction_id=?",
                             (event.provider, event.transaction_id)).fetchone()
            if txn and txn["order_id"] != event.order_id:
                raise ConflictError("transaction already belongs to another order")
            if event.kind in _PAYMENT_KINDS:
                if txn is None:
                    db.execute("INSERT INTO transactions(provider, transaction_id, order_id, period_end) VALUES(?,?,?,?)",
                               (event.provider, event.transaction_id, event.order_id, event.period_end))
                    changed = True
                elif txn["period_end"] is None:
                    db.execute("UPDATE transactions SET period_end=? WHERE provider=? AND transaction_id=?",
                               (event.period_end, event.provider, event.transaction_id))
                    changed = True  # A previously refunded transaction stays refunded.
                elif txn["period_end"] != event.period_end:
                    raise ConflictError("transaction period cannot be rewritten")
            elif txn is None:
                # Refund arriving before purchase: tombstone prevents later reactivation.
                db.execute("INSERT INTO transactions(provider, transaction_id, order_id, refunded) VALUES(?,?,?,1)",
                           (event.provider, event.transaction_id, event.order_id))
                changed = True
            elif not txn["refunded"]:
                db.execute("UPDATE transactions SET refunded=1 WHERE provider=? AND transaction_id=?",
                           (event.provider, event.transaction_id))
                changed = True
        elif event.kind in {"cancelled", "resumed"}:
            if (event.occurred_at, event.event_id) > (order["schedule_at"], order["schedule_event_id"]):
                new_value = int(event.kind == "cancelled")
                changed = new_value != order["cancel_at_end"]
                db.execute("UPDATE orders SET cancel_at_end=?, schedule_at=?, schedule_event_id=? WHERE order_id=?",
                           (new_value, event.occurred_at, event.event_id, event.order_id))
        # payment_failed is recorded, but must never erase a paid period.
        db.execute("INSERT INTO events(provider, event_id, order_id, digest) VALUES(?,?,?,?)",
                   (event.provider, event.event_id, event.order_id, digest))
        db.execute("UPDATE orders SET revision=revision+1 WHERE order_id=?", (event.order_id,))
        return WebhookResult(duplicate_event=False, changed=changed)

    def snapshot(self, tenant_id: str, account_id: str, order_id: str, *, now: int) -> Snapshot:
        """Server-only projection; NOT a signed grant or client-facing authority."""
        _identifier(tenant_id)
        _identifier(account_id)
        _identifier(order_id)
        _int(now)
        with self._connection() as db:
            db.execute("BEGIN")  # Read order, transactions and revision from one snapshot.
            order = db.execute("SELECT * FROM orders WHERE tenant_id=? AND account_id=? AND order_id=?",
                               (tenant_id, account_id, order_id)).fetchone()
            if order is None:
                raise NotFoundError("order not found")
            summary = db.execute("""
                SELECT MAX(CASE WHEN refunded=0 THEN period_end END) AS paid_until,
                       SUM(CASE WHEN period_end IS NOT NULL THEN 1 ELSE 0 END) AS payments,
                       SUM(CASE WHEN refunded=1 THEN 1 ELSE 0 END) AS refunds
                FROM transactions WHERE order_id=?
            """, (order_id,)).fetchone()
            db.execute("COMMIT")
        paid_until = summary["paid_until"]
        eligible = paid_until is not None and paid_until > now
        if eligible:
            state = "cancellation_scheduled" if order["cancel_at_end"] else "active"
        elif summary["refunds"] and paid_until is None:
            state = "revoked"
        elif summary["payments"]:
            state = "expired"
        else:
            state = "pending"
        return Snapshot(order_id, tenant_id, account_id, order["plan_code"], state, paid_until, eligible, order["revision"])
