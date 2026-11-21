import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import re
import threading
import unittest

from wexum_identity import (
    AuthorizationCapacityExceeded,
    AuthorizationRejected,
    AuthorizationTransactions,
)


CONFIG = dict(
    browser_session="server-issued-browser-session-a",
    issuer="https://identity.example.test",
    client_id="wexum-vpn",
    redirect_uri="https://vpn.example.test/callback",
)


class OAuthTransactionTests(unittest.TestCase):
    def setUp(self):
        self.now = [1000.0]
        self.transactions = AuthorizationTransactions(clock=lambda: self.now[0])

    def start(self):
        return self.transactions.begin(**CONFIG)

    def consume(self, start, **updates):
        params = {**CONFIG, "state": start.state, "response_issuer": CONFIG["issuer"]}
        params.update(updates)
        return self.transactions.consume(**params)

    def test_pkce_s256_and_oidc_nonce(self):
        start = self.start()
        proof = self.consume(start)
        self.assertEqual(start.code_challenge_method, "S256")
        self.assertTrue(re.fullmatch(r"[A-Za-z0-9_-]{43,128}", proof.code_verifier))
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(proof.code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        self.assertEqual(start.code_challenge, expected_challenge)
        self.assertEqual(start.nonce, proof.expected_nonce)
        self.assertNotEqual(start.state, start.nonce)
        self.assertNotIn(proof.code_verifier, repr(start))

    def test_nonce_state_and_verifier_are_unique(self):
        first = self.start()
        second = self.start()
        first_context = self.consume(first)
        second_context = self.consume(second)
        self.assertNotEqual(first.state, second.state)
        self.assertNotEqual(first.nonce, second.nonce)
        self.assertNotEqual(first_context.code_verifier, second_context.code_verifier)

    def test_callback_is_single_use(self):
        start = self.start()
        self.consume(start)
        with self.assertRaises(AuthorizationRejected):
            self.consume(start)

    def test_browser_session_mismatch_denied_without_consuming(self):
        start = self.start()
        with self.assertRaises(AuthorizationRejected):
            self.consume(start, browser_session="different-browser-session")
        self.consume(start)

    def test_wrong_issuer_and_response_issuer_denied(self):
        start = self.start()
        for change in ({"issuer": "https://evil.example.test"},
                       {"response_issuer": "https://evil.example.test"},
                       {"response_issuer": ""}):
            with self.assertRaises(AuthorizationRejected):
                self.consume(start, **change)
        self.consume(start)

    def test_cross_client_and_redirect_denied(self):
        start = self.start()
        with self.assertRaises(AuthorizationRejected):
            self.consume(start, client_id="wexum-hub")
        with self.assertRaises(AuthorizationRejected):
            self.consume(start, redirect_uri="https://hub.example.test/callback")
        self.consume(start)

    def test_expired_transaction_is_not_recovered(self):
        start = self.start()
        self.now[0] += 300
        with self.assertRaises(AuthorizationRejected):
            self.consume(start)

    def test_small_global_capacity_gets_safe_default_per_session_cap(self):
        registry = AuthorizationTransactions(clock=lambda: self.now[0], max_pending=1)
        registry.begin(**CONFIG)
        with self.assertRaises(AuthorizationCapacityExceeded):
            registry.begin(**CONFIG)

    def test_expiry_frees_bounded_capacity(self):
        registry = AuthorizationTransactions(clock=lambda: self.now[0], max_pending=1, ttl_seconds=3)
        registry.begin(**CONFIG)
        with self.assertRaises(AuthorizationCapacityExceeded):
            registry.begin(**CONFIG)
        self.now[0] += 3
        registry.begin(**CONFIG)

    def test_per_browser_capacity_isolated_from_other_sessions(self):
        registry = AuthorizationTransactions(
            clock=lambda: self.now[0], max_pending=5, max_pending_per_session=2
        )
        first = registry.begin(**CONFIG)
        second = registry.begin(**CONFIG)
        with self.assertRaises(AuthorizationCapacityExceeded):
            registry.begin(**CONFIG)
        other = {**CONFIG, "browser_session": "other-server-issued-session"}
        registry.begin(**other)
        registry.consume(**{**CONFIG, "state": first.state, "response_issuer": CONFIG["issuer"]})
        registry.begin(**CONFIG)
        with self.assertRaises(AuthorizationCapacityExceeded):
            registry.begin(**CONFIG)
        self.assertNotEqual(first.state, second.state)

    def test_session_capacity_frees_on_expiry(self):
        registry = AuthorizationTransactions(
            clock=lambda: self.now[0], ttl_seconds=2,
            max_pending=10, max_pending_per_session=1
        )
        registry.begin(**CONFIG)
        with self.assertRaises(AuthorizationCapacityExceeded):
            registry.begin(**CONFIG)
        self.now[0] += 2
        registry.begin(**CONFIG)

    def test_session_limit_configuration_rejected_when_invalid(self):
        for invalid in (0, -1, True, 4, 1.0):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                AuthorizationTransactions(max_pending=3, max_pending_per_session=invalid)

    def test_parallel_begin_respects_session_capacity(self):
        registry = AuthorizationTransactions(
            clock=lambda: self.now[0], max_pending=100, max_pending_per_session=3
        )
        count = 12
        gate = threading.Barrier(count)

        def try_begin(_):
            gate.wait(timeout=5)
            try:
                registry.begin(**CONFIG)
                return True
            except AuthorizationCapacityExceeded:
                return False

        with ThreadPoolExecutor(max_workers=count) as pool:
            outcomes = list(pool.map(try_begin, range(count)))
        self.assertEqual(sum(outcomes), 3)

    def test_repr_redacts_sensitive_authorization_fields(self):
        start = self.start()
        self.assertNotIn(start.state, repr(start))
        self.assertNotIn(start.nonce, repr(start))
        context = self.consume(start)
        self.assertNotIn(context.code_verifier, repr(context))
        self.assertNotIn(context.expected_nonce, repr(context))
        self.assertEqual(context.expected_nonce, start.nonce)

    def test_discard_is_scoped_to_original_browser_session(self):
        first = self.start()
        second = self.start()
        another_session = {**CONFIG, "browser_session": "a-different-server-session"}
        unrelated = self.transactions.begin(**another_session)
        self.assertEqual(
            self.transactions.discard_pending_for_session(browser_session=CONFIG["browser_session"]),
            2,
        )
        self.assertEqual(
            self.transactions.discard_pending_for_session(browser_session=CONFIG["browser_session"]),
            0,
        )
        for start in (first, second):
            with self.assertRaises(AuthorizationRejected):
                self.consume(start)
        self.transactions.consume(**{
            **another_session, "state": unrelated.state, "response_issuer": CONFIG["issuer"]
        })
        # Upstream must revoke the actual browser session; this store alone cannot.
        self.start()

    def test_discard_rejects_invalid_session_without_mutation(self):
        start = self.start()
        for bad in (None, 17, "", " ", " invalid "):
            with self.assertRaises(ValueError):
                self.transactions.discard_pending_for_session(browser_session=bad)
        self.consume(start)

    def test_discard_and_consume_race_never_replays(self):
        start = self.start()
        gate = threading.Barrier(2)

        def consume():
            gate.wait(timeout=5)
            try:
                self.consume(start)
                return True
            except AuthorizationRejected:
                return False

        def discard():
            gate.wait(timeout=5)
            return self.transactions.discard_pending_for_session(
                browser_session=CONFIG["browser_session"]
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(consume)
            b = pool.submit(discard)
            won, discarded = a.result(), b.result()
        self.assertEqual(int(won) + discarded, 1)
        with self.assertRaises(AuthorizationRejected):
            self.consume(start)

    def test_malformed_untrusted_callback_denied(self):
        start = self.start()
        for bad in (None, 23, "", " ", "state invalid "):
            with self.assertRaises(AuthorizationRejected):
                self.consume(start, state=bad)
        self.consume(start)

    def test_untrusted_or_empty_server_configuration_denied(self):
        for key in CONFIG:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.transactions.begin(**{**CONFIG, key: " "})
        with self.assertRaises(ValueError):
            AuthorizationTransactions(ttl_seconds=0)
        with self.assertRaises(ValueError):
            AuthorizationTransactions(max_pending=0)

    def test_restart_fails_closed_instead_of_resuming_unknown_state(self):
        start = self.start()
        replacement = AuthorizationTransactions(clock=lambda: self.now[0])
        with self.assertRaises(AuthorizationRejected):
            replacement.consume(**{**CONFIG, "state": start.state, "response_issuer": CONFIG["issuer"]})

    def test_atomic_callback_race_only_one_succeeds(self):
        start = self.start()
        count = 12
        gate = threading.Barrier(count)

        def try_consume(_):
            gate.wait(timeout=5)
            try:
                self.consume(start)
                return True
            except AuthorizationRejected:
                return False

        with ThreadPoolExecutor(max_workers=count) as pool:
            results = list(pool.map(try_consume, range(count)))
        self.assertEqual(sum(results), 1)


if __name__ == "__main__":
    unittest.main()
