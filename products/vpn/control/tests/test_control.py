"""Deterministic control-plane tests; no external auth service or VPN tunnel."""

import asyncio
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wexum_vpn_control import (
    AccessDenied, AuthenticatedActor, DeviceControlService, DeviceLimitReached,
    DeviceNotFound, EnrollmentUnavailable, EntitlementDecision, IdempotencyConflict,
    InvalidRequest, SQLiteDeviceStore,
)

BASE = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)
SCOPE = frozenset({'vpn:device:read', 'vpn:device:write'})


def actor(tenant='tenant-A', subject='subject-A', **kwargs):
    return AuthenticatedActor(
        tenant_id=tenant, subject_id=subject,
        issuer=kwargs.pop('issuer', 'https://issuer.example'),
        audience=kwargs.pop('audience', 'wexum-vpn-control'),
        issued_at=kwargs.pop('issued_at', BASE-timedelta(minutes=1)),
        expires_at=kwargs.pop('expires_at', BASE+timedelta(minutes=20)),
        scopes=kwargs.pop('scopes', SCOPE), **kwargs,
    )


def decision(tenant='tenant-A', subject='subject-A', *, active=True, limit=2, expiry=None):
    return EntitlementDecision(tenant, subject, active,
                               expiry or BASE + timedelta(days=7), limit)


class DeviceServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / 'devices.sqlite3'
        self.store = SQLiteDeviceStore(self.db)
        self.now = BASE
        self.answer = decision()
        self.calls = 0

        async def checker(tenant, subject):
            self.calls += 1
            return self.answer

        self.checker = checker
        self.service = self.make_service()

    async def asyncTearDown(self):
        self.tmp.cleanup()

    def make_service(self, checker=None, **kw):
        return DeviceControlService(
            store=self.store,
            check_entitlement=checker or self.checker,
            trusted_issuer='https://issuer.example',
            expected_audience='wexum-vpn-control',
            clock=lambda: self.now, **kw,
        )

    async def register(self, key='1234567890abcdef', platform='android', principal=None):
        return await self.service.enroll(
            actor=principal or actor(), platform=platform, idempotency_key=key)

    async def test_register_persists_and_owner_can_list(self):
        device = await self.register()
        self.assertEqual(device.tenant_id, 'tenant-A')
        self.assertEqual(device.subject_id, 'subject-A')
        self.assertEqual(device.platform, 'android')
        self.assertIsNone(device.revoked_at)
        self.assertEqual(self.service.list_devices(actor=actor()), [device])
        other_store = SQLiteDeviceStore(self.db)
        self.assertEqual(other_store.list_for_owner(tenant_id='tenant-A', subject_id='subject-A'), [device])

    async def test_new_active_device_is_listed_after_200_revocations(self):
        principal = actor()
        history = []
        for index in range(200):
            device = self.store.enroll(
                tenant_id=principal.tenant_id, subject_id=principal.subject_id,
                platform='android', request_key=f'historic_key_{index:04d}',
                now=BASE, expires_at=BASE + timedelta(days=1), max_devices=1,
            )
            history.append(self.service.revoke_device(actor=principal, device_id=device.device_id))
        history.sort(key=lambda device: device.device_id)

        self.now = BASE + timedelta(minutes=1)
        active = await self.register(principal=principal)
        listed = self.service.list_devices(actor=principal)
        self.assertEqual([device.device_id for device in listed[:1]], [active.device_id])
        self.assertEqual(listed[1:], history[:199])

        revoked = self.service.revoke_device(actor=principal, device_id=active.device_id)
        self.assertIsNotNone(revoked.revoked_at)
        self.assertEqual(self.service.revoke_device(actor=principal, device_id=active.device_id), revoked)
        self.assertEqual(self.service.list_devices(actor=principal), history)

    async def test_full_active_allowance_is_listed_ahead_of_expired_history(self):
        principal = actor()
        self.now = BASE + timedelta(minutes=1)
        for index in range(200):
            self.store.enroll(
                tenant_id=principal.tenant_id, subject_id=principal.subject_id,
                platform='android', request_key=f'expired_key_{index:04d}',
                now=BASE, expires_at=self.now, max_devices=200,
            )

        self.answer = decision(limit=200)
        active = [
            await self.register(key=f'current_key_{index:04d}', principal=principal)
            for index in range(200)
        ]
        active_ids = sorted(device.device_id for device in active)
        listed = self.service.list_devices(actor=principal)
        self.assertEqual(len(listed), 200)
        self.assertEqual([device.device_id for device in listed], active_ids)

    async def test_listing_active_and_historical_rows_is_scoped_to_tenant_and_subject(self):
        own_history = await self.register()
        own_history = self.service.revoke_device(actor=actor(), device_id=own_history.device_id)
        self.now = BASE + timedelta(minutes=1)
        own_active = await self.register(key='own_active_key_0001')

        for tenant, subject in [('tenant-B', 'subject-A'), ('tenant-A', 'subject-B')]:
            principal = actor(tenant, subject)
            self.answer = decision(tenant=tenant, subject=subject)
            history = await self.register(principal=principal)
            history = self.service.revoke_device(actor=principal, device_id=history.device_id)
            active = await self.register(key='other_active_key_01', principal=principal)
            self.assertEqual(self.service.list_devices(actor=principal), [active, history])
            with self.assertRaises(DeviceNotFound):
                self.service.revoke_device(actor=principal, device_id=own_active.device_id)

        self.assertEqual(self.service.list_devices(actor=actor()), [own_active, own_history])

    async def test_duplicate_request_is_idempotent_even_at_limit(self):
        self.answer = decision(limit=1)
        first = await self.register()
        again = await self.register()
        self.assertEqual(first.device_id, again.device_id)
        with self.assertRaises(DeviceLimitReached):
            await self.register(key='another_key_1234567')

    async def test_reused_key_for_different_platform_conflicts(self):
        await self.register()
        with self.assertRaises(IdempotencyConflict):
            await self.register(platform='ios')

    async def test_idempotency_is_scoped_to_owner(self):
        first = await self.register()
        self.answer = decision(tenant='tenant-B', subject='subject-B')
        second = await self.register(principal=actor('tenant-B','subject-B'))
        self.assertNotEqual(first.device_id, second.device_id)
        self.assertEqual(len(self.service.list_devices(actor=actor('tenant-B','subject-B'))), 1)
        self.assertEqual(len(self.service.list_devices(actor=actor())), 1)

    async def test_other_tenant_and_owner_cannot_read_or_revoke(self):
        device = await self.register()
        for principal in [actor('tenant-B','subject-A'), actor('tenant-A','subject-B')]:
            self.assertEqual(self.service.list_devices(actor=principal), [])
            with self.assertRaises(DeviceNotFound):
                self.service.revoke_device(actor=principal, device_id=device.device_id)
        self.assertIsNone(self.service.list_devices(actor=actor())[0].revoked_at)

    async def test_revocation_is_idempotent_and_allows_new_device(self):
        self.answer = decision(limit=1)
        device = await self.register()
        revoked = self.service.revoke_device(actor=actor(), device_id=device.device_id)
        self.assertIsNotNone(revoked.revoked_at)
        again = self.service.revoke_device(actor=actor(), device_id=device.device_id)
        self.assertEqual(revoked, again)
        replacement = await self.register(key='new_key_0123456789')
        self.assertNotEqual(device.device_id, replacement.device_id)

    async def test_same_idempotency_key_does_not_resurrect_revoked_device(self):
        device = await self.register()
        self.service.revoke_device(actor=actor(), device_id=device.device_id)
        again = await self.register()
        self.assertIsNotNone(again.revoked_at)
        self.assertEqual(device.device_id, again.device_id)

    async def test_invalid_request_denied_without_provider_call(self):
        for bad_platform in ['linux', '', None, [], {'os':'android'}]:
            with self.subTest(platform=bad_platform):
                with self.assertRaises(InvalidRequest):
                    await self.register(platform=bad_platform)
        with self.assertRaises(InvalidRequest):
            await self.register(key='short')
        self.assertEqual(self.calls, 0)

    async def test_actor_must_have_verified_issuer_audience_and_scope(self):
        bad = [
            actor(issuer='https://imposter.example'),
            actor(audience='wexum-hub'),
            actor(scopes=frozenset({'vpn:device:read'})),
            actor(issued_at=BASE + timedelta(minutes=2)),
            actor(expires_at=BASE),
            actor(tenant=''),
            actor(subject=' '),
        ]
        for principal in bad:
            with self.subTest(principal=principal):
                with self.assertRaises(AccessDenied):
                    await self.register(principal=principal)
        self.assertEqual(self.calls, 0)

    async def test_missing_scope_denies_list_or_revoke(self):
        device = await self.register()
        with self.assertRaises(AccessDenied):
            self.service.list_devices(actor=actor(scopes=frozenset({'vpn:device:write'})))
        with self.assertRaises(AccessDenied):
            self.service.revoke_device(actor=actor(scopes=frozenset({'vpn:device:read'})), device_id=device.device_id)

    async def test_entitlement_inactive_and_owner_mismatch_denied(self):
        for answer in [decision(active=False), decision(subject='other'),
                       decision(tenant='other'), decision(limit=0),
                       decision(expiry=BASE), None, {'active': True}]:
            self.answer = answer
            with self.subTest(answer=answer):
                with self.assertRaises(AccessDenied):
                    await self.register()
        self.assertEqual(self.service.list_devices(actor=actor()), [])

    async def test_entitlement_failure_and_timeout_fail_closed(self):
        async def broken(_tenant, _subject):
            raise OSError('billing backend unavailable')
        async def slow(_tenant, _subject):
            await asyncio.sleep(1)
            return decision()
        for fn in (broken, slow):
            service = self.make_service(checker=fn, entitlement_timeout=0.05)
            with self.assertRaises(EnrollmentUnavailable):
                await service.enroll(actor=actor(), platform='android',
                                     idempotency_key='1234567890abcdef')
        self.assertEqual(self.service.list_devices(actor=actor()), [])

    async def test_actor_expiry_during_entitlement_fetch_fails_closed(self):
        async def moving(_tenant, _subject):
            self.now = BASE + timedelta(minutes=30)
            return decision()
        service = self.make_service(checker=moving)
        with self.assertRaises(AccessDenied):
            await service.enroll(actor=actor(), platform='android',
                                 idempotency_key='1234567890abcdef')

    async def test_device_expiry_follows_entitlement_not_short_session_token(self):
        registered = await self.register()
        self.assertEqual(registered.expires_at,
                         (BASE+timedelta(days=7)).isoformat(timespec='microseconds'))

    async def test_short_entitlement_expiry_bounds_enrollment(self):
        self.answer = decision(expiry=BASE+timedelta(seconds=30))
        device = await self.register()
        self.assertEqual(device.expires_at,
                         (BASE+timedelta(seconds=30)).isoformat(timespec='microseconds'))

    async def test_revocation_allowed_when_entitlement_service_is_down(self):
        device = await self.register()
        self.answer = None
        self.assertIsNotNone(self.service.revoke_device(actor=actor(),device_id=device.device_id).revoked_at)

    async def test_expired_device_no_longer_counts_for_device_cap(self):
        self.answer = decision(limit=1, expiry=BASE+timedelta(minutes=2))
        await self.register()
        self.now = BASE+timedelta(minutes=3)
        self.answer = decision(limit=1, expiry=BASE+timedelta(days=2))
        next_actor = actor(expires_at=BASE+timedelta(hours=1))
        later = await self.register(key='fresh_key_12345678', principal=next_actor)
        self.assertIsNone(later.revoked_at)

    async def test_store_rejected_if_backend_locked(self):
        lock = sqlite3.connect(self.db, isolation_level=None, timeout=0.1)
        try:
            lock.execute('BEGIN IMMEDIATE')
            service = DeviceControlService(
                store=SQLiteDeviceStore(self.db, busy_timeout_seconds=0.1),
                check_entitlement=self.checker,
                trusted_issuer='https://issuer.example',
                expected_audience='wexum-vpn-control', clock=lambda: self.now)
            with self.assertRaises(EnrollmentUnavailable):
                await service.enroll(actor=actor(), platform='android',idempotency_key='1234567890abcdef')
        finally:
            lock.rollback()
            lock.close()

    async def test_database_device_limit_transaction_safe_under_threads(self):
        self.answer = decision(limit=1)
        def enroll_raw(key):
            return self.store.enroll(tenant_id='tenant-A',subject_id='subject-A',
                platform='android',request_key=key,now=BASE,
                expires_at=BASE+timedelta(days=1),max_devices=1)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(enroll_raw, 'concurrent_req_1234'+str(i)) for i in range(2)]
            outcomes=[]
            for result in futures:
                try:
                    result.result()
                    outcomes.append('ok')
                except Exception as error:
                    outcomes.append(type(error).__name__)
        self.assertCountEqual(outcomes,['ok','StoreLimit'])
        self.assertEqual(len(self.service.list_devices(actor=actor())),1)

    async def test_user_scope_not_bypassed_by_client_device_uuid(self):
        first = await self.register()
        with self.assertRaises(DeviceNotFound):
            self.service.revoke_device(actor=actor('tenant-A','other'),device_id=first.device_id)
        with self.assertRaises(DeviceNotFound):
            self.service.revoke_device(actor=actor(),device_id='00000000-0000-0000-0000-000000000000')


    async def test_database_open_failure_maps_to_service_unavailable(self):
        existing = await self.register()
        self.store.path = self.db.parent / 'missing-parent' / 'devices.sqlite3'
        try:
            with self.assertRaises(EnrollmentUnavailable):
                self.service.list_devices(actor=actor())
            with self.assertRaises(EnrollmentUnavailable):
                self.service.revoke_device(actor=actor(), device_id=existing.device_id)
            with self.assertRaises(EnrollmentUnavailable):
                await self.register(key='another_key_1234567')
        finally:
            self.store.path = self.db
        self.assertEqual(self.service.list_devices(actor=actor()), [existing])


if __name__ == '__main__':
    unittest.main()
