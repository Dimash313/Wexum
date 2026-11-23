## 2026-11-23 — P1 UX user-intent provenance guard (bounded cycle)

- **Scope:** Issue #39, existing branch `docs/vpn/39-interface-specs`, Draft PR #75; proposed UX specification only, no operational VPN. Foundation PR #1 remains unmerged.
- **Change:** `validate_contract.py` now rejects non-`user` source labels for `start_requested`, `disconnect_requested`, `cancel_requested` and `retry`; `test_contract.py` adds 24 negative source mutations and four positive controls. This prevents a trusted backend/OS source label from being misrepresented as explicit user intent in the proposed transition table; it does **not** authenticate runtime event origin.
- **Verification:** GitHub Contents API blob-conditional writes and exact-HEAD readback are source-presence checks only. Python validator, unittest/contract, compileall, native builds, integration and live VPN/device/DNS/IP are **NOT RUN** in this cycle due to local GitHub DNS failure. GitHub Actions and independent audit must be checked on the final exact SHA; no PASS is inferred from authored tests.
- **Next owners / acceptance:** UX owner execute `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on exact head. CTO/Integration owns trusted native event provenance and mandatory CI; Independent Audit independently review the new SHA and negative cases. No merge or protected-status claim until required checks and blockers clear.

## 2026-11-23 — P1 Node Registry provenance regression (bounded cycle)

- **Ownership:** Issue #39, branch `docs/vpn/39-interface-specs`, Draft PR #75. Foundation PR #1 is unmerged. Proposed UX state contract only; no working VPN or authenticated Node Registry adapter.
- **Finding:** previously documented in PR #75 comment #7093206049: `no_eligible_nodes` accepted arbitrary recognized source labels, permitting proposed node-unavailable state drift.
- **Change:** `validate_contract.py` requires `disconnected -> no_nodes` for `no_eligible_nodes` with `trusted_nodes` only. Regression tests include six invalid source labels, two invalid edges, one positive source case. Validator commit `33b86e9a29a1b8d5f78cf7667199a2f5c8710917`; tests commit `847cfd7f801fc8997930c7ede273755362c1d6a2`.
- **Evidence:** GitHub Contents API accepted writes against fetched exact blob SHAs; HEAD rechecked between writes. Python unit/contract, compileall, native builds, integration and live VPN/device/DNS/IP: **NOT RUN**. Source checks are not runtime authentication; do not claim protection. Current-head mandatory CI and independent audit remain unverified.
- **Next / acceptance:** UX owner execute `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on final HEAD. CTO/Integration own authenticated Node Registry event boundary and mandatory CI for stacked PR; Independent Audit review exact SHA and negative cases. No merge before passing required checks and cleared blockers.

## 2026-11-23 — P1 OS network/restart event source guard

