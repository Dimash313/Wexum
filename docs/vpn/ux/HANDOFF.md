# WexumVPN Interfaces & UX — persistent handoff

> **Read this first in every new chat/agent session.** This is the live, issue-owned continuation record, not evidence of product release. Updated: **2026-11-21** (based on GitHub state checked that day). Re-check GitHub before relying on any status below. Do not infer new work from a chat transcript.

## 1. Mission, scope and ownership

- Direction: **WexumVPN — Interfaces & UX**; [issue #39](https://github.com/Dimash313/Wexum/issues/39).
- Repository: [Dimash313/Wexum](https://github.com/Dimash313/Wexum).
- **Exclusive mutable scope:** `docs/vpn/ux/`. Own VPN UX flows, screen specifications, accessible UX copy, native handoff, state/rendering contract proposal, UX research plan and acceptance tests.
- **Not owned:** native apps `apps/vpn/android/`, `apps/vpn/ios/`, `apps/vpn/desktop/`; VPN service/control/entitlements/billing/nodes/security; root workflows; `docs/engineering/STATE.md`, `AGENTS.md`, `docs/design/`, `docs/i18n/`; platform-wide `packages/design-system/` and `packages/i18n/`.
- `packages/vpn-design/` is **NOT approved or created**. Obtain CTO/integrator agreement on exact shared package boundary and design token contract before modifying any package or common API.
- Owner-specific visual constraints: premium monochrome UI, calm typography, no music, no depiction of living beings, no false VPN connection/metrics. Uphold the [religious review policy](../../policy/RELIGIOUS_REVIEW.md).

## 2. Source of truth and operating rules

1. Read latest repo status, PRs, issues, review comments and branch heads; **first** read root `AGENTS.md`, `README.md`, `docs/engineering/STATE.md`, `docs/architecture/SYSTEM.md`, `docs/architecture/BOUNDARIES.md`, `docs/engineering/QUALITY.md`, `docs/engineering/REVIEW_PROTOCOL.md`, `docs/policy/RELIGIOUS_REVIEW.md`.
2. Then read [issue #39](https://github.com/Dimash313/Wexum/issues/39), this file, [README.md](README.md), [SCREENS.md](SCREENS.md), [NATIVE_HANDOFF.md](NATIVE_HANDOFF.md), [connection_states.json](connection_states.json), [validate_contract.py](validate_contract.py) and [test_contract.py](test_contract.py).
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
| UX PR known head before this handoff | `7104e8f5727a2db4a03489ca78377a960c1dcad8`; refresh after this commit |

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

Current artifacts provide no real user-facing VPN connection or status. No native UI, billing, localization catalog or shared components were implemented by this lane.

## 6. Testing — observed evidence vs not run

**Executed and passed in a previous agent turn:** 205 structural JavaScript assertions over six files freshly fetched from the actual GitHub branch (JSON parse, expected state IDs, counts, transition uniqueness, key naming, protection/evidence flags, file presence). This is a *custom structural consistency check*, **NOT** the Python unit suite, CI, UX/device testing, validated native security or an independent audit.

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
2. **Get independent review** of `connection_states.json` and `SCREENS.md`: security #11 + native #5/#6/#7 must validate truth-source boundaries, revoke/expire/loss flows, no stale “Protected” display. Issue comment or PR review links are the evidence; don't claim coordination occurred without posting.
3. Draft proposed **state-to-copy matrix** (including source-authority, disabled actions, screen-reader announcement and recovery behavior) inside `docs/vpn/ux/`; avoid adding translations to `packages/i18n/`. Verify no status, timeout or permission can imply protection without evidence.
4. Confirm CTO-approved **design token and reusable UI boundary** against #42 before any shared component implementation. Seek CTO decision as issue/PR comment; do not create `packages/vpn-design/` prematurely.
5. Create proposed **screen-by-screen accessibility/RTL verification matrix** for Android/iOS/Desktop (compact/dynamic type, keyboard/focus, landscape/tablet, 200% zoom, AR/KK/RU/EN). Later native teams execute device checks and attach evidence.
6. Coordinate `vpn.status.*`/`vpn.detail.*` key contract with i18n owner #44/#46 and arrange human review of safety-critical strings. Don't mark planned locales published.
7. After foundation and dependency reviews, retarget/rebase PR only through approved integrator procedure, run mandatory CI on the actual integration head, and keep Draft state until independent acceptance.

## 9. Reference index

- Core: [Issue #39](https://github.com/Dimash313/Wexum/issues/39), [Draft PR #75](https://github.com/Dimash313/Wexum/pull/75), [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1), [Independent audit #41](https://github.com/Dimash313/Wexum/issues/41), [CTO continuity/governance #76](https://github.com/Dimash313/Wexum/issues/76).
- Design: [Issue #40](https://github.com/Dimash313/Wexum/issues/40), [PR #42](https://github.com/Dimash313/Wexum/pull/42).
- Localization: [Issue #44](https://github.com/Dimash313/Wexum/issues/44), [PR #45](https://github.com/Dimash313/Wexum/pull/45), [PR #50](https://github.com/Dimash313/Wexum/pull/50).
- Platforms: [Android #66](https://github.com/Dimash313/Wexum/pull/66), [iOS #69](https://github.com/Dimash313/Wexum/pull/69), [Desktop #70](https://github.com/Dimash313/Wexum/pull/70).
- Other engineering lanes: [Security #11](https://github.com/Dimash313/Wexum/issues/11), [QA #10](https://github.com/Dimash313/Wexum/issues/10), [Identity #34](https://github.com/Dimash313/Wexum/issues/34), [Entitlements #3](https://github.com/Dimash313/Wexum/issues/3), [Nodes #4](https://github.com/Dimash313/Wexum/issues/4), [Billing #9](https://github.com/Dimash313/Wexum/issues/9).
- Local artifacts: [README](README.md), [screen flows](SCREENS.md), [native handoff](NATIVE_HANDOFF.md), [state contract](connection_states.json), [validator](validate_contract.py), [tests](test_contract.py).
- Project entry points: [AGENTS.md](../../../AGENTS.md), [quality gate](../../engineering/QUALITY.md), [VPN architecture](../ARCHITECTURE.md), [review protocol](../../engineering/REVIEW_PROTOCOL.md).

## 10. Update and reporting protocol

After every substantive change, **update this HANDOFF.md in the same branch** and refresh Draft PR #75 if scope/evidence/risks change. Preserve a precise record of: the actual head SHA, current status, decisions confirmed vs proposed, touched paths, exact tests truly executed (including failures), review feedback, blockers, next one or two actionable tasks, and links. In final chat report always provide **ready / tested / blocked / next / GitHub URL**, never claim asynchronous work.

Do not edit another workstream's HANDOFF.md or its docs without CTO coordination. If this PR is merged, ensure the integrated handoff stays current via the owning issue/next scoped PR, rather than an unmerged stale branch.
