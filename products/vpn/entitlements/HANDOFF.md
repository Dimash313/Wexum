# HANDOFF — WexumVPN Entitlements & Access Grants

**Status as of 2026-11-21:** active, isolated prototype in an **open Draft PR**. This is a continuity record for a replacement ChatGPT/Codex engineer, **not** a release certificate or integration approval. Always verify live GitHub before acting: details below can become stale.

## 1. Owner, mission, exact boundaries

- Direction: **WexumVPN — Entitlements & Access Grants**; GitHub [issue #3](https://github.com/Dimash313/Wexum/issues/3).
- Owned path (exclusive): `products/vpn/entitlements/`. All implementation, tests, design notes and this HANDOFF belong here.
- Responsible for: server-side eligibility; subscription/device/account expiry and binding; eventual **server-issued, node-verifiable short-lived grants**, revocation and replay policy; fail-closed outages; interoperable contracts with Identity, Billing/Subscriptions, VPN Control Plane and VPN Node.
- **Do not modify** root `AGENTS.md`, `docs/engineering/STATE.md`, `docs/vpn/`, shared APIs/CI, other products or sibling VPN lanes without CTO/integrator approval and the required cross-lane ADR/issue.
- Do not self-merge or claim production-ready VPN or independently verified security. No real VPN connection, signed grant, active subscription verifier or deployed authorization API is present in this lane.

## 2. Current architecture and decisions

Source layout:
- `src/wexum_vpn_entitlements/policy.py` — dependency-free Python async `GrantPrecheck.check(actor, device_id, scope)` and data contracts (`AuthenticatedActor`, `AccountState`, `SubscriptionState`, `DeviceState`, `GrantCandidate`), `GrantPrecheckDenied`, `GrantPrecheckUnavailable`.
- `src/wexum_vpn_entitlements/__init__.py` — exports.
- `tests/test_policy.py` — isolated authority-adapter/unit tests (synthetic data only).
- `README.md` — runtime limitations and the proposed integration boundary.
- `HANDOFF.md` — this continuation document.

**Trust boundary:** `AuthenticatedActor` is expected to be created by an upstream **verified Identity adapter**; account, subscription and device snapshots must come from **authenticated authoritative server-to-server adapters**, never client headers, JSON, a UI subscription flag or test mocks in production. This module **cannot** establish those upstream guarantees by itself. `GrantCandidate` is an **unsigned internal precheck result only**; it must never be given to a client, used by a VPN node as a permit, or presented as proof of paid service.

Current fail-closed policy:
- Strict tenant, subject, device, issuer, audience and scope equality/checks; active account, subscription and device; state snapshot freshness (default 10 s) and future skew (default 5 s).
- Actor/session, subscription, device and candidate expirations are checked using timezone-aware times; candidate TTL capped at 120 s and each upstream expiry. Defaults are **provisional**, not approved revocation SLAs.
- `asyncio.TaskGroup` + `asyncio.timeout` cancel/join cooperative sibling authority lookups on an error or timeout. Caller cancellation propagates. Self-cancelled authority => unavailable. Adapters that suppress cancellation are not forcibly terminated; upstream network operations need separate timeouts and review.
- Expired actor denied before authority IO; authority/clock failures fail closed. A wall-clock rollback > configured skew during lookup fails closed; smaller rollback does not extend TTL. Time freshness uses a bounded datetime difference (`now - checked_at`), not timestamp +/- arithmetic at datetime limits; remaining lifetime is capped by actor/subscription/device expiry **before** addition to the clock. Actor issuer/audience must have exact string types, not merely comparison equality. Exception chaining is suppressed from normally displayed traceback, but `__context__` remains inspectable and adapters/loggers must independently avoid secrets.

**Explicitly absent:** signed/asymmetric permit format and verification; device key proof-of-possession; replay/session lease store; atomic issuance versus revocation; key storage/rotation/emergency revocation; node audience enforcement; real billing provider events/verified payments/chargebacks; trusted Identity/OIDC; HTTP API; durable notification/expiry propagation to VPN nodes; production outage/offline session handling. No homemade cryptography or unsigned client-issued credentials may be introduced to bypass these dependencies.

## 3. GitHub task/branch/PR

- Issue: [#3](https://github.com/Dimash313/Wexum/issues/3) (open).
- Branch: `feat/vpn/3-entitlements`, branched from `main`.
- Draft PR: [#64](https://github.com/Dimash313/Wexum/pull/64), targets `main`; do not merge until foundation, independent audit, and contracts approved.
- Last independently checked **source-and-test** commit: `16af20df3b5af523b94a51a208db405709dbe906`. Documentation commits will advance the PR head; always re-query its SHA.
- GitHub account may be shared by AI authors and the reviewer, so a review/comment under the same owner account is **not** necessarily a distinct independent approval.

## 4. Implemented work

- Typed local contracts for checked actor/account/subscription/device states and grant-candidate result.
- Pre-check deny for malformed/wrong issuer/audience/tenant/subject/device/scope, deleted account, inactive/expired subscription, revoked/expired device, stale timestamps and invalid timezone.
- Asynchronous service-authority lookups, bounded timeouts, cancellation handling; explicit unavailable result for faults, no new access while control plane is offline.
- Clock rollback, datetime boundary arithmetic, strict actor string types and displayed-error suppression regression handling; intentionally **no issuance**.
- No persistence/migrations, production secrets, external APIs, new paid services or new dependencies.

## 5. Real test evidence — label scope precisely

Last verified **2026-11-21**, local Python **3.13.5**, exact in-session source/test copies with byte-identical Git blob SHAs to PR #64:
```sh
PYTHONPATH=products/vpn/entitlements/src python -m unittest discover -s products/vpn/entitlements/tests -v
# Observed: Ran 40 tests in 0.072s — OK
python -m compileall -q products/vpn/entitlements/src products/vpn/entitlements/tests
# Observed: exit 0, no errors
```
Source file blob SHA `policy.py=5ec70e2ad6cc8d54bb01212b891e421141c95407`; tests `test_policy.py=65f3cfeeb3e45b3cfc4b02173c2184cf6c212fab`; exports `__init__.py=ea3be77ff6e7bb8b23b4cba37e60ebfab3348d8d`. Four additional tests since the previous checkpoint: near-min datetime snapshot, near-max candidate expiry, future snapshot outside skew near min, and custom equality-impersonation of actor issuer/audience. These verify input/temporal handling **only**, not live service integration.

**No independent clean-clone test, Python 3.12 execution, GitHub CI, deployed tunnel, or full signed-grant verifier has been verified.** Earlier PR head `11c60432` had 0 Actions runs and commit statuses. Re-query CI on the latest head, including documentation commits. Do not claim passing CI merely from local tests.

## 6. Known defects, blockers and review status

- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) is still unmerged at latest inspection (2026-11-21); root `AGENTS.md` and `docs/vpn/ENTITLEMENTS.md` are on its branch and **proposed**, not integrated `main`. Auditor [#41](https://github.com/Dimash313/Wexum/issues/41) has unresolved blockers.
- Independent static-review checkpoint on [PR #64](https://github.com/Dimash313/Wexum/pull/64#issuecomment-7058343912) marked **INCOMPLETE AUDIT / BLOCKED** on old head `93414d3`. Latest work requires fresh independent review and CI; never claim approval.
- Cross-team prerequisites: [Control Plane #2 / PR #55](https://github.com/Dimash313/Wexum/pull/55), [Security Review #11](https://github.com/Dimash313/Wexum/issues/11), [Identity #34 / PR #62](https://github.com/Dimash313/Wexum/pull/62), [Subscriptions #9](https://github.com/Dimash313/Wexum/issues/9) and eventual VPN node verification. Real verified billing and Identity authority adapters do not exist here.
- Control Plane PR #55 has independent CI blocker findings reported under [#11](https://github.com/Dimash313/Wexum/issues/11): active-device listing with >200 revoked rows and unhandled SQLite availability exceptions. **Do not change its files**; owner #2 resolves.
- Unresolved architectural decisions: asymmetric signature format/library, issuer and key custody, tenant+node audience and device-key binding, signed permit TTL, replay/session policy and capacity, atomic revocation generations, session termination, node offline exposure/rotation budgets and security review.
- Other unknowns: performance, concurrency across deployments, cancellation-resistant adapters, storage/transport, user deletion, legal/store/privacy/religious gate, operational telemetry. The code cannot address all of these until authoritative infrastructure exists.

## 7. Next concrete tasks when asked “Продолжаем дальше”

1. **Re-inspect live GitHub**: latest `main`, AGENTS instructions (on foundation branch if not merged), relevant `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/vpn/ENTITLEMENTS.md`, `docs/engineering/QUALITY.md`, policy docs, this HANDOFF, #3, PR #64 comments/reviews/checks, #1/#41, #2/#55, #11, #9 and #34. Determine whether any dependency became approved or whether another engineer edited the lane.
2. Choose the smallest **independently testable issue-owned change** that does not assume signed-credential approval. Review remaining boundaries such as malformed trusted-adapter outputs, clock timezone behavior, concurrent state races, cancellation and tenant isolation. Do not conflate these with finalized signed-permit integration; avoid speculative cross-lane interfaces.
3. Implement within `products/vpn/entitlements/`; add regression tests, run exact commands and record actual output, SHA, and any differences from previous evidence. Baseline local suite is currently 40 passing tests on Python 3.13.5. Do not report "green" for missing GitHub Actions.
4. Coordinate cross-lane open decisions through #3 and #11 / CTO comments without directly editing shared contracts; request approval before designing real signing and gateway acceptance.
5. Update PR #64 with real test evidence, known blockers and changed files; update this HANDOFF **on every substantial change and before stage completion**. Leave PR Draft/unmerged unless integrator authorizes next lifecycle state.

## 8. Authoritative links

- [Repo](https://github.com/Dimash313/Wexum) · [Issue #3](https://github.com/Dimash313/Wexum/issues/3) · [Draft PR #64](https://github.com/Dimash313/Wexum/pull/64) · [owned README](README.md)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) · [Foundation audit #41](https://github.com/Dimash313/Wexum/issues/41) · [Proposed entitlement design](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ENTITLEMENTS.md)
- [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55) · [Security #11](https://github.com/Dimash313/Wexum/issues/11) · [Subscriptions #9](https://github.com/Dimash313/Wexum/issues/9) · [Identity PR #62](https://github.com/Dimash313/Wexum/pull/62)
- [Foundation AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md) · [Quality](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)

## Permanent continuation rule (owner instruction)

On replacement of this AI or creation of a new chat, use **GitHub + `HANDOFF.md`** as durable project memory. On **«Продолжаем дальше»**, independently inspect AGENTS, this HANDOFF, relevant direction documentation, issues and PR state; select and execute the next permitted concrete engineering step, test it, and update PR + HANDOFF without needing the owner to repeat context. Never edit other directions' documentation without CTO authorization; never override integration and review gates.
