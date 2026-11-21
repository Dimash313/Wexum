"""Opt-in contract tests against actual Control Plane source (PR #55 / issue #2).

The entitlement callback is synthetic; the SQLiteDeviceStore and DeviceControlService
must be the real imported implementation. No HTTP, tokens, gateway or tunnel.
"""

import asyncio
import os
import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTROL = ROOT / 'products/vpn/control/src'
CONTROL_SRC = Path(os.environ.get('WEXUM_VPN_CONTROL_SRC', str(DEFAULT_CONTROL))).resolve()
CONTROL_READY = (CONTROL_SRC / 'wexum_vpn_control/__init__.py').is_file()
if os.environ.get('WEXUM_VPN_CONTROL_SRC') and not CONTROL_READY:
    raise RuntimeError('explicit WEXUM_VPN_CONTROL_SRC has no wexum_vpn_control package')
if os.environ.get('WEXUM_VPN_REQUIRE_CONTRACTS') == '1' and not CONTROL_READY:
    raise RuntimeError('required Control Plane source is absent; contract suite cannot skip')
if CONTROL_READY:
    sys.path.insert(0, str(CONTROL_SRC))
    from wexum_vpn_control import (
        AccessDenied, AuthenticatedActor, DeviceControlService,
        DeviceLimitReached, DeviceNotFound, EnrollmentUnavailable,
        EntitlementDecision, IdempotencyConflict, SQLiteDeviceStore,
    )
    from wexum_vpn_control.store import StoreLimit

NOW = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
SCOPES = frozenset({'vpn:device:read', 'vpn:device:write'})


def principal(tenant='tenant-a', subject='subject-a', **overrides):
    fields = dict(tenant_id=tenant, subject_id=subject,
                  issuer='https://issuer.example', audience='wexum-vpn-control',
                  issued_at=NOW-timedelta(minutes=1),
                  expires_at=NOW+timedelta(hours=1), scopes=SCOPES)
    fields.update(overrides)
    return AuthenticatedActor(**fields)


def entitlement(tenant='tenant-a', subject='subject-a', **overrides):
    fields = dict(tenant_id=tenant, subject_id=subject, active=True,
                  expires_at=NOW+timedelta(days=1), device_limit=2)
    fields.update(overrides)
    return EntitlementDecision(**fields)


