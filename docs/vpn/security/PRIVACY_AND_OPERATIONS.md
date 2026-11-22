# VPN privacy engineering, resilience and incident response

**Draft for security issue #11 — not a promise of no logs or anonymity.** Data collection below is a proposed minimization policy. Actual provider behavior, operating-system telemetry, cloud network logs, backup retention and incident/legal requirements remain unverified until deployment reviews.

## Data inventory and purpose limitation

| Surface | Necessary candidate data | Prohibited from routine telemetry | Owner / verification |
| --- | --- | --- | --- |
| Identity | Opaque subject ID; session status; authentication security events | Passwords, raw bearer tokens, identity-proof images, content of recovery factors | #34; log sampling and access controls |
| Control Plane | Tenant + opaque device IDs, approved platform, enrollment/revocation timestamps, hashed idempotency references | Browsing history, full packet capture, raw tokens, unrelated product data | #2; exports, retention/deletion and audit |
| Billing | Verified transaction/provider event references; account-scoped subscription decisions | Payment card data at VPN nodes; client-defined paid status | #9; webhook/auth and reconciliation tests |
| Issuer | Opaque permit ID, scope, node audience, short issuance/expiry metadata | Raw signed grant in logs, private signing keys in app telemetry | #3; issuer log/secret inspection |
| VPN Node | Node health, capacity, aggregate error counters; strictly necessary short-lived connection state | DNS queries, URLs, destinations, content, raw customer IP in general analytics | #4/#8; packet/flow/log/config review |
| Native clients | Connection status and consent failure categories, only with explicit notice if telemetry exists | DNS resolver history, personal IP identity tracking, raw VPN profile or secrets in crash dumps | #5/#6/#7; OS privacy instrumentation |
| Observability | Aggregate availability, saturation, error class, anonymized operational signals | Destination addresses, customer search or browsing timeline, raw authorization headers | #8; canary testing |
| Backups / incident | Encrypted configuration and recoverable authoritative records only after review | Indefinite retained secrets or untracked snapshots | CTO/#8; restore/delete/key custody review |

**Exact fields, default collection, legal retention periods, backups, subprocess logging, hosting geography and user notice are unresolved**. Before any deployment, publish a field-by-field inventory with controller, purpose, storage region, retention duration, legal basis, who can access, deletion schedule and third-party processors. If the service provider mandates network/abuse logs, disclose these rather than pretending they do not exist.

## Product security/privacy requirements

1. Minimize: prefer aggregate node health over identifiable activity. Never collect DNS query names, accessed destinations or traffic contents as routine product analytics.
2. Bound retention: delete purpose-expired data and residual copies in caches, jobs, exports and backups subject to approved legal obligations. No invented universal retention time.
3. Restrict: independent product data ownership, tenant-scoped authorization, least-privileged operator access and auditable security-only admin changes.
4. Encrypt: approved transport protection, at-rest encryption where needed, secrets in platform-backed keystores or protected server secret store, not source or crash reports.
5. Limit tracing: strip Authorization and Cookie headers, key material, grant bodies, full SQL parameters and diagnostic user traffic from errors and distributed traces.
6. Disclose: policy must explain VPN limitations, hosting/provider visibility, split tunneling, kill-switch behavior and the difference between connection status and actual anonymity.
7. Test: synthetic canaries for tokens and query names must not appear in normal application logs, metrics, traces, exports, crash analytics or backup indexes.
8. Control analytics and notices: no undisclosed SDK profiling or cross-product correlation. Validate user deletion and account closure against residual authorization and marketing data.

## Failure and recovery policy

| Event | New privileged action | Existing connection / user-visible state | Evidence required |
| --- | --- | --- | --- |
| Identity, billing or device authority unavailable | Deny new grants and device enrollment if authoritative result cannot be verified | No silent renewal; session survival only if explicitly risk-approved and bounded | Fault injection with clock drift, timeout and restored authority |
| Node unreachable / OS tunnel down | Deny protected claim | Native client must stop claiming protected; route/kill-switch semantics tested on real OS | Real DNS/IP leak captures under network transitions |
| Revocation or refund | New grants blocked after authoritative decision | Enforce node-side cutoff within **approved** budget; until approved, no offline grace is accepted in release gate | Event replay, partition and node restart checks |
| Signing key compromised | Freeze issuance with old key and reject its signatures after emergency invalidate | Disconnect/reauthorize as required; never fall back to unsigned | Rotation drill with unknown KID/old key and complete node acknowledgments |
| Restore after data loss | No duplicate or replay-based authorizations | Restore only protected, consistent state and replay-safe reconciliation | Encrypted restore drills; integrity/tenant/revocation checks |
| Service or telemetry outage | Telemetry cannot grant access | Accurate degraded/error state; privacy controls cannot be disabled for convenience | Negative tests for log fallback and degraded service |

## Incident playbook (proposed)

1. **Detect:** alert on unusual issuance, replay rejects, key access, failed revocations, node freshness and actual outage; alert payloads must avoid user destinations and raw tokens.
2. **Contain:** restrict potentially compromised service credentials and keys, disable suspicious node registration and stop new grants as necessary; preserve a narrow security-only audit trail.
3. **Assess:** record affected regions, tenants (opaque), times and artifact hashes. Do not capture private traffic merely to investigate unless separately justified and authorized.
4. **Recover:** rotate keys/credentials, revalidate revoked subjects and device state, reconcile billing/refunds, restore audited data and confirm node health and client routing.
5. **Verify:** independent test of stale grants, cross-tenant separation, DNS/IP leaks, deletion and rollback at exact build/commit; reopen only with approved residual risk.
6. **Notify:** coordinate legal/regulatory/provider notices as applicable; communicate precisely what data may have been exposed and what remains unknown.

## Platform-specific real tunnel verification gate

For Android, iOS and desktop, test representative versions of each OS and both IPv4/IPv6. Capture on controlled **test networks using synthetic destinations** while switching Wi-Fi/cellular, connecting/reconnecting, sleep/resume, captive portal, lost permissions, transport outage, DNS fallback and split-tunnel configurations. Define expected treatment of locally excluded traffic. Compare before/after public IP, DNS resolver paths and application route behavior. Fail the release gate on unintended traffic escape or unverified kill-switch behavior. A state machine passing JVM/Swift unit tests does not meet this gate.

## Open decisions / no claims

- Exact legal and processor obligations for each market; store restrictions and review.
- Hosting/network provider data practices, VPN protocol selection, DNS handling and traffic retention.
- Incident evidence retention, deletion/backup policy and lawful access workflow.
- Full independent security audit, network packet tests and operations drills.
- Qualified policy reviews for affected religious/ethical/legal capabilities.

Owner #11 documents requirements; CTO coordinates cross-lane changes. Reviewers must not treat this text as an external guarantee.
