"""Composed boundary tests: parser + single-use state consumption, no HTTP/OIDC."""

import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import threading
import unittest

from wexum_identity import (
    AuthorizationRejected,
    AuthorizationResponseRejected,
    AuthorizationTransactions,
    prepare_code_exchange,
)


CONFIG = {
    "browser_session": "server-issued-session-A",
    "issuer": "https://identity.example.test/tenant",
    "client_id": "wexum-vpn",
    "redirect_uri": "https://vpn.example.test/oauth/callback",
}


class PreExchangeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.now = [5000.0]
        self.store = AuthorizationTransactions(clock=lambda: self.now[0])
        self.started = self.store.begin(**CONFIG)

    def pairs(self, **changes):
        fields = {
            "state": self.started.state,
            "code": "untrusted-authorization-code",
            "iss": CONFIG["issuer"],
        }
        fields.update(changes)
        return list(fields.items())

    def prepare(self, pairs=None, **trusted_config):
        return prepare_code_exchange(
            self.store,
            decoded_pairs=self.pairs() if pairs is None else pairs,
            **{**CONFIG, **trusted_config},
        )

    def test_complete_handoff_preserves_trusted_provider_and_pkce(self):
        handoff = self.prepare()
        self.assertEqual(handoff.authorization_code, "untrusted-authorization-code")
        self.assertEqual(handoff.issuer, CONFIG["issuer"])
        self.assertEqual(handoff.client_id, CONFIG["client_id"])
        self.assertEqual(handoff.redirect_uri, CONFIG["redirect_uri"])
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(handoff.code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(challenge, self.started.code_challenge)
        self.assertEqual(handoff.expected_nonce, self.started.nonce)

    def test_handoff_repr_does_not_expose_code_verifier_or_nonce(self):
        handoff = self.prepare()
        for secret in (handoff.authorization_code, handoff.code_verifier, handoff.expected_nonce):
            self.assertNotIn(secret, repr(handoff))
        self.assertNotIn(self.started.state, repr(handoff))

    def test_replay_denied_after_successful_preparation(self):
        self.prepare()
        with self.assertRaises(AuthorizationRejected):
            self.prepare()

    def test_duplicate_callback_field_does_not_consume_state(self):
        for name in ("state", "code", "iss", "custom"):
            pairs = self.pairs()
            if name == "custom":
                pairs.append(("custom", "first"))
            pairs.append((name, "second"))
            with self.subTest(name=name), self.assertRaises(AuthorizationResponseRejected):
                self.prepare(pairs=pairs)
        self.prepare()

    def test_error_and_mixed_error_response_do_not_consume(self):
        cases = (
            [("state", self.started.state), ("error", "access_denied"), ("iss", CONFIG["issuer"])],
            [*self.pairs(), ("error", "server_error")],
        )
        for case in cases:
            with self.assertRaises(AuthorizationResponseRejected):
                self.prepare(pairs=case)
        self.prepare()

    def test_missing_callback_fields_do_not_consume_state(self):
        for missing in ("state", "code", "iss"):
            with self.subTest(missing=missing), self.assertRaises(AuthorizationResponseRejected):
                self.prepare(pairs=[(k, v) for k, v in self.pairs() if k != missing])
        self.prepare()

    def test_wrong_response_issuer_fails_without_consuming(self):
        with self.assertRaises(AuthorizationRejected):
            self.prepare(pairs=self.pairs(iss="https://different.example.test"))
        self.prepare()

    def test_wrong_browser_session_fails_without_consuming(self):
        with self.assertRaises(AuthorizationRejected):
            self.prepare(browser_session="another-session")
        self.prepare()

    def test_wrong_client_and_redirect_fail_without_consuming(self):
        with self.assertRaises(AuthorizationRejected):
            self.prepare(client_id="wexum-hub")
        with self.assertRaises(AuthorizationRejected):
            self.prepare(redirect_uri="https://hub.example.test/callback")
        self.prepare()

    def test_cross_application_callback_never_consumes_other_client_state(self):
        hub = {**CONFIG, "client_id": "wexum-hub", "redirect_uri": "https://hub.example.test/oauth"}
        hub_start = self.store.begin(**hub)
        with self.assertRaises(AuthorizationRejected):
            self.prepare(pairs=[("state", hub_start.state), ("code", "hub-code"), ("iss", CONFIG["issuer"])])
        handoff = prepare_code_exchange(
            self.store,
            decoded_pairs=[("state", hub_start.state), ("code", "hub-code"), ("iss", CONFIG["issuer"])],
            **hub,
        )
        self.assertEqual(handoff.client_id, "wexum-hub")
        self.prepare()

    def test_expiry_fails_closed_without_creating_exchange(self):
        self.now[0] += 300
        with self.assertRaises(AuthorizationRejected):
            self.prepare()

    def test_session_rotation_discard_denies_old_callback(self):
        self.assertEqual(self.store.discard_pending_for_session(browser_session=CONFIG["browser_session"]), 1)
        with self.assertRaises(AuthorizationRejected):
            self.prepare()

    def test_unrelated_extension_is_allowed_without_changing_security_binding(self):
        handoff = self.prepare(pairs=[*self.pairs(), ("ext", "unverified")])
        self.assertEqual(handoff.issuer, CONFIG["issuer"])
        self.assertEqual(handoff.expected_nonce, self.started.nonce)

    def test_malformed_callback_rejection_is_generic_and_has_no_secret(self):
        code = "very-sensitive-authorization-code"
        pairs = [*self.pairs(code=code), ("state", "duplicated")]
        with self.assertRaises(AuthorizationResponseRejected) as failure:
            self.prepare(pairs=pairs)
        self.assertNotIn(code, str(failure.exception))
        self.assertNotIn(self.started.state, str(failure.exception))
        self.prepare()

    def test_parallel_preparation_only_one_receives_code_and_verifier(self):
        workers = 10
        gate = threading.Barrier(workers)

        def attempt(_):
            gate.wait(timeout=5)
            try:
                self.prepare()
                return True
            except AuthorizationRejected:
                return False

        with ThreadPoolExecutor(max_workers=workers) as pool:
            outcomes = list(pool.map(attempt, range(workers)))
        self.assertEqual(sum(outcomes), 1)
        with self.assertRaises(AuthorizationRejected):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
