# WexumVPN Node Registry & Infrastructure — engineering handoff

**Updated:** 2026-11-21 UTC (rechecked in GitHub).
**Owner lane:** GitHub issue [#4](https://github.com/Dimash313/Wexum/issues/4).
**Work branch:** `feat/vpn/4-node-registry`.
**Draft PR:** [#65](https://github.com/Dimash313/Wexum/pull/65) (open, draft, **not merged**).
**Functional-code checkpoint before this document:** `cebf51dfc2548b6410be37731071580eea3f36c3`. Always inspect the latest PR head rather than assuming this SHA is current.
**Integrated baseline:** PR [#1](https://github.com/Dimash313/Wexum/pull/1) was still open and unmerged when last checked; do **not** treat unmerged foundation documentation as integrated.

> **Session continuity policy (per project owner):** Treat this file as the lane-specific restart checkpoint. At every substantive implementation, test, audit, or dependency change update it *in this branch* before ending the stage. A new ChatGPT/Codex agent must read it and the live GitHub state before coding. No edits outside `products/vpn/nodes/` without explicit CTO/integrator approval. The issue, PR, and current repository remain the authoritative record when statements here become stale.

## 1. Scope and ownership

Own only `products/vpn/nodes/`: trusted inventory of VPN nodes, region/capability identifiers, health freshness and availability state, deterministic capacity-aware node selection, failure exclusion, bounded resource usage, internal contracts and tests, future scaling designs.

**Do not own** VPN tunnel/data plane, native clients, billing/entitlements, identity/authentication, connection-grant issuance, Control Plane HTTP APIs, shared contracts, shared CI or platform-wide documentation. Neighboring teams must retain their own APIs; propose cross-lane changes to CTO first.

Relevant boundaries: `products/vpn/control/` (Control Plane, issue [#2](https://github.com/Dimash313/Wexum/issues/2)); `products/vpn/entitlements/` ([#3](https://github.com/Dimash313/Wexum/issues/3)); identity ([#34](https://github.com/Dimash313/Wexum/issues/34)); operations/observability ([#8](https://github.com/Dimash313/Wexum/issues/8)); testing ([#10](https://github.com/Dimash313/Wexum/issues/10)); security ([#11](https://github.com/Dimash313/Wexum/issues/11)).

## 2. Architecture / decisions (proposed local implementation, not an approved cross-lane interface)

- Python standard library only. Pure in-memory, synchronous `NodeRegistry`; no database, external I/O, networking, monitoring service, secrets or runtime third-party dependencies.
- Immutable typed data: `Node`, `HealthObservation`, `NodeAvailability`, `NodeSelection`; enums `HealthStatus`, `AvailabilityStatus`, exception `StaleObservationError`.
- All operations on inventory and observations are serialized with `threading.RLock`. Registry capacity, reported sessions, identifier format, health TTL and snapshot size are bounded; the injected `now` must be UTC aware.
- `register(node)` creates an opaque random 128-bit `registration_id`; the health report must carry that generation. Disable/re-enable or remove/re-register invalidates previous registrations. Older/same-timestamp, future, expired and generation-mismatched reports are rejected. Registration IDs must **never** be mistaken for source authentication.
- Node discovery fails closed: only fresh, enabled, healthy, not-saturated nodes with matching region/capabilities are considered. Deterministic choice: lowest `active_sessions / max_sessions` (exact `Fraction`), then `node_id`.
- `NodeSelection` is an advisory snapshot, **not** a VPN permission, ticket, capacity reservation, real-time claim or signed authorization. Future Control Plane must independently authorize actor/tenant/device, recheck generation/health, and validate access grants.
- All `test-*` server/region identifiers are **synthetic**. No real servers, countries, latencies, uptime measurements, deployed tunnel, IP/DNS tests, geographic proof, or production data exist.
- Authoritative details, contract signatures and limitations: [lane README](README.md), [registry implementation](registry.py).

## 3. Implemented files / behavior

- `registry.py`: bounded node registration/removal/toggling; per-registration generation; trusted UTC health ingestion; stale/replay exclusion; snapshot enumeration and deterministic selection.
- `test_registry.py`: synthetic positive, negative and concurrency unit tests; includes removal/re-registration old-report replay and disable/re-enable rotation.
- `README.md`: trust boundary, internal contract proposal, error semantics, in-memory limitations, security/privacy/deployment blockers.
- `HANDOFF.md`: this continuity record. Update after material changes.

The code uses **no imports** from currently unmerged foundation PR #1. No public API or shared schema was changed. Draft PR #65 currently targets `main`; CTO/integrator decides approved retargeting/integration strategy.

## 4. Real verification and evidence (distinguish reported from independently checked)

**Reported previous local execution** in PR #65 at functional-code checkpoint `cebf51df` (not newly executed while writing this file):
- `python -X dev -m unittest discover -s products/vpn/nodes -p 'test_*.py' -v` — **18/18 passed** (reported Python 3.13).
- `python -m compileall -q products/vpn/nodes` — **passed**.
- **1000/1000** synthetic remove/re-register replay cycles rejected (reported local fault loop; not CI).
- Source file equality with tested local copies was reported and later GitHub lengths/hashes checked: `registry.py` length 10243, FNV32 `932381a5`; `test_registry.py` length 13456, FNV32 `25bc655d` (hashes are integrity comparisons only, not cryptographic verification).

**Independently rechecked now via GitHub API:** PR #65 open/draft; file blobs present at functional checkpoint; no formal submitted PR reviews; commit `cebf51df` has **no reported combined-status checks and no pull-request workflow runs** via available GitHub tools. Therefore **do not claim green CI, independent approval, production security or verified deployment**.

**Not executed in this handoff session:** a fresh full-checkout test run. Local container could not resolve `github.com` for `git ls-remote`; the documentation-only change needs its own latest-head CI/independent checks. The earlier 18/18 local report must not be silently upgraded to current-head CI proof.

To reproduce with a real checkout:

```sh
git switch feat/vpn/4-node-registry
python -X dev -m unittest discover -s products/vpn/nodes -p 'test_*.py' -v
python -m compileall -q products/vpn/nodes
```

Confirm test collection from the repository root, current branch head, interpreter version and GitHub Actions outcome.

## 5. Known findings / limitations / blockers

1. **Independent reviewer finding (MEDIUM) on old head `cacda031`:** stale old-instance report could reactivate a node after removal and re-registration. [Reviewer detail](https://github.com/Dimash313/Wexum/pull/65#issuecomment-7058339208). A per-registration ID fix and regressions were proposed in `cebf51df`; [re-audit requested](https://github.com/Dimash313/Wexum/pull/65#issuecomment-7058489564). **Do not mark the finding independently closed** before the auditor confirms it on the newest code.
2. Foundation [PR #1](https://github.com/Dimash313/Wexum/pull/1) remains unmerged/audit-blocked per latest check; audit [#41](https://github.com/Dimash313/Wexum/issues/41), authorization [#57](https://github.com/Dimash313/Wexum/issues/57) / draft [#58](https://github.com/Dimash313/Wexum/pull/58), catalog [#59](https://github.com/Dimash313/Wexum/issues/59) / draft [#60](https://github.com/Dimash313/Wexum/pull/60), CI coordination [#61](https://github.com/Dimash313/Wexum/issues/61), review governance [#38](https://github.com/Dimash313/Wexum/issues/38). Always recheck live status.
3. No trusted management/probe authentication, authorization, signed discovery, durable inventory, multi-worker consistency, persistent generation/sequence ordering, real monitoring, capacity reservation or automatic failover is implemented. In-memory restarts lose node state and fail closed.
4. Region IDs are declared identifiers, **not verified physical location**. Active sessions are trusted supplied metrics, not measured load. Bad/malicious adapters can fabricate observations. Monotonic timestamp comparisons rely on a trusted clock/source.
5. CTO must approve any external Control Plane/Entitlements contract and security/visibility policy before changes outside this lane. Real load, outage, DNS/IP-leak, security, legal, platform/store and religious reviews remain required before release.

## 6. Next concrete engineering steps (priority order)

1. Re-read live #4, PR #65 files/head, reviewer comments/threads, PR #1 and linked blocking issues. Check `AGENTS.md` and this file. **If an audit comment or code changed since this checkpoint, adapt before coding.**
2. Obtain independent retest of regression across remove/re-register, disable/re-enable, replay and concurrent update after the per-registration fix. Address any remaining review findings **only in owned files**; record exact test evidence in this document and PR.
3. Run unit/syntax tests against the newest checked-out branch and get current-head GitHub Actions checks via CTO-approved CI setup. Do not alter shared workflow without approval. Consider tests for long-lived restart semantics, expired/down concurrent reports and snapshot eligibility under churn.
4. Propose to CTO (issue/PR comment first) typed authenticated management/probe source, generation transfer/rotation, trust and time authority, node-visibility/tenant scope, recheck at allocation, and error/failure behavior. **Do not independently change `products/vpn/control/` or shared `docs/vpn/`**.
5. After interface approval, plan authoritative persistent inventory and multi-worker atomic state/replay protection, recovery drills and measured capacity; obtain infrastructure/cost/security review before provisioning.
6. Keep PR draft until foundation integration, interface decisions, final-head CI, independent audit and integrator approval. No direct `main` modification, self-review approval, force-push or self-merge.
7. Refresh `HANDOFF.md` after every major change (including changed issue/PR/base/SHA, executed test results, auditor disposition, next action); add a short PR checkpoint comment linking this file.

## 7. Linked source of truth

- Issue: [#4](https://github.com/Dimash313/Wexum/issues/4); working PR: [#65](https://github.com/Dimash313/Wexum/pull/65); branch: [feat/vpn/4-node-registry](https://github.com/Dimash313/Wexum/tree/feat/vpn/4-node-registry).
- [Lane README](README.md) and [code](registry.py) / [tests](test_registry.py).
- [AGENTS.md in foundation branch](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md), [VPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md), [VPN requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md).
- [Engineering quality](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md), [Review protocol](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/REVIEW_PROTOCOL.md), [Integrated state (integrator-owned)](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/STATE.md), [Religious review](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/policy/RELIGIOUS_REVIEW.md), [Agent startup](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/AGENT_START.md).

## 8. New-session execution rule

When the user says **«Продолжаем дальше»**, do not ask the owner to resend context. First inspect GitHub repository/main/branch/PR #65/issue #4 and updated shared policies, read this HANDOFF and lane README, determine current blockers and highest-priority **available** work, then implement it with tests inside this lane. Reconcile this file with real outcomes and report PR link, evidence and blockers. Only approach the owner for decisions requiring owner authority (e.g. budget/strategy/major product tradeoffs). Cross-team technical choices go to CTO/integrator through GitHub. Do not treat document existence as authorization to bypass reviews.
