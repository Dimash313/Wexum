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
- `Sources/WexumVPNCore/ConnectionState.swift`: **pure Swift, UI-only fail-closed reducer**, independently packaged with `Package.swift`. Events cover configuration, native status, network loss/recovery, permission/observer failure and process reset. A native `connected` result maps to `connectedUnverified`; `isProtectionVerified` is always `false`. State does **not** authorize tunnel use.
- `WexumVPNApp/ConnectionStore.swift`: read-only `NETunnelProviderManager.loadAllFromPreferences`, `NEVPNStatusDidChange`, `NWPathMonitor`, app lifecycle refresh; generation guard for superseded preference reads; more than one visible manager fails closed. Local system status is **not** a packet-protection assertion.
- No calls to `startVPNTunnel`, `saveToPreferences`, or tunnel network settings. No packet tunnel extension, real VPN engine, server API, enrollment, identity, grants, node selection, billing, secrets or background traffic are implemented.
- `WexumVPNApp/*.lproj/Localizable.strings`: EN/RU/KK/AR from OS per-app/device language settings; no geolocation/IP/payment-based language inference. Persisted manual language override/approved i18n adapter pending [PR #50](https://github.com/Dimash313/Wexum/pull/50). Native-speaker, VoiceOver and RTL review not completed.
- `WexumVPNApp/WexumVPNApp.entitlements` requests `packet-tunnel-provider`; file presence is **not** proof that Apple grants or provisioning enable the capability. See `Docs/APPLE_GATES.md`.
- Strict separation: eventual data plane = independently audited packet tunnel gateway; control plane = approved enrollment/device/entitlements/node API; management plane is not on each packet. No invented cryptography or unapproved cross-lane interfaces.

## 3. GitHub work tracking

- Issue: [#6](https://github.com/Dimash313/Wexum/issues/6) (open).
- Branch: [`feat/vpn/6-client-ios`](https://github.com/Dimash313/Wexum/tree/feat/vpn/6-client-ios).
- Draft PR: [#69 — iOS status shell](https://github.com/Dimash313/Wexum/pull/69) (open, draft); last checked head `96208713f7830923e998c1d86cd30af72b20e76b`.
- **Stacked PR base:** `architecture/foundation-and-agent-operating-system`, not `main`, because [foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) was open/unmerged at last check. Do not treat that base as integrated; CTO/integrator must coordinate rebasing/retargeting.
- All 16 files in the PR at last inspection were inside the owned `apps/vpn/ios/` path; adding this file increases that count. No merge or public release.

## 4. Implemented and proposed artifacts

- Pure state reducer, test target `Tests/WexumVPNCoreTests/ConnectionStateTests.swift` (11 test methods).
- Native SwiftUI status/disclaimer screen with a **refresh-only** action; connect/disconnect intentionally unavailable.
- Read-only native configuration/status observer and network path monitor.
- Four localized string catalogs and initial accessibility hints.
- Xcode project/shared scheme, entitlements request, Apple gate document, and `ci/ios-check.sh`.
- Work is **candidate implementation**, not real VPN functionality or a production-ready signed iOS artifact.

## 5. Verification ledger — separate evidence from claims

- **Reported in prior PR #69 description:** `cd apps/vpn/ios && swift test` — 11/11 passed in Linux Swift 6.2.1; `swiftc -frontend -parse WexumVPNApp/*.swift`, `bash -n ci/ios-check.sh`, local `plutil -lint` — reported passed. These results are historical statements in the PR, **not independently reproduced during this handoff update**; attach machine-readable logs on a fresh independent run.
- **Rechecked via GitHub in this handoff:** issue #6 open, PR #69 open and draft, foundation PR #1 not merged, PR files restricted to owned path before this new file, and **zero GitHub Actions workflow runs on head `96208713f7830923e998c1d86cd30af72b20e76b`**.
- **Environment in handoff update:** Swift executable and `plutil` available; Xcode/`xcodebuild` not present. Remote Git clone from this environment cannot resolve github.com. No new Swift unit/test execution in this update.
- **Not executed / not demonstrated:** Xcode project compilation, iOS Simulator, physical iPhone installation, provisioning/signing, Packet Tunnel Provider, native permission prompt, IPv4/IPv6/DNS leak checks, network transition tests on real devices, failover, CI required check, VoiceOver/RTL review, or third-party security assessment.
- Only mark a check PASS when the exact current commit, command, environment and actual outcome are recorded.

## 6. Known risks, gaps and blockers

1. **No real tunnel**: missing separately signed `NEPacketTunnelProvider`, approved maintained protocol engine, lifecycle and traffic/route verification. Native `connected` alone is insufficient.
2. **Apple capability/store gate**: eligibility and signed Network Extension provisioning unverified. Apple App Review 5.4 requires VPN provider organization enrollment and before-use/purchase collection/use disclosure; privacy, licensing and regulatory review remain open.
3. **Foundation & contracts**: PR #1 unmerged; [Control Plane #2](https://github.com/Dimash313/Wexum/issues/2), [Entitlements #3](https://github.com/Dimash313/Wexum/issues/3), [Node Registry #4](https://github.com/Dimash313/Wexum/issues/4), [Identity #34](https://github.com/Dimash313/Wexum/issues/34) and i18n PR #50 require owner/integrator agreement before wiring network/auth.
4. **State/UI risks:** current state is process-local and non-authoritative; uncertain profile ownership, revocation/expiry, stale OS events and multi-profile behavior need explicit design, adversarial tests, and independent review before adding start/stop. OS network path monitoring must not be represented as proof of tunnel security.
5. **Verification gap**: no macOS runner or shared CI integration; Xcode project and SwiftUI/NetworkExtension APIs have not been compiled against the Apple SDK. Existing script in owned directory does not activate GitHub Actions.
6. **Product readiness:** real backend, per-user isolation, key/storage design, load/resilience, privacy claims, localized accessibility and legal/religious approvals missing. No product launch.

## 7. Next precise tasks (in order)

1. **Re-read live GitHub** for issue #6, PR #69 comments/checks/head, foundation PR #1, dependencies and conflicts; compare working tree before editing. Read root `AGENTS.md`, `docs/engineering/STATE.md`, `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/engineering/QUALITY.md`, `docs/policy/RELIGIOUS_REVIEW.md`, `apps/vpn/ios/README.md`, this file.
2. **Validate candidate against actual Apple toolchain**: on a macOS runner, run `cd apps/vpn/ios && swift test`, `xcodebuild -project WexumVPN.xcodeproj -scheme WexumVPN -sdk iphonesimulator -configuration Debug CODE_SIGNING_ALLOWED=NO build`, and `plutil -lint` on project/entitlements. Record logs and fix compile defects **only under owned path**. If runner unavailable, state BLOCKED.
3. **Harden fail-closed native status bridge** with injected test seams, stale-callback/session-token and profile identity checks, observer lifecycle and network switch tests. Avoid enabling connect before audited backend/engine/provider decisions. Keep tests deterministic.
4. **Prepare integrator-reviewed CI proposal** for macOS/Xcode tests without editing shared workflows directly. Request activation by CTO/integrator; require head-commit checks.
5. **Document provider and provisioning architecture** in owned docs; do not add an unreviewed packet engine or credentials. Resolve API/identity/grant interface decisions with respective owners; design revoke/expiry and crash/recovery behavior.
6. **Accessibility/i18n**: native VoiceOver, Dynamic Type, contrast, RTL/Arabic/Kazakh, per-app system locale and manual override tests once i18n contract approved.
7. Upon each substantial change: update this `HANDOFF.md` and PR #69 with exact evidence, blocker list, dependency state, next issue-specific action, and commit links; do not self-merge.

## 8. Links and continuation procedure

- [Issue #6](https://github.com/Dimash313/Wexum/issues/6) · [Draft PR #69](https://github.com/Dimash313/Wexum/pull/69) · [iOS branch](https://github.com/Dimash313/Wexum/tree/feat/vpn/6-client-ios)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) · [Localization PR #50](https://github.com/Dimash313/Wexum/pull/50)
- [AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md) · [VPN architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md) · [VPN requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md) · [Quality](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)
- [iOS README](README.md) · [Apple gates](Docs/APPLE_GATES.md) · [Validation script](ci/ios-check.sh)

**When the owner says «Продолжаем дальше»:** inspect current GitHub, read the mandatory docs and this handoff, choose the highest-priority unblocked item within issue #6, implement it in this branch, run every available genuine check, update Draft PR #69 and this handoff. If a cross-lane decision or Apple account is required, record the blocker and ask the integrator/owner through GitHub without modifying other lanes. A fresh AI should be able to continue from this document without asking the owner to repeat the history.
