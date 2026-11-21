"""Negative, tenant-bound and failure-path tests for the non-issuing precheck."""

import asyncio
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from wexum_vpn_entitlements import (
    AccountState, AuthenticatedActor, DeviceState, GrantPrecheck,
    GrantPrecheckDenied, GrantPrecheckUnavailable, SubscriptionState,
)

NOW = datetime(2026, 11, 21, 8, tzinfo=timezone.utc)


class Accounts:
    def __init__(self, state):
        self.state = state
        self.calls = 0
        self.delay = 0
        self.error = None

    async def read_account(self, tenant_id, subject_id):
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.state


class Subscriptions:
    def __init__(self, state):
        self.state = state
        self.calls = 0
        self.delay = 0
        self.error = None

    async def read_subscription(self, tenant_id, subject_id):
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.state


class Devices:
    def __init__(self, state):
        self.state = state
        self.calls = 0
        self.delay = 0
        self.error = None

    async def read_device(self, tenant_id, subject_id, device_id):
        self.calls += 1
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.state


class GrantPrecheckTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.actor = AuthenticatedActor("t-A", "user-A", "issuer", "vpn-control", frozenset({"vpn:grant:create"}), NOW + timedelta(minutes=5))
        self.accounts = Accounts(AccountState("t-A", "user-A", True, NOW))
        self.subscriptions = Subscriptions(SubscriptionState("t-A", "user-A", True, NOW, NOW + timedelta(minutes=8), frozenset({"vpn:connect"})))
        self.devices = Devices(DeviceState("t-A", "user-A", "dev-A", True, NOW, NOW + timedelta(minutes=7)))
        self.clock = lambda: NOW
        self.svc = self.service()

    def service(self, **kwargs):
        options = dict(accounts=self.accounts, subscriptions=self.subscriptions,
                       devices=self.devices, expected_issuer="issuer", expected_audience="vpn-control",
                       clock=self.clock)
        options.update(kwargs)
        return GrantPrecheck(**options)

    async def _deny(self, *, actor=None, device_id="dev-A", scope="vpn:connect"):
        with self.assertRaises(GrantPrecheckDenied):
            await self.svc.check(actor=self.actor if actor is None else actor, device_id=device_id, scope=scope)

    async def test_valid_candidate_is_bounded_and_not_a_permit(self):
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=120))
        self.assertEqual(candidate.device_id, "dev-A")
        self.assertFalse(hasattr(candidate, "signature"))
        self.assertFalse(hasattr(self.svc, "mint"))

    async def test_identity_mismatch_denied_before_calling_adapters(self):
        await self._deny(actor=replace(self.actor, issuer="attacker"))
        await self._deny(actor=replace(self.actor, audience="node"))
        await self._deny(actor=replace(self.actor, scopes=frozenset()))
        self.assertEqual(self.accounts.calls, 0)

    async def test_invalid_identity_or_device_ids_denied(self):
        for bad in (0, " ", "\n", "bad/id", "a" * 129):
            await self._deny(actor=replace(self.actor, tenant_id=bad))
            await self._deny(device_id=bad)

    async def test_expired_identity_denied(self):
        await self._deny(actor=replace(self.actor, expires_at=NOW))

    async def test_cross_tenant_and_subject_snapshots_denied(self):
        for adapter in (self.accounts, self.subscriptions, self.devices):
            original = adapter.state
            for field, other in (("tenant_id", "t-B"), ("subject_id", "user-B")):
                adapter.state = replace(original, **{field: other})
                await self._deny()
            adapter.state = original

    async def test_other_device_denied(self):
        await self._deny(device_id="dev-B")

    async def test_deleted_account_denied(self):
        self.accounts.state = replace(self.accounts.state, active=False)
        await self._deny()

    async def test_revoked_device_denied(self):
        self.devices.state = replace(self.devices.state, active=False)
        await self._deny()

    async def test_inactive_subscription_denied(self):
        self.subscriptions.state = replace(self.subscriptions.state, active=False)
        await self._deny()

    async def test_expired_subscription_denied(self):
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=NOW)
        await self._deny()

    async def test_expired_device_denied(self):
        self.devices.state = replace(self.devices.state, expires_at=NOW)
        await self._deny()

    async def test_stale_account_and_entitlement_denied(self):
        self.accounts.state = replace(self.accounts.state, checked_at=NOW - timedelta(seconds=11))
        await self._deny()
        self.accounts.state = replace(self.accounts.state, checked_at=NOW)
        self.subscriptions.state = replace(self.subscriptions.state, checked_at=NOW - timedelta(seconds=11))
        await self._deny()

    async def test_stale_device_snapshot_denied(self):
        self.devices.state = replace(self.devices.state, checked_at=NOW - timedelta(seconds=11))
        await self._deny()

    async def test_clock_skew_over_budget_denied(self):
        self.subscriptions.state = replace(self.subscriptions.state, checked_at=NOW + timedelta(seconds=6))
        await self._deny()
        self.subscriptions.state = replace(self.subscriptions.state, checked_at=NOW + timedelta(seconds=5))
        await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_scope_denials(self):
        await self._deny(scope="vpn:admin")
        await self._deny(scope="vpn:connect:unexpected")
        await self._deny(scope="unacceptable scope")
        self.subscriptions.state = replace(self.subscriptions.state, allowed_scopes=frozenset())
        await self._deny()

    async def test_ttl_capped_by_each_server_expiry(self):
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=NOW + timedelta(seconds=18))
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=18))
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=NOW + timedelta(minutes=8))
        self.devices.state = replace(self.devices.state, expires_at=NOW + timedelta(seconds=7))
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=7))

    async def test_grant_does_not_outlive_actor(self):
        actor = replace(self.actor, expires_at=NOW + timedelta(seconds=3))
        candidate = await self.svc.check(actor=actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=3))

    async def test_authority_outage_denies_new_grants(self):
        for adapter in (self.accounts, self.subscriptions, self.devices):
            adapter.error = ConnectionError("simulated outage")
            with self.assertRaises(GrantPrecheckUnavailable):
                await self.svc.check(actor=self.actor, device_id="dev-A")
            adapter.error = None

    async def test_timeout_is_bounded(self):
        self.subscriptions.delay = 0.1
        self.svc = self.service(timeout_seconds=0.01)
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_actor_expiring_during_lookup_denied(self):
        self.accounts.delay = 0.001
        self.clock = lambda: NOW + timedelta(minutes=5)
        self.svc = self.service()
        await self._deny()

    async def test_malformed_snapshots_fail_closed(self):
        self.accounts.state = replace(self.accounts.state, active=1)
        await self._deny()
        self.accounts.state = AccountState("t-A", "user-A", True, NOW)
        self.subscriptions.state = replace(self.subscriptions.state, allowed_scopes={"vpn:connect"})
        await self._deny()

    async def test_bad_authority_result_denied(self):
        self.devices.state = {"device_id": "dev-A", "active": True}
        await self._deny()

    async def test_timezone_naive_timestamp_denied(self):
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=NOW.replace(tzinfo=None))
        await self._deny()

    async def test_trusted_clock_unavailable(self):
        self.clock = lambda: None
        self.svc = self.service()
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_invalid_configuration_rejected(self):
        for options in (dict(timeout_seconds=0), dict(max_grant_seconds=3600),
                        dict(max_clock_skew_seconds=-1), dict(max_state_age_seconds=True)):
            with self.assertRaises(ValueError):
                self.service(**options)

    async def test_server_revalidation_after_revocation(self):
        await self.svc.check(actor=self.actor, device_id="dev-A")
        self.devices.state = replace(self.devices.state, active=False)
        await self._deny()

    async def test_multiple_subjects_do_not_share_grants(self):
        await self._deny(actor=replace(self.actor, subject_id="user-B"))


if __name__ == "__main__":
    unittest.main()
