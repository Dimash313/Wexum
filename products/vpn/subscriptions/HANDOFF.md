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
- **Data store:** local SQLite with WAL and per-call connections; `BEGIN IMMEDIATE` serializes event application and checkout order creation, unique provider/event IDs and provider/transaction IDs enforce deduplication. The additive `order_requests` table binds a hashed, tenant+account scoped checkout request to one order; on collision with different terms the transaction rolls back and raises `ConflictError`. Snapshot reads order + ledger in one DB transaction.
- **Models:** immutable `Plan`, `VerifiedEvent`, `Snapshot`, `WebhookResult`.
- **Entry boundary:** `BillingEngine.create_order(..., *, now, request_id)` now **requires** an opaque stable checkout request ID supplied by a trusted, **already authenticated and authorized** server. Same scoped request and same plan/currency/amount/provider returns the same order across threads/processes/restarts; a reused request with different terms is rejected. The idempotency token is not proof of payment or identity; this module does not authenticate callers. All snapshot queries require tenant/account match. Previously created orders without an `order_requests` row cannot be retroactively deduplicated.
- **Webhook boundary:** `ProviderAdapter.verify(body, headers, received_at)` returns verified normalized events; **only** `TestHmacAdapter` exists, requiring explicit `allow_test_adapters=True`. It is a synthetic test fixture and **must never be wired to real payments**. Unapproved live providers are rejected.
- **Ledger semantics:** duplicate event ID with same body is idempotent; collisions are rejected; same transaction cannot grant another order; refund/chargeback tombstones can precede purchase events; cancellation leaves already-paid time in place; payment failure never grants access; a separate legitimately paid transaction can retain rights after another payment is refunded.
- **Projection:** `snapshot(tenant_id, account_id, order_id, now=...)` exposes server-side subscription eligibility. It is **NOT** a signed entitlement, JWT, access grant, proof of live payment, or client trust token.
- **Financial/privacy boundary:** no real payment execution or card storage; persist opaque order/tenant/account/transaction/event IDs, a SHA-256 hash of scoped checkout request identity, plan price snapshot, timestamps, refund state and webhook hash, but not raw webhook bodies or raw checkout request keys. Storage encryption, retention, secure backup and reconciliation are **not implemented**.
- **Integration design:** provider → verified billing event ledger → future approved Entitlements authority → VPN control plane → node. **No direct cross-lane interface implemented.** Shared contract requires integrator-approved proposal/ADR.
- **Religious/commercial boundary:** no interest-based charges, gambling, hidden fees, fake discounts or silent subscription claims. Store/legal/qualified religious approval is required before real monetization. Synthetic fixture values are not approved retail prices.

## 3. Tracking and current GitHub pointers

