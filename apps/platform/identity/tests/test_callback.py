"""Negative and positive tests for the untrusted OAuth callback boundary."""

import unittest

from wexum_identity.callback import (
    AuthorizationResponseRejected,
    parse_authorization_callback,
)


VALID = [
    ("state", "opaque-state"),
    ("code", "opaque-code"),
    ("iss", "https://identity.example.test/tenant"),
]


class CallbackParsingTests(unittest.TestCase):
    def test_success_fields_and_secret_redaction(self):
        result = parse_authorization_callback(VALID)
        self.assertEqual(result.state, "opaque-state")
        self.assertEqual(result.code, "opaque-code")
        self.assertEqual(result.response_issuer, "https://identity.example.test/tenant")
        self.assertNotIn(result.state, repr(result))
        self.assertNotIn(result.code, repr(result))

    def test_tolerates_unrecognized_single_extension(self):
        self.assertEqual(
            parse_authorization_callback([*VALID, ("vendor_ext", "anything")]).code,
            "opaque-code",
        )

    def test_optional_extension_may_be_empty(self):
        self.assertEqual(
            parse_authorization_callback([*VALID, ("vendor_empty", "")]).state,
            "opaque-state",
        )

    def test_duplicate_sensitive_and_extension_parameters_rejected(self):
        for key in ("state", "code", "iss", "custom"):
            base = VALID if key != "custom" else [*VALID, ("custom", "one")]
            with self.subTest(key=key), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback([*base, (key, "another")])

    def test_error_response_and_ambiguous_success_error_rejected(self):
        for pairs in (
            [("error", "access_denied"), ("state", "opaque-state"), ("iss", "https://identity.example.test")],
            [*VALID, ("error", "access_denied")],
        ):
            with self.subTest(pairs=pairs), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback(pairs)

    def test_missing_fields_rejected(self):
        for key in ("code", "state", "iss"):
            with self.subTest(key=key), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback([(k, v) for k, v in VALID if k != key])

    def test_wrong_transport_shape_rejected(self):
        cases = ({"state": "opaque-state", "code": "opaque-code", "iss": "https://example.test"},
                 iter(VALID), None, "state=x", [], ["state=x"], [("state",)],
                 [("state", "value", "extra")])
        for item in cases:
            with self.subTest(item=repr(item)), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback(item)

    def test_oversized_or_nonprinting_fields_rejected(self):
        for pairs in (
            [*VALID, ("big", "A" * 4097)],
            [*VALID, ("many", "Ä" * 4096), ("more", "a")],
            [*VALID, ("\x00", "value")],
            [*VALID, ("unknown", "line\nbreak")],
            [("state", " "), *VALID[1:]],
            [("code", ""), *[pair for pair in VALID if pair[0] != "code"]],
            [*VALID, *[(f"ext{x}", "1") for x in range(30)]],
        ):
            with self.subTest(pairs=repr(pairs)[:100]), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback(pairs)

    def test_invalid_rfc9207_issuer_rejected(self):
        issuers = (
            "http://identity.example.test", "https://identity.example.test?query=x",
            "https://identity.example.test#fragment", "https://identity.example.test#",
            "https://identity.example.test?", "https://x:y@identity.example.test",
            "not-a-url", "https://", "https://identity.example.test:bogus",
            "https://identity.example.test:0", " https://identity.example.test",
        )
        for issuer in issuers:
            with self.subTest(issuer=issuer), self.assertRaises(AuthorizationResponseRejected):
                parse_authorization_callback([*VALID[:2], ("iss", issuer)])

    def test_issuer_with_path_and_nonzero_port_allowed(self):
        self.assertEqual(
            parse_authorization_callback([*VALID[:2], ("iss", "https://issuer.example.test:8443/tenant")]).response_issuer,
            "https://issuer.example.test:8443/tenant",
        )


if __name__ == "__main__":
    unittest.main()