- **Issue / branch / Draft PR:** #39 / `docs/vpn/39-interface-specs` / #75. Proposed UX contract only, not an operational VPN. Foundation #1 remains unmerged.
- **Risk:** `network_lost`, `network_restored` and `app_restarted` could previously accept any recognized source label (including `user`), permitting proposed lifecycle authority drift. No runtime exploit is asserted.
- **Change:** validator requires `native_os` for all three event names. Authored two regression methods: 18 negative source mutations and three positive native-OS checks. Validator commit `80210d86e141ed76e868879ae810d926c6835a9c`; tests commit `595e85faa168da7663987be73bf11fd50e4e562d`.
- **Checks:** GitHub Contents API accepted both source writes on current file blob SHAs. Python unit/contract, compileall, native builds, integration, live VPN/device/DNS/IP: **NOT RUN**. Source labels do not authenticate actual OS callbacks; native clients must verify callback provenance and attempt freshness.
- **Next:** UX owner execute `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on final exact HEAD; Independent Audit inspect mutation tests and current SHA; CTO/Integration approve native provenance contract and required CI. No merge or protected-state claim.

## 2026-11-23 — P1 native connection observation provenance guard

- **Issue/branch/Draft PR:** #39 / `docs/vpn/39-interface-specs` / #75. Unmerged UX specification only; Foundation #1 remains unmerged.
- **Change:** `native_connected_unverified` must be exactly `connecting -> connected_unverified` with `native_os` source. This prevents specification drift that could represent user/provider-origin status as an OS observation; it does **not** authenticate runtime OS callbacks or assert VPN protection.
- **Regressions authored:** six negative sources, two wrong edges and one positive OS observation. Source-label validation only, no actual device/transport proof.
- **Checks:** GitHub Contents API writes on previously read blob SHA; Python unit/contract, compileall, native build, integration and live VPN/device/DNS/IP **NOT RUN** because local GitHub checkout fails DNS. GitHub Actions on final head and independent audit remain required.
- **Next:** UX owner run `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p "test_*.py" -v`, `python -m compileall -q docs/vpn/ux`; CTO/Integration own native callback authentication and CI; independent auditor inspect exact final SHA. Do not merge or imply a working VPN.

## 2026-11-23 — P1 OS permission source guard (one bounded cycle)

- **Ownership:** Issue #39; existing branch `docs/vpn/39-interface-specs`; Draft PR #75. Foundation PR #1 remains unmerged; this is a **proposed UX contract only**, not a working VPN.
- **Finding:** Issue raised in [PR #75 comment](https://github.com/Dimash313/Wexum/pull/75#issuecomment-7088953577): permission lifecycle event source could be changed to another recognized source without validator rejection.
- **Change:** `validate_contract.py` now requires `native_os` for `permission_missing`, `permission_granted`, and `permission_denied`. The additional missing-permission case shares the same OS authority boundary. `test_contract.py` adds 18 negative source mutations (3 events × 6 other sources) and 3 positive native OS cases.
- **Commits:** guard `f807843d4cb1445ab21e982930ea5df14cc1b2c7`; regression source `8bfbb4c10eba2e6f6ad16f2ff32bfc9c2fd2ad64`. GitHub Contents API confirmed writes on exact previous blobs.
- **Checks:** `git ls-remote https://github.com/Dimash313/Wexum.git HEAD` attempted in local container: **FAILED** (DNS `Could not resolve host: github.com`). Python validator, unit/contract suite, compileall, native build, integration, and live VPN/device/DNS/IP: **NOT RUN**. New tests are authored, **not** claimed passing. GitHub Actions on final HEAD must be checked separately.
- **Risk:** JSON `source` is a specification label, not an authenticated OS callback. Native clients must bind real OS permission state and reject stale results. No claim of traffic protection or real consent validation.
- **Next owners / acceptance:** UX owner runs `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` at exact latest SHA; independent auditor reviews all source-mutation negatives and current SHA; CTO/Integration owns mandatory CI and native source-authentication contract. No merge until required checks and independent review pass.

## 2026-11-22 — P1 engine failure event authority (bounded cycle)

