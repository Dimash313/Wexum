# WexumVPN — Network Observability & Operations: HANDOFF

**Last reviewed:** 2026-11-21 (UTC+05, project activity). Latest local test evidence recorded below; update after material changes.
**Repository:** https://github.com/Dimash313/Wexum
**Owner lane:** `products/vpn/observability/` **only**.
**Status:** Standalone implementation proposed in Draft PR; not integrated, deployed, or independently approved.

## 1. Scope and responsibilities

**Direction:** Network Observability & Operations, WexumVPN management plane.

This lane owns technical health probes, service availability observations, resource measurements, operational alert signals, performance/error-budget evidence, diagnostics and incident/recovery playbooks with strict privacy minimization. It **does not** own the VPN data plane, account identities, entitlements, node registry, VPN protocol, mobile/desktop clients, shared APIs, infrastructure provider configuration or global CI. Do not edit sibling work lanes or shared contracts/docs without CTO/integrator-approved ADR and coordination.

**Privacy invariant:** Do not collect or export users' packet contents, browsing destinations, DNS histories, account/device/session identifiers or IPs for these technical metrics. Never assert infrastructure-wide no-logs compliance on the strength of this isolated module.

## 2. Architecture and technical decisions

- **Independent Python standard-library module** under `products/vpn/observability/`, not dependent on pending Foundation PR #1 contracts.
- `health.py`: `HealthMonitor` rejects monotonic clock rollback across all services, snapshots and Prometheus exposition, prevents accumulated duration overflow before committing counters, and maintains bounded process-local probe observations for five *fixed, operator-defined service categories*: `control_plane`, `node_registry`, `entitlements`, `identity`, `gateway`. Hard-coded label vocabulary protects metric cardinality/PII; arbitrary labels are rejected. Monotonic clock, lock-protected updates, rolling window default 300 seconds, 1000 samples/category default, unknown/stale/degraded/down/healthy states, sampled success ratio and relative SLO error-budget estimate. Process-lifetime counters reset on restart.
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
- Earlier reviewed heads included `bfff09382ab5b11df2366c77b67a9ac224ab1b38`; do not assume a saved SHA is current. Always query live PR head before continuing. This handoff includes fixes and proposal committed after that SHA.
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
- `INTEGRATION_PROPOSAL.md`: CTO proposal for an authenticated, replay-safe, strictly private technical telemetry boundary; **not an approved shared contract**.

No live node deployment, true tunnel verification, cross-service monitoring integration or production data collection has been performed.

## 5. Test evidence — distinguish local verification from CI

**Fresh evidence from current continuation (2026-11-21, Python 3.13.5):** The five Python module files and existing test file were reconstructed locally from source text in the working branch and checked for matching length and FNV32 fingerprint before test execution (non-cryptographic consistency evidence). GitHub file re-fetches confirmed original fingerprints. Baseline:

- `python -X dev -m unittest discover -s products/vpn/observability/tests -v` — **15/15 passed** against the GitHub-matching original.
- `python -m compileall -q products/vpn/observability` — **passed** against that original.

Reproduced two defects in the original: a backwards fake monotonic clock returned a false `HEALTHY` snapshot, and two individually finite large durations accumulated to an `inf` Prometheus counter.

Fixes pushed in this branch:
- `health.py`: global backwards-clock guard used by `record`, `snapshot` and `render_prometheus`; reject overflow before recording partial sample/counter; validate maximum sample count before comparing it to minimum sample count.
- `tests/test_observability.py`: three negative regression tests for clock rollback, atomic duration-overflow rejection and invalid sample-count type.

**Local retest with the corrected exact content committed to PR #72**:
- `python -X dev -m unittest discover -s products/vpn/observability/tests -v` — **18/18 passed**, Python **3.13.5**.
- `python -m compileall -q products/vpn/observability` — **passed**.
- `health.py` length `8537`, FNV32 `9843107e`; `tests/test_observability.py` length `8779`, FNV32 `e7253179`. The transformation applied in GitHub was checked against these locally verified fingerprints before each commit.
- Test sockets are mocked. One actual local process/disk resource read runs in unit tests. **No live VPN node, true tunnel, DNS leak, cloud egress, production load or operational failover test occurred.**
- Note: FNV32 matching is a non-cryptographic equality check, not a security attestation; re-fetch and validate current GitHub blobs and rerun under authoritative CI before merge.

