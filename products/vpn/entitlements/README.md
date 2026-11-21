# WexumVPN — entitlement eligibility precheck (issue #3)

**Status: isolated prototype; no real VPN access is issued or enforced.** This work is deliberately not a token-signing service, entitlement database, payment verifier, OAuth verifier, HTTP endpoint, node verifier or VPN tunnel. It depends on no pending foundation files, and it changes no sibling lane or shared interface. Foundation PR #1 is unmerged and independent audit #41 is blocking integration.

## Boundary

The server-only GrantPrecheck.check(actor, device_id, scope) checks an already-verified actor from Identity, and fresh, authoritative account/subscription/device states retrieved through trusted backend adapters. It denies mismatched tenants/subjects, inactive or expired states, wrong scope/issuer/audience, expired sessions, malformed values, stale authority snapshots and failed/slow lookups. A returned GrantCandidate is **only a local eligibility result**, not an access credential, and MUST NOT be returned to a VPN client or accepted by a VPN node. No client can self-mint a usable permit with this code. Cryptographic signature verification has **not** been implemented and no proof-of-possession mechanism exists.

The caller MUST authenticate every upstream authority over a trusted service channel and construct AuthenticatedActor only from a real, verified Identity session. Test doubles are confined to tests. Never deserialize AuthenticatedActor, AccountState, SubscriptionState or DeviceState from a client request. The code cannot enforce this prerequisite and must not be wired to public requests before an independently reviewed adapter exists. Subscription truth must originate from the authoritative billing system and verified/reconciled webhooks, not from user input or a cached UI flag.

- **Fail closed:** every new eligibility check needs all three authority lookups; if any is down, malformed or outside the timeout, it cannot return a candidate. On adapter failure, other pending lookups are cancelled and joined before returning; caller cancellation propagates. Expired actors are denied before any authority IO. No indefinite offline access.
- **Adapter constraint:** backend adapters must be cancellation-cooperative and use their own network timeouts; Python cannot forcibly stop adapters that suppress cancellation. An authority that cancels itself is treated as unavailable.
- **Time:** validated timezone-aware timestamps; preflight account, subscription and device snapshot freshness <= 10 seconds with at most 5 seconds future-skew; maximum candidate TTL = 120 seconds, also bounded by actor, subscription and device expiration. These numbers are **provisional local policy**, not approved production revocation budgets.
- **Isolation:** candidate requires matching tenant and subject in all three server-owned records, exact device ID and scope. No client-supplied tenant overrides are read.
- **Read-only check:** there is no token ID, signature, gateway audience, proof of device key possession, atomic session lease, payment processing or replay prevention. Concurrent checks do not create any access; binding, atomic issuance and active session limits belong to separately approved control/node integration.
- **Privacy:** only opaque IDs, flags, allowed scopes and timestamps are passed. No VPN destinations, payment card details or traffic data are logged or stored by this module. Operational retention, audit logging and event integration remain open.

## Tests

Python 3.12+ standard library. From repository root:

    PYTHONPATH=products/vpn/entitlements/src python -m unittest discover -s products/vpn/entitlements/tests -v
    python -m compileall -q products/vpn/entitlements/src products/vpn/entitlements/tests

Tests use synthetic, local-only authority adapters; they are **not** evidence of real subscription enforcement. No network or production credentials are needed.

## Required CTO / #2 / #11 integration decisions (BLOCKING)

1. Merge/review foundation PR #1, resolve independent security audit #41 and stabilize Identity #34 + Control Plane #2 contracts.
2. Approve signed-grant format, maintained asymmetric-signature implementation, server-side signing key custody, key-ID rotation and emergency revocation, bound node audience, issuer, tenant, device proof-of-possession, single-use replay/session semantics and strict canonical claim encoding. **Do not treat this preflight as a verifier.**
3. Implement billing authority verification of provider webhook signatures, cancellations, refunds, chargebacks, account deletion, idempotent state changes and monotonic revocation generation.
4. Define race-safe grant issuance with device/session caps and rejection of stale concurrent snapshots; ensure post-issuance revocation propagates to nodes with measured upper bound and bounded offline behavior.
5. Test tampered signatures, unknown KID, key rotation overlap, node restart, node replay, tenant substitution, clock anomalies, propagation delays, and real gateway enforcement; independently audit the final implementation before deployment.

**Rollback:** the PR adds only a non-public Python library and tests under this lane. Removing or reverting it has no data migrations, node traffic impact or external calls. No published API or contract is changed. Legal, app-store, religious-policy, and customer VPN end-to-end verification remain outside this prototype and are release gates.