- **Issue / branch / Draft PR:** #39 / `docs/vpn/39-interface-specs` / #75. Proposed UX contract only, not merged; foundation PR #1 remains unmerged.
- **Architecture:** `engine_failed` in the illustrative state contract is now accepted only from `trusted_service` for the exact `connecting -> error` edge. Source labels are documentation, **not** authenticated runtime identities.
- **Commits:** validator `e07d07e9f204da1d3e5ddac4c21ef07af704f168`; regression tests `2994926a6780d71ac4f6e5cef61324ed87d7dd81`. Re-fetch current PR HEAD before further edits.
- **Tests authored:** negative matrix for six non-service sources and two invalid lifecycle edges; positive trusted-service case. GitHub Contents writes confirmed. Python unit/contract, compileall, native builds, integration, Actions on final SHA and live VPN/device/DNS/IP: **NOT RUN**. Local `git ls-remote` failed DNS resolution of github.com; no false green claims.
- **Risks / next owners:** UX owner to execute `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on exact SHA; independent auditor to inspect the exact source and negative cases; CTO/integrator to define authenticated native service event provenance and mandatory CI. No merge until checks/audit and contract approval.

## 2026-11-22 — P1 identity event-source trust guard

- **Scope:** Issue #39 / existing Draft PR #75, branch `docs/vpn/39-interface-specs`; source baseline `335674daddd862ca2528d2dae0382ad697980dfe` (unmerged foundation PR #1).
- **Defect:** proposed validator previously accepted `sign_in_required` and `sign_in_complete` with arbitrary recognized source labels, including `user`, permitting a forged identity-completion edge in the UX specification. This is a contract-validation issue, not proof of a live identity bypass.
- **Correction:** both events require `trusted_identity`. Added negative matrix (2 events × 6 non-identity sources = 12 cases) and positive cases for the intended source. Files: `validate_contract.py`, `test_contract.py`.
- **Source commits:** validator `7e7ec7212d31c843e44f0b47b170b49747d0eb0d`; tests `57695d0a0e7c3c8a17cbe9e3dccef9c147132919`.
- **Checks:** connector-confirmed GitHub writes; in-tool structural checks of guard and negative/positive test definitions PASS. Python validator, unittest, compileall: **NOT RUN** (container cannot resolve github.com to check out exact source). GitHub Actions, native build, integration and live VPN/device/DNS/IP: **NOT RUN**. Authored tests are not claimed passing.
- **Risks:** `source` is only a proposed JSON label; future native clients must authenticate actual identity producer and bind session/attempt freshness. No working VPN/identity integration is claimed.
- **Next:** UX owner run Python validator/unittest/compileall on exact latest PR HEAD; Independent Audit verify negative cases and exact SHA; CTO/Integration ensure identity contract and mandatory CI. No merge pending checks and audit.

## 2026-11-22 — P1 engine-error retry truthfulness correction

- **Scope:** Issue #39, existing branch `docs/vpn/39-interface-specs`, Draft PR #75. Foundation PR #1 remains unmerged; proposed UX contract only.
- **Source finding:** independent review https://github.com/Dimash313/Wexum/pull/75#issuecomment-7081176762 identified `connecting -> error -> disconnected` on user retry without trusted tunnel stop acknowledgement.
- **Changes:** validator now rejects transitions from `connecting` or `error` to `disconnected` without `service_stopped`; proposed `error/retry` now enters non-protected `interrupted` pending reconciliation. Added two negative regression methods.
- **Commits:** validator `7eb70ee63e4184acf7a4c6a0cdfed34e11621c64`; contract `aa2492ef0aca85fb3e0f7b01e2b7fecdc008bece`; tests `4f1c05a0bd74cef75b6daf785c7a69a6ff6971a9`.
- **Verification:** GitHub accepted all three file updates with current blob SHA. Python validator/unittest/compileall on the resulting SHA: **NOT RUN**; native build, integration, device VPN/DNS/IP: **NOT RUN**. No claim of passing tests or real VPN.
- **Next owners:** UX lane runs `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, and `python -m compileall -q docs/vpn/ux` on exact final SHA; Independent Audit reviews negative cases; CTO/Integration specifies authenticated service teardown and mandatory CI. The `interrupted` state is non-protected, not proof of teardown. Do not merge until checks and independent audit pass.

## 2026-11-22 — P1 entitlement authority regression fix (current cycle)

