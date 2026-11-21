import math
import threading
import unittest
from unittest.mock import Mock

from products.vpn.observability.alerts import AlertEngine
from products.vpn.observability.health import HealthMonitor, HealthState
from products.vpn.observability.probes import ProbeTarget, tcp_probe
from products.vpn.observability.resources import read_resources


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.monitor = HealthMonitor(clock=self.clock, min_samples=3, stale_after_seconds=10, window_seconds=30)

    def test_unknown_is_not_reported_healthy(self):
        s = self.monitor.snapshot()["gateway"]
        self.assertEqual(s.state, HealthState.UNKNOWN)
        self.assertIsNone(s.availability)
        self.assertNotIn('service="gateway"} 1', self.monitor.render_prometheus())

    def test_observed_success_and_sampled_availability(self):
        for _ in range(3):
            self.monitor.record("gateway", True, 0.1)
        s = self.monitor.snapshot()["gateway"]
        self.assertEqual(s.state, HealthState.HEALTHY)
        self.assertEqual(s.availability, 1.0)
        self.assertEqual(s.error_budget_used, 0.0)
        self.assertIn('wexum_vpn_probe_total{service="gateway",result="success"} 3', self.monitor.render_prometheus())

    def test_failure_alert_transitions_and_recovery(self):
        alerts = AlertEngine(self.monitor, watched_services=("gateway",))
        self.assertIn(("gateway", "telemetry_missing", True), [(x.service, x.code, x.active) for x in alerts.evaluate()])
        self.assertFalse(alerts.evaluate())
        for _ in range(3):
            self.monitor.record("gateway", False, 0.5)
        opened = [(x.service, x.code, x.active) for x in alerts.evaluate()]
        self.assertIn(("gateway", "probe_failures", True), opened)
        self.assertIn(("gateway", "sample_error_budget_exhausted", True), opened)
        self.assertIn(("gateway", "telemetry_missing", False), opened)
        self.assertEqual(self.monitor.snapshot()["gateway"].state, HealthState.DOWN)
        for _ in range(400):
            self.monitor.record("gateway", True, 0)
        closed = [(x.service, x.code, x.active) for x in alerts.evaluate()]
        self.assertIn(("gateway", "probe_failures", False), closed)
        self.assertIn(("gateway", "sample_error_budget_exhausted", False), closed)
        self.assertEqual(self.monitor.snapshot()["gateway"].state, HealthState.HEALTHY)

    def test_stale_and_eviction_are_distinct(self):
        for _ in range(3):
            self.monitor.record("identity", True, .02)
        self.clock.now = 10
        self.assertEqual(self.monitor.snapshot()["identity"].state, HealthState.STALE)
        self.clock.now = 30
        self.assertEqual(self.monitor.snapshot()["identity"].state, HealthState.UNKNOWN)
        self.assertIsNone(self.monitor.snapshot()["identity"].availability)

    def test_reject_pii_labels_without_mutation(self):
        with self.assertRaises(ValueError):
            self.monitor.record("alice@example.com", True, .2)
        with self.assertRaises(ValueError):
            self.monitor.record('gateway",user="alice', True, .2)
        with self.assertRaises(ValueError):
            self.monitor.record("gateway", True, float("nan"))
        with self.assertRaises(TypeError):
            self.monitor.record("gateway", 1, .2)
        self.assertEqual(self.monitor.snapshot()["gateway"].samples, 0)
        self.assertNotIn("alice", self.monitor.render_prometheus())

    def test_clock_rollback_is_rejected(self):
        self.clock.now = 2
        self.monitor.record("gateway", True, 0)
        self.clock.now = 1
        with self.assertRaises(ValueError):
            self.monitor.record("gateway", True, 0)

    def test_clock_rollback_blocks_snapshot_and_export(self):
        self.clock.now = 100
        for _ in range(3):
            self.monitor.record("gateway", True, 0.1)
        self.assertEqual(self.monitor.snapshot()["gateway"].state, HealthState.HEALTHY)
        self.clock.now = 99
        with self.assertRaises(ValueError):
            self.monitor.snapshot()
        with self.assertRaises(ValueError):
            self.monitor.render_prometheus()
        with self.assertRaises(ValueError):
            self.monitor.record("identity", True, 0)

    def test_duration_overflow_rejected_without_partial_sample(self):
        m = HealthMonitor(clock=self.clock, min_samples=1)
        m.record("gateway", True, 1e308)
        with self.assertRaises(ValueError):
            m.record("gateway", True, 1e308)
        summary = m.snapshot()["gateway"]
        self.assertEqual(summary.samples, 1)
        self.assertEqual(summary.successes, 1)
        self.assertNotIn(" inf", m.render_prometheus())
        self.assertIn('result="success"} 1', m.render_prometheus())

    def test_invalid_max_samples_type_is_rejected(self):
        with self.assertRaises(ValueError):
            HealthMonitor(max_samples_per_service="12")

    def test_bound_memory_and_total_counters(self):
        m = HealthMonitor(clock=self.clock, min_samples=1, max_samples_per_service=5)
        for _ in range(200):
            m.record("gateway", True, 0)
        self.assertEqual(m.snapshot()["gateway"].samples, 5)
        self.assertIn('wexum_vpn_probe_total{service="gateway",result="success"} 200', m.render_prometheus())

    def test_concurrent_recording_no_lost_totals(self):
        m = HealthMonitor(min_samples=1, max_samples_per_service=200)
        threads = [threading.Thread(target=lambda: [m.record("gateway", True, 0.001) for _ in range(100)]) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertIn('wexum_vpn_probe_total{service="gateway",result="success"} 800', m.render_prometheus())
        self.assertLessEqual(m.snapshot()["gateway"].samples, 200)

    def test_unwatched_services_do_not_raise_missing_telemetry(self):
        engine = AlertEngine(self.monitor, watched_services=("gateway",))
        self.assertEqual({x.service for x in engine.evaluate()}, {"gateway"})
        with self.assertRaises(ValueError):
            AlertEngine(self.monitor, watched_services=("untrusted-user",))

    def test_bad_configuration_rejected(self):
        for params in ({"window_seconds": math.inf}, {"target_slo": 1}, {"min_samples": 0}, {"failure_threshold": 0}, {"max_samples_per_service": 0}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                HealthMonitor(**params)


class ProbeTests(unittest.TestCase):
    def test_trusted_probe_success_and_failure_no_host_export(self):
        clock = FakeClock()
        monitor = HealthMonitor(clock=clock, min_samples=1)
        sock = Mock()
        target = ProbeTarget("gateway", "node.internal.invalid", 443)
        ok = tcp_probe(target, monitor, clock=clock, connector=Mock(return_value=sock))
        self.assertTrue(ok)
        sock.close.assert_called_once()
        failed = tcp_probe(target, monitor, clock=clock, connector=Mock(side_effect=OSError("address private-secret.local")))
        self.assertFalse(failed)
        exposition = monitor.render_prometheus()
        self.assertNotIn("internal.invalid", exposition)
        self.assertNotIn("private-secret", exposition)
        self.assertIn('result="failure"} 1', exposition)

    def test_no_catching_programming_bugs(self):
        monitor = HealthMonitor()
        target = ProbeTarget("gateway", "node.internal.invalid", 443)
        with self.assertRaises(RuntimeError):
            tcp_probe(target, monitor, connector=Mock(side_effect=RuntimeError("broken adapter")))

    def test_config_validation(self):
        for options in ({"host": ""}, {"port": 0}, {"port": 65536}, {"timeout_seconds": -1}, {"service": "device_123"}):
            config = dict(service="gateway", host="internal.invalid", port=443)
            config.update(options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                ProbeTarget(**config)


class ResourceTests(unittest.TestCase):
    def test_real_readings_nonnegative(self):
        r = read_resources()
        self.assertGreaterEqual(r.process_cpu_seconds, 0)
        self.assertGreaterEqual(r.disk_total_bytes, r.disk_free_bytes)
        if r.process_rss_bytes is not None:
            self.assertGreaterEqual(r.process_rss_bytes, 0)

    def test_missing_mount_errors_instead_of_making_up_zero(self):
        with self.assertRaises(FileNotFoundError):
            read_resources(disk_path="/path/that/cannot/exist/for/wexum/observability")


if __name__ == "__main__":
    unittest.main()
