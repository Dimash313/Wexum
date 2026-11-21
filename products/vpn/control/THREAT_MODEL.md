# VPN Device Control — Threat Model (prototype)

Owner: issue #2. Status: proposed, independent audit required.

| Threat | Current defense | Remaining gap / blocker |
| --- | --- | --- |
| Forged user or tenant header | Service requires trusted actor type, issuer/audience, scopes and nonexpired timestamps; rejects absent actor | No token cryptographic validation or trusted HTTP adapter yet. **Never** accept actor from client payload |
| Cross-tenant reads or revocations | Every query filters tenant AND subject, including per-ID lookup and mutation; opaque not-found response | Independent review and production DB row-level policies needed |
| Fraudulent active subscription | Injected async entitlement authority must match tenant and subject; rejects stale/inactive/invalid results and times out closed | Authority/webhook signatures, refunds and offline revocation are not implemented |
| Repeated enrollment / race on device cap | SQLite BEGIN IMMEDIATE transaction and request-key dedup, raw key hashed; tested concurrent limit | Idempotency ledger unbounded, cleanup and multi-instance scaling pending |
| Expired access token mid-request | Actor revalidated after async entitlement call | Token signature and audience validation must be at trust boundary |
| Reusing revoked device ID | Registration key replay returns revoked record (not reactivation); new request generates new ID | No cryptographic binding to device public key; no node enforcement |
| Platform or ID injection | Platform allowlist, strict request-key syntax, server-generated UUID; parameterized SQL | Public HTTP schemas, rate limits and size limits pending |
| SQLite lock or entitlement outage | Bounded SQLite timeout, bounded async entitlement timeout, generic service error | No HA, circuit breaker, persistence replication or disaster recovery |
| Directory symlink or filesystem breach | Server-owned path documented; DB path not request-controlled | Symlink-safe DB creation, permissions and sandboxing required before real deployment |
| User privacy / deletion | No traffic histories, remote IP addresses, payment details or tokens in records | Lifecycle deletion, backup retention and legal privacy review pending |
| Revenue entitlement bypass | Device registration denied if authority cannot verify | Device row is not signed VPN access; node/key gates not implemented |

## Invariants

1. All mutating privileged actions fail closed on missing/wrong actor scopes, issuer, audience, expiry, tenant or subscription authority.
2. Revocation is owner-scoped and **does not depend on billing availability**.
3. No device in another tenant or user is enumerated or revoked by ID alone.
4. No endpoint is mounted publicly before trusted OIDC authentication and explicit provider-/tenant-boundary tests are added.
5. An idempotency key does not create two devices, even with concurrent writers.
6. A valid database row is not evidence of a VPN tunnel, subscription payment, gateway cryptographic access or protected traffic.

No cryptographic or production security rating is assigned.
