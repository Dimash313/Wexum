"""Fail-closed device control service behind a future verified auth adapter.

No HTTP server is exposed. Never create AuthenticatedActor from client-supplied JSON.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from .store import (Device, SQLiteDeviceStore, StoreBusy, StoreConflict,
                    StoreLimit, utc_stamp)

_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$')
_REQUEST_KEY = re.compile(r'^[a-zA-Z0-9_-]{16,128}$')
_PLATFORMS = frozenset({'android', 'ios', 'desktop'})


class AccessDenied(Exception):
    """Authentication or authorization cannot be established."""


class EnrollmentUnavailable(Exception):
    """An authoritative subscription decision could not be obtained."""


class DeviceLimitReached(Exception):
    """Active device allowance has been exhausted."""


class IdempotencyConflict(Exception):
    """A request key was reused for a different platform."""


class DeviceNotFound(Exception):
    """Missing or inaccessible device; never distinguish cross-tenant existence."""


class InvalidRequest(Exception):
    """Request contains invalid public fields."""


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    """Trusted edge adapter output, NOT a remotely constructible credential.

    The future adapter must validate actual signature, issuer, audience and
    revocation policy before constructing this object.
    """
    tenant_id: str
    subject_id: str
    issuer: str
    audience: str
    issued_at: datetime
    expires_at: datetime
    scopes: frozenset[str]


@dataclass(frozen=True, slots=True)
class EntitlementDecision:
    """Authoritative billing/entitlement adapter output, not client input."""
    tenant_id: str
    subject_id: str
    active: bool
    expires_at: datetime
    device_limit: int


class DeviceControlService:
    def __init__(self, *, store: SQLiteDeviceStore,
                 check_entitlement: Callable[[str, str], Awaitable[EntitlementDecision]],
                 trusted_issuer: str, expected_audience: str,
                 entitlement_timeout: float = 1.5,
                 max_device_lifetime: timedelta = timedelta(days=30),
                 clock: Callable[[], datetime] | None = None):
        if not callable(check_entitlement) or not trusted_issuer or not expected_audience:
            raise ValueError('trusted issuer, audience and entitlement verifier are required')
        if not (0.05 <= entitlement_timeout <= 10.0):
            raise ValueError('invalid entitlement timeout')
        if not (timedelta(minutes=1) <= max_device_lifetime <= timedelta(days=30)):
            raise ValueError('invalid device lifetime')
        self._store = store
        self._check = check_entitlement
        self._issuer = trusted_issuer
        self._audience = expected_audience
        self._timeout = entitlement_timeout
        self._lifetime = max_device_lifetime
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self) -> datetime:
        now = self._clock()
        utc_stamp(now)
        return now.astimezone(timezone.utc)

    def _authorize(self, actor: AuthenticatedActor, required_scope: str, now: datetime) -> None:
        if not isinstance(actor, AuthenticatedActor):
            raise AccessDenied('access denied')
        try:
            valid = (all(isinstance(x, str) and _ID.fullmatch(x)
                         for x in (actor.tenant_id, actor.subject_id))
                     and actor.issuer == self._issuer
                     and actor.audience == self._audience
                     and isinstance(actor.scopes, frozenset)
                     and required_scope in actor.scopes
                     and utc_stamp(actor.issued_at) <= utc_stamp(now)
                     and utc_stamp(now) < utc_stamp(actor.expires_at))
        except (TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            raise AccessDenied('access denied')

    async def enroll(self, *, actor: AuthenticatedActor, platform: str,
                     idempotency_key: str) -> Device:
        now = self._now()
        self._authorize(actor, 'vpn:device:write', now)
        if not isinstance(platform, str) or platform not in _PLATFORMS or not isinstance(idempotency_key, str) or not _REQUEST_KEY.fullmatch(idempotency_key):
            raise InvalidRequest('invalid device registration parameters')
        try:
            # Timeout is enforceable only for cooperative async adapters.
            decision = await asyncio.wait_for(
                self._check(actor.tenant_id, actor.subject_id), timeout=self._timeout)
        except (Exception, asyncio.CancelledError) as error:
            if isinstance(error, asyncio.CancelledError):
                raise
            raise EnrollmentUnavailable('entitlement check unavailable') from error
        now = self._now()
        self._authorize(actor, 'vpn:device:write', now)  # token may expire while waiting
        try:
            valid = (isinstance(decision, EntitlementDecision)
                     and decision.tenant_id == actor.tenant_id
                     and decision.subject_id == actor.subject_id
                     and decision.active is True
                     and type(decision.device_limit) is int
                     and 1 <= decision.device_limit <= 200
                     and utc_stamp(now) < utc_stamp(decision.expires_at))
        except (TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            raise AccessDenied('entitlement inactive or inconsistent')
        expiry = min(now + self._lifetime, decision.expires_at)
        if expiry <= now:
            raise AccessDenied('entitlement expired')
        try:
            return self._store.enroll(
                tenant_id=actor.tenant_id, subject_id=actor.subject_id,
                platform=platform, request_key=idempotency_key,
                now=now, expires_at=expiry, max_devices=decision.device_limit)
        except StoreLimit as error:
            raise DeviceLimitReached('device limit reached') from error
        except StoreConflict as error:
            raise IdempotencyConflict('idempotency key conflict') from error
        except StoreBusy as error:
            raise EnrollmentUnavailable('device store unavailable') from error

    def list_devices(self, *, actor: AuthenticatedActor) -> list[Device]:
        now = self._now()
        self._authorize(actor, 'vpn:device:read', now)
        try:
            return self._store.list_for_owner(tenant_id=actor.tenant_id, subject_id=actor.subject_id)
        except StoreBusy as error:
            raise EnrollmentUnavailable('device store unavailable') from error

    def revoke_device(self, *, actor: AuthenticatedActor, device_id: str) -> Device:
        now = self._now()
        self._authorize(actor, 'vpn:device:write', now)
        if not isinstance(device_id, str) or len(device_id) > 64:
            raise InvalidRequest('invalid device identifier')
        try:
            record = self._store.revoke(tenant_id=actor.tenant_id, subject_id=actor.subject_id,
                                        device_id=device_id, now=now)
        except StoreBusy as error:
            raise EnrollmentUnavailable('device store unavailable') from error
        if record is None:
            raise DeviceNotFound('device not found')
        return record
