## Backend checkpoint — 2026-11-22: concurrent conflicting checkout idempotency regression

- **Scope/priority:** Issue #9, branch `feat/vpn/9-subscription-adapter`, Draft PR #73; billing-owned test and HANDOFF only. P2 concurrency integrity regression, not a production change.
- **Test:** `test_concurrent_conflicting_checkout_terms_create_only_one_order` starts two synchronized checkout attempts using the same tenant/account/request key but different server-approved plan terms. Exactly one must create an order, the other must raise `ConflictError`; one request mapping must remain, no second new order and no access grant. This complements existing same-key/same-terms concurrency and sequential conflicting-terms tests.
- **Test commit:** [69ae135](https://github.com/Dimash313/Wexum/commit/69ae13561dbd90d4215a521e910d7d9171ace64b). **Evidence:** GitHub file write PASS; local checkout blocked by DNS (`Could not resolve host: github.com`); Python unittest NOT RUN, compileall NOT RUN. Prior PR head `fe4e8e22` had zero commit statuses and zero PR workflow runs; latest HEAD CI NOT VERIFIED; independent audit PENDING.
- **Next:** run `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests` against the exact latest branch head, inspect CI and request independent audit. Keep PR Draft; do not merge or activate real payments.

## Backend checkpoint — 2026-11-22: reject ephemeral SQLite storage

- **Scope:** Issue #9, existing Draft PR #73, billing-owned source/tests/HANDOFF only. P2 reliability and integrity guard; no cross-lane API, payment integration, deployment or migration.
- **Defect:** BillingEngine uses separate SQLite connections for schema creation, checkout, ledger updates and reads. Accepting `:memory:` silently creates an independent empty database on each call, breaking the durable-ledger contract. Empty or non-path inputs could also reach sqlite3 with uncontrolled errors.
- **Fix:** reject `:memory:`, empty strings and non-`str`/`Path` values with sanitized `SecurityError("durable billing database path required")` before connecting. This does not claim to guarantee durable disk or forbid caller-provided special filesystem paths; the deployment adapter must still supply and protect an approved persistent path.
- **Source commit:** [bc5aeb1](https://github.com/Dimash313/Wexum/commit/bc5aeb15bed6f123721df7eceba93af98a3dfb2c). **Regression commit:** [f4a69d8](https://github.com/Dimash313/Wexum/commit/f4a69d82c111401d4725d9cb84d7b58da1fcae57), four invalid path values and unchanged existing ledger state.
- **Evidence:** GitHub writes **PASS**. Python unit tests **NOT RUN**, compileall **NOT RUN**, exact-head CI **NOT VERIFIED**, independent audit **PENDING**. No successful runtime tests are claimed.
- **Next:** execute `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests` on latest exact source; coordinate final-head CI with integrator and independent audit. PR remains Draft; no merge or real payments.

## Backend checkpoint — 2026-11-21: atomic event-ledger fault regression

- **Scope / priority:** Billing issue #9, existing branch `feat/vpn/9-subscription-adapter`, Draft PR #73. Targeted P1 integrity regression; no production logic or cross-lane contracts changed.
- **New test:** `test_event_insert_failure_rolls_back_payment_and_allows_retry` injects a SQLite `BEFORE INSERT ON events` abort *after* the transaction row would be inserted. It asserts sanitized `BillingError`, zero event/transaction rows, unchanged order revision, no entitlement, and a successful retry after the trigger is removed. This exercises the all-or-nothing payment/ledger boundary and guards against future transaction refactors.
- **Commit:** [47e1129](https://github.com/Dimash313/Wexum/commit/47e1129cc1999d9794559ffa6c2c5907d5f18619), `products/vpn/subscriptions/tests/test_core.py` only.
- **Evidence:** GitHub file update **PASS**; local Python unittest **NOT RUN** and compileall **NOT RUN** because the execution environment could not resolve `github.com` for checkout; GitHub combined statuses on preceding head `97956bb5`: empty, not a CI pass. Exact new-head GitHub CI **NOT VERIFIED**. Independent review **PENDING**.
- **Next:** run `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests` on this branch, activate/verify CI via integrator-owned workflow, request independent audit. Foundation #1, provider authority, Identity/Entitlements integration remain blocked. Do not merge or deploy.

## Backend checkpoint — 2026-11-21: signed JSON nesting failure

- **Issue/ownership:** #9, branch `feat/vpn/9-subscription-adapter`, Draft PR #73; only billing-owned `core.py`, `test_core.py`, and this HANDOFF changed. Existing foundation and payment-authority contracts remain unmerged/unapproved.
- **Defect and correction:** A correctly HMAC-signed but deeply nested JSON body can raise Python `RecursionError` in `json.loads`, escaping the intended sanitized `SecurityError` boundary. The test-only adapter now catches `RecursionError` alongside JSON parse errors, returning `SecurityError("invalid webhook JSON")` without changing ledger state. No change to accepted events or production integrations.
- **Code:** [e5ad60b](https://github.com/Dimash313/Wexum/commit/e5ad60b5486cd51b0bcd92ea80577adce5ba7d71). **Regression:** [d896d58](https://github.com/Dimash313/Wexum/commit/d896d5820cdc6000f29db8cf6bb213e7cb7cacb4), signs a 1200-level nested JSON array and checks sanitized rejection, unchanged revision and no eligibility.
- **Evidence:** GitHub code/test writes PASS. Python billing unit tests **NOT RUN**; compileall **NOT RUN**; GitHub Actions latest-head **NOT VERIFIED**; independent review **PENDING**. Local `git ls-remote` failed with `Could not resolve host: github.com`; authored test is not evidence of execution.
- **Next:** run `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests` on exact head; coordinate final-head CI with integrator and independent audit. PR remains Draft, no merge, no real payments.

## Backend engineering checkpoint — 2026-11-21: bounded synthetic webhook headers

- **Scope:** Subscriptions & Billing #9, Draft PR #73, only `products/vpn/subscriptions/`; no shared contract changes. This remains a test-only HMAC adapter and is not a real payment gateway.
- **Change:** bound HTTP-header container to at most 32 entries, each key to 128 characters, each value to 256 characters, and reject non-ASCII header names before case normalization. This limits untrusted parsing work and removes Unicode case-fold ambiguity. The existing duplicate-header, type, timestamp and signature checks remain in place.
- **Code:** [f874187](https://github.com/Dimash313/Wexum/commit/f8741879dc06e5602221e315616169a3fc320372); **regression:** [de42b06](https://github.com/Dimash313/Wexum/commit/de42b06a1573257a2faa238b709b9f65db46ad21), covering excess header count, key/value length, Unicode header name and unchanged ledger/eligibility on rejection.
- **Verification:** GitHub writes PASS. Python unit tests **NOT RUN**; compileall **NOT RUN**; latest-head CI **NOT VERIFIED**; independent audit **PENDING**. Direct Git clone in local runtime failed DNS resolution for `github.com`. Authored regression assertions are not execution evidence.
- **Next:** run full billing tests and compileall on exact source, then final-head CI and independent review. Foundation #1 and approved Identity/Entitlements/payment-provider contracts remain blocking; do not merge or deploy.

## Backend engineering checkpoint — 2026-11-21: malformed webhook provider identifier

- **Scope:** Subscriptions & Billing issue #9, existing Draft PR #73, owned path `products/vpn/subscriptions/` only. Foundation remains unmerged.
- **Problem:** `accept_webhook(provider, ...)` previously passed an arbitrary provider value directly to `dict.get`; unhashable input such as `[]` or `{}` raised uncontrolled `TypeError` instead of the established `SecurityError` boundary. This is defensive input handling for a synthetic adapter, not proof of a public exploit or real provider integration.
- **Change:** enforce string provider type before adapter lookup; preserve existing unknown-provider rejection. Regression tests supply `None`, `[]`, `{}`, and integer provider and verify unchanged revision and no eligibility.
- **Code commit:** [59796b8](https://github.com/Dimash313/Wexum/commit/59796b841a7dae6d7c8cdf3ba2429f3c95ab40c4); **test commit:** [a8cb5fa](https://github.com/Dimash313/Wexum/commit/a8cb5fa71e2078d4c1dff7b40a96685f2a523bcd).
- **Actual evidence:** GitHub write PASS; Python unittest **NOT RUN**; compileall **NOT RUN**; current-head GitHub Actions **NOT VERIFIED**; independent audit **PENDING**. Direct git clone from container failed DNS resolution (`Could not resolve host: github.com`). No green CI claim.
- **Next:** execute `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests` on exact source; obtain independent review and final-head CI. No merge; no live payment adapter.

# WexumVPN — Subscriptions & Billing | Agent Handoff

## Backend engineering checkpoint — 2026-11-21: reject non-mapping webhook headers

- **Scope:** Subscriptions & Billing, issue #9, branch `feat/vpn/9-subscription-adapter`, Draft PR #73. No changes outside `products/vpn/subscriptions/`.
- **Change:** `TestHmacAdapter.verify` now checks that `headers` implements `Mapping` before invoking `.items()`. Previously a missing or list/string header container could raise an uncontrolled `AttributeError`; now it fails closed with `SecurityError("invalid test signature headers")`. This remains a synthetic test adapter, **not** a production webhook or payment authority.
- **Code:** [4dfbe27](https://github.com/Dimash313/Wexum/commit/4dfbe277a85ad73f07d8b24bcfe90337f9819dd8); **regression:** [cfd8f2e](https://github.com/Dimash313/Wexum/commit/cfd8f2ef5d61fa5e58b61555bd297d8352ddea4e), one test method with four malformed container cases, checking no ledger revision or eligibility mutation.
- **Evidence:** GitHub write and source reread **PASS**; Python unittest **NOT RUN**; compileall **NOT RUN**; exact-head GitHub Actions **NOT VERIFIED**; independent audit **PENDING**. Do not infer PASS from authored tests. CI workflow activation is integrator-owned; foundation #1 and trusted identity/entitlement/provider integrations remain blocked.
- **Next:** run `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests`; obtain exact-head CI and distinct independent audit. Keep PR Draft; no merge.


## Backend engineering checkpoint — 2026-11-21: duplicate signature-header ambiguity

- **P1 security hardening (test-only webhook boundary):** `TestHmacAdapter.verify` now rejects case-insensitively duplicate HTTP header names instead of silently choosing the last value. It also rejects non-string header keys/values as `SecurityError` rather than leaking an accidental `AttributeError`. This prevents differing proxy/framework header canonicalization from making signature verification ambiguous. No real payment provider is enabled or added.
- **Code commit:** [d152924](https://github.com/Dimash313/Wexum/commit/d1529243112c9f8b3f6ae24acaf586b2886b3fd8). **Regression tests commit:** [96987de](https://github.com/Dimash313/Wexum/commit/96987def9d7642503f19510c92f57f395c6746b1). Only billing-owned files changed.
- Added two test methods: four conflicting/equivalent mixed-case signature/timestamp variants must reject with no ledger mutation, and non-string header values/keys must reject with no ledger mutation. Existing valid single-case headers remain supported by implementation.
- **Verification:** GitHub connector write/read of changed source/test files PASS; Python unit tests **NOT RUN**, compileall **NOT RUN**, GitHub Actions on latest PR head **NOT VERIFIED**, independent audit **PENDING**. These tests are authored but not execution evidence. No merge or live deployment.
- **Next:** run `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v`, compileall, inspect exact-head CI and request independent audit. Coordinate shared CI with integrator; foundation #1 and trusted Identity/Entitlements/provider integrations remain blocking.


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


## Backend engineering checkpoint — 2026-11-21 (storage outage)

- Issue #9 / Draft PR #73 / branch `feat/vpn/9-subscription-adapter`: scoped fix in `core.py` wraps SQLite connection/open and SQLite operation failures as generic `BillingError("billing storage unavailable")`, suppressing raw SQLite exception chaining in normal traceback output. No billing state or payment semantics intentionally changed. SQLite transactions remain rollback-protected on write failures.
- Added two negative tests in `tests/test_core.py` for inaccessible database parent and a database path replaced by a directory after initialization. These verify sanitized, fail-closed storage outage handling and no exposed original exception cause.
- GitHub commits: core `18df5c669b775e081486b213a6dd07e8bad1b3f5`; tests `401c25a2f4a87b540f56171f52d596460c5be16a`. Before writes, Draft PR #73 head was `a4d4e2f1e0c780f11964c42ec9f52f761e27a089`; fetched exact blob SHAs were `14a1a7e5de8afbb94f0f3a7f5b2fab44ec1392d1` and `a0f33b1341b2032ae68457c8ee878b585217c3a2`.
- **Tests on these new commits: NOT RUN**; **compileall: NOT RUN**; **GitHub Actions current-head: NOT VERIFIED**. Prior 32/32 local tests covered older source and do not certify this patch. Rerun full 34-test suite and compileall in an executable checkout, then obtain independent review/CI. No production payment adapter, entitlement grant or deployment exists.
- Remaining blockers: unmerged foundation PR #1, independent audit, approved Identity/Entitlements contracts, provider verification and reconciliation, operational database recovery. Rollback by reverting these two commits on the Draft PR branch; do not merge without review.

## Backend engineering checkpoint — 2026-11-21 (SQLite failure regression alignment)

- Issue #9 / Draft PR #73 / branch `feat/vpn/9-subscription-adapter`. Source `core.py` was not changed in this checkpoint.
- Fixed the **existing** `test_order_request_insert_failure_rolls_back` assertion in `tests/test_core.py`: the preceding storage-error hardening intentionally converts `sqlite3.Error` to sanitized `BillingError("billing storage unavailable")`. The old test still expected raw `sqlite3.DatabaseError` and would fail even when rollback worked. It now expects `BillingError` with no explicit exception cause, while retaining the rollback/no-ghost-order and successful-retry assertions.
- Test commit: [`6a07cfd42b2235e5a6a8d3965c11c74312d40bbb`](https://github.com/Dimash313/Wexum/commit/6a07cfd42b2235e5a6a8d3965c11c74312d40bbb). Current PR head must be refreshed before further writes.
- **Evidence:** GitHub file update accepted; unit tests **NOT RUN** in this checkpoint, compileall **NOT RUN**. Prior 32-test local evidence predates the SQLite exception translation and cannot certify this current source/test pair. Latest previously queried PR head `9bfc69a0` had zero GitHub Actions runs/statuses. Verify new head CI separately.
- **Next:** execute `PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v` and `python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests`; confirm exact-head GitHub CI through CTO-owned integration lane; request independent audit of the storage-error mapping and regression. No merge until required gates pass.
- **Remaining blockers:** foundation #1, governance #38, independent audit, provider/identity/entitlements integration, data retention/backup, legal/store/qualified religious approval. No real payment adapter, VPN grant or deployed service.


## Backend P1 checkpoint — 2026-11-23 (Billing exact-source CI regression)

- **Scope/ownership:** Issue #9, existing Draft PR #73, branch `feat/vpn/9-subscription-adapter`. CTO reported a real red `core` run on CI-only candidate #87 (`c505a1ac2c9c8e8c2da5a33239c11f0cd24294c6`) containing byte-exact source `fbdab4ead52529ed97b0333a382357e633b32708`: 42/43 Billing tests passed; `test_deeply_nested_signed_json_fails_closed` expected `invalid webhook JSON` but received `invalid event fields`. CodeQL workflow completed successfully. Evidence: [core run](https://github.com/Dimash313/Wexum/actions/runs/45092740188), [candidate #87](https://github.com/Dimash313/Wexum/pull/87), [CTO dispatch](https://github.com/Dimash313/Wexum/pull/73).
- **Root cause and narrow correction:** JSON nesting acceptance varies with interpreter/runtime; the 1200-level signed array can parse successfully but is still rejected by the top-level event schema. The test now accepts either sanitized rejection **without permitting success or ledger writes**. A new deterministic `unittest.mock.patch` test forces `json.loads` to raise `RecursionError` and requires the exact sanitized `SecurityError("invalid webhook JSON")`, unchanged revision and no eligibility. No production provider or entitlement behavior changed.
- **Source test commit:** `fd60ec36f924f3dc3911282b226abea1d4663396`; modified only `tests/test_core.py` before this HANDOFF update. Existing implementation `core.py` unchanged.
- **Evidence:** earlier red CI applies to **old source** only. On the new source commit, local repository unittest **NOT RUN** (container DNS prevents git clone), compileall **NOT RUN**, GitHub Actions exact-head **NOT VERIFIED**, independent review **PENDING**. Do not claim PASS from static review. CI-only candidate #87 is not a production merge candidate.
- **Next:** CTO/integrator #56 must refresh the byte-exact Billing files from current #73 source into a CI-only candidate, run full Billing unittest + compileall and required CodeQL, inspect the actual checkout/tree SHA and logs, then request independent audit. Keep #73 Draft/BLOCKED until all gates pass; no live payment adapter, signed VPN grant or production rollout.
