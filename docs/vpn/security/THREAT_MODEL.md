# WexumVPN threat model and adversarial evidence register

Status: **DRAFT**. Reviewed on 2026-11-21. These requirements target a product that is **not deployed**. Foundation PR #1 is unmerged; statements about its architecture are design proposals. This analysis is not an independent audit.

## Scope, assets and adversaries

**Assets:** trusted account/session context; tenant and device ownership; subscription authority; signed VPN grants and signing keys; node private keys, configurations and admin credentials; DNS/routing privacy; revocation state; backup/incident evidence. Users' destinations and traffic content should not enter ordinary application telemetry.

**Adversaries:** malicious public client; subscriber using a stolen device or token; different tenant/subject; webhook spoofer; compromised node or CI/deploy credential; external network observer; accidental operator/debug-log exposure. Do not assume a node, cloud provider, local OS or payment provider is intrinsically trusted.

**Trust boundaries (B1–B8):**
1. Public client → Identity: client identity, roles and scopes cannot be self-asserted.
2. Verified Identity → Control Plane: authenticated actor provenance and intended audience are mandatory.
3. Billing provider → verified billing adapter → entitlement authority: payment events and refunds must be authenticated and idempotent.
4. Entitlement/Control Plane → grant issuer: only fresh authoritative tenant+device-scoped decisions may mint signed permits.
5. Grant issuer → node verifier: asymmetric signatures, per-node audience, device/session binding and revocation checks.
6. Client OS/network → VPN tunnel: platform consent is not proof of a protected data path.
7. VPN node → metrics, storage and operators: collect operational aggregates by default, never browsing destinations or raw credentials.
8. CI, deploy and backup → live infrastructure: privileged credentials require least privilege, isolation, rotation and auditable recovery.

## STRIDE risk register

Category: S = Spoofing, T = Tampering, R = Repudiation, I = Information disclosure, D = Denial of service, E = Elevation of privilege. Severity is **proposed impact-based triage**, not proof an exploit exists.

| ID | Category / severity | Threat and concrete negative scenario | State / evidence | Owner and required mitigation |
| --- | --- | --- | --- | --- |
| SEC-CTRL-001 | D/E — HIGH | After 200 revoked historical devices, newly active device is absent in the owner listing; user may not discover or manage it via list UI | **Confirmed code defect**, PR #55 head 66532b4; failing negative case on PR #67 exact head ea88245 | #2: active-first bounded listing or durable pagination; verify 201+ records and tenant-scoped cursors |
| SEC-CTRL-002 | D/I — MEDIUM | Database parent disappears after initialization; enrollment/list/revoke exposes raw sqlite3.OperationalError rather than stable service-level outage | **Confirmed code defect**, same source / PR #67 | #2: translate connection-creation errors, close/rollback safely, test every operation and redact external response |
| SEC-IDENT-001 | S/E — CRITICAL if exposed | Client sends forged actor, tenant or admin scopes to API; future adapter constructs trusted actor from unverified JSON | **Architectural release blocker**, no production OIDC verifier; no claim current remote exploit | #34 and CTO: signature/issuer/audience/expiry checks at trusted edge, request-level tenant-resource authorization |
| SEC-GRANT-001 | S/T/E — CRITICAL if exposed | Node accepts unsigned, tampered or wrong-key grant; compromised node mints new permissions | **Unimplemented**, PR #64 explicitly precheck only | #3, #4, CTO: reviewed asymmetric signature format, canonical encoding, strict verifier, managed key custody |
| SEC-GRANT-002 | T/E — HIGH | Valid grant replayed on second device, session, node or different tenant | **Unimplemented** | #3, #4: enforce device and per-node audience; bind session; exact expiry/not-before; replay cache or reviewed proof-of-possession design |
| SEC-GRANT-003 | E — HIGH | Refund, device revoke or compromised key is not recognized by disconnected node; indefinite cached permit survives | **Unresolved contract** | #3, #4, #9, CTO: bounded revocation propagation, key denylist/epochs, test temporary outage and emergency cut-off |
| SEC-NODE-001 | S/T/D — HIGH | Untrusted node health metadata or retired node remains selectable | **Unresolved**, PR #65 inventory not authenticated live management | #4, #8: authenticated source, freshness+monotonic generation, unhealthy exclusion and capacity fencing |
| SEC-PRIV-001 | I — HIGH | Query names, destination IPs, raw tokens, device identifiers, payment details or full client IPs enter metrics, logs, exceptions or backups | **Unverified across deployment** | #8 and all lanes: field-level allowlist, log/trace scrubbing and automated secret/PII fixture checks; retention and deletion review |
| SEC-PRIV-002 | I — HIGH | DNS/IPv4/IPv6/WebRTC or split-tunnel leakage when network changes, VPN fails, resumes or suspends | **No real tunnel/device measurements** | #5, #6, #7, #10: platform-native tests on actual data path and documented kill-switch semantics |
| SEC-UX-001 | S/I — HIGH | UI displays PROTECTED from user consent or mocked engine status without verified OS/engine data-plane evidence | **Currently shells only**, no real engine; design gate | #5, #6, #7, #39: trusted native state source; negative reordering/revocation tests |
| SEC-AUTH-001 | S/T — HIGH | Forged billing webhook or duplicate/refund out-of-order event creates or resurrects subscription | **No production payment provider** | #9: verified provider signature and transaction idempotency; reconciliation, refund/chargeback tests |
| SEC-OPS-001 | D — HIGH | Management outage, stale clocks or failed failover cause stale privilege or persistent false protected state | **No operational integration tests** | #3, #4, #8, #10: deny new permits on authority outage; bounded existing-session policy; drills |
| SEC-KEY-001 | I/E — CRITICAL if deployed | Signing key or deploy credential leaks through CI, logs or node images | **No live keys deployed** | CTO/#3/#4/#8: no keys in git or tickets; segregated issuer custody, KID rotation, tested emergency revocation |
| SEC-TENANT-001 | E/I — CRITICAL if exposed | Actor for tenant A lists, revokes or grants device for tenant B | **Prototype tests only; no verified end-to-end HTTP edge** | #2, #3, #34, #10: negative cross-tenant tests at API, DB and node boundaries with opaque error behavior |
| SEC-SUPPLY-001 | T/E — HIGH | Compromised dependency, runner or build artifact injects client/issuer trust violation | **Unreviewed release pipeline** | CTO/#5/#6/#7: least-privilege runner, pinned dependencies, reproducible signed artifacts and provenance checks |

