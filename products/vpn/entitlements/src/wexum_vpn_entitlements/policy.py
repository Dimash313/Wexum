"""Fail-closed server-side preflight for VPN grants; does NOT issue permits.

Only trusted backend adapters may supply actor and authority snapshots. A successful
result is not a VPN access credential; a separate approved cryptographic issuer,
node verifier, replay protection and revocation delivery remain required.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol

_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z")
_SCOPE = re.compile(r"[a-z][a-z0-9:_-]{1,63}\Z")


class GrantPrecheckDenied(Exception):
    """Access may not be granted; deliberately lacks sensitive decision detail."""


class GrantPrecheckUnavailable(Exception):
    """Trusted state could not be established within the allowed time budget."""


@dataclass(frozen=True, slots=True)
class AuthenticatedActor:
    """MUST be built from a verified Identity session by a trusted adapter."""

    tenant_id: str = field(repr=False)
    subject_id: str = field(repr=False)
    issuer: str
    audience: str
    scopes: frozenset[str]
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AccountState:
    """Result of an authoritative, server-to-server account lookup."""

    tenant_id: str = field(repr=False)
    subject_id: str = field(repr=False)
    active: bool
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class SubscriptionState:
    """Result of an authoritative, server-to-server billing entitlement lookup."""

    tenant_id: str = field(repr=False)
    subject_id: str = field(repr=False)
    active: bool
    checked_at: datetime
    expires_at: datetime
    allowed_scopes: frozenset[str]


@dataclass(frozen=True, slots=True)
class DeviceState:
    """Result of an authoritative device registry lookup, not client metadata."""

    tenant_id: str = field(repr=False)
    subject_id: str = field(repr=False)
    device_id: str = field(repr=False)
    active: bool
    checked_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class GrantCandidate:
    """Preflight result ONLY. Not signed, transferable or accepted by VPN nodes."""

    tenant_id: str = field(repr=False)
    subject_id: str = field(repr=False)
    device_id: str = field(repr=False)
    scope: str
    expires_at: datetime


class AccountAuthority(Protocol):
    async def read_account(self, tenant_id: str, subject_id: str) -> AccountState: ...


class SubscriptionAuthority(Protocol):
    async def read_subscription(self, tenant_id: str, subject_id: str) -> SubscriptionState: ...


class DeviceAuthority(Protocol):
    async def read_device(self, tenant_id: str, subject_id: str, device_id: str) -> DeviceState: ...


def _id(value: object) -> bool:
    return type(value) is str and _IDENTIFIER.fullmatch(value) is not None


def _scope(value: object) -> bool:
    return type(value) is str and _SCOPE.fullmatch(value) is not None


def _instant(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is not None and value.utcoffset() is not None


def _fresh(checked_at: datetime, now: datetime, max_age: timedelta, skew: timedelta) -> bool:
    return _instant(checked_at) and now - max_age <= checked_at <= now + skew


class GrantPrecheck:
    """Server-only check requiring live authoritative state; never mints a grant.

    The calling service must authenticate its adapters. Do not expose this as a
    public API or accept AccountState/SubscriptionState/DeviceState from clients.
    New grants FAIL CLOSED during control-plane or authority outages.
    """

    def __init__(
        self,
        *,
        accounts: AccountAuthority,
        subscriptions: SubscriptionAuthority,
        devices: DeviceAuthority,
        expected_issuer: str,
        expected_audience: str,
        timeout_seconds: float = 2.0,
        max_state_age_seconds: int = 10,
        max_clock_skew_seconds: int = 5,
        max_grant_seconds: int = 120,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if (
            not _id(expected_audience)
            or type(expected_issuer) is not str
            or not expected_issuer.strip()
            or len(expected_issuer) > 256
            or type(timeout_seconds) not in (int, float)
            or not 0 < timeout_seconds <= 30
            or type(max_state_age_seconds) is not int
            or not 1 <= max_state_age_seconds <= 60
            or type(max_clock_skew_seconds) is not int
            or not 0 <= max_clock_skew_seconds <= 30
            or type(max_grant_seconds) is not int
            or not 1 <= max_grant_seconds <= 300
            or not callable(clock)
        ):
            raise ValueError("invalid server-owned grant policy configuration")
        self._accounts = accounts
        self._subscriptions = subscriptions
        self._devices = devices
        self._issuer = expected_issuer
        self._audience = expected_audience
        self._timeout = timeout_seconds
        self._age = timedelta(seconds=max_state_age_seconds)
        self._skew = timedelta(seconds=max_clock_skew_seconds)
        self._ttl = timedelta(seconds=max_grant_seconds)
        self._clock = clock

    async def check(
        self, *, actor: AuthenticatedActor, device_id: str, scope: str = "vpn:connect"
    ) -> GrantCandidate:
        """Return a candidate ONLY after authenticated, tenant-bound live checks."""
        if (
            type(actor) is not AuthenticatedActor
            or not _id(actor.tenant_id)
            or not _id(actor.subject_id)
            or not _id(device_id)
            or not _scope(scope)
            or actor.issuer != self._issuer
            or actor.audience != self._audience
            or type(actor.scopes) is not frozenset
            or any(not _scope(s) for s in actor.scopes)
            or "vpn:grant:create" not in actor.scopes
            or not _instant(actor.expires_at)
        ):
            raise GrantPrecheckDenied("VPN access denied")

        try:
            account, subscription, device = await asyncio.wait_for(
                asyncio.gather(
                    self._accounts.read_account(actor.tenant_id, actor.subject_id),
                    self._subscriptions.read_subscription(actor.tenant_id, actor.subject_id),
                    self._devices.read_device(actor.tenant_id, actor.subject_id, device_id),
                ),
                timeout=self._timeout,
            )
            now = self._clock()
        except Exception as exc:
            raise GrantPrecheckUnavailable("authoritative VPN state unavailable") from exc

        if not _instant(now):
            raise GrantPrecheckUnavailable("trusted clock unavailable")
        tenant, subject = actor.tenant_id, actor.subject_id
        if (
            type(account) is not AccountState
            or type(subscription) is not SubscriptionState
            or type(device) is not DeviceState
            or type(account.active) is not bool
            or type(subscription.active) is not bool
            or type(device.active) is not bool
            or not account.active
            or not subscription.active
            or not device.active
            or any(
                not _id(value)
                for value in (
                    account.tenant_id, account.subject_id,
                    subscription.tenant_id, subscription.subject_id,
                    device.tenant_id, device.subject_id, device.device_id,
                )
            )
            or any(state.tenant_id != tenant or state.subject_id != subject for state in (account, subscription, device))
            or device.device_id != device_id
            or not _fresh(account.checked_at, now, self._age, self._skew)
            or not _fresh(subscription.checked_at, now, self._age, self._skew)
            or not _fresh(device.checked_at, now, self._age, self._skew)
            or type(subscription.allowed_scopes) is not frozenset
            or any(not _scope(s) for s in subscription.allowed_scopes)
            or scope not in subscription.allowed_scopes
            or not _instant(subscription.expires_at)
            or not _instant(device.expires_at)
            or actor.expires_at <= now
            or subscription.expires_at <= now
            or device.expires_at <= now
        ):
            raise GrantPrecheckDenied("VPN access denied")

        expires_at = min(actor.expires_at, subscription.expires_at, device.expires_at, now + self._ttl)
        return GrantCandidate(tenant, subject, device_id, scope, expires_at)