**GitHub CI:** No workflow runs or combined status checks were returned on earlier PR heads. CTO owns shared CI; check the **latest head** on every resume. **No CI pass or independent reviewer approval claimed.**

## 6. Known limitations, threats and blockers

1. **Untrusted inputs:** `HealthMonitor.record` itself does not authenticate producer identity. Never expose it directly to external/client-origin reports. Source authenticity, scope and replay prevention remain future adapter requirements.
2. **Unverified targets:** `ProbeTarget` only applies syntactic checks; a future privileged scheduler must restrict targets through trusted static allowlisting and prevent server-side request forgery or unrestricted scans.
3. **Clock and overflow handling:** Local rollback/overflow regressions now reject invalid observations instead of emitting false health or non-finite Prometheus metrics. Future orchestrators must interpret exceptions as unknown/missing measurement, not hide them or claim uptime.
4. **Timeout caveat:** `socket.create_connection` timeout does not guarantee an absolute deadline for DNS resolution. A bounded scheduler/hard deadline, concurrency/rate controls, backoff and jitter are still needed.
5. **Single-process memory:** Samples/counters are volatile; no durable distributed ordering or historically valid uptime/SLA accounting.
6. **Alert delivery missing:** Only deduplicated state changes exist; no paging or reliable notifications.
7. **No deployed monitoring:** No protected scrape endpoint, network probes against production, remote resource adapters, node egress cost measurement or real-service failure drills.
8. **Privacy beyond this code unverified:** Gateway, proxy, cloud, DNS, security and host logging/retention must be audited before making public no-logs assertions.
9. **Upstream dependencies:** Foundation PR #1 pending; Node Registry PR #65 unmerged. CTO must approve management-plane interface contracts, identity/registration generations, trust/authorization and shared CI modifications.
10. **Release blockers:** Current-head CI, independent security/privacy review, integration/operational tests, provider/legal/store/religious review where relevant.
11. **Quality checks:** Existing tests and module do not establish a 10/10 quality rating or production readiness.

## 7. Next concrete tasks (in priority order)

1. On `Продолжаем дальше`, re-read current `AGENTS.md`, this `HANDOFF.md`, lane docs, issue #8, PR #72 reviews/discussions/CI, Foundation PR #1 and Node Registry PR #65. Inspect branch HEAD and possible concurrent changes before writing.
2. On the **latest PR HEAD**, rerun and independently review the 18 unit tests plus compile checks; add tests for more realistic fault injection (frozen/backwards time, worker loss, repeated signals, metric counter bounds) where useful. Check sample SLO/error-budget meaning against explicit traces.
3. Request CTO feedback on [INTEGRATION_PROPOSAL.md](INTEGRATION_PROPOSAL.md): authenticated probe worker identity, generation/freshness/replay guard against PR #65, private management scopes, static target allowlist and transparent failure mode. Do not integrate across lane boundaries without approval.
4. Design/implement only approved bounded scheduler, management adapter and secure metrics/alert delivery in owned path. Keep no customer identifiers or browsing history in metrics; request CTO to own CI/workflow and cross-team contracts.
5. Request independent audit of **new head**; address review findings and verify CI status. No self-approval/merge or production readiness assertion.
6. Update `HANDOFF.md`, issue #8 and PR #72 after significant changes, with actual commands/results, dependencies, residual risks, and accurate PR link.

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
- [CTO integration proposal](INTEGRATION_PROPOSAL.md)
- [Operational playbook](OPERATIONS.md)

## Nonnegotiable continuation policy

Follow repository ownership and source-of-truth policies. Work only in this issue's branch/owned path unless explicitly approved by CTO/integrator. Keep tests, actual measurements, known flaws, next tasks and links current. Do not silently edit shared docs, neighboring directions, or `main`. Do not fabricate evidence or merge without required checks and independent audit.