Severity of SEC-CTRL-001 is conditional on device-list UI being a principal revocation path. There is **no evidence** that it causes a currently deployed tunnel to remain connected; none is deployed. SEC-CTRL-002's information-disclosure impact depends on the future HTTP error adapter and logs; the demonstrated bug is uncontrolled exception propagation.

## Evidence (exact source and test identities)

- PR #55 source: https://github.com/Dimash313/Wexum/blob/66532b4df984c091b46e53697218b82557bb4bbd/products/vpn/control/src/wexum_vpn_control/store.py
- PR #55 service: https://github.com/Dimash313/Wexum/blob/66532b4df984c091b46e53697218b82557bb4bbd/products/vpn/control/src/wexum_vpn_control/service.py
- PR #67 negative test: https://github.com/Dimash313/Wexum/blob/ea882455a788dd76e07fee106409c2c33654ad77/tests/integration/test_vpn_control_blockers.py
- Github Actions failed run: https://github.com/Dimash313/Wexum/actions/runs/44873727876 — failed assertion + 3 errors (on this candidate head only).
- Foundation architecture (proposed): https://github.com/Dimash313/Wexum/pull/1
- Independent foundation audit task: https://github.com/Dimash313/Wexum/issues/41

## Priority abuse-test catalogue for integration owner

1. Construct wrong issuer, audience, tenant, device, scope and node IDs; deny with no grant or record disclosure.
2. Corrupt one signed payload byte, use unknown KID, old revoked signing key, future not-before, expired TTL and duplicate session ID; deny.
3. Revoke device and send concurrent enroll/renew across regions; no resurrection after acknowledged revocation; fail closed on missing authority.
4. Lose Identity/Billing/Node Registry, crash node, shift clock backwards/forwards, restart verifier and partition revocation channel; explicitly observe policy limits.
5. Change Wi-Fi ↔ mobile; suspend/resume and terminate VPN; measure DNS, IPv4, IPv6 and other app traffic separately on **real devices**, including forced network failures.
6. Inject synthetic canary credentials and destination names into exception paths, telemetry, crash reports and backup export; verify absence without using real private traffic.
7. Validate controls under concurrent multi-tenant requests and 201+ historical devices, including exact filtered pagination semantics.
8. Attempt unauthorized deployment from an untrusted CI context and emergency credential/key rotation; check denied privileges and restored service state.

No penetration-testing or live traffic result is asserted by this plan.
