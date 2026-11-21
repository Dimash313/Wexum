"""Local contract tests; every name/region/observation in this file is synthetic."""

import threading
from dataclasses import replace
import unittest
from datetime import datetime, timedelta, timezone

from registry import (
    AvailabilityStatus,
    HealthObservation,
    HealthStatus,
    Node,
    NodeRegistry,
    StaleObservationError,
)


NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)  # TEST ONLY


def node(name="test-node-a", region="test-region-a", sessions=10, caps=frozenset({"test-wireguard"})):
    return Node(name, region, caps, sessions)


def observe(name="test-node-a", *, registration_id, at=NOW, status=HealthStatus.HEALTHY, active=0):
    return HealthObservation(name, registration_id, status, at, active)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = NodeRegistry(health_ttl_seconds=10, max_nodes=3)
        self.registrations = {"test-node-a": self.registry.register(node())}

    def observe(self, name="test-node-a", **kwargs):
        return observe(name, registration_id=self.registrations[name], **kwargs)

    def test_unreported_is_never_selected(self):
        self.assertIsNone(self.registry.select(now=NOW))
        self.assertEqual(self.registry.snapshot(now=NOW)[0].status, AvailabilityStatus.UNREPORTED)

    def test_fresh_health_and_exact_expiry_boundary(self):
        self.registry.record_health(self.observe(active=3), now=NOW)
        result = self.registry.select(now=NOW + timedelta(seconds=9))
        self.assertEqual((result.node_id, result.active_sessions), ("test-node-a", 3))
        self.assertEqual(result.expires_at, NOW + timedelta(seconds=10))
        self.assertIsNone(self.registry.select(now=NOW + timedelta(seconds=10)))
        self.assertEqual(self.registry.snapshot(now=NOW + timedelta(seconds=10))[0].status, AvailabilityStatus.STALE)

    def test_down_and_overloaded_fail_closed(self):
        self.registry.record_health(self.observe(status=HealthStatus.DOWN), now=NOW)
        self.assertEqual(self.registry.snapshot(now=NOW)[0].status, AvailabilityStatus.DOWN)
        self.assertIsNone(self.registry.select(now=NOW))
        self.registry.record_health(self.observe(at=NOW + timedelta(seconds=1), active=10), now=NOW + timedelta(seconds=1))
        self.assertEqual(self.registry.snapshot(now=NOW + timedelta(seconds=1))[0].status, AvailabilityStatus.SATURATED)
        self.assertIsNone(self.registry.select(now=NOW + timedelta(seconds=1)))

    def test_disable_enable_resets_old_health(self):
        self.registry.record_health(self.observe(), now=NOW)
        self.registry.set_enabled("test-node-a", False)
        self.assertEqual(self.registry.snapshot(now=NOW)[0].status, AvailabilityStatus.DISABLED)
        self.registry.set_enabled("test-node-a", True)
        self.assertEqual(self.registry.snapshot(now=NOW)[0].status, AvailabilityStatus.UNREPORTED)
        self.assertIsNone(self.registry.select(now=NOW))

    def test_disable_reenable_rejects_old_health_replay(self):
        self.registry.record_health(self.observe(), now=NOW)
        self.registry.set_enabled("test-node-a", False)
        with self.assertRaises(ValueError):
            self.registry.record_health(self.observe(at=NOW + timedelta(seconds=1)), now=NOW + timedelta(seconds=1))
        previous_registration = self.registrations["test-node-a"]
        self.registrations["test-node-a"] = self.registry.set_enabled("test-node-a", True)
        self.assertNotEqual(previous_registration, self.registrations["test-node-a"])
        with self.assertRaises(StaleObservationError):
            self.registry.record_health(observe(registration_id=previous_registration), now=NOW + timedelta(seconds=1))
        self.assertIsNone(self.registry.select(now=NOW + timedelta(seconds=1)))
        self.registry.record_health(self.observe(at=NOW + timedelta(seconds=2)), now=NOW + timedelta(seconds=2))
        self.assertEqual(self.registry.select(now=NOW + timedelta(seconds=2)).registration_id, self.registrations["test-node-a"])

    def test_removed_node_old_generation_cannot_reactivate_same_id(self):
        old_generation = self.registrations["test-node-a"]
        self.registry.record_health(self.observe(), now=NOW)
        self.registry.remove("test-node-a")
        new_generation = self.registry.register(node())
        self.registrations["test-node-a"] = new_generation
        self.assertNotEqual(old_generation, new_generation)
        with self.assertRaises(StaleObservationError):
            self.registry.record_health(
                observe(registration_id=old_generation, at=NOW + timedelta(seconds=1)),
                now=NOW + timedelta(seconds=2),
            )
        self.assertIsNone(self.registry.select(now=NOW + timedelta(seconds=2)))
        self.registry.record_health(self.observe(at=NOW + timedelta(seconds=2)), now=NOW + timedelta(seconds=2))
        self.assertEqual(self.registry.select(now=NOW + timedelta(seconds=2)).registration_id, new_generation)

    def test_registration_id_is_required_and_validated(self):
        with self.assertRaises(ValueError):
            HealthObservation("test-node-a", "test-fake", HealthStatus.HEALTHY, NOW, 0)
        with self.assertRaises(ValueError):
            HealthObservation("test-node-a", None, HealthStatus.HEALTHY, NOW, 0)
        with self.assertRaises(StaleObservationError):
            self.registry.record_health(
                observe(registration_id="0" * 32), now=NOW
            )
        self.assertIsNone(self.registry.select(now=NOW))

    def test_concurrent_remove_recreate_and_old_report_fails(self):
        old_generation = self.registrations["test-node-a"]
        self.registry.record_health(self.observe(), now=NOW)
        completed = threading.Event()
        failures = []

        def rotate():
            self.registry.remove("test-node-a")
            self.registrations["test-node-a"] = self.registry.register(node())
            completed.set()

        def delayed_old_report():
            if not completed.wait(timeout=5):
                failures.append("rotation timeout")
                return
            try:
                self.registry.record_health(
                    observe(registration_id=old_generation, at=NOW + timedelta(seconds=1)),
                    now=NOW + timedelta(seconds=2),
                )
                failures.append("old report unexpectedly accepted")
            except StaleObservationError:
                pass

        threads = [threading.Thread(target=rotate), threading.Thread(target=delayed_old_report)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertFalse(failures)
        self.assertIsNone(self.registry.select(now=NOW + timedelta(seconds=2)))

    def test_remove_and_duplicate_inventory(self):
        with self.assertRaises(ValueError):
            self.registry.register(node())
        self.registry.record_health(self.observe(), now=NOW)
        self.registry.remove("test-node-a")
        self.assertEqual(self.registry.snapshot(now=NOW), ())
        with self.assertRaises(KeyError):
            self.registry.record_health(self.observe(), now=NOW)

    def test_out_of_order_and_replay_rejected(self):
        self.registry.record_health(self.observe(at=NOW + timedelta(seconds=2)), now=NOW + timedelta(seconds=2))
        for at in (NOW + timedelta(seconds=1), NOW + timedelta(seconds=2)):
            with self.assertRaises(StaleObservationError):
                self.registry.record_health(self.observe(at=at, status=HealthStatus.DOWN), now=NOW + timedelta(seconds=3))
        self.assertIsNotNone(self.registry.select(now=NOW + timedelta(seconds=3)))

    def test_future_and_expired_reports_fail_closed(self):
        for reported, received in ((NOW + timedelta(seconds=1), NOW), (NOW, NOW + timedelta(seconds=10))):
            with self.assertRaises(StaleObservationError):
                self.registry.record_health(self.observe(at=reported), now=received)
        self.assertIsNone(self.registry.select(now=NOW))

    def test_region_and_capability_are_exact(self):
        self.registry.record_health(self.observe(), now=NOW)
        self.assertIsNone(self.registry.select(now=NOW, region_id="test-region-b"))
        self.assertIsNone(self.registry.select(now=NOW, required_capabilities=frozenset({"test-openvpn"})))
        self.assertEqual(self.registry.select(now=NOW, region_id="test-region-a").node_id, "test-node-a")

    def test_normalized_capacity_and_stable_tie_break(self):
        self.registrations["test-node-b"] = self.registry.register(node("test-node-b", sessions=20))
        self.registrations["test-node-c"] = self.registry.register(node("test-node-c", sessions=30))
        self.registry.record_health(self.observe(active=5), now=NOW)
        self.registry.record_health(self.observe("test-node-b", active=10), now=NOW)
        self.registry.record_health(self.observe("test-node-c", active=5), now=NOW)
        self.assertEqual(self.registry.select(now=NOW).node_id, "test-node-c")
        self.registry.record_health(self.observe("test-node-c", at=NOW + timedelta(seconds=1), active=15), now=NOW + timedelta(seconds=1))
        self.assertEqual(self.registry.select(now=NOW + timedelta(seconds=1)).node_id, "test-node-a")

    def test_registry_and_query_resource_bounds(self):
        self.registry.register(node("test-node-b"))
        self.registry.register(node("test-node-c"))
        with self.assertRaises(ValueError):
            self.registry.register(node("test-node-d"))
        for bad in (0, 201, True, "3"):
            with self.assertRaises(ValueError):
                self.registry.snapshot(now=NOW, limit=bad)

    def test_invalid_input_rejected(self):
        invalid_nodes = [
            ("", "test-region-a", frozenset(), 5),
            (" TEST", "test-region-a", frozenset(), 5),
            (123, "test-region-a", frozenset(), 5),
            ("test-node", "../bad", frozenset(), 5),
            ("test-node", "test-region", {"test-cap"}, 5),
            ("test-node", "test-region", frozenset(), True),
            ("test-node", "test-region", frozenset(), 0),
        ]
        for args in invalid_nodes:
            with self.subTest(args=args), self.assertRaises(ValueError):
                Node(*args)
        with self.assertRaises(ValueError):
            Node("test-id", "test-region", frozenset({"TEST"}), 10)
        with self.assertRaises(ValueError):
            HealthObservation("test-node-a", "0" * 32, "healthy", NOW, 0)
        with self.assertRaises(ValueError):
            HealthObservation("test-node-a", "0" * 32, HealthStatus.HEALTHY, NOW, -1)
        with self.assertRaises(ValueError):
            HealthObservation("test-node-a", "0" * 32, HealthStatus.HEALTHY, NOW.replace(tzinfo=None), 0)
        with self.assertRaises(ValueError):
            self.registry.select(now=NOW.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            self.registry.select(now=NOW, required_capabilities={"test-wireguard"})
        with self.assertRaises(ValueError):
            NodeRegistry(max_nodes=0)
        with self.assertRaises(ValueError):
            NodeRegistry(health_ttl_seconds=301)

    def test_revalidate_selection_rejects_expiry_and_health_change(self):
        self.registry.record_health(self.observe(active=2), now=NOW)
        choice = self.registry.select(now=NOW)
        self.assertTrue(self.registry.revalidate_selection(choice, now=NOW + timedelta(seconds=9)))
        self.assertFalse(self.registry.revalidate_selection(choice, now=NOW + timedelta(seconds=10)))
        self.assertFalse(self.registry.revalidate_selection(choice, now=NOW - timedelta(seconds=1)))
        self.registry.record_health(
            self.observe(at=NOW + timedelta(seconds=1), status=HealthStatus.DOWN),
            now=NOW + timedelta(seconds=1),
        )
        self.assertFalse(self.registry.revalidate_selection(choice, now=NOW + timedelta(seconds=1)))
        self.registry.record_health(
            self.observe(at=NOW + timedelta(seconds=2), active=3),
            now=NOW + timedelta(seconds=2),
        )
        self.assertFalse(self.registry.revalidate_selection(choice, now=NOW + timedelta(seconds=2)))
        fresh = self.registry.select(now=NOW + timedelta(seconds=2))
        self.assertTrue(self.registry.revalidate_selection(fresh, now=NOW + timedelta(seconds=2)))
        self.registry.record_health(
            self.observe(at=NOW + timedelta(seconds=3), active=10),
            now=NOW + timedelta(seconds=3),
        )
        self.assertFalse(self.registry.revalidate_selection(fresh, now=NOW + timedelta(seconds=3)))

    def test_revalidate_selection_rejects_rotation_and_removal(self):
        self.registry.record_health(self.observe(), now=NOW)
        old = self.registry.select(now=NOW)
        self.registry.set_enabled("test-node-a", False)
        self.assertFalse(self.registry.revalidate_selection(old, now=NOW))
        new_id = self.registry.set_enabled("test-node-a", True)
        self.registrations["test-node-a"] = new_id
        self.assertFalse(self.registry.revalidate_selection(old, now=NOW))
        self.registry.record_health(self.observe(at=NOW + timedelta(seconds=1)), now=NOW + timedelta(seconds=1))
        latest = self.registry.select(now=NOW + timedelta(seconds=1))
        self.assertFalse(self.registry.revalidate_selection(old, now=NOW + timedelta(seconds=1)))
        self.assertTrue(self.registry.revalidate_selection(latest, now=NOW + timedelta(seconds=1)))
        self.registry.remove("test-node-a")
        self.assertFalse(self.registry.revalidate_selection(latest, now=NOW + timedelta(seconds=1)))
        self.registry.register(node())
        self.assertFalse(self.registry.revalidate_selection(latest, now=NOW + timedelta(seconds=1)))

    def test_revalidate_selection_rejects_forgery_and_invalid_input(self):
        self.registry.record_health(self.observe(active=1), now=NOW)
        choice = self.registry.select(now=NOW)
        for modified in (
            replace(choice, registration_id="0" * 32),
            replace(choice, node_id="test-unknown"),
            replace(choice, region_id="test-region-b"),
            replace(choice, observed_at=NOW + timedelta(seconds=1)),
            replace(choice, active_sessions=0),
            replace(choice, max_sessions=99),
        ):
            with self.subTest(modified=modified):
                self.assertFalse(self.registry.revalidate_selection(modified, now=NOW))
        with self.assertRaises(TypeError):
            self.registry.revalidate_selection(None, now=NOW)
        with self.assertRaises(ValueError):
            self.registry.revalidate_selection(choice, now=NOW.replace(tzinfo=None))

    def test_revalidate_selection_after_concurrent_disable(self):
        self.registry.record_health(self.observe(), now=NOW)
        old = self.registry.select(now=NOW)
        disabled = threading.Event()
        errors = []

        def toggle():
            self.registry.set_enabled("test-node-a", False)
            disabled.set()

        def recheck():
            if not disabled.wait(timeout=5):
                errors.append("disable timed out")
                return
            if self.registry.revalidate_selection(old, now=NOW):
                errors.append("stale selection was accepted")

        threads = [threading.Thread(target=toggle), threading.Thread(target=recheck)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
            self.assertFalse(t.is_alive())
        self.assertFalse(errors)

    def test_snapshot_is_immutable_and_sorted(self):
        self.registry.register(node("test-node-c"))
        self.registry.register(node("test-node-b"))
        first = self.registry.snapshot(now=NOW, limit=2)
        self.assertEqual(tuple(v.node_id for v in first), ("test-node-a", "test-node-b"))
        with self.assertRaises((AttributeError, TypeError)):
            first[0].status = AvailabilityStatus.HEALTHY

    def test_parallel_registration_cannot_bypass_capacity(self):
        reg = NodeRegistry(max_nodes=1)
        barrier = threading.Barrier(8)
        results = []
        mutex = threading.Lock()

        def work(i):
            barrier.wait()
            try:
                reg.register(node(f"test-node-{i}"))
                outcome = "accepted"
            except ValueError:
                outcome = "rejected"
            with mutex:
                results.append(outcome)

        threads = [threading.Thread(target=work, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(results.count("accepted"), 1)
        self.assertEqual(len(reg.snapshot(now=NOW)), 1)

    def test_parallel_health_updates_never_overwrite_newer(self):
        barrier = threading.Barrier(2)
        errors = []

        def work(offset):
            barrier.wait()
            at = NOW + timedelta(seconds=offset)
            try:
                self.registry.record_health(self.observe(at=at, active=offset), now=NOW + timedelta(seconds=3))
            except StaleObservationError:
                errors.append(offset)

        threads = [threading.Thread(target=work, args=(offset,)) for offset in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(self.registry.select(now=NOW + timedelta(seconds=3)).active_sessions, 2)
        self.assertTrue(set(errors).issubset({1}))


if __name__ == "__main__":
    unittest.main()
