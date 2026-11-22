"""Security boundary tests for immutable, server-selected web OAuth settings."""

from dataclasses import FrozenInstanceError
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest
from urllib.parse import quote

from wexum_identity import (
    AuthorizationRejected,
    AuthorizationResponseRejected,
    AuthorizationTransactions,
)
from wexum_identity.webclient import ConfiguredWebOAuthClient


ISSUER = "https://id.example.test/realm"
CLIENT = ConfiguredWebOAuthClient(
    issuer=ISSUER,
    client_id="wexum-vpn",
    redirect_uri="https://vpn.example.test/oauth/callback",
)


class WebOAuthClientTests(unittest.TestCase):
    def setUp(self):
        self.transactions = AuthorizationTransactions()
        self.start = CLIENT.begin(self.transactions, browser_session="server-issued-browser-session")
        self.query = (
            f"state={self.start.state}&code=opaque-code&iss={quote(ISSUER, safe='')}"
        ).encode("ascii")

    def callback(self, client=CLIENT, **changes):
        kwargs = {
            "browser_session": "server-issued-browser-session",
            "method": "GET",
            "query_string": self.query,
        }
        kwargs.update(changes)
        return client.prepare_callback(self.transactions, **kwargs)

    def test_end_to_end_pinned_client_prepares_unverified_exchange(self):
        result = self.callback()
        self.assertEqual(result.issuer, ISSUER)
        self.assertEqual(result.client_id, CLIENT.client_id)
        self.assertEqual(result.redirect_uri, CLIENT.redirect_uri)
        self.assertEqual(result.expected_nonce, self.start.nonce)
        self.assertEqual(result.authorization_code, "opaque-code")

    def test_cannot_mutate_configuration_after_start(self):
        with self.assertRaises(FrozenInstanceError):
            CLIENT.issuer = "https://attacker.example.test"
        self.callback()

    def test_replay_cannot_reuse_exchanged_state(self):
        self.callback()
        with self.assertRaises(AuthorizationRejected):
            self.callback()

    def test_cross_client_even_same_issuer_and_session_rejected(self):
        different = ConfiguredWebOAuthClient(
            issuer=ISSUER,
            client_id="wexum-hub",
            redirect_uri="https://hub.example.test/oauth/callback",
        )
        with self.assertRaises(AuthorizationRejected):
            self.callback(different)
        self.callback()

    def test_wrong_browser_session_denied_without_burning(self):
        with self.assertRaises(AuthorizationRejected):
            self.callback(browser_session="attacker-browser")
        self.callback()

    def test_wrong_issuer_denied_without_burning(self):
        wrong = self.query.replace(b"id.example.test", b"attacker.example.test")
        with self.assertRaises(AuthorizationRejected):
            self.callback(query_string=wrong)
        self.callback()

    def test_mode_downgrade_rejected(self):
        with self.assertRaises(AuthorizationResponseRejected):
            self.callback(method="POST", body=self.query, query_string=b"", content_type="application/x-www-form-urlencoded")
        self.callback()

    def test_form_post_mode_requires_post_not_get(self):
        form = ConfiguredWebOAuthClient(
            issuer=ISSUER,
            client_id=CLIENT.client_id,
            redirect_uri=CLIENT.redirect_uri,
            response_mode="form_post",
        )
        with self.assertRaises(AuthorizationResponseRejected):
            self.callback(form)
        result = self.callback(
            form,
            method="POST",
            query_string=b"",
            body=self.query,
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(result.authorization_code, "opaque-code")

    def test_unsafe_issuers_rejected_at_configuration_time(self):
        invalid = (
            "http://id.example.test", "https://user@id.example.test",
            "https://id.example.test?login=1", "https://id.example.test#",
            "https://id.example.test:0", "https://id.example.test:bogus",
            "https://id.example.test:", "https://id.example.test\\@attacker.test",
            "https://%69d.example.test", "https://", "https://id.example.test/space here",
            "https://id.example.test/\n", "https://id.example.test:65536",
        )
        for issuer in invalid:
            with self.subTest(issuer=issuer), self.assertRaises(ValueError):
                ConfiguredWebOAuthClient(issuer=issuer, client_id="client", redirect_uri=CLIENT.redirect_uri)

    def test_unsafe_redirects_rejected_at_configuration_time(self):
        invalid = (
            "http://vpn.example.test/callback", "https://user@vpn.example.test/callback",
            "https://vpn.example.test/callback#fragment",
            "https://vpn.example.test/callback?static=1",
            "https://vpn.example.test/callback\\@bad.test",
            "javascript:alert(1)", "wexum://callback", "https://vpn.example.test:0/",
        )
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(ValueError):
                ConfiguredWebOAuthClient(issuer=ISSUER, client_id="client", redirect_uri=uri)

    def test_empty_or_untrusted_config_shapes_rejected(self):
        for client_id in (None, "", " ", 1, True, " x", "x\n"):
            with self.subTest(client_id=client_id), self.assertRaises(ValueError):
                ConfiguredWebOAuthClient(issuer=ISSUER, client_id=client_id, redirect_uri=CLIENT.redirect_uri)
        for mode in ("", None, True, "fragment", "form-post", "QUERY"):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                ConfiguredWebOAuthClient(issuer=ISSUER, client_id="client", redirect_uri=CLIENT.redirect_uri, response_mode=mode)

    def test_malformed_callback_cannot_burn_state(self):
        with self.assertRaises(AuthorizationResponseRejected):
            self.callback(query_string=self.query + b"&%73tate=duplicate")
        self.callback()

    def test_logout_discards_all_matching_pending_sessions(self):
        self.transactions.discard_pending_for_session(browser_session="server-issued-browser-session")
        with self.assertRaises(AuthorizationRejected):
            self.callback()

    def test_parallel_callbacks_only_one_exchange_context(self):
        gate = threading.Barrier(10)

        def worker(_):
            gate.wait(timeout=5)
            try:
                self.callback()
                return True
            except AuthorizationRejected:
                return False

        with ThreadPoolExecutor(max_workers=10) as executor:
            self.assertEqual(sum(executor.map(worker, range(10))), 1)


if __name__ == "__main__":
    unittest.main()
