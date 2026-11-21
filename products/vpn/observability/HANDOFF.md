# WexumVPN — Network Observability & Operations: HANDOFF

**Last reviewed:** 2026-11-21 (UTC+05, project activity); update this document after material changes.
**Repository:** https://github.com/Dimash313/Wexum
**Owner lane:** `products/vpn/observability/` **only**.
**Status:** Standalone implementation proposed in Draft PR; not integrated, deployed, or independently approved.

## 1. Scope and responsibilities

**Direction:** Network Observability & Operations, WexumVPN management plane.

This lane owns technical health probes, service availability observations, resource measurements, operational alert signals, performance/error-budget evidence, diagnostics and incident/recovery playbooks with strict privacy minimization. It **does not** own the VPN data plane, account identities, entitlements, node registry, VPN protocol, mobile/desktop clients, shared APIs, infrastructure provider configuration or global CI. Do not edit sibling work lanes or shared contracts/docs without CTO/integrator-approved ADR and coordination.

**Privacy invariant:** Do not collect or export users' packet contents, browsing destinations, DNS histories, account/device/session identifiers or IPs for these technical metrics. Never assert infrastructure-wide no-logs compliance on the strength of this isolated module.

## 2. Architecture and technical decisions

- **Independent Python standard-library module** under `products/vpn/observability/`, not dependent on pending Foundation PR #1 contracts.
- `health.py`: `HealthMonitor` maintains bounded process-local probe observations for five *fixed, operator-defined service categories*: `control_plane`, `node_registry`, `entitlements`, `identity`, `gateway`. Hard-coded label vocabulary protects metric cardinality/PII; arbitrary labels are rejected. Monotonic clock, lock-protected updates, rolling window default 300 seconds, 1000 samples/category default, unknown/stale/degraded/down/healthy states, sampled success ratio and relative SLO error-budget estimate. Process-lifetime counters reset on restart.
- `probes.py`: `ProbeTarget` defines an explicitly operator-configured TCP endpoint; `tcp_probe` records only connect success/failure and local elapsed time. **TCP reachability is not a functional VPN, DNS leak, true user availability or security test**. Probe invocation has no automatic scheduler; no untrusted target values should flow into configuration.
- `alerts.py`: `AlertEngine` transitions for missing telemetry, repeated probe failures and estimated sample error-budget exhaustion. No notification transport or durable queue.
- `resources.py`: `read_resources` gathers current **local monitoring process** CPU time, optional Linux RSS and local disk capacity. It does *not* measure remote gateway usage, cloud egress or provider bills. Missing RSS is represented as `None`, not zero.
- Prometheus plaintext exposition returned from `HealthMonitor.render_prometheus()`; **no HTTP endpoint, service, authentication or network publisher** has been deployed. Transport/access restrictions belong to the future CTO-approved adapter.
- No runtime external dependencies, credentials, telemetry databases, task schedulers, logs or cloud services added.
- No paid services or additional infrastructure authorized.

## 3. GitHub issue, branch, PR and source-of-truth

