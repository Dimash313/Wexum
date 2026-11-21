# Proposed WexumVPN management-plane telemetry boundary (CTO approval required)

**Status:** Proposal only, issue [#8](https://github.com/Dimash313/Wexum/issues/8), [Draft PR #72](https://github.com/Dimash313/Wexum/pull/72). Does not approve or change a shared interface.

## Goal

Feed **verified aggregate technical observations** to the existing isolated `HealthMonitor` without turning node discovery or management-plane metrics into a user tracking system. The observability library is not an authority for node availability, subscriptions, customer sessions, incident response or routing.

## Trust boundary and intended producer

- Producer: explicitly enrolled **management-plane probe worker**, not a VPN client or untrusted caller. CTO/Identity team must approve the service identity mechanism, scope/audience, rotation and revocation. Never treat a node ID or registration generation as proof of probe authentication.
- Target: configured and reviewed static allowlist per environment; no free-form target URL/address from users. The worker must enforce bounded rate/concurrency, hard wall-clock deadline (including DNS), conservative retries and no redirected outbound probes.
- Internal event candidate: `{service_category, probe_kind, status, elapsed_seconds, checked_at, source_identity, node_generation, event_id}`. These names are **illustrative only**, not an approved API or schema. All producer-identity/generation/event fields stay within an authenticated private adapter; **none** become public metric labels or appear in exported Prometheus text. Only fixed category, result and state leave the adapter for aggregation.
- Node Registry owner verifies that a node's registration generation matches the current inventory entry, freshness is acceptable, the observation belongs to that node and replay/out-of-order samples are rejected. This adapter must not silently create a new node or change inventory state.
- Consumer validates exact allowed category, status enum, finite nonnegative elapsed time, clock semantics, bounds and freshness before calling `HealthMonitor.record`. Invalid, stale, unknown, duplicate or unauthenticated events must **not** change success counters. Record rejection and source outages as **technical gaps** without sensitive original payloads.
- Aggregate reports identify only technical component categories. No user IDs, IP addresses, DNS queries, browsing destinations, connection histories, device IDs, account identifiers, unreviewed region/hostname or raw infrastructure endpoint data are published in metrics.

## Operational considerations

- A TCP handshake is a weak technical signal, not proof of tunnel availability. True VPN tunnel and DNS leak tests belong to controlled, independent end-to-end rigs.
- Define observation cadence, failure threshold, sample minimum and SLO target from operational testing. This library's default 99% ratio is a **local estimate**, not a customer SLA.
- Clock rollback raises a validation error (not `healthy`), counters must remain finite, unknown/stale must be visible, and restart resets the volatile window.
- Secure metrics endpoint, notification transport, access permissions, storage retention, audit logs, incident paging, on-call response and cloud egress-cost sources require separate design/deployment approval. Do not claim zero logs before reviewing provider, gateway and proxy settings.
- If trusted telemetry is unavailable, alert on the measurement gap instead of inventing availability or feeding stale successful samples.
- No live customer data or credentials in unit/integration tests.

## Acceptance tests before actual integration

1. Deny unauthenticated or wrong-audience sample; reject expired, duplicate, out-of-order and mismatched node-generation reports (especially delete/re-register).
2. Reject unconfigured source/target and malicious destination; validate host allowlisting, ingress permissions, bounded concurrency, absolute deadline, timeout and resource exhaustion behavior.
3. Injection test arbitrary labels, user-identifying fields, non-finite durations and malformed event payloads; verify no sensitive data reaches logs, metrics or notifications.
4. Simulate exporter restart, missing probes, worker outage, monotonic-clock rollback, network partitions and delayed events; status must remain unknown/stale or fail closed.
5. Independent audit of SLO/burn logic against known synthetic traces; measure actual stage/region infrastructure in controlled tests only.
6. Verify any storage/logging retention/deletion and RBAC, secure transport, alerts and resource-cost accounting with deployment-specific evidence.

## Decisions requested from CTO

1. Authoritative management probe identity, transport and trust boundary.
2. Whether Node Registry [PR #65](https://github.com/Dimash313/Wexum/pull/65) and Control Plane accept a proposed internal observation contract; exact authenticated node-generation verification and source of truth.
3. Scrape/alert access, data retention and scheduling/cost budget; who owns shared API, CI and deployment.
4. Review responsibilities, rollout/rollback gates, and no-logs/privacy policy evidence.

No implementation against sibling modules, shared docs, platform contracts or live infrastructure is authorized by this proposal.