@unittest.skipUnless(CONTROL_READY, 'real Control Plane source absent; supply WEXUM_VPN_CONTROL_SRC')
class ControlPlaneContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addAsyncCleanup(self._cleanup)
        self.db = Path(self.temp.name) / 'control.db'
        self.store = SQLiteDeviceStore(self.db)
        self.answer = entitlement()
        self.entitlement_calls = 0

        async def checker(tenant, subject):
            self.entitlement_calls += 1
            return self.answer

        self.checker = checker
        self.service = self._service()

    async def _cleanup(self):
        self.temp.cleanup()

    def _service(self, **overrides):
        params = dict(store=self.store, check_entitlement=self.checker,
                      trusted_issuer='https://issuer.example',
                      expected_audience='wexum-vpn-control', clock=lambda: NOW)
        params.update(overrides)
        return DeviceControlService(**params)

    async def enroll(self, key='test_request_123456', actor=None):
        return await self.service.enroll(actor=actor or principal(),
                                         platform='android', idempotency_key=key)

    async def test_cross_tenant_and_cross_subject_cannot_list_or_revoke(self):
        device = await self.enroll()
        for other in (principal('tenant-b', 'subject-a'),
                      principal('tenant-a', 'subject-b')):
            with self.subTest(other=other):
                self.assertEqual(self.service.list_devices(actor=other), [])
                with self.assertRaises(DeviceNotFound):
                    self.service.revoke_device(actor=other, device_id=device.device_id)
        self.assertIsNone(self.service.list_devices(actor=principal())[0].revoked_at)

    async def test_invalid_authority_cannot_reach_entitlement_provider(self):
        for actor in (principal(issuer='https://other.example'),
                      principal(scopes=frozenset({'vpn:device:read'})),
                      principal(expires_at=NOW),
                      principal(tenant='other-tenant', audience='other-service')):
            with self.subTest(actor=actor), self.assertRaises(AccessDenied):
                await self.enroll(actor=actor)
        self.assertEqual(self.entitlement_calls, 0)

    async def test_unavailable_entitlement_fails_closed(self):
        async def unreachable(*_args):
            raise OSError('test-only provider outage')
        self.service = self._service(check_entitlement=unreachable)
        with self.assertRaises(EnrollmentUnavailable):
            await self.enroll()
        self.assertEqual(self.store.list_for_owner(tenant_id='tenant-a', subject_id='subject-a'), [])

    async def test_wrong_owner_entitlement_fails_closed(self):
        self.answer = entitlement(tenant='tenant-b')
        with self.assertRaises(AccessDenied):
            await self.enroll()
        self.assertEqual(self.service.list_devices(actor=principal()), [])

    async def test_inactive_and_expired_entitlement_fails_closed(self):
        for answer in (entitlement(active=False), entitlement(expires_at=NOW)):
            self.answer = answer
            with self.subTest(answer=answer), self.assertRaises(AccessDenied):
                await self.enroll()
        self.assertEqual(self.service.list_devices(actor=principal()), [])

    async def test_retry_idempotent_and_limit_is_enforced(self):
        self.answer = entitlement(device_limit=1)
        first = await self.enroll()
        self.assertEqual((await self.enroll()).device_id, first.device_id)
        with self.assertRaises(DeviceLimitReached):
            await self.enroll(key='another_test_key_123')
        self.assertEqual(len(self.service.list_devices(actor=principal())), 1)

    async def test_reused_key_different_platform_is_conflict(self):
        await self.enroll()
        with self.assertRaises(IdempotencyConflict):
            await self.service.enroll(actor=principal(), platform='ios',
                                      idempotency_key='test_request_123456')

    async def test_revocation_idempotent_and_not_resurrected(self):
        device = await self.enroll()
        revoked = self.service.revoke_device(actor=principal(), device_id=device.device_id)
        self.assertIsNotNone(revoked.revoked_at)
        self.assertEqual(revoked, self.service.revoke_device(actor=principal(), device_id=device.device_id))
        self.assertIsNotNone((await self.enroll()).revoked_at)

    async def test_entitlement_cancellation_propagates_no_device(self):
        async def cancelled(*_args):
            raise asyncio.CancelledError()
        self.service = self._service(check_entitlement=cancelled)
        with self.assertRaises(asyncio.CancelledError):
            await self.enroll()
        self.assertEqual(self.store.list_for_owner(tenant_id='tenant-a', subject_id='subject-a'), [])

    async def test_sqlite_lock_denies_enrollment_without_partial_row(self):
        lock = sqlite3.connect(self.db, isolation_level=None, timeout=0.1)
        try:
            lock.execute('BEGIN IMMEDIATE')
            service = self._service(store=SQLiteDeviceStore(self.db, busy_timeout_seconds=0.1))
            with self.assertRaises(EnrollmentUnavailable):
                await service.enroll(actor=principal(), platform='android',
                                     idempotency_key='test_request_123456')
        finally:
            lock.rollback()
            lock.close()
        self.assertEqual(self.service.list_devices(actor=principal()), [])

    async def test_concurrent_device_cap_is_atomic(self):
        def add(index):
            return self.store.enroll(tenant_id='tenant-a', subject_id='subject-a',
                platform='android', request_key=f'concurrent_req_1234{index}',
                now=NOW, expires_at=NOW+timedelta(days=1), max_devices=1)
        outcomes = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for future in [executor.submit(add, n) for n in range(4)]:
                try:
                    future.result()
                    outcomes.append('created')
                except StoreLimit:
                    outcomes.append('limit')
        self.assertCountEqual(outcomes, ['created', 'limit', 'limit', 'limit'])
        self.assertEqual(len(self.service.list_devices(actor=principal())), 1)

    async def test_idempotency_secret_not_stored_as_plaintext(self):
        await self.enroll(key='unique_sensitive_key_123456')
        with sqlite3.connect(self.db) as db:
            hashes = [row[0] for row in db.execute('SELECT request_hash FROM enrollment_requests')]
        self.assertEqual(len(hashes), 1)
        self.assertNotIn('unique_sensitive_key_123456', hashes)
        self.assertEqual(len(hashes[0]), 64)

    def _make_store_unavailable(self):
        # Stable and OS-independent: connect() cannot create a missing parent.
        self.store.path = Path(self.temp.name) / 'missing_parent' / 'control.db'

    async def test_regression_sqlite_open_failure_maps_to_service_error_on_enroll(self):
        self._make_store_unavailable()
        with self.assertRaises(EnrollmentUnavailable):
            await self.enroll()

    async def test_regression_sqlite_open_failure_maps_to_service_error_on_list(self):
        self._make_store_unavailable()
        with self.assertRaises(EnrollmentUnavailable):
            self.service.list_devices(actor=principal())

    async def test_regression_sqlite_open_failure_maps_to_service_error_on_revoke(self):
        device = await self.enroll()
        self._make_store_unavailable()
        with self.assertRaises(EnrollmentUnavailable):
            self.service.revoke_device(actor=principal(), device_id=device.device_id)

    async def test_regression_recent_active_device_not_hidden_by_history(self):
        """Known #2/#56 blocker: PR #55 currently truncates 200 oldest rows."""
        for i in range(200):
            instant = NOW-timedelta(days=10)+timedelta(minutes=2*i)
            self.store.enroll(tenant_id='tenant-a', subject_id='subject-a',
                platform='android', request_key=f'old_request_{i:04d}_key',
                now=instant, expires_at=instant+timedelta(minutes=1), max_devices=1)
        active = await self.enroll(key='latest_active_key_123456')
        visible_ids = {item.device_id for item in self.service.list_devices(actor=principal())}
        self.assertTrue(active.device_id in visible_ids, 'active device hidden by history pagination')


if __name__ == '__main__':
    unittest.main()