- **Repository:** [Dimash313/Wexum](https://github.com/Dimash313/Wexum).
- **Owned issue:** [#9 — subscription-adapter](https://github.com/Dimash313/Wexum/issues/9) (open as checked 2026-11-21).
- **Working branch:** `feat/vpn/9-subscription-adapter`, based on `main`; never commit directly to `main`.
- **Draft PR:** [#73 — atomic verified-event ledger](https://github.com/Dimash313/Wexum/pull/73), open, Draft, **not merged** (checked 2026-11-21).
- **Latest executable code blobs locally run and matched to GitHub:** `core.py=14a1a7e5de8afbb94f0f3a7f5b2fab44ec1392d1`, `test_core.py=a0f33b1341b2032ae68457c8ee878b585217c3a2`. Latest code+README commit before this handoff update: `30e2c677a324659c5c909efa69ead88b103ea0f6`. Inspect GitHub for the new branch HEAD after this handoff commit.
- **Upstream foundation:** [PR #1](https://github.com/Dimash313/Wexum/pull/1) remains open/unmerged as checked 2026-11-21; proposed docs are in its branch `architecture/foundation-and-agent-operating-system` until integrated.

## 4. Implemented files and behavior

1. [`src/wexum_vpn_billing/core.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/src/wexum_vpn_billing/core.py) — data types, test-only verification, atomic checkout idempotency (`order_requests` and required `request_id`), event ingestion, projections.
2. [`src/wexum_vpn_billing/__init__.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/src/wexum_vpn_billing/__init__.py) — public package exports.
3. [`tests/test_core.py`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/tests/test_core.py) — 32 local synthetic positive/negative/concurrency tests, including 7 checkout idempotency scenarios.
4. [`README.md`](https://github.com/Dimash313/Wexum/blob/feat/vpn/9-subscription-adapter/products/vpn/subscriptions/README.md) — trust boundaries, restrictions, manual test commands and release blockers.
5. `HANDOFF.md` — this agent continuation record.

No real provider adapter, checkout, receipt status API, issuer, distributed outbox, HTTP server or card processing is deployed.

## 5. Executed tests and verifiability

- **Reproduced locally this session on 2026-11-21:** checked out the prior GitHub source from the mounted working directory and verified the old `core.py` and `test_core.py` Git blob SHA matched the baseline GitHub blobs. Python 3.13.5, `25/25` existing tests passed (0.274 seconds).
- **Test-first exercise:** before implementation, the new API-based test suite was run against old source; it failed with `BillingEngine.create_order() got an unexpected keyword argument 'request_id'`. No false success claimed.
- **After implementing and locally testing the updated source:** **32/32 unittests passed, 0.346 seconds**, using the command below; `python -m compileall -q` passed without errors. The 7 additional tests cover same checkout retry, conflict on changed plan, tenant+account scoping, restart persistence, 8-thread simultaneous duplicate checkout, injected SQLite failure rollback, and invalid request keys.
- **GitHub parity checked:** GitHub code blobs exactly match locally tested source: `core.py=14a1a7e5de8afbb94f0f3a7f5b2fab44ec1392d1`; `test_core.py=a0f33b1341b2032ae68457c8ee878b585217c3a2`.
- **GitHub CI/review check:** on commit `30e2c677a324659c5c909efa69ead88b103ea0f6`, **0 PR workflow runs**, **0 commit statuses** and **0 review submissions**. These results do NOT certify green CI or independent validation; a later handoff/docs commit also needs rechecking.
- **Local clone limitation:** container cannot resolve `github.com` for direct `git clone`, but source files were available in the mounted local working directory. They were verified by Git SHA against the live GitHub connector before editing; no network dependency is used for tests.

Commands run from local working directory root:

```sh
PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v
# Ran 32 tests in 0.346s — OK
python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests
# Exit 0
```

Other coverage includes invalid signatures/timestamps, malformed JSON, repeated/colliding events, cross-order transaction reuse, wrong tenant/account, price mismatch, refund-before-payment, no resurrection, cancellation/resume, failed payment, expiry, restart persistence and concurrent deliveries. Real vendor reconciliation/failure and end-to-end security tests do **not** exist.

## 6. Known errors, risks and blocking dependencies

- **Foundation blocking:** [PR #1](https://github.com/Dimash313/Wexum/pull/1) not yet integrated; do not depend on proposed shared interfaces as if merged. Recheck before any further work.
- **Entitlements / trust blocking:** [Issue #3](https://github.com/Dimash313/Wexum/issues/3), [PR #64](https://github.com/Dimash313/Wexum/pull/64) and identity [Issue #34](https://github.com/Dimash313/Wexum/issues/34). No approved trusted identity adapter, signed grants, atomic revocation transport, offline policy, or published Billing↔Entitlements event contract.
- **Live payments blocking:** no selected merchant/store vendor, no real receipt/webhook signature and merchant-account verification, no authenticated verification against provider records, no provider reconciliation or failure policy. Synthetic HMAC signing is test-only.
- **Store/legal/ethical blocking:** country/store requirements, age and merchant eligibility, payout/tax obligations, explicit recurring-billing consent, refunds/cooling-off, fair price display, and qualified religious review not approved.
- **Operational gaps:** additive `order_requests` DDL exists but there is no production migration plan for pre-existing orders/checkout keys; no data deletion/retention, DB file permission/encryption guarantees, disaster recovery / backup tests, outbox, replay audit export, rate limiting, monitoring or real-volume performance data.
- **Consistency gap:** snapshots are local projections without distributed invalidation. Consumers could grant access from stale caches after refund unless a reviewed revocation and freshness contract is designed.
- **Event semantics gap:** this is a minimal synthetic event schema; real providers differ in receipt ownership, partial refunds, chronology, renewal retries, store-side grace, cancellation semantics and out-of-order updates. Do not claim production correctness.
- **CI gap:** no verified green GitHub Actions for this branch; independently reviewed regression suite and security assessment are pending.
- **Current tooling issue:** container cannot resolve github.com for a direct clone; mounted exact source was available and executed locally, and GitHub connector reads and writes do work.

## 7. Concrete next tasks (in priority order)

1. **Session intake:** inspect repo/head, `AGENTS.md`, this file, current #9 and PR #73, PR #1 state, latest reviews/CI, owner comments, and Entitlements/Identity dependency issues. Check no competing ownership and no unexpected branch changes.
2. **Verify the new head:** rerun all 32 tests when new code lands or on a network-enabled runner; verify latest executable blob SHA and independent CI evidence here and in PR #73. The local rerun of the current executable changes is complete, but GitHub CI is not.
3. **Independent review:** audit new order-request idempotency key lifecycle, request replay conflicts, historical-order migration, tenant binding, ledger replay consistency, refund chronology, SQLite crash/rollback, cancellation races, timestamp assumptions and privacy. Add minimal failing regression tests before repairs, only in this owned directory.
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
