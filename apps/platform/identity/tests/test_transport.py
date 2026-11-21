"""Transport-decoding and composed state-binding security regression tests."""

from concurrent.futures import ThreadPoolExecutor
import threading
import unittest

from wexum_identity import (
    AuthorizationRejected,
    AuthorizationResponseRejected,
    AuthorizationTransactions,
    prepare_code_exchange,
)
from wexum_identity.transport import decode_callback_pairs


CONFIG = {
    "browser_session": "trusted-server-session",
    "issuer": "https://id.example.test/org",
    "client_id": "wexum-vpn",
    "redirect_uri": "https://vpn.example.test/oauth/callback",
}


class CallbackTransportTests(unittest.TestCase):
    def setUp(self):
        self.store = AuthorizationTransactions()
        self.start = self.store.begin(**CONFIG)
        self.query = (
            f"state={self.start.state}&code=untrusted-code&iss=https%3A%2F%2Fid.example.test%2Forg"
        ).encode("ascii")

    def get(self, raw=Ellipsis, **changes):
        params = {
            "method": "GET", "response_mode": "query",
            "query_string": self.query if raw is Ellipsis else raw,
        }
        params.update(changes)
        return decode_callback_pairs(**params)

    def post(self, raw=Ellipsis, **changes):
        params = {
            "method": "POST", "response_mode": "form_post",
            "content_type": "application/x-www-form-urlencoded",
            "body": self.query if raw is Ellipsis else raw,
        }
        params.update(changes)
        return decode_callback_pairs(**params)

    def prepare(self, pairs):
        return prepare_code_exchange(self.store, decoded_pairs=pairs, **CONFIG)

    def test_valid_query_get_composes_into_single_use_exchange(self):
        exchange = self.prepare(self.get())
        self.assertEqual(exchange.issuer, CONFIG["issuer"])
        self.assertEqual(exchange.authorization_code, "untrusted-code")
        with self.assertRaises(AuthorizationRejected):
            self.prepare(self.get())

    def test_valid_form_post_composes_into_single_use_exchange(self):
        exchange = self.prepare(self.post())
        self.assertEqual(exchange.expected_nonce, self.start.nonce)
        with self.assertRaises(AuthorizationRejected):
            self.prepare(self.post())

    def test_utf8_percent_encoded_unrecognized_extension(self):
        pairs = self.get(self.query + b"&label=%D0%A2%D0%B5%D1%81%D1%82")
        self.assertIn(("label", "Тест"), pairs)
        self.prepare(pairs)

    def test_encoding_alias_duplicate_is_rejected_before_consumption(self):
        for extra in (b"&%73tate=bad", b"&co%64e=bad", b"&i%73s=https%3A%2F%2Fevil.test"):
            with self.subTest(extra=extra), self.assertRaises(AuthorizationResponseRejected):
                self.prepare(self.get(self.query + extra))
        self.prepare(self.get())

    def test_raw_transport_mixing_and_wrong_methods_denied(self):
        cases = [
            (self.get, {"body": b"code=overridden"}),
            (self.get, {"content_type": "application/x-www-form-urlencoded"}),
            (self.get, {"method": "POST"}),
            (self.get, {"response_mode": "form_post"}),
            (self.post, {"query_string": b"tracking=1"}),
            (self.post, {"method": "GET"}),
            (self.post, {"response_mode": "query"}),
            (self.post, {"content_type": "text/plain"}),
            (self.post, {"content_type": None}),
            (self.post, {"content_type": "application/json"}),
            (self.post, {"content_type": "application/x-www-form-urlencoded; charset=iso-8859-1"}),
        ]
        for function, changes in cases:
            with self.subTest(changes=changes), self.assertRaises(AuthorizationResponseRejected):
                function(**changes)
        self.prepare(self.get())

    def test_form_post_content_type_utf8_allowed(self):
        pairs = self.post(content_type="application/x-www-form-urlencoded; charset=UTF-8")
        self.prepare(pairs)

    def test_invalid_raw_types_rejected(self):
        for bad in (None, "state=abc", bytearray(self.query), memoryview(self.query), 27):
            with self.subTest(bad=type(bad).__name__), self.assertRaises(AuthorizationResponseRejected):
                self.get(bad)
        with self.assertRaises(AuthorizationResponseRejected):
            self.post(body=None)
        self.prepare(self.get())

    def test_bad_percent_encoding_fails_closed(self):
        for bad in (b"%", b"%0", b"%ZZ", b"%GG", b"%%41", b"%Aq", b"%u0041"):
            with self.subTest(bad=bad), self.assertRaises(AuthorizationResponseRejected):
                self.get(self.query + b"&vendor=" + bad)
        self.prepare(self.get())

    def test_invalid_utf8_fails_closed(self):
        for bad in (b"%FF", b"%C0%AF", b"%E2%28%A1", b"%ED%A0%80", b"%00"):
            with self.subTest(bad=bad), self.assertRaises(AuthorizationResponseRejected):
                self.prepare(self.get(self.query + b"&x=" + bad))
        self.prepare(self.get())

    def test_forbidden_raw_control_unicode_and_fragment(self):
        for bad in (b"\n", b"\r", b"\t", b"\x00", b"\x7f", b"\x80", b"#fragment"):
            with self.subTest(bad=bad), self.assertRaises(AuthorizationResponseRejected):
                self.get(self.query + b"&x=" + bad)
        self.prepare(self.get())

    def test_empty_bare_and_extra_delimiters_rejected(self):
        for bad in (self.query + b"&", b"&" + self.query, self.query + b"&&x=1", self.query + b"&flag", self.query + b"&=1", b""):
            with self.subTest(bad=bad[:40]), self.assertRaises(AuthorizationResponseRejected):
                self.get(bad)
        self.prepare(self.get())

    def test_limits_before_or_after_decoding(self):
        for raw in (b"x=" + b"A" * 8192, self.query + b"&long=" + b"A" * 8192,
                    self.query + b"&" + b"&".join(b"a%d=1" % n for n in range(40))):
            with self.subTest(length=len(raw)), self.assertRaises(AuthorizationResponseRejected):
                self.prepare(self.get(raw))
        self.prepare(self.get())

    def test_extension_empty_value_and_plus_encoded_value(self):
        pairs = self.get(self.query + b"&blank=&extension=hello+world%2B")
        self.assertEqual(pairs[-2:], (("blank", ""), ("extension", "hello world+")))
        self.prepare(pairs)

    def test_replayed_raw_query_cannot_create_second_exchange(self):
        self.prepare(self.get())
        with self.assertRaises(AuthorizationRejected):
            self.prepare(self.get())

    def test_wrong_response_issuer_in_transport_does_not_consume_original(self):
        pairs = self.get(self.query.replace(b"id.example.test", b"evil.example.test"))
        with self.assertRaises(AuthorizationRejected):
            self.prepare(pairs)
        self.prepare(self.get())

    def test_transport_parse_failure_exposes_no_auth_code(self):
        secret = "SENSITIVE-CODE-EXAMPLE"
        with self.assertRaises(AuthorizationResponseRejected) as ctx:
            self.get(self.query.replace(b"untrusted-code", secret.encode()) + b"&oops=%")
        self.assertNotIn(secret, str(ctx.exception))
        self.prepare(self.get())

    def test_parallel_valid_raw_callbacks_have_one_winner(self):
        n = 8
        barrier = threading.Barrier(n)

        def attempt(_):
            pairs = self.get()
            barrier.wait(timeout=5)
            try:
                self.prepare(pairs)
                return True
            except AuthorizationRejected:
                return False

        with ThreadPoolExecutor(max_workers=n) as pool:
            outcomes = list(pool.map(attempt, range(n)))
        self.assertEqual(sum(outcomes), 1)


if __name__ == "__main__":
    unittest.main()
