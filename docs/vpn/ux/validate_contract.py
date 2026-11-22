"""Validate the proposed WexumVPN UX state documentation; not a VPN runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTRACT_FILE = Path(__file__).with_name("connection_states.json")

REQUIRED_STATES = frozenset({
    "prototype_unavailable", "signed_out", "permission_required",
    "permission_denied", "disconnected", "connecting",
    "connected_unverified", "verified_connected", "reconnecting",
    "disconnecting", "interrupted", "offline", "subscription_expired",
    "access_check_unavailable", "revoked", "no_nodes", "error",
})
PROOFS = frozenset({
    "os_tunnel_active", "authenticated_engine_session",
    "same_attempt_and_generation", "fresh_authoritative_entitlement",
    "device_not_revoked", "network_path_current",
    "verified_route_and_dns_policy",
})
GATES = frozenset({
    "actual_connect_engine", "authoritative_entitlement",
    "real_node_registry", "independent_security_review",
    "network_and_dns_leak_device_tests",
})
ACTIONS = frozenset({
    "none", "sign_in", "request_permission", "open_settings",
    "connect", "cancel", "disconnect", "retry", "manage_subscription",
})
SOURCES = frozenset({
    "user", "native_os", "trusted_identity", "trusted_entitlement",
    "trusted_nodes", "trusted_service", "trusted_provider",
})
FORBIDDEN = frozenset({
    "permission_granted", "native_connected_unverified", "network_restored",
    "animation_finished", "timer_elapsed", "cached_snapshot", "ui_toggle",
})


def _fail(message: str) -> None:
    raise ValueError(message)


def _unique_strings(values: Any, label: str) -> set[str]:
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        _fail(f"{label}: expected nonempty string list")
    if len(set(values)) != len(values):
        _fail(f"{label}: duplicate entry")
    return set(values)


def validate(data: Any) -> None:
    if not isinstance(data, dict) or data.get("schema") != 1:
        _fail("unsupported contract schema")
    if data.get("status") != "proposed":
        _fail("must remain a proposed UX specification")
    if data.get("default_state") != "prototype_unavailable":
        _fail("prototype must default to unavailable, never to connected")
    if data.get("verified_state") != "verified_connected":
        _fail("verified state identifier has changed")
    if _unique_strings(data.get("verified_evidence"), "proofs") != PROOFS:
        _fail("verified evidence is incomplete or changed")
    if _unique_strings(data.get("runtime_feature_gates"), "gates") != GATES:
        _fail("runtime feature release gates are incomplete")
    if _unique_strings(data.get("explicitly_forbidden_claim_triggers"), "forbidden") != FORBIDDEN:
        _fail("forbidden claim triggers were weakened")

    states = data.get("states")
    if not isinstance(states, list):
        _fail("states must be a list")
    ids: list[str] = []
    protected_count = 0
    for state in states:
        if not isinstance(state, dict):
            _fail("state must be an object")
        identifier = state.get("id")
        if not isinstance(identifier, str):
            _fail("state id must be a string")
        ids.append(identifier)
        if state.get("status_key") != f"vpn.status.{identifier}":
            _fail(f"{identifier}: invalid status translation key")
        if state.get("detail_key") != f"vpn.detail.{identifier}":
            _fail(f"{identifier}: invalid detail translation key")
        action = state.get("primary_action")
        if action not in ACTIONS:
            _fail(f"{identifier}: invalid action")
        if action == "connect" and identifier != "disconnected":
            _fail("connect action allowed only in disconnected")
        claim = state.get("protection_claim")
        if type(claim) is not bool or claim != (identifier == "verified_connected"):
            _fail(f"{identifier}: unjustified protection claim")
        expected_proof = PROOFS if claim else frozenset()
        if _unique_strings(state.get("minimum_evidence"), f"{identifier} proofs") != expected_proof:
            _fail(f"{identifier}: incorrect evidence requirements")
        if claim:
            protected_count += 1
    if set(ids) != REQUIRED_STATES or len(ids) != len(REQUIRED_STATES) or protected_count != 1:
        _fail("states absent, duplicated, extra or protection claim invalid")

    transitions = data.get("transitions")
    if not isinstance(transitions, list) or not transitions:
        _fail("transitions must be a nonempty list")
    seen: set[tuple[str, str]] = set()
    for transition in transitions:
        if not isinstance(transition, dict):
            _fail("transition must be an object")
        origin = transition.get("from")
        target = transition.get("to")
        event = transition.get("event")
        source = transition.get("source")
        if origin not in REQUIRED_STATES or target not in REQUIRED_STATES:
            _fail("transition references unknown state")
        if not isinstance(event, str) or not event.strip():
            _fail("transition requires event name")
        if source not in SOURCES:
            _fail("unknown or untrusted event source")
        key = (origin, event)
        if key in seen:
            _fail("ambiguous duplicate transition")
        seen.add(key)
        if target == "disconnected" and origin in {"interrupted", "verified_connected", "connected_unverified", "reconnecting", "disconnecting"} and event != "service_stopped":
            _fail("tunnel lifecycle cannot assert disconnected without trusted stop acknowledgement")
        if event == "service_stopped" and (origin != "disconnecting" or target != "disconnected" or source != "trusted_service"):
            _fail("service stop acknowledgement requires trusted service and disconnecting origin")
        if event == "engine_integrated_and_preconditions_ready" and (
            origin != "prototype_unavailable" or target != "disconnected" or source != "trusted_service"
        ):
            _fail("prototype activation requires trusted service and exact lifecycle edge")
        if target == "verified_connected":
            if origin not in {"connecting", "connected_unverified", "reconnecting"}:
                _fail("verified state requires an active connection attempt origin")
            if event != "fresh_verified_snapshot" or source != "trusted_provider":
                _fail("verified state requires authenticated, fresh combined proof")
        elif event == "fresh_verified_snapshot":
            _fail("verified proof event must target verified state")
        if event in FORBIDDEN and target == "verified_connected":
            _fail("forbidden event creates a protection claim")
    if not any(t["to"] == "verified_connected" for t in transitions):
        _fail("verified-state transition guard is untestable")


def main() -> None:
    validate(json.loads(CONTRACT_FILE.read_text(encoding="utf-8")))
    print("WexumVPN UX proposed state contract: valid")


if __name__ == "__main__":
    main()
