"""Short-lived, single-use OAuth/OIDC authorization transactions.

This component neither authenticates a user nor validates OAuth tokens. An outer
OIDC adapter must select trusted provider configuration, exchange the code and
verify the resulting tokens before establishing any authenticated principal.
"""

import base64
import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Callable


class AuthorizationRejected(Exception):
    """A callback cannot be linked to a live authorization transaction."""


class AuthorizationCapacityExceeded(Exception):
    """The bounded pending-transaction budget has been exhausted."""


@dataclass(frozen=True, slots=True)
class AuthorizationStart:
    state: str
    code_challenge: str
    nonce: str
    code_challenge_method: str = "S256"


@dataclass(frozen=True, slots=True)
class ExchangeContext:
    """Server-only parameters for the next token-exchange and ID-token checks."""

    code_verifier: str
    expected_nonce: str


@dataclass(frozen=True, slots=True)
class _Pending:
    binding_digest: bytes
    issuer: str
    client_id: str
    redirect_uri: str
    code_verifier: str
    nonce: str
    expires_at: float


def _require_config(value: str, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 2048:
        raise ValueError(f"invalid {name}")
    return value


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


class AuthorizationTransactions:
    """Process-local fail-closed state store, with atomic single-use consumption.

    Sessions, issuer, client ID and redirect URI MUST come from trusted server
    context/configuration, never from callback query fields. This is an interim
    single-process building block, not a distributed session implementation.
    """

    def __init__(
        self,
        *,
        ttl_seconds: int = 300,
        max_pending: int = 1024,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 900:
            raise ValueError("ttl_seconds must be between 1 and 900")
        if type(max_pending) is not int or max_pending < 1:
            raise ValueError("max_pending must be positive")
        self._ttl_seconds = ttl_seconds
        self._max_pending = max_pending
        self._clock = clock
        self._pending: dict[bytes, _Pending] = {}
        self._lock = threading.Lock()

    def _expire(self, now: float) -> None:
        for key, transaction in tuple(self._pending.items()):
            if now >= transaction.expires_at:
                del self._pending[key]

    def begin(
        self,
        *,
        browser_session: str,
        issuer: str,
        client_id: str,
        redirect_uri: str,
    ) -> AuthorizationStart:
        _require_config(browser_session, "browser_session")
        _require_config(issuer, "issuer")
        _require_config(client_id, "client_id")
        _require_config(redirect_uri, "redirect_uri")

        with self._lock:
            now = self._clock()
            self._expire(now)
            if len(self._pending) >= self._max_pending:
                raise AuthorizationCapacityExceeded("pending authorization capacity reached")

            state = secrets.token_urlsafe(32)
            state_key = _digest(state)
            if state_key in self._pending:
                raise AuthorizationCapacityExceeded("cannot allocate unique authorization state")
            verifier = secrets.token_urlsafe(64)
            nonce = secrets.token_urlsafe(32)
            challenge = base64.urlsafe_b64encode(_digest(verifier)).rstrip(b"=").decode("ascii")
            self._pending[state_key] = _Pending(
                binding_digest=_digest(browser_session),
                issuer=issuer,
                client_id=client_id,
                redirect_uri=redirect_uri,
                code_verifier=verifier,
                nonce=nonce,
                expires_at=now + self._ttl_seconds,
            )
            return AuthorizationStart(state=state, code_challenge=challenge, nonce=nonce)

    def consume(
        self,
        *,
        state: str,
        browser_session: str,
        issuer: str,
        client_id: str,
        redirect_uri: str,
        response_issuer: str,
    ) -> ExchangeContext:
        """Consume only when browser, configured client and RFC 9207 iss match.

        The result is NOT an authenticated principal. A trusted OIDC adapter
        must still perform token exchange, issuer/audience/signature/time/nonce
        checks and server-side authorization. Any failed exchange must restart
        the login; this transaction cannot be replayed.
        """
        values = (state, browser_session, issuer, client_id, redirect_uri, response_issuer)
        if any(not isinstance(x, str) or not x or x != x.strip() or len(x) > 2048 for x in values):
            raise AuthorizationRejected("invalid or expired authorization transaction")

        with self._lock:
            now = self._clock()
            self._expire(now)
            key = _digest(state)
            pending = self._pending.get(key)
            if pending is None:
                raise AuthorizationRejected("invalid or expired authorization transaction")
            if not (
                hmac.compare_digest(pending.binding_digest, _digest(browser_session))
                and pending.issuer == issuer == response_issuer
                and pending.client_id == client_id
                and pending.redirect_uri == redirect_uri
            ):
                raise AuthorizationRejected("invalid or expired authorization transaction")
            del self._pending[key]
            return ExchangeContext(code_verifier=pending.code_verifier, expected_nonce=pending.nonce)
