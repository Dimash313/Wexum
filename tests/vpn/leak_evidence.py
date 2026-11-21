"""Offline classification of VPN probe evidence; never performs network I/O.

A CONSISTENT result means only that provided observations match policy. It is
not proof of tunnel integrity, absence of leaks, or provenance of the probes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address


class Verdict(str, Enum):
    REJECTED = "rejected"
    INCOMPLETE = "incomplete"
    CONSISTENT = "consistent"


@dataclass(frozen=True)
class ExpectedPath:
    ipv4_egress: frozenset[str]
    ipv6_egress: frozenset[str]
    dns_resolvers: frozenset[str]
    ipv6_probe_required: bool


@dataclass(frozen=True)
class ProbeEvidence:
    tunnel_reported: bool
    route_enforced: bool
    ipv4_egress: frozenset[str]
    ipv6_egress: frozenset[str]
    dns_resolvers: frozenset[str]


@dataclass(frozen=True)
class Assessment:
    verdict: Verdict
    reasons: tuple[str, ...]


def _addresses(value: object, family: int | None, field: str) -> None:
    if not isinstance(value, frozenset):
        raise ValueError(f"{field} must be a frozenset")
    for raw in value:
        if not isinstance(raw, str):
            raise ValueError(f"{field} contains a non-string address")
        try:
            address = ip_address(raw)
        except ValueError as error:
            raise ValueError(f"{field} contains an invalid address") from error
        if family is not None and address.version != family:
            raise ValueError(f"{field} contains the wrong IP family")
        if str(address) != raw:
            raise ValueError(f"{field} must contain canonical IP addresses")


def assess(expected: ExpectedPath, observed: ProbeEvidence) -> Assessment:
    if not isinstance(expected, ExpectedPath) or not isinstance(observed, ProbeEvidence):
        raise TypeError("ExpectedPath and ProbeEvidence are required")
    for label, flag in (("ipv6_probe_required", expected.ipv6_probe_required),
                        ("tunnel_reported", observed.tunnel_reported),
                        ("route_enforced", observed.route_enforced)):
        if type(flag) is not bool:
            raise ValueError(f"{label} must be boolean")
    for source, name in ((expected, "expected"), (observed, "observed")):
        _addresses(source.ipv4_egress, 4, name + ".ipv4_egress")
        _addresses(source.ipv6_egress, 6, name + ".ipv6_egress")
        _addresses(source.dns_resolvers, None, name + ".dns_resolvers")
    if not expected.ipv4_egress or not expected.dns_resolvers:
        raise ValueError("expected IPv4 egress and DNS resolvers are mandatory")
    if expected.ipv6_probe_required and not expected.ipv6_egress:
        raise ValueError("IPv6 probe requires an explicit expected IPv6 egress")

    violations = []
    if not observed.tunnel_reported:
        violations.append("tunnel_not_reported")
    if not observed.route_enforced:
        violations.append("route_not_verified")
    if not observed.ipv4_egress.issubset(expected.ipv4_egress):
        violations.append("unexpected_ipv4_egress")
    if not observed.ipv6_egress.issubset(expected.ipv6_egress):
        violations.append("unexpected_ipv6_egress")
    if not observed.dns_resolvers.issubset(expected.dns_resolvers):
        violations.append("unexpected_dns_resolver")
    if violations:
        return Assessment(Verdict.REJECTED, tuple(violations))

    incomplete = []
    if not observed.ipv4_egress:
        incomplete.append("missing_ipv4_probe")
    if expected.ipv6_probe_required and not observed.ipv6_egress:
        incomplete.append("missing_ipv6_probe")
    if not observed.dns_resolvers:
        incomplete.append("missing_dns_probe")
    if incomplete:
        return Assessment(Verdict.INCOMPLETE, tuple(incomplete))
    return Assessment(Verdict.CONSISTENT, ())
