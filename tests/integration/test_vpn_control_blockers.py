"""Independent integration regressions for outstanding PR #55 review findings.

These tests enforce the previously observed Control Plane negative cases.
Clock-dependent fixtures use a deterministic explicitly supplied instant.
Only stdlib and synthetic test data; no VPN or external service is required.
"""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wexum_vpn_control import (
    AuthenticatedActor,
    DeviceControlService,
    EnrollmentUnavailable,
    EntitlementDecision,
    SQLiteDeviceStore,
)

NOW = datetime(2026, 11, 21, 12, tzinfo=timezone.utc)


class HistoricalDeviceVisibility(unittest.TestCase):
    def test_new_active_device_is_visible_after_200_revocations(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteDeviceStore(Path(directory) / "devices.sqlite3")
            for index in range(200):
                device = store.enroll(
                    tenant_id="tenant-a", subject_id="subject-a",
                    platform="android", request_key=f"historic-key-{index}",
                    now=NOW, expires_at=NOW + timedelta(days=3), max_devices=1,
                )
                store.revoke(
                    tenant_id="tenant-a", subject_id="subject-a",
                    device_id=device.device_id, now=NOW,
                )
            fresh = store.enroll(
                tenant_id="tenant-a", subject_id="subject-a",
                platform="android", request_key="newest-key",
                now=NOW + timedelta(hours=1),
                expires_at=NOW + timedelta(days=3), max_devices=1,
            )
            listed = store.list_for_owner(
                tenant_id="tenant-a", subject_id="subject-a",
                now=NOW + timedelta(hours=1),
            )
            self.assertIn(fresh.device_id, {item.device_id for item in listed})


class StoreOpeningOutage(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = SQLiteDeviceStore(
            Path(self.directory.name) / "devices.sqlite3"
        )
        # Point to a nonexistent parent after successful store initialization.
        # This is deterministic across runners and does not require chmod/root.
        self.store.path = Path(self.directory.name) / "missing" / "devices.sqlite3"
        self.actor = AuthenticatedActor(
            tenant_id="tenant-a",
            subject_id="subject-a",
            issuer="https://issuer.example",
            audience="wexum-vpn-control",
            issued_at=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(minutes=20),
            scopes=frozenset({"vpn:device:read", "vpn:device:write"}),
        )

        async def entitlement(tenant_id, subject_id):
            return EntitlementDecision(
                tenant_id, subject_id, True,
                NOW + timedelta(days=1), 2,
            )

        self.service = DeviceControlService(
            store=self.store,
            check_entitlement=entitlement,
            trusted_issuer="https://issuer.example",
            expected_audience="wexum-vpn-control",
            clock=lambda: NOW,
        )

    async def asyncTearDown(self):
        self.directory.cleanup()

    async def test_list_outage_maps_to_stable_service_error(self):
        with self.assertRaises(EnrollmentUnavailable):
            self.service.list_devices(actor=self.actor)

    async def test_revoke_outage_maps_to_stable_service_error(self):
        with self.assertRaises(EnrollmentUnavailable):
            self.service.revoke_device(
                actor=self.actor,
                device_id="00000000-0000-0000-0000-000000000000",
            )

    async def test_enroll_outage_maps_to_stable_service_error(self):
        with self.assertRaises(EnrollmentUnavailable):
            await self.service.enroll(
                actor=self.actor, platform="android",
                idempotency_key="regression_key_123456",
            )


if __name__ == "__main__":
    unittest.main()
