"""Integrator-owned adversarial test of VPN node registration generations.

Only synthetic node IDs and timestamps. Exercises the current exact-source
NodeRegistry copied from draft PR #65 without modifying the product lane.
"""

import threading
import unittest
from datetime import datetime, timedelta, timezone

from registry import (
    HealthObservation, HealthStatus, Node, NodeRegistry, StaleObservationError,
)

START = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)


def node():
    return Node("test-node-a", "test-region-a", frozenset({"test-wireguard"}), 10)


def report(registration_id, offset=0):
    return HealthObservation(
        "test-node-a", registration_id, HealthStatus.HEALTHY,
        START + timedelta(seconds=offset), 1,
    )


class IndependentNodeGenerationRegressions(unittest.TestCase):
    def test_old_generation_cannot_mark_recreated_node_healthy(self):
        registry = NodeRegistry(health_ttl_seconds=30)
        old_id = registry.register(node())
        registry.record_health(report(old_id), now=START)
        registry.remove("test-node-a")
        fresh_id = registry.register(node())
        self.assertNotEqual(old_id, fresh_id)
        # A deliberately newer (not just equal) timestamp must not circumvent
        # generation binding after re-registration of the same logical node.
        with self.assertRaises(StaleObservationError):
            registry.record_health(report(old_id, 3), now=START + timedelta(seconds=4))
        self.assertIsNone(registry.select(now=START + timedelta(seconds=4)))
        registry.record_health(report(fresh_id, 5), now=START + timedelta(seconds=5))
        self.assertEqual(
            registry.select(now=START + timedelta(seconds=5)).registration_id, fresh_id
        )

    def test_old_selection_is_invalid_after_remove_recreate(self):
        registry = NodeRegistry(health_ttl_seconds=30)
        old_id = registry.register(node())
        registry.record_health(report(old_id), now=START)
        old_selection = registry.select(now=START)
        registry.remove("test-node-a")
        fresh_id = registry.register(node())
        registry.record_health(report(fresh_id, 1), now=START + timedelta(seconds=1))
        self.assertFalse(
            registry.revalidate_selection(old_selection, now=START + timedelta(seconds=2))
        )
        self.assertTrue(
            registry.revalidate_selection(
                registry.select(now=START + timedelta(seconds=2)),
                now=START + timedelta(seconds=2),
            )
        )

    def test_delayed_health_report_after_generation_rotation(self):
        registry = NodeRegistry(health_ttl_seconds=30)
        old_id = registry.register(node())
        rotated = threading.Event()
        result = []

        def rotate():
            registry.remove("test-node-a")
            registry.register(node())
            rotated.set()

        def delayed():
            if not rotated.wait(timeout=5):
                result.append("timeout")
                return
            try:
                registry.record_health(report(old_id, 2), now=START + timedelta(seconds=2))
            except StaleObservationError:
                result.append("rejected")
            else:
                result.append("accepted")

        first = threading.Thread(target=rotate)
        second = threading.Thread(target=delayed)
        first.start()
        second.start()
        first.join(timeout=5)
        second.join(timeout=5)
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(result, ["rejected"])
        self.assertIsNone(registry.select(now=START + timedelta(seconds=2)))


if __name__ == "__main__":
    unittest.main()
