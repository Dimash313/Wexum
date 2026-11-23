"""Positive and negative checks for the WexumVPN proposed UX contract."""

import copy
import json
import unittest

from validate_contract import CONTRACT_FILE, validate


class VPNUXContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))

    def state(self, identifier: str) -> dict:
        return next(s for s in self.data["states"] if s["id"] == identifier)

    def test_reference_contract_is_valid(self):
        validate(self.data)

    def test_no_prototype_protection_claim(self):
        self.assertFalse(self.state("prototype_unavailable")["protection_claim"])
        self.assertEqual(self.data["default_state"], "prototype_unavailable")

    def test_all_nonverified_states_deny_protection(self):
        for state in self.data["states"]:
            with self.subTest(state=state["id"]):
                if state["id"] != "verified_connected":
                    self.assertFalse(state["protection_claim"])

    def test_permission_approval_cannot_claim_protection(self):
        self.state("permission_required")["protection_claim"] = True
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_os_connected_only_cannot_claim_protection(self):
        self.state("connected_unverified")["protection_claim"] = True
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_verified_state_requires_all_proofs(self):
        self.state("verified_connected")["minimum_evidence"].pop()
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_verified_gate_requires_native_tunnel(self):
        self.data["verified_evidence"].remove("os_tunnel_active")
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_verified_gate_requires_device_nonrevocation(self):
        self.data["verified_evidence"].remove("device_not_revoked")
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_runtime_capability_gates_cannot_be_dropped(self):
        self.data["runtime_feature_gates"].remove("independent_security_review")
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_no_faked_success_from_permission(self):
        edge = next(t for t in self.data["transitions"]
                    if t["from"] == "permission_required" and t["event"] == "permission_granted")
        edge["to"] = "verified_connected"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_no_faked_success_from_animation(self):
        self.data["transitions"].append({
            "from": "connecting", "event": "animation_finished",
            "to": "verified_connected", "source": "user",
        })
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_untrusted_engine_event_cannot_verify_connection(self):
        edge = next(t for t in self.data["transitions"] if t["to"] == "verified_connected")
        edge["source"] = "user"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_proof_trigger_cannot_be_reused_for_unverified_state(self):
        edge = next(t for t in self.data["transitions"] if t["to"] == "verified_connected")
        edge["to"] = "connected_unverified"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_prototype_activation_requires_trusted_service(self):
        for source in ("user", "native_os", "trusted_identity", "trusted_provider"):
            with self.subTest(source=source):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"]
                            if t["event"] == "engine_integrated_and_preconditions_ready")
                edge["source"] = source
                with self.assertRaises(ValueError):
                    validate(data)

    def test_prototype_activation_cannot_skip_lifecycle(self):
        for origin, target in (("signed_out", "disconnected"),
                               ("prototype_unavailable", "verified_connected")):
            with self.subTest(origin=origin, target=target):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"]
                            if t["event"] == "engine_integrated_and_preconditions_ready")
                edge["from"] = origin
                edge["to"] = target
                with self.assertRaises(ValueError):
                    validate(data)

    def test_engine_failure_requires_trusted_service_and_exact_edge(self):
        for source in ("user", "native_os", "trusted_identity", "trusted_entitlement", "trusted_nodes", "trusted_provider"):
            with self.subTest(source=source):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == "engine_failed")
                edge["source"] = source
                with self.assertRaises(ValueError):
                    validate(data)
        for origin, target in (("disconnected", "error"), ("connecting", "disconnected")):
            with self.subTest(origin=origin, target=target):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == "engine_failed")
                edge["from"] = origin
                edge["to"] = target
                with self.assertRaises(ValueError):
                    validate(data)

    def test_engine_lifecycle_provenance_rejects_untrusted_sources_and_wrong_edges(self):
        for event, expected_target in (("engine_channel_lost", "interrupted"),
                                       ("reassertion_started", "reconnecting")):
            for source in ("user", "native_os", "trusted_identity",
                           "trusted_entitlement", "trusted_nodes", "trusted_provider"):
                with self.subTest(event=event, source=source):
                    data = copy.deepcopy(self.data)
                    edge = next(x for x in data["transitions"] if x["event"] == event)
                    edge["source"] = source
                    with self.assertRaises(ValueError):
                        validate(data)
            for origin, target in (("connecting", expected_target),
                                   ("verified_connected", "disconnected")):
                with self.subTest(event=event, origin=origin, target=target):
                    data = copy.deepcopy(self.data)
                    edge = next(x for x in data["transitions"] if x["event"] == event)
                    edge["from"] = origin
                    edge["to"] = target
                    with self.assertRaises(ValueError):
                        validate(data)

    def test_engine_lifecycle_provenance_accepts_trusted_service(self):
        for event in ("engine_channel_lost", "reassertion_started"):
            with self.subTest(event=event):
                data = copy.deepcopy(self.data)
                edge = next(x for x in data["transitions"] if x["event"] == event)
                edge["source"] = "trusted_service"
                validate(data)

    def test_engine_failure_accepts_trusted_service(self):
        data = copy.deepcopy(self.data)
        edge = next(t for t in data["transitions"] if t["event"] == "engine_failed")
        edge["source"] = "trusted_service"
        validate(data)

    def test_os_permission_events_reject_non_os_sources(self):
        for event in ("permission_missing", "permission_granted", "permission_denied"):
            for source in ("user", "trusted_identity", "trusted_entitlement",
                           "trusted_nodes", "trusted_service", "trusted_provider"):
                with self.subTest(event=event, source=source):
                    data = copy.deepcopy(self.data)
                    edge = next(t for t in data["transitions"] if t["event"] == event)
                    edge["source"] = source
                    with self.assertRaises(ValueError):
                        validate(data)

    def test_os_permission_events_accept_native_os(self):
        for event in ("permission_missing", "permission_granted", "permission_denied"):
            with self.subTest(event=event):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == event)
                edge["source"] = "native_os"
                validate(data)

    def test_identity_lifecycle_requires_trusted_identity(self):
        for event in ("sign_in_required", "sign_in_complete"):
            for source in ("user", "native_os", "trusted_entitlement", "trusted_service", "trusted_provider", "trusted_nodes"):
                with self.subTest(event=event, source=source):
                    data = copy.deepcopy(self.data)
                    edge = next(t for t in data["transitions"] if t["event"] == event)
                    edge["source"] = source
                    with self.assertRaises(ValueError):
                        validate(data)

    def test_identity_lifecycle_accepts_trusted_identity(self):
        for event in ("sign_in_required", "sign_in_complete"):
            with self.subTest(event=event):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == event)
                edge["source"] = "trusted_identity"
                validate(data)

    def test_entitlement_lifecycle_events_require_trusted_source(self):
        for event in ("grant_revoked", "grant_expired", "entitlement_check_failed"):
            for source in ("user", "native_os", "trusted_identity", "trusted_service", "trusted_provider"):
                with self.subTest(event=event, source=source):
                    data = copy.deepcopy(self.data)
                    edge = next(t for t in data["transitions"] if t["event"] == event)
                    edge["source"] = source
                    with self.assertRaises(ValueError):
                        validate(data)

    def test_entitlement_lifecycle_events_accept_trusted_source(self):
        for event in ("grant_revoked", "grant_expired", "entitlement_check_failed"):
            with self.subTest(event=event):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == event)
                edge["source"] = "trusted_entitlement"
                validate(data)

    def test_service_stopped_requires_trusted_service(self):
        for source in ("user", "native_os", "trusted_provider"):
            with self.subTest(source=source):
                data = copy.deepcopy(self.data)
                edge = next(t for t in data["transitions"] if t["event"] == "service_stopped")
                edge["source"] = source
                with self.assertRaises(ValueError):
                    validate(data)

    def test_verified_snapshot_requires_active_attempt_origin(self):
        for origin in ("prototype_unavailable", "signed_out", "disconnected",
                       "offline", "revoked", "subscription_expired", "error"):
            with self.subTest(origin=origin):
                data = copy.deepcopy(self.data)
                data["transitions"].append({
                    "from": origin, "event": "fresh_verified_snapshot",
                    "to": "verified_connected", "source": "trusted_provider",
                })
                with self.assertRaises(ValueError):
                    validate(data)

    def test_recovery_and_restart_cannot_assert_tunnel_stopped(self):
        for origin, event in (("interrupted", "network_restored"), ("verified_connected", "app_restarted")):
            with self.subTest(origin=origin, event=event):
                data = copy.deepcopy(self.data)
                edge = next(x for x in data["transitions"] if x["from"] == origin and x["event"] == event)
                edge["to"] = "disconnected"
                with self.assertRaises(ValueError):
                    validate(data)

    def test_error_retry_never_certifies_teardown(self):
        edge = next(t for t in self.data["transitions"]
                    if t["from"] == "error" and t["event"] == "retry")
        self.assertEqual(edge["to"], "interrupted")
        self.assertFalse(self.state("interrupted")["protection_claim"])
        edge["to"] = "disconnected"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_connecting_failure_cannot_claim_disconnected(self):
        data = copy.deepcopy(self.data)
        edge = next(t for t in data["transitions"]
                    if t["from"] == "connecting" and t["event"] == "engine_failed")
        edge["to"] = "disconnected"
        with self.assertRaises(ValueError):
            validate(data)

    def test_restart_cannot_default_connected(self):
        self.data["default_state"] = "verified_connected"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_unknown_state_is_rejected(self):
        self.data["states"].append(copy.deepcopy(self.state("error")))
        self.data["states"][-1]["id"] = "fake_protected"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_duplicate_transitions_are_rejected(self):
        self.data["transitions"].append(copy.deepcopy(self.data["transitions"][0]))
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_only_disconnected_can_expose_connect_action(self):
        self.state("offline")["primary_action"] = "connect"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_status_keys_are_namespaced(self):
        self.state("revoked")["status_key"] = "protected"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_claim_gate_cannot_be_declared_approved(self):
        self.data["status"] = "approved"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_forbidden_trigger_list_cannot_be_dropped(self):
        self.data["explicitly_forbidden_claim_triggers"].remove("cached_snapshot")
        with self.assertRaises(ValueError):
            validate(self.data)


if __name__ == "__main__":
    unittest.main()
