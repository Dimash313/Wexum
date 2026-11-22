# Proposal: cross-lane VPN security contracts for CTO decision

**Status:** security engineering **decision request**, not an accepted ADR, implementable API or deployed system. Owned by #11, written only in `docs/vpn/security/`. 2026-11-21 inspection. CTO/integrator owns approval of shared contracts; #2/#3/#4/#8/#9/#10/#34 implement only in their own lanes. Independent auditor remains separate.

## Actual source inspected

- [Control Plane #55](https://github.com/Dimash313/Wexum/pull/55), head `66532b4df984c091b46e53697218b82557bb4bbd`: no trusted public auth adapter; unresolved owner-list truncation and SQLite open-error mapping.
- [Entitlements #64](https://github.com/Dimash313/Wexum/pull/64), head `8acebae483a146c5adf68bd82ba4c440f01e3e7f`: `GrantCandidate` precheck only; **not** a signed node grant. Author reports 40 local tests, not production integration.
- [Node Registry #65](https://github.com/Dimash313/Wexum/pull/65), head `5103d986323767c4457a941a058c877ffd0083f1`: generation/registration ID is intended to prevent stale probe observations, **not** probe authentication or persistent distributed fencing.
- [Observability #72](https://github.com/Dimash313/Wexum/pull/72), head `bfff09382ab5b11df2366c77b67a9ac224ab1b38`: fixed category-only metrics and operator-configured TCP probes. No authenticated probe writers or allowlisted network target source; probe success is not tunnel integrity. Source static review described below.
- [Billing #73](https://github.com/Dimash313/Wexum/pull/73), head `bff44a49fa024b2df4d87d4bf0ac557b3856bcd8`: verified-event ledger uses a **test-only** HMAC adapter and operator-approved `allow_test_adapters`; no vendor webhook/receipt validation or signed grants.
- [QA #74](https://github.com/Dimash313/Wexum/pull/74), head `0404c3fa1d4f9023a1b03bb1e412c8555a4f0036`: offline IPv4/IPv6/DNS observation classifier marks `CONSISTENT` only for submitted data, expressly **not** source authenticity or actual tunnel proof. Reported QA: 11 leak-classifier tests pass; 13 Control Plane tests skipped on main-only checkout.
- [Identity #62](https://github.com/Dimash313/Wexum/pull/62), head `76de9d8e803ec206ab0d6abbd5ca9fff63ff222a`: OAuth transaction boundary only; no actual verified OIDC session, public token verification or VPN actor adapter.
- Proposed foundational contract from [PR #1](https://github.com/Dimash313/Wexum/pull/1) remains unmerged. None of the above is an integrated production deployment.

## Decisions requested (do not silently assume values)

| Decision | Required named owner(s) | Testable acceptance / forbidden shortcut |
| --- | --- | --- |
| **D1. Actor provenance** | CTO, Identity #34, Control #2 | Establish actor only from verified issuer, audience, expiry, session and tenant-scoped identity; reject caller-constructed actor, mismatched tenant, role or stale session |
| **D2. Grant wire format and trust** | CTO, Entitlements #3, Nodes #4 | Approve signed format, strict algorithm/key IDs, canonical serialization, size bounds and per-node audience; reject altered payload, unknown keys and cross-node grants |
| **D3. Device and session binding** | CTO, #2/#3/#4/#34 | Choose proof-of-possession/session mechanism, replay cache or equivalent; demonstrate denial of replay on a different device/session/tenant, including restarts/concurrency |
| **D4. Revocation consistency** | CTO, #2/#3/#4/#9 | Define refund/account-delete/device-revoke propagation, acknowledgement, persistence, offline grace and observable maximum exposure; deny new authorization on authority outage |
| **D5. Node identity/health** | CTO, #4/#8 | Authenticate management/probe writers and generation; prevent spoofed/stale health and discovery of nodes with no confirmed capacity; bind selection to fresh validated node generation |
| **D6. Real tunnel/privacy evidence** | CTO, client #5/#6/#7, QA #10 | Test actual OS network routing, DNS/IPv4/IPv6, split-tunnel exceptions, network transitions and permission revocation; synthetic reports are only preliminary |
| **D7. Provider/payment and retention** | CTO, #9/#8 | Live vendor signature verification, merchant/order binding, refunded access cutoff, collection/retention/processor inventory and scrubbed telemetry; never use the test HMAC adapter for live eligibility |
| **D8. Release authority** | CTO, independent auditor #41, #11 | Require reviewed exact commit hashes, mandatory green CI, independent artifact validation and legal/store/ethical reviews; `gate_check.py` cannot yield release clearance from supplied metadata |

## Additional static review finding for Observability (request negative regression, not independently executed)

**SEC-OBS-001 — preliminary LOW/MEDIUM reliability/security reporting risk; unconfirmed runtime repro.** At [`health.py` for PR #72](https://github.com/Dimash313/Wexum/blob/bfff09382ab5b11df2366c77b67a9ac224ab1b38/products/vpn/observability/health.py), `HealthMonitor.record()` rejects backwards time relative to last sample. But `snapshot()` calls `_summary()`, which computes `age=max(0, now-last_sample_time)`; if a custom/provisioned clock moves backward after recording successful samples, reading a snapshot may still report `HEALTHY` instead of unreliable/stale telemetry. The production default is `time.monotonic`, so realistic exploitability and severity are **unestablished**.

**Minimal negative test requested of #8 owner** (not run by #11):
1. Construct `HealthMonitor(clock=FakeClock, min_samples=3)`.
2. Clock = 100; record three successful gateway samples; assert HEALTHY.
3. Clock = 90 (before last sample); read `snapshot()['gateway'].state` and rendered metric status.
4. Require explicit invalid/unknown/degraded disposition or an error; do not describe stale/future evidence as healthy. Verify that recovery to monotonic time does not silently clear a genuine outage.

If #8 owner accepts the test, fix source in the #8 branch, rerun on exact corrected SHA and solicit independent reviewer confirmation. **No claim of customer traffic leakage or real deployed vulnerability** is made.

## Independent acceptance scenarios

- Refuse metadata-only/unsigned `GrantCandidate` as a VPN access credential.
- Deny spoofed issuer/device/node/tenant/session even if an upstream component erroneously claims eligibility.
- Handle deletion/re-registration probe replay despite generation rollover and process restart.
- Reject refund-before-purchase, duplicate/late webhooks and cross-tenant receipts at the *real vendor* boundary, not solely in test HMAC fixtures.
- Treat observed `CONSISTENT` egress classification as evidence awaiting trustworthy test execution provenance. The tester must record OS/build SHA, interface/routing state, expected DNS/IPv4/IPv6 sources, capture methodology and signed report identity.
- Transport failure, untrusted probe origin and clock anomaly must never create a false externally advertised `protected` state.
- During metadata-only test simulation, even an all-`attested` fabricated `release_gates.json` must fail the dedicated `--require-attested` CLI mode (separate external release authority is mandatory).

**No cross-lane code, root CI, issuer key, configuration or deployed resource is changed by this proposal.**