- **Issue/branch/PR:** #39, `docs/vpn/39-interface-specs`, Draft PR #75; foundation PR #1 remains unmerged and is not an integrated dependency.
- **Finding:** independent audit comment https://github.com/Dimash313/Wexum/pull/75#issuecomment-7079735120 reported that `grant_revoked`, `grant_expired`, and `entitlement_check_failed` accepted arbitrary recognized event sources, including `user`.
- **Code:** `validate_contract.py` now requires `trusted_entitlement` for each of those event names. This is a static proposed UX contract check, **not** native authorization or verified VPN functionality.
- **Regression source:** `test_contract.py` adds a negative matrix across all three events and five non-entitlement source values, plus positive checks for `trusted_entitlement`.
- **Commits:** validator `b519cf877127d56e4e5d3eef86652c5824431a35`; regression tests `669577dd72990c60fe59a3863279f346b6cea26a`. Re-fetch PR HEAD before any further changes.
- **Evidence:** GitHub Contents API accepted both writes with expected prior blob SHA; `git ls-remote https://github.com/Dimash313/Wexum.git HEAD` attempted in local shell and failed `Could not resolve host: github.com`. Python `unittest`, validator execution, `compileall`, GitHub Actions on final SHA, native builds, integration and real VPN/device tests: **NOT RUN**. Authored tests are not a PASS.
- **Next owner/acceptance:** UX lane executes `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on exact new HEAD; independent auditor checks negative cases and fresh SHA; CTO/integrator owns mandatory CI and shared source-authentication contract. Require successful actual checks and independent review before integration. Do not merge, self-approve, or claim working VPN.
- **Risks:** source labels in a JSON spec are not cryptographic authentication; future native clients must verify trusted producer identity, session freshness, revocation and teardown with platform-specific tests. Earlier P1 stop-acknowledgement lifecycle concern remains a separate cross-platform dependency.

# WexumVPN Interfaces & UX — persistent handoff

> **Read this first in every new chat/agent session.** This is the live, issue-owned continuation record, not evidence of product release. Updated: **2026-11-21** (GitHub rechecked at start of continued work; PR #75 remains open/draft and foundation PR #1 remains unmerged). Re-check GitHub before relying on any status below. Do not infer new work from a chat transcript.

## 1. Mission, scope and ownership

- Direction: **WexumVPN — Interfaces & UX**; [issue #39](https://github.com/Dimash313/Wexum/issues/39).
- Repository: [Dimash313/Wexum](https://github.com/Dimash313/Wexum).
- **Exclusive mutable scope:** `docs/vpn/ux/`. Own VPN UX flows, screen specifications, accessible UX copy, native handoff, state/rendering contract proposal, UX research plan and acceptance tests.
- **Not owned:** native apps `apps/vpn/android/`, `apps/vpn/ios/`, `apps/vpn/desktop/`; VPN service/control/entitlements/billing/nodes/security; root workflows; `docs/engineering/STATE.md`, `AGENTS.md`, `docs/design/`, `docs/i18n/`; platform-wide `packages/design-system/` and `packages/i18n/`.
- `packages/vpn-design/` is **NOT approved or created**. Obtain CTO/integrator agreement on exact shared package boundary and design token contract before modifying any package or common API.
- Owner-specific visual constraints: premium monochrome UI, calm typography, no music, no depiction of living beings, no false VPN connection/metrics. Uphold the [religious review policy](../../policy/RELIGIOUS_REVIEW.md).

## 2. Source of truth and operating rules

1. Read latest repo status, PRs, issues, review comments and branch heads; **first** read root `AGENTS.md`, `README.md`, `docs/engineering/STATE.md`, `docs/architecture/SYSTEM.md`, `docs/architecture/BOUNDARIES.md`, `docs/engineering/QUALITY.md`, `docs/engineering/REVIEW_PROTOCOL.md`, `docs/policy/RELIGIOUS_REVIEW.md`.
2. Then read [issue #39](https://github.com/Dimash313/Wexum/issues/39), this file, [README.md](README.md), [SCREENS.md](SCREENS.md), [NATIVE_HANDOFF.md](NATIVE_HANDOFF.md), [connection_states.json](connection_states.json), [validate_contract.py](validate_contract.py) [test_contract.py](test_contract.py), [STATE_COPY.md](STATE_COPY.md) and [ACCESSIBILITY_QA.md](ACCESSIBILITY_QA.md).
3. Inspect PR #75 head files and comments, PR #1 status, platform drafts and design/i18n prerequisites **again** each session. Don't overwrite another agent's new work; use current blob SHA when editing existing files.
4. When owner says **«Продолжаем дальше»**, independently select the highest-priority *unblocked* UX task, implement it on the issue branch, actually run available checks, update the existing Draft PR and this handoff, then report results, blockers and exact GitHub URLs. Don't ask owner to allocate routine technical tasks.
5. **Never** directly push to main, force-push, edit another team's files, self-approve or merge. Ask CTO for cross-boundary decisions. If work is blocked, document the exact blocker and use the smallest safe change inside owned docs; do not pretend integration succeeded.
6. Before ending any meaningful work stage, update sections 3–8 here: current branch/PR, artifacts, tests with exact evidence, risks, next steps and related URLs. Keep evidence *actual*, mark not-run items, distinguish proposed from approved/integrated.

## 3. GitHub work state at last verification

| Item | Verified status (2026-11-21) |
| --- | --- |
| Main task | [Issue #39](https://github.com/Dimash313/Wexum/issues/39) **open** |
| Working branch | `docs/vpn/39-interface-specs` |
| Draft PR | [#75 — VPN UX: fail-closed cross-platform screen and state specifications](https://github.com/Dimash313/Wexum/pull/75) **open, draft, not merged** |
| PR target (stacked) | `architecture/foundation-and-agent-operating-system`, the head branch of [foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) |
| Foundation | PR #1 **open / unmerged**, with independent audit blockers under [#41](https://github.com/Dimash313/Wexum/issues/41). No implication that its files are on main |
| UX PR previously verified head (before this continued-work stage) | `505616cfdcca1cb4206b11d8e6bd42f445765d0a`; re-read GitHub for the latest head after commits |

Do not merge/retarget on assumption. Once foundation integrates, CTO decides proper base/rebase and independent CI review; this lane does not alter integration ownership.

## 4. Architecture and decisions currently proposed

- **Specification-only workstream.** `connection_states.json` is an illustrative UX state/rendering contract, **not** an API schema, production state reducer, cryptographic proof or VPN tunnel adapter.
- 17 explicit UX states, 34 modeled transitions, seven proposed evidence gates for a future trusted `verified_connected`; 12 screen/device acceptance cases. See the committed schema, not a copied chart, for latest details.
- **Fail-closed copy:** permission accepted != connected; native OS-connected event != verified privacy; animation/saved flags != protection. Only fresh, authenticated evidence from native tunnel, engine, valid entitlement/device and active network policy could ever justify a verified claim. **No existing scaffold produces such proof.**
- On service loss, revocation, network interruption, expiry, restart or old session callback, stop displaying any verified status until fresh authoritative revalidation. A UI snapshot is not security authority.
- Locations come only from real authenticated, eligible node inventory; never fabricate countries or latency. Subscription data comes only from billing/entitlement ownership, not invented plan/price/expiry.
- **Design source:** [platform Experience PR #42](https://github.com/Dimash313/Wexum/pull/42) is a *proposed*, not integrated, token contract. Use the semantic architecture after approval; avoid duplicating palette/type scales here.
- **i18n source:** [PR #45](https://github.com/Dimash313/Wexum/pull/45) (registry) and [PR #50](https://github.com/Dimash313/Wexum/pull/50) (adapter) are separate drafts. `en-US`, `ru-RU`, `kk-KZ`, `ar-SA` are candidate locale tags, not shipped translations. RTL, text expansion, screen-reader phrasing and security terms require native-speaker review.
- Screen layouts are textual specifications, **not rendered screenshots or product-ready implementations**. Native app owners must approve connection states and accessibility handoff.

## 5. Work delivered on Draft PR #75

| Path under `docs/vpn/ux/` | Present / purpose |
| --- | --- |
| `README.md` | Ownership, persona **hypotheses**, user journeys, IA and truth constraints |
| `SCREENS.md` | Home, locations, account/billing, onboarding consent, interruption/errors, settings/help; 12 testable native acceptance scenarios |
| `NATIVE_HANDOFF.md` | Android/iOS/Desktop mapping, responsive, accessibility, RTL, privacy and dependencies |
| `connection_states.json` | Proposed machine-readable states, transitions and anti-deception gates |
| `validate_contract.py` | Python stdlib static contract validator |
| `test_contract.py` | 20 drafted Python `unittest` methods for positive and negative contract behavior |
| `STATE_COPY.md` | Proposed status titles/detail, authority/preconditions, action handling and screen-reader announcement policy for all 17 states |
| `ACCESSIBILITY_QA.md` | 18 explicit per-platform accessibility/RTL/responsive acceptance cases, evidence format, honest NOT RUN/BLOCKED inventory |

Current artifacts provide no real user-facing VPN connection or status. No native UI, billing, localization catalog or shared components were implemented by this lane.

## 6. Testing — observed evidence vs not run

**Executed and passed in a previous agent turn:** 205 structural JavaScript assertions over six files freshly fetched from the actual GitHub branch (JSON parse, expected state IDs, counts, transition uniqueness, key naming, protection/evidence flags, file presence). This is a *custom structural consistency check*, **NOT** the Python unit suite, CI, UX/device testing, validated native security or an independent audit.

**Executed in this continued-work stage:** GitHub connector fetched the actual five current branch files (`connection_states.json`, `STATE_COPY.md`, `ACCESSIBILITY_QA.md`, `SCREENS.md`, `README.md`) and JavaScript structural assertions passed: exact 17/17 ID coverage with uniqueness and correct matrix columns, 18 unique accessibility case IDs, 12 referenced base scenarios, truthful revocation/permission semantics, and README links. These checks establish internal document consistency only, not Python runtime execution or UI quality.

**Attempted repository checkout:** `git ls-remote --heads https://github.com/Dimash313/Wexum.git 'docs/vpn/39-interface-specs'` failed because this isolated container could not resolve `github.com`; direct raw-file retrieval was also unavailable. This is a network/tooling blocker, not a Python test result.

