"""Deterministic, deduplicated alert state; no notification or user tracking."""

from dataclasses import dataclass
from threading import RLock
from .health import HealthMonitor, HealthState, SERVICES


@dataclass(frozen=True)
class AlertTransition:
    service: str
    code: str
    active: bool


class AlertEngine:
    """Only emits changes to technical alert states; delivery is a future adapter."""

    def __init__(self, monitor: HealthMonitor, *, watched_services: tuple[str, ...]) -> None:
        if not watched_services or any(name not in SERVICES for name in watched_services):
            raise ValueError("configure at least one known service to watch")
        self.watched_services = frozenset(watched_services)
        self.monitor = monitor
        self._lock = RLock()
        self._active: set[tuple[str, str]] = set()

    def evaluate(self) -> list[AlertTransition]:
        snapshots = self.monitor.snapshot()
        current: set[tuple[str, str]] = set()
        for service, summary in snapshots.items():
            if service not in self.watched_services:
                continue
            if summary.state in (HealthState.UNKNOWN, HealthState.STALE):
                current.add((service, "telemetry_missing"))
            if summary.state == HealthState.DOWN:
                current.add((service, "probe_failures"))
            if summary.error_budget_used is not None and summary.error_budget_used > 1:
                current.add((service, "sample_error_budget_exhausted"))
        with self._lock:
            opened = current - self._active
            resolved = self._active - current
            self._active = current
            return [AlertTransition(service, code, True) for service, code in sorted(opened)] + [AlertTransition(service, code, False) for service, code in sorted(resolved)]
