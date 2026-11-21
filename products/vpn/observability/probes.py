"""Explicit technical checks. TCP handshake is not VPN tunnel or DNS leak proof."""

from dataclasses import dataclass
import math
import re
import socket
import time
from typing import Callable

from .health import HealthMonitor, SERVICES


@dataclass(frozen=True)
class ProbeTarget:
    service: str
    host: str
    port: int
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        if not isinstance(self.service, str) or self.service not in SERVICES:
            raise ValueError("unknown service category")
        if not isinstance(self.host, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,253}", self.host) is None:
            raise ValueError("invalid operator-configured host")
        if not isinstance(self.port, int) or isinstance(self.port, bool) or not 1 <= self.port <= 65535:
            raise ValueError("invalid TCP port")
        if not isinstance(self.timeout_seconds, (int, float)) or isinstance(self.timeout_seconds, bool) or not math.isfinite(self.timeout_seconds) or not 0 < self.timeout_seconds <= 10:
            raise ValueError("timeout must be in (0, 10] seconds")


def tcp_probe(
    target: ProbeTarget,
    monitor: HealthMonitor,
    *,
    clock: Callable[[], float] = time.monotonic,
    connector: Callable[..., socket.socket] = socket.create_connection,
) -> bool:
    """Probe only explicitly configured infrastructure; discard connection details.

    DNS resolution may exceed the socket connect timeout; external scheduling must
    bound concurrent probes and wall time. No target/exception is logged or exported.
    """
    if not isinstance(target, ProbeTarget):
        raise TypeError("target must be ProbeTarget")
    start = clock()
    if not math.isfinite(start):
        raise ValueError("invalid clock")
    try:
        connection = connector((target.host, target.port), timeout=target.timeout_seconds)
        connection.close()
        success = True
    except OSError:
        success = False
    duration = clock() - start
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("invalid elapsed time")
    monitor.record(target.service, success, duration)
    return success