**Authored but not confirmed executed:**
```sh
python docs/vpn/ux/validate_contract.py
python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v
python -m compileall -q docs/vpn/ux
```
Run from repo root on the **current PR head**. Record real Python interpreter, command, pass/fail/skip counts, SHA, errors and any needed corrective commits here and in PR. Do not count authored test methods as passing tests.

**Not executed:** Android/iOS/Desktop real-device screens, TalkBack/VoiceOver/desktop reader, 200% text, color/focus/RTL checks, native speaker proofreading, VPN engine/traffic/DNS/IP leak testing, node/entitlement/live billing, and user research with verified personas. These remain acceptance blockers; don't claim a 10/10 score.

## 7. Open risks and blockers

1. [PR #1](https://github.com/Dimash313/Wexum/pull/1) remains audit-blocked; [issue #41](https://github.com/Dimash313/Wexum/issues/41) and integrator decisions govern readiness. PR #75 is stacked on it.
2. [Design PR #42](https://github.com/Dimash313/Wexum/pull/42) and [i18n PRs #45/#50](https://github.com/Dimash313/Wexum/pull/50) need integration approval before shared/native implementations rely on their contracts.
3. Native Android [PR #66](https://github.com/Dimash313/Wexum/pull/66), iOS [#69](https://github.com/Dimash313/Wexum/pull/69), Desktop [#70](https://github.com/Dimash313/Wexum/pull/70) are non-operational client shells, not real verified VPN engines.
4. Authority needed from Identity [#34](https://github.com/Dimash313/Wexum/issues/34), VPN entitlement [#3](https://github.com/Dimash313/Wexum/issues/3), nodes [#4](https://github.com/Dimash313/Wexum/issues/4), billing [#9](https://github.com/Dimash313/Wexum/issues/9), security [#11](https://github.com/Dimash313/Wexum/issues/11), QA [#10](https://github.com/Dimash313/Wexum/issues/10).
5. No independent proof of accessibility, screen-reader comprehension, native pixel behavior or internationalization quality. Personas are *hypotheses*, not interviewed or validated users.
6. **Known limitations rather than verified code defects:** the documented state transitions are a deliberately partial handoff (not exhaustive production behavior); proposed proof list, DTO shape and exact security wording require trust-boundary review. No fabricated performance/SLA/traffic promises.

## 8. Next specific tasks — autonomous priority order

1. **Execute the actual Python checks** above against PR #75 current head; fix all failures within owned files, report exact output and results. If the execution environment cannot run the code, mark *not run* and use other honest static checks; don't fake Python success.
2. **Independent review requested** in [PR #75 review coordination comment](https://github.com/Dimash313/Wexum/pull/75#issuecomment-7060827763) on 2026-11-21. **No responses/approval verified yet.** Next: inspect actual reviewer feedback from security #11, QA #10, native #5/#6/#7, Experience #40 and i18n #44/#46; repair UX issues within owned files, require CTO for shared API/package decisions.
3. **State-to-copy matrix now drafted** in [STATE_COPY.md](STATE_COPY.md). Next: request native/security/i18n review of its 17 proposed statuses, action-gating and announcement policy, resolve any misleading wording, and align any changes with the UX state contract before production adoption.
4. Confirm CTO-approved **design token and reusable UI boundary** against #42 before any shared component implementation. Seek CTO decision as issue/PR comment; do not create `packages/vpn-design/` prematurely.
5. **Accessibility/RTL test inventory now drafted** in [ACCESSIBILITY_QA.md](ACCESSIBILITY_QA.md) (18 cases). Next: get platform teams to run available nonoperational shell cases, record actual proof with tested SHA/device, and treat engine-dependent scenarios as BLOCKED.
6. Coordinate `vpn.status.*`/`vpn.detail.*` key contract with i18n owner #44/#46 and arrange human review of safety-critical strings. Don't mark planned locales published.
7. After foundation and dependency reviews, retarget/rebase PR only through approved integrator procedure, run mandatory CI on the actual integration head, and keep Draft state until independent acceptance.

## 9. Reference index

- Review coordination: [PR #75 cross-lane requested reviews](https://github.com/Dimash313/Wexum/pull/75#issuecomment-7060827763) — posted, acceptance pending.
- Core: [Issue #39](https://github.com/Dimash313/Wexum/issues/39), [Draft PR #75](https://github.com/Dimash313/Wexum/pull/75), [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1), [Independent audit #41](https://github.com/Dimash313/Wexum/issues/41), [CTO continuity/governance #76](https://github.com/Dimash313/Wexum/issues/76).
- Design: [Issue #40](https://github.com/Dimash313/Wexum/issues/40), [PR #42](https://github.com/Dimash313/Wexum/pull/42).
- Localization: [Issue #44](https://github.com/Dimash313/Wexum/issues/44), [PR #45](https://github.com/Dimash313/Wexum/pull/45), [PR #50](https://github.com/Dimash313/Wexum/pull/50).
- Platforms: [Android #66](https://github.com/Dimash313/Wexum/pull/66), [iOS #69](https://github.com/Dimash313/Wexum/pull/69), [Desktop #70](https://github.com/Dimash313/Wexum/pull/70).
- Other engineering lanes: [Security #11](https://github.com/Dimash313/Wexum/issues/11), [QA #10](https://github.com/Dimash313/Wexum/issues/10), [Identity #34](https://github.com/Dimash313/Wexum/issues/34), [Entitlements #3](https://github.com/Dimash313/Wexum/issues/3), [Nodes #4](https://github.com/Dimash313/Wexum/issues/4), [Billing #9](https://github.com/Dimash313/Wexum/issues/9).
- Local artifacts: [README](README.md), [screen flows](SCREENS.md), [state copy](STATE_COPY.md), [accessibility QA](ACCESSIBILITY_QA.md), [native handoff](NATIVE_HANDOFF.md), [state contract](connection_states.json), [validator](validate_contract.py), [tests](test_contract.py).
- Project entry points: [AGENTS.md](../../../AGENTS.md), [quality gate](../../engineering/QUALITY.md), [VPN architecture](../ARCHITECTURE.md), [review protocol](../../engineering/REVIEW_PROTOCOL.md).

## 10. Update and reporting protocol

After every substantive change, **update this HANDOFF.md in the same branch** and refresh Draft PR #75 if scope/evidence/risks change. Preserve a precise record of: the actual head SHA, current status, decisions confirmed vs proposed, touched paths, exact tests truly executed (including failures), review feedback, blockers, next one or two actionable tasks, and links. In final chat report always provide **ready / tested / blocked / next / GitHub URL**, never claim asynchronous work.

Do not edit another workstream's HANDOFF.md or its docs without CTO coordination. If this PR is merged, ensure the integrated handoff stays current via the owning issue/next scoped PR, rather than an unmerged stale branch.


## 9. Continuation checkpoint — 2026-11-22 (validator trust boundaries)

- **Issue/branch/PR:** #39 / `docs/vpn/39-interface-specs` / Draft PR #75, stacked on unmerged foundation PR #1. This is a UX documentation validator, not a native VPN engine.
- **Change:** `validate_contract.py` now rejects `service_stopped` unless it is the exact `disconnecting → disconnected` edge sourced from `trusted_service`; it also rejects `fresh_verified_snapshot → verified_connected` from states other than `connecting`, `connected_unverified`, or `reconnecting`. Existing valid illustrative edges remain unchanged.
- **Regression coverage authored:** `test_contract.py` adds two methods with negative subtests for untrusted stop acknowledgements and invalid verified-state origins. Commits: [validator](https://github.com/Dimash313/Wexum/commit/eb8b2c9bb6e1073337c9a1e6b4339326d2bd7665) and [tests](https://github.com/Dimash313/Wexum/commit/0e605bfa4c41aa95131a619a407f6306bc197e45).
- **Verification:** GitHub connector confirmed successful commits and file blob updates. Python `validate_contract.py`, `unittest`, `compileall`, CI, native builds, device tests, VPN/traffic/DNS/IP leak checks: **NOT RUN** in this checkpoint. Authored regression tests are **not** reported as passed.
- **Remaining P1 blockers:** The illustrative JSON still has ambiguous `interrupted → disconnected` on network restoration, `verified_connected → disconnected` on app restart, and no modeled trusted stop-acknowledgement lifecycle after revocation/expiry. Prior PR #75 audit comments document these independently; do not infer a real OS tunnel stop from those events. The `service_stopped` source label is only a schema declaration, not cryptographic proof of service identity.
- **Next:** Run `python docs/vpn/ux/validate_contract.py` and `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v` on the exact latest PR head, obtain independent security/QA review, and resolve the remaining misleading disconnected transitions with integrator-approved native lifecycle semantics. Do not merge before required gates.


## 2026-11-22 — P1 lifecycle truthfulness correction

- Issue #39, branch `docs/vpn/39-interface-specs`, Draft PR #75. Removed illustrative `interrupted/network_restored -> disconnected` and `verified_connected/app_restarted -> disconnected` edges. They now go to non-protected `reconnecting` and `interrupted`, respectively, pending authoritative revalidation/stop. A validator guard rejects future direct tunnel-lifecycle `disconnected` claims without `service_stopped`; added a negative regression test covering both cases.
- GitHub contents API accepted three source changes: 537cd0dd5cc3c0e136adeb9242df0238759c1453, 42c99b8b0add8c369654db0c60fb49de3d64748a, b9f5b4a5fdc9575c9121398114e042bb046f2fac. These are source-write confirmations, **not** executed Python tests.
- **NOT RUN:** Python unittest, validator CLI, compileall, GitHub Actions, native builds, integration and live VPN/device tests. The UX contract remains a proposed specification, not a functioning tunnel.
- Next: independently run `python docs/vpn/ux/validate_contract.py` and `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v` on final exact HEAD; audit all remaining paths to `disconnected`, particularly `offline/network_restored` and `error/retry`, against authoritative stop semantics. CTO must approve cross-client contract changes; no merge before audit and CI.

## 2026-11-22 — P1 prototype activation authority guard

- Issue #39, existing branch `docs/vpn/39-interface-specs`, Draft PR #75. No shared or native code changed; foundation PR #1 is still an unmerged dependency.
- Root cause: the proposed transition `prototype_unavailable --engine_integrated_and_preconditions_ready--> disconnected` could previously be rewritten with `source: user` while passing the generic allowed-source validator. A user/UI event must not authorize enabling a nonfunctional VPN scaffold.
- Changed `validate_contract.py` to require the exact origin/target and `trusted_service` authority for this event; added two negative unittest methods in `test_contract.py` covering untrusted sources and wrong lifecycle endpoints.
- Commits: validator `84b6715436f19bf2cb2dd79f31e82b2e24d700ea`; regression source `4d66012726cbdccd3e1d21112bc0ac0817fc460f`. Re-fetch HEAD before any subsequent write.
- Evidence: GitHub accepted both file updates and blob SHAs. Python validator, unittest, compileall, Actions, native build, integration and live VPN/device tests: **NOT RUN** in this cycle. Authored negative tests are not passing test evidence. No actual VPN engine or protected tunnel exists.
- Next: run `python docs/vpn/ux/validate_contract.py` and `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v` on the exact final PR HEAD; independent auditor to review authority semantics and source SHA; CTO/integrator to define authoritative service/engine contract and activate relevant mandatory CI. Acceptance requires actual passing checks and independent non-author review before integration. No self-merge or public release.


## 2026-11-23 — P1 engine lifecycle provenance follow-up

- **Issue/branch/Draft PR:** #39 / `docs/vpn/39-interface-specs` / #75 (unmerged proposed UX contract).
- **Change:** `validate_contract.py` now constrains `engine_channel_lost` to `verified_connected -> interrupted` and `reassertion_started` to `verified_connected -> reconnecting`, both from declared `trusted_service`. Two unittest methods cover 12 wrong-source mutations, 4 wrong-edge mutations, and 2 accepted trusted cases.
- **Evidence:** GitHub Contents API accepted source and test writes on exact prior blobs `d84d91aac4c43352278c5403e96d92345f679e6d` and `1a4e33cb307a6c9b2a328dd00851d53f3d3490ea`. Source inspection only; **Python unit, validator execution, compileall, contract runtime, native build, integration, device/live VPN and leak tests: NOT RUN** (local Git remote DNS unavailable). New tests are authored, **not verified passing**.
- **Architecture/risk:** This validates only labels in a proposed JSON UX contract. It does **not** authenticate event producers or prove OS tunnel teardown, DNS/route correctness or packet protection. Backend/native authority and identity checks require CTO/security review.
- **Next:** execute `python docs/vpn/ux/validate_contract.py`, `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/ux` on final SHA; obtain independent AI audit and mandatory GitHub CI on integration SHA. No self-merge.
