"""Fail-closed monotonic clock fault tests for a process-local OAuth transaction store."""

import math
import unittest

from wexum_identity.transactions import (
    AuthorizationClockUnavailable,
    AuthorizationRejected,
    AuthorizationTransactions,
)


CONFIG = dict(
    browser_session="trusted-server-issued-browser-binding",
    issuer="https://issuer.example.test",
    client_id="wexum-client",
    redirect_uri="https://app.example.test/callback",
)


class ClockFaultTests(unittest.TestCase):
    def setUp(self):
        self.reading = [1000.0]
        self.store = AuthorizationTransactions(clock=lambda: self.reading[0], max_pending=1)

    def consume(self, start):
        return self.store.consume(
            state=start.state,
            response_issuer=CONFIG["issuer"],
            **CONFIG,
        )

    def test_finite_equal_or_increasing_clock_still_allows_normal_flow(self):
        first = self.store.begin(**CONFIG)
        self.consume(first)
        self.reading[0] += 1.5
        second = self.store.begin(**CONFIG)
        self.assertNotEqual(first.state, second.state)
        self.consume(second)

    def test_nonfinite_clock_rejects_begin_and_fresh_attempt_can_restart(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.reading[0] = value
                with self.assertRaises(AuthorizationClockUnavailable):
                    self.store.begin(**CONFIG)
                self.reading[0] = 1000.0
                self.consume(self.store.begin(**CONFIG))

    def test_nonfinite_during_callback_discards_pending_state(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                self.reading[0] = 1000.0
                start = self.store.begin(**CONFIG)
                self.reading[0] = value
                with self.assertRaises(AuthorizationClockUnavailable):
                    self.consume(start)
                self.reading[0] = 1000.0
                with self.assertRaises(AuthorizationRejected):
                    self.consume(start)

    def test_backward_clock_purges_state_instead_of_extending_ttl(self):
        first = self.store.begin(**CONFIG)
        self.reading[0] = 999.0
        with self.assertRaises(AuthorizationClockUnavailable):
            self.consume(first)
        self.reading[0] = 1000.0
        with self.assertRaises(AuthorizationRejected):
            self.consume(first)
        self.consume(self.store.begin(**CONFIG))

    def test_bad_clock_type_is_fail_closed(self):
        for value in (None, False, "1000", (), object()):
            with self.subTest(value=type(value).__name__):
                self.reading[0] = 1000.0
                previous = self.store.begin(**CONFIG)
                self.reading[0] = value
                with self.assertRaises(AuthorizationClockUnavailable):
                    self.consume(previous)
                self.reading[0] = 1000.0
                with self.assertRaises(AuthorizationRejected):
                    self.consume(previous)

    def test_clock_exception_is_sanitized_and_does_not_preserve_state(self):
        class BrokenClock:
            def __init__(self):
                self.fails = False
            def __call__(self):
                if self.fails:
                    raise RuntimeError("untrusted secret text")
                return 1000.0
        clock = BrokenClock()
        store = AuthorizationTransactions(clock=clock)
        state = store.begin(**CONFIG)
        clock.fails = True
        with self.assertRaises(AuthorizationClockUnavailable) as caught:
            store.consume(state=state.state, response_issuer=CONFIG["issuer"], **CONFIG)
        self.assertNotIn("untrusted secret text", str(caught.exception))
        clock.fails = False
        with self.assertRaises(AuthorizationRejected):
            store.consume(state=state.state, response_issuer=CONFIG["issuer"], **CONFIG)

    def test_unrepresentable_expiry_rejected_instead_of_never_expiring(self):
        self.reading[0] = 1e308
        with self.assertRaises(AuthorizationClockUnavailable):
            self.store.begin(**CONFIG)
        self.reading[0] = 1000.0
        self.consume(self.store.begin(**CONFIG))


if __name__ == "__main__":
    unittest.main()
