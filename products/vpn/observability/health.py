"""Bounded aggregate probe observations; never accepts customer-derived labels."""

from collections import deque
from dataclasses import dataclass
from enum import Enum
import math
from threading import RLock
import time
from typing import Callable

# These names are operator-owned component categories, not node, device, user or IP IDs.
SERVICES = frozenset({"control_plane", "node_registry", "entitlements", "identity", "gateway"})


class HealthState(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    STALE = "stale"


@dataclass(frozen=True)
class HealthSummary:
    service: str
    state: HealthState
    samples: int
    successes: int
    failures: int
    availability: float | None
    error_budget_used: float | None
    last_sample_age_seconds: float | None


class HealthMonitor:
    """Process-local, bounded rolling window of *observed* technical probe outcomes.

    Does not monitor user connections, packets, URLs, devices, countries or identities.
    The caller is assumed to be a trusted management-plane adapter. No network endpoint
    or authentication is provided here. Only the local clock determines observation age.
    """

    def __init__(
        self,
        *,
        window_seconds: float = 300.0,
        stale_after_seconds: float = 90.0,
        min_samples: int = 5,
        max_samples_per_service: int = 1000,
        failure_threshold: int = 3,
        target_slo: float = 0.99,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not (math.isfinite(window_seconds) and window_seconds > 0):
            raise ValueError("window_seconds must be positive and finite")
        if not (math.isfinite(stale_after_seconds) and 0 < stale_after_seconds <= window_seconds):
            raise ValueError("stale_after_seconds must be within the window")
        if not (isinstance(min_samples, int) and not isinstance(min_samples, bool) and 1 <= min_samples <= max_samples_per_service):
            raise ValueError("invalid min_samples")
        if not (isinstance(max_samples_per_service, int) and not isinstance(max_samples_per_service, bool) and max_samples_per_service > 0):
            raise ValueError("invalid max_samples_per_service")
        if not (isinstance(failure_threshold, int) and not isinstance(failure_threshold, bool) and failure_threshold > 0):
            raise ValueError("invalid failure_threshold")
        if not (math.isfinite(target_slo) and 0 < target_slo < 1):
            raise ValueError("target_slo must be between zero and one")
        self.window_seconds = window_seconds
        self.stale_after_seconds = stale_after_seconds
        self.min_samples = min_samples
        self.failure_threshold = failure_threshold
        self.target_slo = target_slo
        self.clock = clock
        self._lock = RLock()
        self._window = {name: deque(maxlen=max_samples_per_service) for name in SERVICES}
        self._totals = {name: [0, 0, 0.0] for name in SERVICES}  # ok, fail, elapsed sum

    @staticmethod
    def _validate_service(service: str) -> None:
        if not isinstance(service, str) or service not in SERVICES:
            raise ValueError("service must be a configured, fixed category")

    def record(self, service: str, success: bool, duration_seconds: float) -> None:
        self._validate_service(service)
        if type(success) is not bool:
            raise TypeError("success must be boolean")
        if not isinstance(duration_seconds, (float, int)) or isinstance(duration_seconds, bool) or not math.isfinite(duration_seconds) or duration_seconds < 0:
            raise ValueError("duration_seconds must be finite and nonnegative")
        with self._lock:
            now = self.clock()
            if not math.isfinite(now):
                raise ValueError("invalid monotonic clock")
            self._evict(service, now)
            entries = self._window[service]
            if entries and now < entries[-1][0]:
                raise ValueError("monotonic clock moved backwards")
            entries.append((now, success))
            totals = self._totals[service]
            totals[0 if success else 1] += 1
            totals[2] += float(duration_seconds)

    def _evict(self, service: str, now: float) -> None:
        entries = self._window[service]
        while entries and now - entries[0][0] >= self.window_seconds:
            entries.popleft()

    def _summary(self, service: str, now: float) -> HealthSummary:
        self._evict(service, now)
        entries = self._window[service]
        if not entries:
            return HealthSummary(service, HealthState.UNKNOWN, 0, 0, 0, None, None, None)
        age = max(0.0, now - entries[-1][0])
        good = sum(int(success) for _, success in entries)
        count = len(entries)
        failed = count - good
        availability = good / count if count >= self.min_samples else None
        budget = (failed / count) / (1 - self.target_slo) if availability is not None else None
        consecutive = 0
        for _, success in reversed(entries):
            if success:
                break
            consecutive += 1
        if age >= self.stale_after_seconds:
            state = HealthState.STALE
        elif consecutive >= self.failure_threshold:
            state = HealthState.DOWN
        elif availability is None:
            state = HealthState.UNKNOWN
        elif not entries[-1][1] or budget is not None and budget > 1:
            state = HealthState.DEGRADED
        else:
            state = HealthState.HEALTHY
        return HealthSummary(service, state, count, good, failed, availability, budget, age)

    def snapshot(self) -> dict[str, HealthSummary]:
        with self._lock:
            now = self.clock()
            if not math.isfinite(now):
                raise ValueError("invalid monotonic clock")
            return {service: self._summary(service, now) for service in sorted(SERVICES)}

    def render_prometheus(self) -> str:
        """Text exposition only. Caller must secure the transport and endpoint."""
        with self._lock:
            now = self.clock()
            if not math.isfinite(now):
                raise ValueError("invalid monotonic clock")
            snapshot = {service: self._summary(service, now) for service in sorted(SERVICES)}
            totals = {key: tuple(values) for key, values in self._totals.items()}
        lines = [
            "# HELP wexum_vpn_probe_total Completed management-plane probe attempts.",
            "# TYPE wexum_vpn_probe_total counter",
        ]
        for service in sorted(SERVICES):
            ok, failed, elapsed = totals[service]
            lines.append(f'wexum_vpn_probe_total{{service="{service}",result="success"}} {ok}')
            lines.append(f'wexum_vpn_probe_total{{service="{service}",result="failure"}} {failed}')
        lines.extend([
            "# HELP wexum_vpn_probe_duration_seconds_sum Accumulated probe wall-clock durations.",
            "# TYPE wexum_vpn_probe_duration_seconds_sum counter",
        ])
        for service in sorted(SERVICES):
            lines.append(f'wexum_vpn_probe_duration_seconds_sum{{service="{service}"}} {totals[service][2]:.9g}')
        lines.extend([
            "# HELP wexum_vpn_probe_window_samples Current bounded observation sample count.",
            "# TYPE wexum_vpn_probe_window_samples gauge",
            "# HELP wexum_vpn_probe_state Current local observation status (not tunnel uptime).",
            "# TYPE wexum_vpn_probe_state gauge",
        ])
        for service in sorted(SERVICES):
            summary = snapshot[service]
            lines.append(f'wexum_vpn_probe_window_samples{{service="{service}"}} {summary.samples}')
            for state in HealthState:
                lines.append(f'wexum_vpn_probe_state{{service="{service}",state="{state.value}"}} {int(summary.state == state)}')
        lines.extend([
            "# HELP wexum_vpn_probe_success_ratio Sampled probe success ratio; absent without minimum observations.",
            "# TYPE wexum_vpn_probe_success_ratio gauge",
        ])
        for service in sorted(SERVICES):
            ratio = snapshot[service].availability
            if ratio is not None:
                lines.append(f'wexum_vpn_probe_success_ratio{{service="{service}"}} {ratio:.9g}')
        return "\n".join(lines) + "\n"
