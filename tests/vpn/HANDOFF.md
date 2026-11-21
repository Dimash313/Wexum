# WexumVPN — Testing & Quality Engineering: agent handoff

Last updated: 2026-11-21 UTC. **Draft / pre-integration only.**
This file is the resume point for the next AI engineer. Treat GitHub and the
current checked-out source, not this snapshot, as the authoritative live state.

## 1. Direction and exclusive responsibility

**Owner:** WexumVPN Testing & Quality Engineering, GitHub issue
[#10](https://github.com/Dimash313/Wexum/issues/10).

**Exclusive working tree:** `tests/vpn/`. Design and maintain deterministic,
executable unit/integration/contract regression tests; negative authorization,
tenant/subject isolation, revocation/expiry, concurrency and failure coverage;
prepare measured and independently verified DNS/IP leak testing on real OS VPN
implementations. No production credentials, captured personal traffic, or
functional changes in other product lanes.

**Do not edit:** `products/vpn/**`, `apps/vpn/**`,
`docs/engineering/STATE.md`, `AGENTS.md`, shared APIs/ADRs, or
`.github/workflows/**` without the relevant owner and CTO/integrator approval.
Send cross-boundary findings to their responsible owner via CTO.

## 2. Current architecture and decisions

- Two **independent** suites under `tests/vpn/`, Python stdlib `unittest`,
  Python 3.12+ with no new runtime, cloud, paid or network dependencies.
- `leak_evidence.py` is a **pure offline classifier** of supplied IPv4, IPv6,
  DNS and reported-route evidence. Verdicts: `REJECTED`, `INCOMPLETE`,
  `CONSISTENT`. `CONSISTENT` asserts only internal consistency of provided
  observations; it cannot prove a real tunnel or absence of leaks. Synthetic
  IANA documentation-only IP addresses are used in fixtures.
- `test_control_contract.py` imports the **actual** `DeviceControlService`
  and `SQLiteDeviceStore` in PR #55 when its source is available either in
  the current checkout (`products/vpn/control/src`) or an explicitly provided
  `WEXUM_VPN_CONTROL_SRC`. It does not replace service/store with mocks. The
  injected entitlement result is synthetic; no real Identity, HTTP, provider,
  VPN node, production database or data-plane access is tested.
- With no Control Plane source, 16 tests **skip** by default. This is an
  integration blocker, not a pass. Set \`WEXUM_VPN_REQUIRE_CONTRACTS=1\` for
  mandatory integration CI to fail if the real package is absent; explicitly
  invalid source paths also error.
- Shared CI is exclusively owned by integration/CTO. Do not silently edit
  `.github/workflows`. An integration job must eventually require real
  contract execution (no skips) against an exact, reviewed combined SHA.
- Real DNS/IP, route-switching, reconnect, kill-switch and packet tests need
  dedicated OS/device rigs and independent evidence before they can be claimed.

## 3. GitHub ownership and proposal

- Issue: [#10 — VPN test-lab](https://github.com/Dimash313/Wexum/issues/10).
- Branch: `feat/vpn/10-test-lab` (created from `main`).
- [Draft PR #74 — VPN QA](https://github.com/Dimash313/Wexum/pull/74)
  targets `main`; **do not self-merge or self-approve**.
- Last verified PR #74 head *before this handoff update*:
  `0f1ef89f240b6075601c0bc7487af7ebb3cdfb36`.
  Always refresh head, diff, open reviews and checks before working.
- Issue ownership was claimed in
  [issue #10 discussion](https://github.com/Dimash313/Wexum/issues/10).
  Integrator resolves concurrent owner collisions.

## 4. Implemented components

- `tests/vpn/__init__.py` — package marker.
- `tests/vpn/leak_evidence.py` — strict synthetic observation classifier.
- `tests/vpn/test_leak_evidence.py` — 11 offline positive/negative cases.
- `tests/vpn/test_control_contract.py` — 16 opt-in real-source integration
  tests: scopes/audience/issuer, owner isolation, subscription outages/expiry,
  cancellation, idempotency, revocation, locked SQLite, atomic device limit,
  hash-only idempotency storage, history-truncation regression, and 3 SQLite
  connection-open failure regressions on enroll/list/revoke. Mandatory mode
  `WEXUM_VPN_REQUIRE_CONTRACTS=1` forbids silent skip when source is absent.
- `tests/vpn/README.md` — reproducible commands, limits and real-VPN test plan.
- `tests/vpn/HANDOFF.md` — this continuity record.

No production code, shared workflow or other lane files were changed by #74.

## 5. Tests actually executed, with evidence and limits

**Verified in local Python 3.13.5 with exact GitHub blob bytes, 2026-11-21.**
An isolated checkout contains exact PR #55 Control Plane files and our QA
lab. No source code in another owner's GitHub lane was modified.

```sh
python -m compileall -q tests/vpn
PYTHONPATH=products/vpn/control/src python -m unittest discover -s tests/vpn -p 'test_*.py' -v
```

**Observed: 27 executed; 23 passed, 1 failed assertion, 3 errored, 0 skipped.**
Syntax compile **PASS**. The suite is intentionally **RED** on PR #55 code:
- `test_regression_recent_active_device_not_hidden_by_history` FAIL:
  newest active device is excluded by oldest-200 listing.
- `test_regression_sqlite_open_failure_maps_to_service_error_on_enroll` ERROR:
  raw `sqlite3.OperationalError`, not expected `EnrollmentUnavailable`.
- `test_regression_sqlite_open_failure_maps_to_service_error_on_list` ERROR:
  same unmapped SQLite open failure.
- `test_regression_sqlite_open_failure_maps_to_service_error_on_revoke` ERROR:
  same unmapped SQLite open failure.

**Exact source/test blob SHA checks (`git hash-object`):**
- PR #55 `store.py`: `d00b0427f60ce46ccf049a808e9a692e6db34146`
- PR #55 `service.py`: `de329886873e1cb3a26672b8786712f86df747a4`
- PR #55 `__init__.py`: `8469816eb7c4cd2c6b39a3f28e1ff4426a4216be`
- QA `test_control_contract.py`: `82d66ac38908fc9edcec3642705f3d8b0bcf0fb2`
- QA `leak_evidence.py`: `a5c29c87abdd605422d3cd27de2d303019e0f8ca`
- QA `test_leak_evidence.py`: `6c66ab5fe1ce0cc8b8d906c70595999bec7b5296`

No **GitHub Actions** result is verified for current PR head. No real VPN
tunnel, external network, Android/iOS/desktop device, physical DNS/IP leak,
IPv6 packet, performance or security audit test was executed. Do not mistake
synthetic provider/evidence data for production integration.

**Run with a reviewed source and prevent false-green skips:**

```sh
WEXUM_VPN_REQUIRE_CONTRACTS=1 \
WEXUM_VPN_CONTROL_SRC=/absolute/path/to/reviewed/control/src \
  python -m unittest discover -s tests/vpn -p 'test_*.py' -v
```

## 6. Known issues and blockers

1. [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1)
   remains open/unmerged as of this handoff. Its contracts are proposed,
   not yet integrated.
2. [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55)
   exact head `66532b4df984c091b46e53697218b82557bb4bbd` has two
   independently **reproduced** categories of defects: active-device
   history truncation and unmapped SQLite connection-open failures across
   enroll/list/revoke. The lab now exposes four red test methods.
   Regression tests must remain red until actual corrections land on owner
   code and pass an exact-head retest; QA may not edit owner source.
3. [CI integration PR #67](https://github.com/Dimash313/Wexum/pull/67)
   still needs the integrator to include strict QA tests on a reviewed
   combined commit, with no skipped contracts and required status checks.
4. Identity/Entitlement/Nodes interactions, signed grants, OS tunnel,
   authority, revocation propagation and production failure contracts are
   unapproved or not fully integrated.
5. Independent audit [#41](https://github.com/Dimash313/Wexum/issues/41),
   governance [#38](https://github.com/Dimash313/Wexum/issues/38),
   legal/store/religious review and real OS DNS/IP evidence remain gates.
6. Local container cannot access GitHub via direct git network; use
   connected GitHub tool and check exact files by Git blob SHA. Do not
   claim CI or endpoint testing without evidence.
7. Sensitive findings should use
   [SECURITY.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/SECURITY.md).
   Current generic defects are already publicly known in review; avoid
   posting sensitive details or credentials.

## 7. Concrete next tasks (in order)

1. On `Продолжаем дальше`: read current `AGENTS.md` (from foundation if
   not merged), this `HANDOFF.md`, scope docs, current GitHub issues,
   PR #74, #55, #1, #67, #65, #64 and review/CI status.
2. Pass reproduced **four failures** to Control Plane owner #2 through
   CTO/integrator; coordinate owner correction without QA modifying
   `products/vpn/control/`.
3. After owner updates PR #55 or its successor, fetch **exact new source
   blobs**, re-run all 16 contract tests locally plus 11 classifier tests
   with mandatory `WEXUM_VPN_REQUIRE_CONTRACTS=1`, record passes/failures,
   exact head and rollback. Do not suppress red tests.
4. Extend opt-in tests for Node Registry #65 stale health, generation
   replay, capacity and selection under approved contract, in `tests/vpn/`.
   Add Entitlements #64 tests only after re-reading its actual API surface.
5. Ask CTO/integrator to activate strict no-skip QA in mandatory CI
   on the final independently reviewed integration base.
6. Prepare approved real-device VPN leak testing on IPv4/IPv6/DNS and
   network transitions, with provenance, ethical privacy handling and
   separate real-environment evidence. Until executed mark `NOT TESTED`.
7. Update this handoff and PR #74 after every material change, including
   exact commands, test counts, test/runtime hashes, dependencies, and
   independent review results. Do not merge or approve your own PR.

## 8. Relevant links / documentation

- [QA issue #10](https://github.com/Dimash313/Wexum/issues/10),
  [QA Draft PR #74](https://github.com/Dimash313/Wexum/pull/74)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1),
  [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55),
  [CI integration PR #67](https://github.com/Dimash313/Wexum/pull/67),
  [Node Registry PR #65](https://github.com/Dimash313/Wexum/pull/65),
  [Entitlements PR #64](https://github.com/Dimash313/Wexum/pull/64)
- [AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md)
- [VPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md),
  [VPN requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md),
  [Quality rules](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md),
  [Review protocol](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/REVIEW_PROTOCOL.md),
  [Religious review](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/policy/RELIGIOUS_REVIEW.md)
- [Local lab README](https://github.com/Dimash313/Wexum/blob/feat/vpn/10-test-lab/tests/vpn/README.md)
