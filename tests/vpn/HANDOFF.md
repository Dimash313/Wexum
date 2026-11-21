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
- With no Control Plane source, 13 tests **skip**. This is an integration
  blocker, not a pass. An invalid explicitly supplied source path errors.
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
- Last verified PR #74 head *before this handoff commit*:
  `b31fe5463cea2650fb9c15c3cb809277b5e0306d`.
  Always refresh head, diff, open reviews and checks before working.
- Issue ownership was claimed in
  [issue #10 discussion](https://github.com/Dimash313/Wexum/issues/10).
  Integrator resolves concurrent owner collisions.

## 4. Implemented components

- `tests/vpn/__init__.py` — package marker.
- `tests/vpn/leak_evidence.py` — strict synthetic observation classifier.
- `tests/vpn/test_leak_evidence.py` — 11 offline positive/negative cases.
- `tests/vpn/test_control_contract.py` — 13 opt-in real-source integration
  tests: scopes/audience/issuer, owner isolation, subscription outages/expiry,
  cancellation, idempotency, revocation, locked SQLite, atomic device limit,
  hash-only idempotency storage and known history-truncation regression.
- `tests/vpn/README.md` — reproducible commands, limits and real-VPN test plan.
- `tests/vpn/HANDOFF.md` — this continuity record.

No production code, shared workflow or other lane files were changed by #74.

## 5. Tests actually executed, with evidence and limits

**Reproduced in the 2026-11-21 handoff session, Python 3.13.5:**

```sh
python -m compileall -q tests/vpn
python -m unittest discover -s tests/vpn -p 'test_leak_evidence.py' -v
```

Observed result: **11 passed / 0 failed / 0 skipped** for the synthetic offline
classifier; compilation completed successfully. Tested local file bytes were
confirmed identical to GitHub by `git hash-object`:

- `leak_evidence.py`: `a5c29c87abdd605422d3cd27de2d303019e0f8ca`
- `test_leak_evidence.py`: `6c66ab5fe1ce0cc8b8d906c70595999bec7b5296`

**Not executed in this handoff session:** the 13 `test_control_contract.py`
cases; real Control Plane code is on separate unmerged PR #55. Original PR #74
description records 24 discovered / 11 passed / 0 failed / 13 skipped in an
earlier detached check, but this handoff independently reverified **only the 11
offline cases**, not the whole historical test log or live GitHub Actions.
Current GitHub commit statuses may be absent; do not assume CI success.
No real VPN, network, device, DNS/IP leak, IPv6, load or security audit tests ran.

**Run full lab on an integration checkout:**

```sh
python -m compileall -q tests/vpn
python -m unittest discover -s tests/vpn -p 'test_*.py' -v
# Or set WEXUM_VPN_CONTROL_SRC=/absolute/path/to/reviewed/control/src
# and run the same command. Inspect both failures and SKIPS.
```

## 6. Known issues and blockers

1. [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1)
   was still open/unmerged when this document was written. Its
   `AGENTS.md` and planning docs are **proposals**, not integrated `main`.
2. [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55)
   not integrated into QA checkout; contract suite not yet executed on exact
   owner source. [Integration PR #67](https://github.com/Dimash313/Wexum/pull/67)
   documents a known `list_for_owner` truncation defect that can hide the
   newest active device among 200 historical rows. The new regression is
   **not yet observed running against affected PR code**.
3. PR #67 also documents SQLite open-failure normalization issue; add a
   regression at the approved owner API boundary, without editing owner code.
4. Identity and Entitlement trust boundaries, node discovery and revocation
   propagation lack reviewed cross-lane contracts. No deployed tunnel or
   signed access grant.
5. Mandatory CI activation, exact-head integration, independent audit
   [#41](https://github.com/Dimash313/Wexum/issues/41), governance
   [#38](https://github.com/Dimash313/Wexum/issues/38),
   platform/legal/store/religious reviews remain gating as applicable.
6. Local verification workspace cannot resolve `github.com` using direct
   `git` network access. Use the connected GitHub integration to inspect and
   modify the remote branch. Never claim a GitHub Actions or end-to-end run
   without recorded evidence.
7. Security findings should follow
   [SECURITY.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/SECURITY.md);
   avoid posting exploitable details or sensitive data in public issues.

## 7. Concrete next tasks (in order)

1. On `Продолжаем дальше`: read current AGENTS.md (foundation branch if not
   merged), all relevant architecture/quality docs, this HANDOFF, issue #10,
   latest GitHub PR #74, PR #1, PR #55, PR #67 and open reviews/checks.
2. Check current branch head, diff, duplicate claims, CI status and contracts.
   Do not erase another engineer's changes or treat an unmerged PR as baseline.
3. Obtain the **real, exact-head** Control Plane source for PR #55 or its
   successor in an isolated test checkout; execute all 13 contract tests,
   capture precise pass/fail/skip evidence, and report known regression
   failures to owner #2 via CTO/integrator. Do not patch other lanes.
4. Add independent focused negative tests for unhandled SQLite open failures
   and authorization validation under the approved API; avoid gratuitous mocks
   and don't hard-code unapproved shared interfaces.
5. Once contracts exist, implement independent tests for node stale-health,
   generation replay and entitlement cancellation/expiry; keep them in
   `tests/vpn/` and avoid leaking credentials/test traffic.
6. Ask integrator to enforce the QA suite and **no-skips** on the reviewed
   combined-source CI. Keep shared workflow changes outside this lane.
7. Prepare reproducible real-OS VPN probe harness with approved endpoints,
   packet/DNS evidence handling, consent and data minimization. Until actually
   executed and independently checked, label scenarios `NOT TESTED`.
8. Update PR #74 description and this document after material changes and
   before pausing/handing off; include exact commands, counts, SHAs, blockers,
   reviewer decisions and links. Never claim completeness without evidence.

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