- Issue: [#8 — VPN network observability](https://github.com/Dimash313/Wexum/issues/8), open; ownership claimed via issue comment.
- Working branch: `feat/vpn/8-network-observability`, created from `main`.
- Draft PR: [#72 — Bounded privacy-safe probe metrics and alerts](https://github.com/Dimash313/Wexum/pull/72), open, draft, targeting `main`. **Do not self-merge.**
- Head observed when preparing handoff: `98044b6535ab93c44b78b596741b20bd76e759bb` (before this documentation-only commit). Always fetch current head rather than assuming this SHA remains current.
- Foundation PR [#1](https://github.com/Dimash313/Wexum/pull/1) currently open and unmerged (checked on 2026-11-21).
- Node Registry Draft PR [#65](https://github.com/Dimash313/Wexum/pull/65) currently open, requires separate CTO-approved telemetry interface/authentication/registration-generation mapping.

## 4. Implemented artifacts

- `__init__.py`: stable local imports.
- `health.py`: in-memory aggregate probe state and Prometheus text metrics.
- `alerts.py`: deduplicated alert state transitions.
- `probes.py`: configured TCP handshake probe.
- `resources.py`: local process and disk resource reads.
- `tests/test_observability.py`: deterministic synthetic/unit cases.
- `README.md`: behavior, privacy boundary, usage and restrictions.
- `OPERATIONS.md`: first-response checks, alert semantics, recovery, rollback and integration gates.
- `HANDOFF.md`: this continuity document.

No live node deployment, true tunnel verification, cross-service monitoring integration or production data collection has been performed.

## 5. Test evidence — distinguish historical reports from fresh results

Evidence reported with initial PR #72 work in the preceding session:
- `python -X dev -m unittest discover -s products/vpn/observability/tests -v` — reported **15/15 pass locally**, using mocked sockets and a local resource read.
- `python -m compileall -q products/vpn/observability` — reported pass locally.
- Tested scenarios reported: unknown/stale samples, successful/failed probes, invalid/PII metric labels, non-finite time, monotonic rollback, memory bounds, concurrency, alerts/deduplication, recovery, invalid targets and nonexistent resource mount.
- Initial work compared recorded content checksums of tested files with committed GitHub source.

**Independent rerun in this handoff update:** NOT PERFORMED. Container cannot reach github.com directly in this environment; do not turn previous reports into a new test claim. Re-run against the fresh current PR head before merging. No live node, DNS leak, VPN tunnel, load, cloud cost, real-traffic, provider compliance or operational failover test exists.

**GitHub CI:** On the initial PR head, the GitHub connector returned zero workflow runs and zero combined status checks. Treat this as **no CI evidence**, not as a passing CI signal. CTO controls changes to the shared CI workflow. Recheck statuses on the latest head whenever resuming.

## 6. Known limitations, threats and blockers

1. **Untrusted inputs:** `HealthMonitor.record` itself does not authenticate producer identity. Never expose it directly to external/client-origin reports. Source authenticity, scope and replay prevention remain future adapter requirements.
2. **Unverified targets:** `ProbeTarget` only applies syntactic checks; a future privileged scheduler must restrict targets through trusted static allowlisting and prevent server-side request forgery or unrestricted scans.
3. **Timeout caveat:** `socket.create_connection` timeout does not guarantee an absolute deadline for DNS resolution. A bounded scheduler/hard deadline, concurrency/rate controls, backoff and jitter are still needed.
4. **Single-process memory:** Samples/counters are volatile; no durable distributed ordering or historically valid uptime/SLA accounting.
5. **Alert delivery missing:** Only deduplicated state changes exist; no paging or reliable notifications.
6. **No deployed monitoring:** No protected scrape endpoint, network probes against production, remote resource adapters, node egress cost measurement or real-service failure drills.
7. **Privacy beyond this code unverified:** Gateway, proxy, cloud, DNS, security and host logging/retention must be audited before making public no-logs assertions.
8. **Upstream dependencies:** Foundation PR #1 pending; Node Registry PR #65 unmerged. CTO must approve management-plane interface contracts, identity/registration generations, trust/authorization and shared CI modifications.
9. **Release blockers:** Current-head CI, independent security/privacy review, integration/operational tests, provider/legal/store/religious review where relevant.
10. **Quality checks:** Existing tests and module do not establish a 10/10 quality rating or production readiness.

## 7. Next concrete tasks (in priority order)

1. On `Продолжаем дальше`, re-read current `AGENTS.md`, this `HANDOFF.md`, `README.md`, `OPERATIONS.md`, issue #8, PR #72 discussions/reviews, Foundation PR #1 and Node Registry PR #65. Inspect current branch/head, conflicting changes, open status checks, and incoming CTO decisions. Do not request task reallocation unless owner-only decisions are required.
2. Fetch/checkout latest PR head in a testable runtime and **really execute** the test and compile commands in section 5; record exact outcomes, runtime and SHA here and in PR #72. Add missing negative and fault-injection coverage where justified.
3. Review sampled SLO/error-budget semantics and minimum-sample behavior; ensure unavailable/stale telemetry is never marketed as healthy service uptime. Consider a monotonic aging/recovery/failure injection audit.
4. Propose (do not unilaterally implement cross-lane interfaces) an authenticated, bounded management-plane probe source contract with Node Registry owner/CTO; include freshness, replay/generation checks, allowlist and permission scope. Link approval in PR.
5. Within owned path, design bounded probe scheduling and safe metrics/alert adapters only after interface/security approval; specify sample cadence, explicit timeouts, allowed targets, TLS/access and retention.
6. Request independent audit of current head and address findings in this branch. Never approve or merge own PR. Coordinate any shared CI changes via CTO.
7. Update this `HANDOFF.md`, PR body and issue comments after every major implementation, test result, discovered blocker, or stage completion. Report what is actually measured, what tests were really executed, gaps and link to the Draft PR.

## 8. Links and operating documents

- [Issue #8](https://github.com/Dimash313/Wexum/issues/8)
- [Draft PR #72](https://github.com/Dimash313/Wexum/pull/72)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1)
- [Node Registry PR #65](https://github.com/Dimash313/Wexum/pull/65)
- [Root AGENTS.md — foundation branch](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md)
- [VPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md)
- [VPN product requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md)
- [Quality gates](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)
- [Review protocol](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/REVIEW_PROTOCOL.md)
- [Religious/ethical policy](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/policy/RELIGIOUS_REVIEW.md)
- [Lane README](README.md)
- [Operational playbook](OPERATIONS.md)

## Nonnegotiable continuation policy

Follow repository ownership and source-of-truth policies. Work only in this issue's branch/owned path unless explicitly approved by CTO/integrator. Keep tests, actual measurements, known flaws, next tasks and links current. Do not silently edit shared docs, neighboring directions, or `main`. Do not fabricate evidence or merge without required checks and independent audit.
