# WexumVPN — Subscriptions & Billing | Agent Handoff

> **Scope owner:** GitHub issue [#9](https://github.com/Dimash313/Wexum/issues/9). **Updated:** 2026-11-21 (UTC).
> **Status:** Work in progress, **Draft PR only**; not merged, deployed, or production-ready.
> This file is the resumption point for any replacement engineer or agent.
> GitHub is the source of truth; refresh PR/issue/CI state before trusting this snapshot.

## 1. Direction and exclusive ownership

- **Direction:** WexumVPN — Subscriptions & Billing (subscription adapter).
- **Owned directory:** `products/vpn/subscriptions/`; all implementation, tests, notes, and **this handoff** must remain here unless CTO/integrator explicitly approves an interface proposal.
- **Responsibilities:** plan/order models; authoritative payment event verification boundary; idempotent receipts; renewals/expiry/cancellation; refund/chargeback handling; financially safe concurrency; privacy; prepared integration with Entitlements.
- **Not owned:** `products/vpn/entitlements/`, other products, identity, payment vendor accounts, node issuance, shared contracts, root `AGENTS.md`, `docs/engineering/STATE.md`, CI, legal/religious policy, or app clients. Do not edit sibling lanes or CTO-owned docs.

## 2. Architecture and accepted decisions

- **Source:** Python standard library only, `products/vpn/subscriptions/src/wexum_vpn_billing/`.
- **Data store:** local SQLite with WAL and per-call connections; `BEGIN IMMEDIATE` serializes event application, unique provider/event IDs and provider/transaction IDs enforce deduplication. Snapshot reads order + ledger in one DB transaction.
- **Models:** immutable `Plan`, `VerifiedEvent`, `Snapshot`, `WebhookResult`.
- **Entry boundary:** `BillingEngine.create_order(...)` must be invoked only by a trusted, **already authenticated and authorized** server. This module does not implement authentication. Server order binds tenant/account/plan/provider; all snapshot queries require the tenant and account match.
- **Webhook boundary:** `ProviderAdapter.verify(body, headers, received_at)` returns verified normalized events; **only** `TestHmacAdapter` exists, requiring explicit `allow_test_adapters=True`. It is a synthetic test fixture and **must never be wired to real payments**. Unapproved live providers are rejected.
- **Ledger semantics:** duplicate event ID with same body is idempotent; collisions are rejected; same transaction cannot grant another order; refund/chargeback tombstones can precede purchase events; cancellation leaves already-paid time in place; payment failure never grants access; a separate legitimately paid transaction can retain rights after another payment is refunded.
- **Projection:** `snapshot(tenant_id, account_id, order_id, now=...)` exposes server-side subscription eligibility. It is **NOT** a signed entitlement, JWT, access grant, proof of live payment, or client trust token.
- **Financial/privacy boundary:** no real payment execution or card storage; persist opaque order/tenant/account/transaction/event IDs, plan price snapshot, timestamps, refund state and webhook hash, but not raw webhook bodies. Storage encryption, retention, secure backup and reconciliation are **not implemented**.
- **Integration design:** provider → verified billing event ledger → future approved Entitlements authority → VPN control plane → node. **No direct cross-lane interface implemented.** Shared contract requires integrator-approved proposal/ADR.
- **Religious/commercial boundary:** no interest-based charges, gambling, hidden fees, fake discounts or silent subscription claims. Store/legal/qualified religious approval is required before real monetization. Synthetic fixture values are not approved retail prices.

## 3. Tracking and current GitHub pointers

- **Repository:** [Dimash313/Wexum](https://github.com/Dimash313/Wexum).
- **Owned issue:** [#9 — subscription-adapter](https://github.com/Dimash313/Wexum/issues/9) (open as checked 2026-11-21).
- **Working branch:** `feat/vpn/9-subscription-adapter`, based on `main`; never commit directly to `main`.
- **Draft PR:** [#73 — atomic verified-event ledger](https://github.com/Dimash313/Wexum/pull/73), open, Draft, **not merged** (checked 2026-11-21).
- **Last code head checked before this handoff commit:** `629a917f8d49d84590ac531a495426bc1f7890b5`. This handoff commit necessarily advances the branch head; inspect GitHub for the new SHA.
- **Upstream foundation:** [PR #1](https://github.com/Dimash313/Wexum/pull/1) remains open/unmerged as checked 2026-11-21; proposed docs are in its branch `architecture/foundation-and-agent-operating-system` until integrated.

## 4. Implemented files and behavior

1. [`src/wexum_vpn_billing/core.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/src/wexum_vpn_billing/core.py) — data types, test-only verification, atomic event ingestion, projections.
2. [`src/wexum_vpn_billing/__init__.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/src/wexum_vpn_billing/__init__.py) — public package exports.
3. [`tests/test_core.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/tests/test_core.py) — synthetic positive/negative/concurrency tests.
4. [`README.md`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/README.md) — trust boundaries, restrictions, manual test commands and release blockers.
5. `HANDOFF.md` — this agent continuation record.

No real provider adapter, checkout, receipt status API, issuer, distributed outbox, HTTP server or card processing is deployed.

## 5. Executed tests and verifiability

- **Previously reported in PR #73 (local workspace, Python 3.13.5):** 25/25 `unittest` cases passed; `compileall` reported passing. These are **author-reported local results** from the preceding implementation session, NOT independent CI or production evidence.
- **GitHub code parity reported previously:** executable test and source blob SHAs checked against the tested local copies; see PR body for exact hashes. The new handoff does not modify executable code.
- **Current follow-up check on 2026-11-21:** GitHub reports **0 pull-request workflow runs**, **0 commit statuses**, and **0 review submissions** on code head `629a917f8d49d84590ac531a495426bc1f7890b5`. CI is **unverified**, not green.
- **Current local rerun:** **NOT COMPLETED**. Direct `git clone` in the available container failed: `Could not resolve host: github.com`. Do not record another pass unless the exact commands actually run.

Commands to rerun on a clone of the PR branch (repository root):

```sh
PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v
python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests
```

Coverage includes invalid signatures/timestamps, malformed JSON, repeated/colliding events, cross-order transaction reuse, wrong tenant/account, price mismatch, refund-before-payment, no resurrection, cancellation/resume, failed payment, expiry, restart persistence and concurrent deliveries. Real vendor reconciliation/failure and end-to-end security tests do **not** exist.

## 6. Known errors, risks and blocking dependencies

- **Foundation blocking:** [PR #1](https://github.com/Dimash313/Wexum/pull/1) not yet integrated; do not depend on proposed shared interfaces as if merged. Recheck before any further work.
- **Entitlements / trust blocking:** [Issue #3](https://github.com/Dimash313/Wexum/issues/3), [PR #64](https://github.com/Dimash313/Wexum/pull/64) and identity [Issue #34](https://github.com/Dimash313/Wexum/issues/34). No approved trusted identity adapter, signed grants, atomic revocation transport, offline policy, or published Billing↔Entitlements event contract.
- **Live payments blocking:** no selected merchant/store vendor, no real receipt/webhook signature and merchant-account verification, no authenticated verification against provider records, no provider reconciliation or failure policy. Synthetic HMAC signing is test-only.
- **Store/legal/ethical blocking:** country/store requirements, age and merchant eligibility, payout/tax obligations, explicit recurring-billing consent, refunds/cooling-off, fair price display, and qualified religious review not approved.
- **Operational gaps:** no migrations, data deletion/retention, DB file permission/encryption guarantees, disaster recovery / backup tests, outbox, replay audit export, rate limiting, monitoring or real-volume performance data.
- **Consistency gap:** snapshots are local projections without distributed invalidation. Consumers could grant access from stale caches after refund unless a reviewed revocation and freshness contract is designed.
- **Event semantics gap:** this is a minimal synthetic event schema; real providers differ in receipt ownership, partial refunds, chronology, renewal retries, store-side grace, cancellation semantics and out-of-order updates. Do not claim production correctness.
- **CI gap:** no verified green GitHub Actions for this branch; independently reviewed regression suite and security assessment are pending.
- **Current tooling issue:** container cannot resolve github.com for a direct clone; GitHub connector reads and writes do work.

## 7. Concrete next tasks (in priority order)

1. **Session intake:** inspect repo/head, `AGENTS.md`, this file, current #9 and PR #73, PR #1 state, latest reviews/CI, owner comments, and Entitlements/Identity dependency issues. Check no competing ownership and no unexpected branch changes.
2. **Reproduce tests:** clone/checkout the PR branch in a network-enabled/test runner; run the two commands above; record Python version, latest commit SHA, exact failures/pass counts and CI evidence here and in PR #73. If clone remains unavailable, report it, never guess.
3. **Independent review:** audit ledger for replay consistency, incorrect tenant/order binding, state ordering, refunds vs newer renewal, SQLite crash/rollback, cancellation races, timestamp assumptions and privacy. Add minimal failing regression tests before repairs, only in this owned directory.
4. **Interface proposal (do not edit sibling files):** specify billing-to-Entitlements consumer contract, authority/freshness, event schema, revision/outbox, idempotency and rollback; seek CTO/integrator approval before cross-lane implementation.
5. **Provider design gate:** document vendor/store requirements and jurisdiction restrictions; design a real adapter's receipt verification and reconciliation in a separate approved change, but **do not** connect credentials or execute payments without owner's explicit permission.
6. **Hardening plan:** storage schema migrations, retention/deletion, backup/restore, reconciliation, observability without PII, concurrency and fault injection; implement small incremental changes with tests after upstream contracts are approved.
7. **Before handing off:** update this `HANDOFF.md`, the same Draft PR #73 (one issue/branch/PR), test evidence, blockers and links. No self-merge or claim of readiness.

## 8. References

- [AGENTS.md — proposed foundation](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md)
- [WexumVPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md)
- [WexumVPN product requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md)
- [Proposed entitlement contract](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ENTITLEMENTS.md)
- [Engineering quality requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)
- [Engineering review protocol](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/REVIEW_PROTOCOL.md)
- [Religious review policy](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/policy/RELIGIOUS_REVIEW.md)
- [Issue #9](https://github.com/Dimash313/Wexum/issues/9), [Draft PR #73](https://github.com/Dimash313/Wexum/pull/73), [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1), [Entitlements #3](https://github.com/Dimash313/Wexum/issues/3), [Entitlements PR #64](https://github.com/Dimash313/Wexum/pull/64), [Identity #34](https://github.com/Dimash313/Wexum/issues/34).
