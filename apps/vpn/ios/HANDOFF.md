# WexumVPN iOS — engineering handoff

Updated: 2026-11-21 (UTC). **Source of truth: live GitHub, not a chat transcript.**

## 1. Direction and exclusive ownership

- **Direction:** native standalone WexumVPN iPhone client (Swift, SwiftUI, Apple Network Extension).
- **Owning issue:** [#6 — VPN / client-ios](https://github.com/Dimash313/Wexum/issues/6).
- **Exclusive editable path:** `apps/vpn/ios/`. Do **not** edit other platform lanes, backend, `docs/vpn/`, root `AGENTS.md`, shared `.github/workflows/`, or `docs/engineering/STATE.md` without CTO/integrator coordination and approval.
- Deliver native app lifecycle, user-facing connection state, network changes, accessible/localized UI, controlled API integration after approved contracts, tests and Apple capability evidence. Do not implement or imply a real VPN before proof.
- General rule: one issue/branch/Draft PR; no direct `main` commits, force pushes, self-approval, unreviewed merges, invented pass results or new release numbers.

## 2. Current architecture and decisions

- Standalone iOS application target at `WexumVPN.xcodeproj`, SwiftUI entry `WexumVPNApp/WexumVPNApp.swift` and UI in `ConnectionView.swift`. Intended minimum iOS 16.
- `Sources/WexumVPNCore/ConnectionState.swift`: **pure Swift, UI-only fail-closed reducer** and `ObservationEpoch` generation/token gate, independently packaged with `Package.swift`. Events cover configuration, native status, network loss/recovery, permission/observer failure and process reset. A native `connected` result maps to `connectedUnverified`; `isProtectionVerified` is always `false`. The epoch invalidates pending configuration completions and status reads when a refresh supersedes them or network path changes. State does **not** authorize tunnel use.
- `WexumVPNApp/ConnectionStore.swift`: read-only `NETunnelProviderManager.loadAllFromPreferences`, `NEVPNStatusDidChange`, `NWPathMonitor`, app lifecycle refresh; `ObservationEpoch` gates responses and OS statuses; path changes invalidate old tickets and trigger a fresh configuration load on recovery. Duplicate path events are ignored; notification source identity is checked; more than one visible manager fails closed. Local system status is **not** a packet-protection assertion.
- No calls to `startVPNTunnel`, `saveToPreferences`, or tunnel network settings. No packet tunnel extension, real VPN engine, server API, enrollment, identity, grants, node selection, billing, secrets or background traffic are implemented.
- `WexumVPNApp/*.lproj/Localizable.strings`: EN/RU/KK/AR from OS per-app/device language settings; no geolocation/IP/payment-based language inference. Persisted manual language override/approved i18n adapter pending [PR #50](https://github.com/Dimash313/Wexum/pull/50). Native-speaker, VoiceOver and RTL review not completed.
- `WexumVPNApp/WexumVPNApp.entitlements` requests `packet-tunnel-provider`; file presence is **not** proof that Apple grants or provisioning enable the capability. See `Docs/APPLE_GATES.md`.
- Strict separation: eventual data plane = independently audited packet tunnel gateway; control plane = approved enrollment/device/entitlements/node API; management plane is not on each packet. No invented cryptography or unapproved cross-lane interfaces.

## 3. GitHub work tracking

- Issue: [#6](https://github.com/Dimash313/Wexum/issues/6) (open).
- Branch: [`feat/vpn/6-client-ios`](https://github.com/Dimash313/Wexum/tree/feat/vpn/6-client-ios).
- Draft PR: [#69 — iOS status shell](https://github.com/Dimash313/Wexum/pull/69) (open, draft); inspected up to code/documentation commit `55a5070cbc7e5bd1de10eeb82a489162be679184`. On continuation **fetch the latest head**; this handoff update is a subsequent commit.
- **Stacked PR base:** `architecture/foundation-and-agent-operating-system`, not `main`, because [foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) was open/unmerged at last check. Do not treat that base as integrated; CTO/integrator must coordinate rebasing/retargeting.
- All files in this Draft PR stay inside the owned `apps/vpn/ios/` path (18 paths including the new inactive macOS CI proposal at last count). No merge or public release.

## 4. Implemented and proposed artifacts

- Pure state reducer and observation epoch gate, test target `Tests/WexumVPNCoreTests/ConnectionStateTests.swift` (**16 test methods**, including 5 new stale-callback/network invalidation tests).
- Native SwiftUI status/disclaimer screen with a **refresh-only** action; connect/disconnect intentionally unavailable.
- Read-only native configuration/status observer, epoch-checked notification bridge and network path monitor that invalidates stale tickets on transitions.
- Four localized string catalogs and initial accessibility hints.
- Xcode project/shared scheme, entitlements request, Apple gate document, and `ci/ios-check.sh`, which now **fails with exit 78** if Xcode is missing instead of returning false green; `ci/macos-workflow.proposal.yml` is **not active** and needs integrator approval in the shared workflow directory.
- Work is **candidate implementation**, not real VPN functionality or a production-ready signed iOS artifact.

## 5. Verification ledger — separate evidence from claims

- **Directly executed during this development stage (2026-11-21, Linux x86_64, Swift 6.2.1):** `cd /mnt/data/wexum-ios/apps/vpn/ios && swift test` — **16/16 pass, 0 failures** after epoch gate change; `swiftc -frontend -parse WexumVPNApp/*.swift` — exit 0 (syntax only); `bash -n ci/ios-check.sh` — exit 0; `plutil -lint -- WexumVPN.xcodeproj/project.pbxproj WexumVPNApp/WexumVPNApp.entitlements` — both OK (before this change, project/plist unchanged); `bash ci/ios-check.sh` — **16/16 tests pass, then exit 78** with explicit Xcode unavailable message. Unit test log available in the session local worktree at `/tmp/wexum-ios-script.log` (not GitHub artifact). No Apple SDK typechecking.
- **Rechecked live GitHub this stage:** Issue #6 and Draft PR #69 open, foundation PR #1 still open/unmerged, no new PR review comments at stage start, owned-path-only files. Confirmed GitHub blob SHAs exactly match local tested source for reducer (`644274a4…`), tests (`b2d51994…`), native store (`2c5eb1f3…`), and CI script (`019ef2c4…`). No current-head macOS GitHub Actions result is established.
- **Environment:** Swift, `plutil` and `git` available in Linux container; `xcodebuild` absent. Direct `git` remote lookup failed DNS; all GitHub commits and file parity checks used the authenticated GitHub connector. Linux parse/test results are genuine but do not demonstrate a macOS build.
- **Not executed / not demonstrated:** Xcode project compilation, iOS Simulator, physical iPhone installation, provisioning/signing, Packet Tunnel Provider, native permission prompt, IPv4/IPv6/DNS leak checks, network transition tests on real devices, failover, CI required check, VoiceOver/RTL review, or third-party security assessment.
- Only mark a check PASS when the exact current commit, command, environment and actual outcome are recorded.

## 6. Known risks, gaps and blockers

1. **No real tunnel**: missing separately signed `NEPacketTunnelProvider`, approved maintained protocol engine, lifecycle and traffic/route verification. Native `connected` alone is insufficient.
2. **Apple capability/store gate**: eligibility and signed Network Extension provisioning unverified. Apple App Review 5.4 requires VPN provider organization enrollment and before-use/purchase collection/use disclosure; privacy, licensing and regulatory review remain open.
3. **Foundation & contracts**: PR #1 unmerged; [Control Plane #2](https://github.com/Dimash313/Wexum/issues/2), [Entitlements #3](https://github.com/Dimash313/Wexum/issues/3), [Node Registry #4](https://github.com/Dimash313/Wexum/issues/4), [Identity #34](https://github.com/Dimash313/Wexum/issues/34) and i18n PR #50 require owner/integrator agreement before wiring network/auth.
4. **State/UI risks:** current state is process-local and non-authoritative; stale async configuration results and previous-network statuses now have a deterministic epoch guard, but this native integration has **no Apple SDK/runtime test**, and manager ownership, revocation/expiry, concurrent network callbacks and multi-profile behavior still require design and real-device validation. OS network monitoring is not proof of tunnel security.
5. **Verification gap**: no macOS runner or shared CI integration; Xcode project and SwiftUI/NetworkExtension APIs have not been compiled against the Apple SDK. The owned `ci/macos-workflow.proposal.yml` is deliberately inactive until integrator reviews/copies to shared `.github/workflows/`; the check script exits 78 outside macOS/Xcode.
6. **Product readiness:** real backend, per-user isolation, key/storage design, load/resilience, privacy claims, localized accessibility and legal/religious approvals missing. No product launch.

## 7. Next precise tasks (in order)

1. **Re-read live GitHub** for issue #6, PR #69 comments/checks/head, foundation PR #1, dependencies and conflicts; compare working tree before editing. Read root `AGENTS.md`, `docs/engineering/STATE.md`, `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/engineering/QUALITY.md`, `docs/policy/RELIGIOUS_REVIEW.md`, `apps/vpn/ios/README.md`, this file.
2. **Validate candidate against actual Apple toolchain**: on a macOS runner, run `cd apps/vpn/ios && swift test`, `xcodebuild -project WexumVPN.xcodeproj -scheme WexumVPN -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO build`, and `plutil -lint` on project/entitlements. Record logs and fix compile defects **only under owned path**. If runner unavailable, state BLOCKED.
3. **Continue hardening** by adding a deterministic bridge test seam with mocked native preference loads, notification identity, overlapping refreshes, cancellation, and network path transitions; the newly added `ObservationEpoch` is tested but the actual NetworkExtension callbacks are not (no Apple SDK). Avoid enabling connect before audited backend/engine/provider decisions.
4. **Ask integrator to review/activate** `ci/macos-workflow.proposal.yml` as a proper required root `.github/workflows/` check on a budget-approved macOS runner. Do not edit shared CI directly. Require head-commit checks.
5. **Document provider and provisioning architecture** in owned docs; do not add an unreviewed packet engine or credentials. Resolve API/identity/grant interface decisions with respective owners; design revoke/expiry and crash/recovery behavior.
6. **Accessibility/i18n**: native VoiceOver, Dynamic Type, contrast, RTL/Arabic/Kazakh, per-app system locale and manual override tests once i18n contract approved.
7. Upon each substantial change: update this `HANDOFF.md` and PR #69 with exact evidence, blocker list, dependency state, next issue-specific action, and commit links; do not self-merge.

## 8. Links and continuation procedure

- [Issue #6](https://github.com/Dimash313/Wexum/issues/6) · [Draft PR #69](https://github.com/Dimash313/Wexum/pull/69) · [iOS branch](https://github.com/Dimash313/Wexum/tree/feat/vpn/6-client-ios)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) · [Localization PR #50](https://github.com/Dimash313/Wexum/pull/50)
- [AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md) · [VPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md) · [VPN requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md) · [Quality](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)
- [iOS README](README.md) · [Apple gates](Docs/APPLE_GATES.md) · [Validation script](ci/ios-check.sh) · [Inactive macOS CI proposal](ci/macos-workflow.proposal.yml)

**When the owner says «Продолжаем дальше»:** inspect current GitHub, read the mandatory docs and this handoff, choose the highest-priority unblocked item within issue #6, implement it in this branch, run every available genuine check, update Draft PR #69 and this handoff. If a cross-lane decision or Apple account is required, record the blocker and ask the integrator/owner through GitHub without modifying other lanes. A fresh AI should be able to continue from this document without asking the owner to repeat the history.


## 2026-11-22 — P1 audit remediation: refresh must invalidate stale UI status

- Independent audit: https://github.com/Dimash313/Wexum/pull/69#issuecomment-7063551605 (reviewed old head `72922fd7ddef6562d853bd7bd1b479711819c833`).
- Existing issue #6 / branch `feat/vpn/6-client-ios` / Draft PR #69. Scope exclusively `apps/vpn/ios/`.
- `ConnectionState` now has `configurationRefreshStarted` and a neutral `checkingConfiguration` phase. `ConnectionStore.refreshConfiguration()` clears old manager/ticket and applies the event synchronously before the asynchronous preference load. The view maps it to explicit unverified checking copy in EN/RU/KK/AR. A previous `connectedUnverified` label cannot persist while a new preferences read is pending.
- Two authored deterministic regression XCTest methods cover a never-completing callback/stale native status and a successful refresh requiring fresh native status. **Authored, NOT RUN** on this GitHub source. No new proof of actual tunnel protection.
- **NOT RUN:** Swift unit tests on exact current SHA, Apple SDK/Xcode build, simulator/device, GitHub Actions, integration, VPN traffic/DNS/IP leak tests. Do not treat source edits as successful tests.
- **Remaining P1:** the asynchronous preferences API has no bounded timeout/failure fallback in this change; a missing callback leaves neutral checking status indefinitely. Owner must implement a cancellable, epoch-checked timeout with negative tests and verify on Xcode. Independent auditor must re-review the new exact head. Integrator owns SHA-pinned macOS workflow activation; no shared CI touched.
- Rollback: revert only the above iOS-owned source, test and localization edits; no production deployment, secrets, accounts or migration.


## 2026-11-22 — P1 bounded configuration refresh (client lane)
- Scope: Issue #6, existing Draft PR #69, branch `feat/vpn/6-client-ios`. Only iOS-owned source, XCTest and this HANDOFF changed; no backend/shared workflow or `main` changes.
- Root cause: `NETunnelProviderManager.loadAllFromPreferences` may never invoke its callback, leaving the user-facing neutral `checkingConfiguration` state indefinitely. Previously reported stale-positive status was fixed separately; this checkpoint addresses the remaining unbounded wait.
- Change: `ObservationEpoch.expirePending(ticket)` atomically invalidates only the current, not-yet-activated read; `ConnectionStore.refreshConfiguration()` schedules a 10-second main-actor timeout that clears manager/ticket and moves the UI to `error` if no valid completion arrives. A late callback cannot reactivate an expired epoch. Superseded or completed reads are not invalidated by their old watchdog.
- Regression source: `testPendingPreferencesTimeoutInvalidatesLateCallback` and `testTimeoutCannotInvalidateCompletedOrSupersededRefresh`. Tests are **authored, NOT RUN**; the real 10-second scheduler/NetworkExtension callback ordering needs Xcode/Apple SDK tests and fault injection.
- Evidence: GitHub accepted source commits `5ad1152a0c7da984ad454dbe7c3fab13ff87aca3`, `2c5de40e0fe69954e91eafc39b750ee9f8d25c40`, and XCTest commit `c287c03c1e2749f1c01b0ce966c9fb9cc80f7311`. Read back latest HEAD and CI before any merge.
- Verification: source/blob readback is not a compiler/test run. Swift XCTest, Xcode build, GitHub Actions, integration, real VPN/device, IP/DNS leakage: **NOT RUN** for this change. A working tunnel and verified protection are **NOT IMPLEMENTED**.
- Remaining risks: main-actor scheduling can delay a watchdog; this is a bounded *requested* delay, not a hard real-time OS guarantee. Apple callback/device behavior, NetworkExtension entitlements, native CI and independent SHA-specific audit remain blocking. Future improvement: injectable clock/scheduler and native fault-injection tests for callback-never-arrives, late callback and repeated refresh.
- Next owners: iOS #6—run Swift tests and macOS Xcode build on exact current head; CTO/Integration—approve/activate macOS CI under shared workflow ownership; Independent Audit—review the exact source SHA and negative lifecycle cases. Acceptance: actual green XCTest/Xcode CI plus negative callback timeout evidence and independent review, not merely source presence.
