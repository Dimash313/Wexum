# HANDOFF — WexumVPN Android Engineering

> Last reconciled with GitHub: 2026-11-21 (Asia/Almaty).
> Status: **development-only, not a functioning VPN**. Update this file whenever the lane changes substantially, before handing off or completing a stage. GitHub is the source of truth, not past chat messages.
> This document records the Android lane only. It does not assert integration, audit approval, or production readiness.

## 1. Lane ownership and boundaries

- Product/lane: **WexumVPN — Android Application** (native Kotlin, Android SDK and official `VpnService` API).
- Repository: https://github.com/Dimash313/Wexum
- Exclusive editable path: **`apps/vpn/android/`**. Implement Android application source, UI, permission/lifecycle handling, Android-native resources, focused tests, Android-local build instructions and this handoff.
- Do **not** edit sibling VPN lanes, Wexum Core, `docs/vpn/`, `docs/engineering/STATE.md`, shared APIs/contracts, `.github/workflows/`, or another lane's documentation without CTO/integrator approval.
- Shared Android CI must be activated by the integration/CI owner under `.github/workflows/` (tracked in #68), not silently added by this lane.
- Do not merge/approve own PR; do not push to `main`; do not claim security, compliance, availability, or "10/10" without independent evidence.

## 2. Current architecture and technical decisions

The current Android project is an **honest permission-only scaffold**, not a usable VPN client.

- Build: `apps/vpn/android/settings.gradle.kts`, root `build.gradle.kts`, `app/build.gradle.kts`; Kotlin Android plugin **2.0.21**, Android Gradle Plugin **8.9.2**, `minSdk 26`, `compileSdk/targetSdk 35`, JDK 17, intended Gradle 8.11.1.
- UI: `app/src/main/java/com/ihsansoft/wexumvpn/MainActivity.kt` uses Android framework views with premium black-and-white presentation; status always reflects current process-local snapshot, not a guessed server or tunnel state. Subscription begins in `onStart`, closes in `onStop`, and renders on UI thread.
- Permission: explicit user action calls `VpnService.prepare(context)`. `UserPort` manages consent attempts and rejects superseded/stale results; Activity rechecks OS permission after result and on resume. **Granted permission means PERMISSION_READY, not CONNECTED.**
- State: `ConnectionStateMachine.kt` provides synchronized process-local snapshots and revision numbers, observers, permission attempt IDs, and engine session IDs. UI is limited to `UserPort`; `ServicePort` handles service/engine lifecycle events. Current `EngineSignal` values: STARTING / INTERRUPTED / STOPPED / FAILED. There is intentionally **no verification event** capable of entering PROTECTED. The enum retains that phase only as future work.
- Engine boundary: `VpnEngineContract.kt` is an unimplemented, internal interface reserved for an independently reviewed transport. Its session ID is a stale-callback guard, **not** cryptographic proof, entitlement, or remote authorization. Do not accept arbitrary booleans, UI state, or backend strings as proof of a working tunnel.
- Service: `WexumVpnService.kt` declares OS `BIND_VPN_SERVICE` and handles `onRevoke`/`onDestroy`; the current `onStartCommand` fails closed and stops without creating a TUN interface. Manifest marks always-on unsupported for this nonworking scaffold.
- Locales: EN, RU, KK, AR resources under `app/src/main/res/values*/`, `locales_config.xml`, RTL enabled; Android 13+ OS per-app language settings. Shared i18n adapter #50 not integrated.
- Privacy: no stored "protected" flag, credentials, traffic capture, browsing history or real network transport. No deployed backend call. No runtime external SDK beyond Android/Kotlin.

**Trust caveat:** Kotlin `internal`/`UserPort`/`ServicePort` is an organizational boundary inside one application, **not** security isolation between processes. A future tunnel adapter must enforce authoritative, service-owned evidence and undergo review. An actual verified protected state and associated transition rules are **not implemented**.

**Engineering checkpoint (2026-11-21):** `ServicePort.attach()` now grants a unique lease per actual Android `VpnService` instance; `onStartCommand` and `onDestroy` must supply it. An old service cannot erase a newer state, and an OS permission revocation invalidates all leases. Invalid or out-of-order engine signals return false, rather than reporting success. Observer failures are isolated and report only the exception class; other observers and revocations continue. Local-only leases are stale-callback guards, not trust credentials. Current logic does not produce PROTECTED.

## 3. GitHub coordination

- Primary issue: **#5** — https://github.com/Dimash313/Wexum/issues/5
- Dedicated branch: **`feat/vpn/5-client-android`**
- Existing Draft PR: **#66** — https://github.com/Dimash313/Wexum/pull/66
- PR base: `main`; at this handoff, PR #66 remained open/draft. Previous code baseline: `fc1f7129bce5d29a7c1eae2a4974899010c1fec4` (HANDOFF creation). The current pending hardening commit advances this; always re-fetch the latest branch head.
- CI integration blocker: **#68** — https://github.com/Dimash313/Wexum/issues/68
- Foundation dependency: **PR #1** — https://github.com/Dimash313/Wexum/pull/1 (still unmerged at handoff).
- Do not start another PR for the same issue unless integrator explicitly requests it; continue #66.

## 4. Implemented source and checks

- Native app shell and permission request flow: `MainActivity.kt`, `AndroidManifest.xml`.
- Fail-closed VPN service placeholder: `WexumVpnService.kt`.
- Separate UI-consent versus service-engine state ports and process-local reactive state: `ConnectionStateMachine.kt`, `VpnRuntime.kt`.
- Future-only transport interface: `VpnEngineContract.kt`.
- Minimalist translated resources: English, Russian, Kazakh and Arabic.
- Negative unit tests: `app/src/test/java/com/ihsansoft/wexumvpn/ConnectionStateMachineTest.kt` (23 JUnit test methods written; actual Android Gradle JUnit not yet run).
- Kotlin-only standalone smoke: `tests/StateMachineSmoke.kt` (includes 100 consent/revoke race iterations).
- Local Android build gate: `ci/android-check.sh`.
- SHA-pinned *proposal only*, **NOT an active GitHub workflow**: `ci/android-workflow.proposal.yml`.
- Scope and integration notes: `README.md`.

## 5. Actually observed versus unverified test results

**Previous development report (2026-11-21, for code head `96ce997`):**
- Pure Kotlin state-machine smoke reported **PASS** using Kotlin CLI 1.9.0 and Java 21; included denied permission, stale consent/event replay, UI observer lifecycle, interruption, service restart, and 100 concurrent grant/revoke trials.
- A GitHub blob-SHA parity check for core Kotlin source and smoke file was reported: `ConnectionStateMachine.kt` blob `d0eb573b71768193be9d42787135e8bb63e3f4d3`; `StateMachineSmoke.kt` blob `bf07a38512343e521935aef8fd6164c926b90881`.
- Shell syntax check (`bash -n`) and manifest/XML/workflow YAML parsing reported **PASS** in prior development report.

**Critical evidence limitation:** these are **prior author reports**, not a new run or full Android suite during this handoff update. Re-run them on current head before asserting a new pass; retain exact commands, tool versions, output and Git SHA.

**Verified by GitHub read at this handoff:** PR #66 open and draft on the branch; zero PR-triggered workflow runs found for the previous code head `96ce997`. No Android CI green status can be asserted.

**NOT executed/NOT verified:** Android Gradle build (`assembleDebug`), `testDebugUnitTest` (16 JUnit tests), Android lint, emulator/physical device lifecycle, real VPN permission/revoke behavior, foreground services, tunnel handshake, routing, DNS/IP leaks, latency/load, always-on/lockdown, security audit, store/legal/religious release approvals. Gradle/Android SDK were unavailable in earlier local environment.

Reproduction from repo root (requires Gradle 8.11.1, JDK 17, SDK platform 35 and Build Tools 35.0.0):

```sh
bash apps/vpn/android/ci/android-check.sh
```

Kotlin-only smoke from `apps/vpn/android/`:

```sh
kotlinc app/src/main/java/com/ihsansoft/wexumvpn/ConnectionStateMachine.kt tests/StateMachineSmoke.kt -include-runtime -d /tmp/wexumvpn-state-tests.jar
java -jar /tmp/wexumvpn-state-tests.jar
```

Do not substitute a Kotlin smoke PASS for Android build, JUnit, emulator or VPN evidence.

**Current locally rerun candidate checks (2026-11-21):**
- `kotlinc-jvm 1.9.0` and Java 21: compiled and ran pure Kotlin `ConnectionStateMachine.kt` + `StateMachineSmoke.kt`: **PASS**, including 100 concurrent consent/revoke iterations, invalid transitions, expired service leases and observer error isolation.
- Kotlin JUnit-source methods were compiled and invoked with **temporary local Java stubs of JUnit annotations and assertions**: **23/23 PASS**. This does *not* mean Android Gradle `testDebugUnitTest` or real JUnit was executed.
- `WexumVpnService.kt` and `VpnRuntime.kt` compiled and ran one lifecycle test with a **temporary Android API stub**: **PASS** (stopSelf, onRevoke followed by onDestroy). This is not an emulator/OS test.
- Verified Git blob SHA parity on candidate tree: model `87c4b1dc4d134aad8df5c7e2ad27bb16b424aab2`, smoke `f2fcffffa1268740fa092d5788f4bbb1fdb3786a`, JUnit source `30061a854ebc3e824ec69c84d96cd8e4bf78265a`, service `34d7892d2281a7948e7410b60eda8229f0534126`.
- **Still unverified:** Gradle/Android SDK build, lint, actual JUnit runner, emulator/real device behavior, real VPN connection, CI on this head, full independent review.

## 6. Known problems, limitations and blockers

1. **No real VPN engine, verified tunnel, gateway transport, route/DNS setup, protected sockets, or connection lifecycle**. `PROTECTED` is purposely unreachable from existing engine events.
2. **No actual Android CI**: workflow is in a proposal file under the owned path, not GitHub's root workflows directory. #68 is assigned to integrator. Prior head had 0 workflow runs and 0 legacy statuses.
3. **Missing Android SDK/Gradle verification**: compilation/lint/JUnit/instrumented tests cannot be treated as passing; no emulator or device evidence.
4. **Control-plane dependencies unapproved/unintegrated**: Foundation PR #1 and independent audit #41; Identity #34; VPN Control Plane #2, Entitlements #3, Nodes #4; i18n #50. Do not invent or lock cross-team wire/API contracts without CTO-approved ADR.
5. **Security and lifecycle unknowns**: revocation under all Android process/service lifecycles; network switching and outage; always-on/lockdown; Android foreground-service policy; re-entrancy and observer ordering; races between OS consent callbacks and service revocation; no persistence of safe authoritative service state across process death. None has live Android test evidence.
6. **Governance/release blockers**: #38 independent reviewer enforcement, #41 audit, Google Play/platform policy, lawful operation/privacy and religious review. Green isolated tests are insufficient.
7. **Build reproducibility incomplete** until independently validated on CI; no reviewed Gradle wrapper/checksum is committed and the proposed Android workflow is not active.

## 7. Concrete next tasks (priority order)

1. **On any "Продолжаем дальше"**: read the repository's *current* `AGENTS.md` (if still absent on main, read from foundation PR #1), `README.md`, `docs/engineering/STATE.md`, `docs/engineering/QUALITY.md`, `docs/engineering/REVIEW_PROTOCOL.md`, `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/policy/RELIGIOUS_REVIEW.md`, **this `HANDOFF.md`**, issue #5, PR #66 discussion/reviews, related open PRs and current branch head. Inspect all changed Android source before editing. Do not assume previous state is still current.
2. Coordinate #68 with integrator to activate required Android CI in shared `.github/workflows/` under an authorized **separate** integration PR; demand exact PR-head/merge-candidate GitHub Actions logs, JUnit, lint and debug build. Never move or duplicate shared workflows unilaterally.
3. On a machine with Android SDK, reproduce `ci/android-check.sh`, fix any compiler/manifest/resources/lint/test errors within the Android-owned path; add tests for OS consent cancel/failure, Activity recreation, service onRevoke/onDestroy, observer teardown and stale callbacks.
4. Continue negative and concurrency testing of the stricter service-lease state model on Android; prove OS consent cancellation, Activity recreation, service callbacks and observer failure isolation on an emulator. The pure-JVM lease/transition/observer tests are complete only as narrow local evidence.
5. Under CTO/security agreement, define an interface contract for authoritative tunnel verification without claiming booleans are proof. Obtain approved protocol, entitlement, node and identity contracts **before** connecting any real engine.
6. Implement tested service-owned engine integration, correct foreground notifications, socket protection, network lifecycle, cancellation and cleanup only after the approved architecture exists. Add instrumentation tests, real device handover/revocation and DNS/IP leak testing. Do not show "protected" before real end-to-end verification.
7. Request independent audit of PR #66 on the latest head; close findings with tests, refresh PR description and **update this HANDOFF.md** on every substantive change or before stage handoff. Never self-approve or merge.

## 8. Source links and resume rules

- [Issue #5 — Android lane](https://github.com/Dimash313/Wexum/issues/5)
- [Draft PR #66 — Android source](https://github.com/Dimash313/Wexum/pull/66)
- [Issue #68 — activate Android CI](https://github.com/Dimash313/Wexum/issues/68)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1)
- [Independent foundation audit #41](https://github.com/Dimash313/Wexum/issues/41)
- [Governance/required approvals #38](https://github.com/Dimash313/Wexum/issues/38)
- [Android README](README.md)
- [WexumVPN architecture](../../../docs/vpn/ARCHITECTURE.md) (currently in foundation PR #1)
- [WexumVPN requirements](../../../docs/vpn/PRODUCT_REQUIREMENTS.md) (currently in foundation PR #1)
- [Quality standard](../../../docs/engineering/QUALITY.md) (currently in foundation PR #1)
- [Engineering rules](../../../AGENTS.md) (currently in foundation PR #1)

**Permanent continuation rule:** act autonomously within Android ownership when given "Продолжаем дальше": inspect latest GitHub + docs + this handoff, pick the highest-priority unblocked Android task, commit real changes to the existing branch, run available tests, update Draft PR #66 and this file, and report exact evidence. Never require the owner to reassign already clear work. Never alter another lane's docs without CTO authorization. No self-merge, invented test outcomes, or "VPN is working" claims.

## 2026-11-22 — Android P1 CI compiler unblock (one scoped cycle)

- Issue #5, existing branch `feat/vpn/5-client-android`, Draft PR #66. Integration-owned CI blocker #68 / Draft PR #82 remains separate; no root workflow touched.
- Exact pre-fix Android PR head: `8b4474947861b2a22ebb86d721d24eb6c2e0423d`. Integration observed Kotlin compiler failure `MainActivity.kt:81:13 Unresolved reference 'fillViewport'` on two GitHub Actions runs: https://github.com/Dimash313/Wexum/actions/runs/45001211641 and https://github.com/Dimash313/Wexum/actions/runs/45001263031.
- Source-only fix: `MainActivity.kt` uses Android `ScrollView.isFillViewport = true` (the Kotlin Boolean Java-bean property) instead of nonexistent `fillViewport = true`. Commit `1bd9550cca27784a92316f387af7cf81e4558ed2`. No VPN state, service, consent, permission, or networking behavior changed.
- **Evidence:** GitHub contents update returned commit and blob `b173279249824748ee4fd929fe4481f3338416ad`; re-fetch after handoff update to verify final HEAD. This is a targeted source correction, **not a passing compilation**.
- **Tests:** prior Android GitHub CI = FAIL on old SHA. New-head Gradle compilation, Android unit, lint, assembleDebug, integration and live VPN/device tests = **NOT RUN / awaiting CI**. No working VPN engine exists.
- **Next owner:** CTO/Integration (#68/#82) must rebase/recreate the CI-only candidate against new PR #66 head, then execute JDK 17 / Gradle 8.11.1 / AGP 8.9.2 / SDK 35 tasks `:app:testDebugUnitTest :app:lintDebug :app:assembleDebug`, record Actions run URL + exact SHA and require independent review. Android lane fixes any remaining product-source errors in PR #66. Do not merge either PR while red/unreviewed; foundation PR #1 remains unmerged.
