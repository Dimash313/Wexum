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
