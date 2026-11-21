# WexumVPN authorization, grant and key security contract

**Status:** issue #11 security proposal; CTO and dependent lane owners must approve any shared wire contract or lifetime budget. This document does not create an operational token issuer or node verifier.

## Trust chain

Public client → separately verified Identity auth adapter (#34) → Control Plane (#2) → authoritative account/device/subscription authorities (#3/#9) → isolated signing issuer (#3) → authenticated VPN node (#4) → native trusted tunnel implementation (#5/#6/#7).

- A client-supplied username, tenant, subscription receipt, boolean status, arbitrary JSON actor or grant candidate is **never authority**.
- Authenticate service-to-service operations and authorize tenant, subject, device and exact operation again at each boundary. Node verification cannot call the payment database for every packet.
- Hub is a consumer of status and device-management APIs, not a tunnel owner, issuer, superuser or alternate login bypass.
- Default when identity or authoritative subscription/device state is unavailable: **no new grant**. Do not broaden rights because a previous billing event once existed.

## Required signed permit claims (proposal, not locked schema)

Exact names/wire format are **TBD** by integrator-approved API/ADR. A permit must, at minimum, carry an opaque unique ID (replay control), explicit signer/issuer and algorithm, KID, tenant and opaque subject/device IDs, exact node audience, authorized operation(s), issued-at, not-before and expiry, plus explicit session/device proof binding. Reject missing, duplicated, unrecognized, oversized or inconsistent claims, unsafe algorithm negotiation and ambiguous canonical representations. Sign only after atomic authoritative preconditions; no grant constructed from untrusted adapter return values.

Verifier:
1. Confirm a trusted, configured verification key for signer+KID and an allowlisted protocol/algorithm. Never accept unsigned or client-chosen keys.
2. Bind to tenant, device, node and session/connection authorization; deny arbitrary cross-region/cross-node replay.
3. Evaluate scope, revocation epoch, nbf/exp, clock skew and one-time/session policy using server-controlled clocks; reject malformed or stale state.
4. Revalidate on reconnect/rekey/session renewal; no silent continuation beyond approved offline/revocation budget.
5. Record security events with opaque correlation IDs, not raw permits, usernames or browsing data.

**No premature numeric guarantee:** proposed PR #64 limits an unsigned grant *candidate* to <=300 seconds by its Python policy, with 120-second default. This does not establish signed permit TTL, revocation SLA, offline grace period or any acceptable operational risk. For issue #11 release gate, until signed off, **existing-session outage grace = 0 in the metadata baseline**; a nonzero value needs an explicit CTO and security decision backed by node tests. It is not a declaration that a future VPN implementation already enforces zero grace.

## Key and secret custody

- Use an established independently reviewed asymmetric signing library and supported key-management provider. Do not implement cryptographic primitives or trust a symmetric signing secret on every data-plane node.
- Signer private keys remain restricted to issuer service identity. Nodes receive only necessary public verification material; never private issuer keys. Node transport/private keys are distinct from issuer keys.
- Production secrets must be provisioned through approved secret management, never git, PRs, test fixtures, CI logs, image layers, user analytics or backup manifests.
- Require separate development/staging/production roots; least privilege, audited issuance, rotation ownership, expiration, alerts for unexpected signing attempts.
- Roll rotation: distribute new public key, ensure acknowledgment from authorized nodes, activate signer, enforce bounded old-key window; reject unknown KID. Incident rotation: revoke compromised signer and invalidate exposed grants immediately according to pre-reviewed emergency policy.
- Backups of keys (if permitted) need encryption, minimal custodians, separate access controls, restore testing and documented deletion and incident response.

## Required negative test matrix

| Test ID | Denial / safety expectation | Evidence owner |
| --- | --- | --- |
| AC-01 | Forged public actor or client-entered tenant/subject/role cannot authorize | Identity #34, Control #2, Tests #10 |
| AC-02 | Expired, future nbf, invalid issuer, audience, scope or signature denies | Entitlements #3, Nodes #4, Tests #10 |
| AC-03 | Other tenant/device/node/session replay denies; duplicate jti cannot create multiple live sessions outside declared policy | #3/#4/#10 |
| AC-04 | Revoked device, deleted account, refund/chargeback or revoked signing key cannot obtain new grant | #3/#9/#34/#10 |
| AC-05 | Outage / timeout / stale or non-monotonic authoritative snapshot never issues a new permit | #2/#3/#10 |
| AC-06 | Simultaneous enroll and revoke cannot bypass device cap, reuse revoked identity or resurrect access | #2/#3/#10 |
| AC-07 | Node restart, auth partition, rotation overlap and emergency compromise respect precisely approved bounded-session policy | #3/#4/#8/#10 |
| AC-08 | Client status only shows protected after trusted native engine and data-path proof, not consent | #5/#6/#7/#10 |
| AC-09 | Failure paths redact raw permit and DB internals in API, logs and exception telemetry | #2/#8/#10 |
| AC-10 | Management credential/signer key rotation and disaster recovery are reproducible under least privilege | #4/#8/#10 |

## Required architecture decisions through CTO

1. Grant format/canonicalization, verifier libraries and algorithm allowlist; issuer-key custody and trust anchors.
2. Tenant/subject/device identity representation; proof-of-possession; binding to node/session; replay cache persistence.
3. Max grant lifetime, clock skew and deterministic refresh timing; revocation propagation + acknowledgments; acceptable offline window (if any).
4. Exact error taxonomy and response behavior; HTTP mapping for missing/unavailable store; log-redaction policy.
5. Node metadata signatures/source of truth and emergency disabling.
6. Compatible evolution of shared APIs across #2/#3/#4/#9/#34/#10.

A successful check in PR #64 is **only** a GrantCandidate, never a transferable authorization credential or permission to connect.
