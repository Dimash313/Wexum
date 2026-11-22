"""Negative, tenant-bound and failure-path tests for the non-issuing precheck."""

import asyncio
import traceback
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

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

    async def test_expired_actor_denied_without_authority_io(self):
        await self._deny(actor=replace(self.actor, expires_at=NOW))
        self.assertEqual(self.accounts.calls, 0)
        self.assertEqual(self.subscriptions.calls, 0)
        self.assertEqual(self.devices.calls, 0)

    async def test_clock_failure_denies_without_authority_io(self):
        self.clock = lambda: (_ for _ in ()).throw(RuntimeError("clock failure"))
        self.svc = self.service()
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(self.accounts.calls, 0)

    async def test_authority_failure_cancels_sibling_lookups(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        class BlockedDevice:
            async def read_device(self, tenant_id, subject_id, device_id):
                started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    raise

        async def fail_account(tenant_id, subject_id):
            await started.wait()
            raise OSError("simulated authority failure")

        self.accounts.read_account = fail_account
        self.svc = self.service(devices=BlockedDevice(), timeout_seconds=0.5)
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertTrue(cancelled.is_set(), "sibling lookup must be cancelled before return")

    async def test_authority_self_cancellation_is_unavailable(self):
        async def cancelled_account(tenant_id, subject_id):
            raise asyncio.CancelledError()

        self.accounts.read_account = cancelled_account
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_caller_cancellation_propagates_to_authorities(self):
        started = asyncio.Event()
        cancelled = asyncio.Event()

        class BlockedDevice:
            async def read_device(self, tenant_id, subject_id, device_id):
                started.set()
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    cancelled.set()
                    raise

        self.svc = self.service(devices=BlockedDevice())
        check_task = asyncio.create_task(
            self.svc.check(actor=self.actor, device_id="dev-A")
        )
        await asyncio.wait_for(started.wait(), timeout=0.5)
        check_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await check_task
        self.assertTrue(cancelled.is_set())

    async def test_datetime_min_valid_snapshots_do_not_underflow(self):
        edge = datetime.min.replace(tzinfo=timezone.utc)
        self.actor = replace(self.actor, expires_at=edge + timedelta(minutes=5))
        self.accounts.state = replace(self.accounts.state, checked_at=edge)
        self.subscriptions.state = replace(
            self.subscriptions.state,
            checked_at=edge,
            expires_at=edge + timedelta(minutes=8),
        )
        self.devices.state = replace(
            self.devices.state,
            checked_at=edge,
            expires_at=edge + timedelta(minutes=7),
        )
        self.clock = lambda: edge
        self.svc = self.service()
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, edge + timedelta(seconds=120))

    async def test_datetime_max_expiration_is_capped_without_overflow(self):
        edge = datetime.max.replace(tzinfo=timezone.utc)
        now = edge - timedelta(seconds=1)
        self.actor = replace(self.actor, expires_at=edge)
        self.accounts.state = replace(self.accounts.state, checked_at=now)
        self.subscriptions.state = replace(
            self.subscriptions.state, checked_at=now, expires_at=edge
        )
        self.devices.state = replace(self.devices.state, checked_at=now, expires_at=edge)
        self.clock = lambda: now
        self.svc = self.service()
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, edge)

    async def test_future_snapshot_too_far_is_denied_at_datetime_min(self):
        edge = datetime.min.replace(tzinfo=timezone.utc)
        self.actor = replace(self.actor, expires_at=edge + timedelta(minutes=5))
        self.accounts.state = replace(
            self.accounts.state, checked_at=edge + timedelta(seconds=6)
        )
        self.subscriptions.state = replace(
            self.subscriptions.state, checked_at=edge,
            expires_at=edge + timedelta(minutes=8),
        )
        self.devices.state = replace(
            self.devices.state, checked_at=edge,
            expires_at=edge + timedelta(minutes=7),
        )
        self.clock = lambda: edge
        self.svc = self.service()
        await self._deny()

    async def test_actor_issuer_and_audience_must_be_plain_strings(self):
        class StringImpersonator:
            def __eq__(self, other):
                return True
            def __ne__(self, other):
                return False

        for change in (
            {"issuer": StringImpersonator()},
            {"audience": StringImpersonator()},
        ):
            with self.subTest(change=tuple(change)):
                await self._deny(actor=replace(self.actor, **change))
        self.assertEqual(self.accounts.calls, 0)

    async def test_backward_clock_beyond_budget_fails_closed(self):
        readings = iter((NOW, NOW - timedelta(seconds=6)))
        self.clock = lambda: next(readings)
        self.svc = self.service()
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_small_backward_clock_never_extends_candidate_lifetime(self):
        readings = iter((NOW, NOW - timedelta(seconds=2)))
        self.clock = lambda: next(readings)
        self.svc = self.service()
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=120))

    async def test_upstream_secret_does_not_appear_in_displayed_traceback(self):
        self.accounts.error = RuntimeError("bearer-secret-should-not-appear")
        with self.assertRaises(GrantPrecheckUnavailable) as caught:
            await self.svc.check(actor=self.actor, device_id="dev-A")
        rendered = "".join(traceback.format_exception(caught.exception))
        self.assertNotIn("bearer-secret-should-not-appear", rendered)
        self.assertIn("authoritative VPN state unavailable", rendered)

    async def test_clock_error_does_not_appear_in_displayed_traceback(self):
        def failing_clock():
            raise RuntimeError("private-clock-error-sentinel")
        self.clock = failing_clock
        self.svc = self.service()
        with self.assertRaises(GrantPrecheckUnavailable) as caught:
            await self.svc.check(actor=self.actor, device_id="dev-A")
        rendered = "".join(traceback.format_exception(caught.exception))
        self.assertNotIn("private-clock-error-sentinel", rendered)

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

    async def test_broken_timezone_offsets_fail_closed(self):
        from datetime import tzinfo

        class BrokenTimezone(tzinfo):
            def utcoffset(self, dt):
                raise RuntimeError("untrusted timezone failure")
            def dst(self, dt):
                return None

        broken = NOW.replace(tzinfo=BrokenTimezone())
        await self._deny(actor=replace(self.actor, expires_at=broken))
        self.accounts.state = replace(self.accounts.state, checked_at=broken)
        await self._deny()
        self.accounts.state = replace(self.accounts.state, checked_at=NOW)
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=broken)
        await self._deny()
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=NOW + timedelta(minutes=8))
        self.clock = lambda: broken
        self.svc = self.service()
        with self.assertRaises(GrantPrecheckUnavailable):
            await self.svc.check(actor=self.actor, device_id="dev-A")

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


    async def test_dst_fold_stale_authority_snapshots_denied(self):
        zone = ZoneInfo("America/New_York")
        old = datetime(2026, 11, 1, 1, 0, 0, tzinfo=zone, fold=0)
        current = datetime(2026, 11, 1, 1, 0, 5, tzinfo=zone, fold=1)
        self.clock = lambda: current
        self.actor = replace(self.actor, expires_at=current.astimezone(timezone.utc) + timedelta(minutes=5))
        self.svc = self.service()
        for adapter in (self.accounts, self.subscriptions, self.devices):
            adapter.state = replace(adapter.state, checked_at=current)
        for adapter in (self.accounts, self.subscriptions, self.devices):
            original = adapter.state
            adapter.state = replace(original, checked_at=old)
            with self.subTest(authority=type(adapter).__name__):
                await self._deny()
            adapter.state = original
        # Ensure other snapshots are fresh when the DST-fold snapshot is tested.
        for adapter in (self.accounts, self.subscriptions, self.devices):
            adapter.state = replace(adapter.state, checked_at=current)
        await self.svc.check(actor=self.actor, device_id="dev-A")

    async def test_dst_fold_expired_actor_subscription_and_device_denied(self):
        zone = ZoneInfo("America/New_York")
        expired = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
        current = datetime(2026, 11, 1, 1, 0, 5, tzinfo=zone, fold=1)
        self.clock = lambda: current
        for adapter in (self.accounts, self.subscriptions, self.devices):
            adapter.state = replace(adapter.state, checked_at=current)
        self.svc = self.service()
        valid = current.astimezone(timezone.utc) + timedelta(minutes=5)
        self.actor = replace(self.actor, expires_at=valid)
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=valid)
        self.devices.state = replace(self.devices.state, expires_at=valid)
        await self._deny(actor=replace(self.actor, expires_at=expired))
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=expired)
        await self._deny()
        self.subscriptions.state = replace(self.subscriptions.state, expires_at=valid)
        self.devices.state = replace(self.devices.state, expires_at=expired)
        await self._deny()

    async def test_distinct_timezone_offsets_use_utc_instants(self):
        other = timezone(timedelta(hours=3))
        self.accounts.state = replace(self.accounts.state, checked_at=NOW.astimezone(other))
        self.subscriptions.state = replace(self.subscriptions.state, checked_at=NOW.astimezone(other))
        self.devices.state = replace(self.devices.state, checked_at=NOW.astimezone(other))
        self.actor = replace(self.actor, expires_at=self.actor.expires_at.astimezone(other))
        candidate = await self.svc.check(actor=self.actor, device_id="dev-A")
        self.assertEqual(candidate.expires_at, NOW + timedelta(seconds=120))

if __name__ == "__main__":
    unittest.main()
