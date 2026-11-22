"""Synthetic observations test only the offline classifier, NOT a VPN tunnel."""

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from leak_evidence import ExpectedPath, ProbeEvidence, Verdict, assess


class EvidenceClassifierTests(unittest.TestCase):
    def setUp(self):
        self.expected = ExpectedPath(
            ipv4_egress=frozenset({'198.51.100.7'}),
            ipv6_egress=frozenset({'2001:db8::7'}),
            dns_resolvers=frozenset({'192.0.2.53'}),
            ipv6_probe_required=True,
        )
        self.observed = ProbeEvidence(
            tunnel_reported=True, route_enforced=True,
            ipv4_egress=frozenset({'198.51.100.7'}),
            ipv6_egress=frozenset({'2001:db8::7'}),
            dns_resolvers=frozenset({'192.0.2.53'}),
        )

    def test_matching_synthetic_evidence_is_only_consistent(self):
        result = assess(self.expected, self.observed)
        self.assertEqual(result.verdict, Verdict.CONSISTENT)
        self.assertEqual(result.reasons, ())

    def test_disconnected_fails_even_when_addresses_match(self):
        result = assess(self.expected, replace(self.observed, tunnel_reported=False))
        self.assertEqual(result.verdict, Verdict.REJECTED)
        self.assertIn('tunnel_not_reported', result.reasons)

    def test_no_route_proof_rejected(self):
        result = assess(self.expected, replace(self.observed, route_enforced=False))
        self.assertIn('route_not_verified', result.reasons)

    def test_unapproved_ipv4_egress_rejected(self):
        result = assess(self.expected, replace(self.observed, ipv4_egress=frozenset({'203.0.113.12'})))
        self.assertIn('unexpected_ipv4_egress', result.reasons)

    def test_unapproved_ipv6_egress_rejected(self):
        result = assess(self.expected, replace(self.observed, ipv6_egress=frozenset({'2001:db8::8'})))
        self.assertIn('unexpected_ipv6_egress', result.reasons)

    def test_unapproved_dns_resolver_rejected(self):
        result = assess(self.expected, replace(self.observed, dns_resolvers=frozenset({'203.0.113.53'})))
        self.assertIn('unexpected_dns_resolver', result.reasons)

    def test_no_ipv6_probe_is_incomplete_not_success(self):
        result = assess(self.expected, replace(self.observed, ipv6_egress=frozenset()))
        self.assertEqual(result.verdict, Verdict.INCOMPLETE)
        self.assertIn('missing_ipv6_probe', result.reasons)

    def test_missing_ipv4_dns_probes_are_incomplete(self):
        result = assess(self.expected, replace(self.observed, ipv4_egress=frozenset(), dns_resolvers=frozenset()))
        self.assertEqual(result.verdict, Verdict.INCOMPLETE)
        self.assertCountEqual(result.reasons, ['missing_ipv4_probe', 'missing_dns_probe'])

    def test_ipv6_disabled_rejects_any_observed_ipv6(self):
        expectation = replace(self.expected, ipv6_egress=frozenset(), ipv6_probe_required=False)
        self.assertIn('unexpected_ipv6_egress', assess(expectation, self.observed).reasons)

    def test_invalid_or_ambiguous_inputs_fail(self):
        invalid = [
            replace(self.expected, ipv4_egress=frozenset({'not-an-ip'})),
            replace(self.expected, ipv4_egress=frozenset({'2001:db8::1'})),
            replace(self.expected, dns_resolvers=frozenset()),
            replace(self.expected, ipv6_egress=frozenset()),
            replace(self.expected, ipv6_probe_required=1),
        ]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                assess(item, self.observed)

    def test_unspecified_or_multicast_expected_addresses_fail_closed(self):
        invalid = [
            replace(self.expected, ipv4_egress=frozenset({'0.0.0.0'})),
            replace(self.expected, ipv4_egress=frozenset({'224.0.0.1'})),
            replace(self.expected, ipv6_egress=frozenset({'::'})),
            replace(self.expected, ipv6_egress=frozenset({'ff02::1'})),
            replace(self.expected, dns_resolvers=frozenset({'0.0.0.0'})),
            replace(self.expected, dns_resolvers=frozenset({'ff02::1'})),
        ]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                assess(item, self.observed)

    def test_unspecified_or_multicast_observed_addresses_fail_closed(self):
        invalid = [
            replace(self.observed, ipv4_egress=frozenset({'0.0.0.0'})),
            replace(self.observed, ipv6_egress=frozenset({'ff02::1'})),
            replace(self.observed, dns_resolvers=frozenset({'224.0.0.251'})),
        ]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                assess(self.expected, item)

    def test_noncanonical_ip_inputs_fail(self):
        altered = replace(self.observed, ipv6_egress=frozenset({'2001:0db8::7'}))
        with self.assertRaises(ValueError):
            assess(self.expected, altered)


if __name__ == '__main__':
    unittest.main()
