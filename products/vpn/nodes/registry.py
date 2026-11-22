"""In-process VPN node inventory and verified-health snapshot selection.

This module performs no probing, authentication, networking, or persistence.
Only a trusted management-plane adapter may supply inventory and observations.
"""

from __future__ import annotations

import re
from secrets import token_hex
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from fractions import Fraction
from threading import RLock


_IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,63}\Z", re.ASCII)
_MAX_CAPABILITIES = 16
_REGISTRATION_ID = re.compile(r"[0-9a-f]{32}\Z", re.ASCII)


def _identifier(value: object, field: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase ASCII identifier (1..64 chars)")


def _capabilities(value: object) -> None:
    if not isinstance(value, frozenset) or len(value) > _MAX_CAPABILITIES:
        raise ValueError("capabilities must be a frozenset of at most 16 identifiers")
    for capability in value:
        _identifier(capability, "capability")


def _utc(value: object, field: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != timedelta(0)
    ):
        raise ValueError(f"{field} must be a timezone-aware UTC datetime")


def _integer(value: object, field: str, minimum: int, maximum: int) -> None:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{field} must be an integer in [{minimum}, {maximum}]")


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DOWN = "down"


class AvailabilityStatus(str, Enum):
    DISABLED = "disabled"
    UNREPORTED = "unreported"
    STALE = "stale"
    DOWN = "down"
    SATURATED = "saturated"
    HEALTHY = "healthy"


@dataclass(frozen=True, slots=True)
class Node:
    node_id: str
    region_id: str
    capabilities: frozenset[str]
    max_sessions: int
    enabled: bool = True

    def __post_init__(self) -> None:
        _identifier(self.node_id, "node_id")
        _identifier(self.region_id, "region_id")
        _capabilities(self.capabilities)
        _integer(self.max_sessions, "max_sessions", 1, 100_000)
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a boolean")


@dataclass(frozen=True, slots=True)
class HealthObservation:
    node_id: str
    registration_id: str
    status: HealthStatus
    observed_at: datetime
    active_sessions: int

    def __post_init__(self) -> None:
        _identifier(self.node_id, "node_id")
        if not isinstance(self.registration_id, str) or _REGISTRATION_ID.fullmatch(self.registration_id) is None:
            raise ValueError("registration_id must be 32 lowercase hex characters")
        if not isinstance(self.status, HealthStatus):
            raise ValueError("status must be a HealthStatus")
        _utc(self.observed_at, "observed_at")
        _integer(self.active_sessions, "active_sessions", 0, 1_000_000)


@dataclass(frozen=True, slots=True)
class NodeAvailability:
    node_id: str
    region_id: str
    status: AvailabilityStatus
    observed_at: datetime | None
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class NodeSelection:
    node_id: str
    registration_id: str
    region_id: str
    observed_at: datetime
    expires_at: datetime
    active_sessions: int
    max_sessions: int


class StaleObservationError(ValueError):
    """The observation is expired, replayed, or out of chronological order."""


class NodeRegistry:
    """Bounded, thread-safe inventory; discovery fails closed on missing health.

    Selection is only an advisory snapshot, not a VPN access permission. The
    control plane must independently check identity, grants, and fresh health.
    """

    def __init__(self, *, health_ttl_seconds: int = 30, max_nodes: int = 2048):
        _integer(health_ttl_seconds, "health_ttl_seconds", 1, 300)
        _integer(max_nodes, "max_nodes", 1, 10_000)
        self._ttl = timedelta(seconds=health_ttl_seconds)
        self._max_nodes = max_nodes
        self._nodes: dict[str, Node] = {}
        self._observations: dict[str, HealthObservation] = {}
        self._registrations: dict[str, str] = {}
        self._last_observed_at: dict[str, datetime] = {}
        self._lock = RLock()

    def register(self, node: Node) -> str:
        if not isinstance(node, Node):
            raise TypeError("node must be a Node")
        with self._lock:
            if node.node_id in self._nodes:
                raise ValueError("node_id is already registered")
            if len(self._nodes) >= self._max_nodes:
                raise ValueError("node registry capacity exceeded")
            registration_id = token_hex(16)
            self._nodes[node.node_id] = node
            self._registrations[node.node_id] = registration_id
            return registration_id

    def set_enabled(self, node_id: str, enabled: bool) -> str | None:
        _identifier(node_id, "node_id")
        if type(enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        with self._lock:
            previous = self._nodes[node_id]
            if previous.enabled != enabled:
                self._nodes[node_id] = Node(
                    previous.node_id,
                    previous.region_id,
                    previous.capabilities,
                    previous.max_sessions,
                    enabled,
                )
                # A new generation is required for a disabled node to become eligible.
                self._observations.pop(node_id, None)
                self._last_observed_at.pop(node_id, None)
                if enabled:
                    self._registrations[node_id] = token_hex(16)
            return self._registrations[node_id] if enabled else None

    def remove(self, node_id: str) -> None:
        _identifier(node_id, "node_id")
        with self._lock:
            del self._nodes[node_id]
            self._observations.pop(node_id, None)
            self._last_observed_at.pop(node_id, None)
            self._registrations.pop(node_id, None)

    def record_health(self, observation: HealthObservation, *, now: datetime) -> None:
        if not isinstance(observation, HealthObservation):
            raise TypeError("observation must be a HealthObservation")
        _utc(now, "now")
        age = now - observation.observed_at
        if age < timedelta(0) or age >= self._ttl:
            raise StaleObservationError("observation must be fresh and not from the future")
        try:
            observation.observed_at + self._ttl
        except OverflowError as exc:
            raise StaleObservationError("observation expiry is outside supported datetime range") from exc
        with self._lock:
            node = self._nodes.get(observation.node_id)
            if node is None:
                raise KeyError("unregistered node")
            if not node.enabled:
                raise ValueError("disabled node cannot receive health reports")
            if observation.registration_id != self._registrations[observation.node_id]:
                raise StaleObservationError("observation registration mismatch")
            last_at = self._last_observed_at.get(observation.node_id)
            if last_at is not None and observation.observed_at <= last_at:
                raise StaleObservationError("replayed or older observation")
            self._observations[observation.node_id] = observation
            self._last_observed_at[observation.node_id] = observation.observed_at

    def _availability(self, node: Node, now: datetime) -> NodeAvailability:
        observation = self._observations.get(node.node_id)
        observed_at = observation.observed_at if observation is not None else None
        expires_at = observed_at + self._ttl if observed_at is not None else None
        if not node.enabled:
            state = AvailabilityStatus.DISABLED
        elif observation is None:
            state = AvailabilityStatus.UNREPORTED
        elif now < observation.observed_at or now >= expires_at:
            state = AvailabilityStatus.STALE
        elif observation.status != HealthStatus.HEALTHY:
            state = AvailabilityStatus.DOWN
        elif observation.active_sessions >= node.max_sessions:
            state = AvailabilityStatus.SATURATED
        else:
            state = AvailabilityStatus.HEALTHY
        return NodeAvailability(node.node_id, node.region_id, state, observed_at, expires_at)

    def snapshot(self, *, now: datetime, limit: int = 100) -> tuple[NodeAvailability, ...]:
        _utc(now, "now")
        _integer(limit, "limit", 1, 200)
        with self._lock:
            return tuple(
                self._availability(self._nodes[node_id], now)
                for node_id in sorted(self._nodes)[:limit]
            )

    def select(
        self,
        *,
        now: datetime,
        region_id: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> NodeSelection | None:
        _utc(now, "now")
        if region_id is not None:
            _identifier(region_id, "region_id")
        _capabilities(required_capabilities)
        with self._lock:
            eligible: list[tuple[Fraction, str, Node, HealthObservation]] = []
            for node in self._nodes.values():
                if region_id is not None and node.region_id != region_id:
                    continue
                if not required_capabilities.issubset(node.capabilities):
                    continue
                if self._availability(node, now).status != AvailabilityStatus.HEALTHY:
                    continue
                observation = self._observations[node.node_id]
                eligible.append(
                    (Fraction(observation.active_sessions, node.max_sessions), node.node_id, node, observation)
                )
            if not eligible:
                return None
            _, _, selected, observation = min(eligible)
            return NodeSelection(
                selected.node_id,
                self._registrations[selected.node_id],
                selected.region_id,
                observation.observed_at,
                observation.observed_at + self._ttl,
                observation.active_sessions,
                selected.max_sessions,
            )

    def revalidate_selection(self, selection: NodeSelection, *, now: datetime) -> bool:
        """Check that a previous advisory selection is still exactly current.

        This atomic local comparison is not authorization or a capacity lease;
        the node can change again immediately after the method returns.
        """
        if not isinstance(selection, NodeSelection):
            raise TypeError("selection must be a NodeSelection")
        _utc(now, "now")
        with self._lock:
            node = self._nodes.get(selection.node_id)
            if node is None or self._availability(node, now).status != AvailabilityStatus.HEALTHY:
                return False
            observation = self._observations[node.node_id]
            return selection == NodeSelection(
                node.node_id,
                self._registrations[node.node_id],
                node.region_id,
                observation.observed_at,
                observation.observed_at + self._ttl,
                observation.active_sessions,
                node.max_sessions,
            )
