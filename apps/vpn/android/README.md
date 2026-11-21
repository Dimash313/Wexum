# WexumVPN Android — isolated engineering work (issue #5)

This is **not a working VPN**. No tunnel, authentication handshake, gateway, DNS/route verification, production traffic or entitlements are implemented. Granting Android VPN permission only means **permission granted — not connected**.

## Scope
- Native Kotlin + Android SDK shell: AGP 8.9.2, Kotlin plugin 2.0.21, compile/target SDK 35 and min SDK 26.
- User-driven `VpnService.prepare(context)` permission flow. Explicit OS permission recheck after callback and on Activity resume; failed consent intent and invalid results never report protection.
- Thread-safe process-local state with a separate Activity `UserPort` and internal `ServicePort`. Pending consent IDs and engine-session IDs reject stale messages after revoke/crash. The future engine interface has no event that can claim a verified tunnel.
- Lifecycle-bound UI observer subscribes onStart and unsubscribes onStop, rendering current service state on the UI thread. Status is never persisted.
- Placeholder `VpnService` immediately stops without starting TUN or modifying routes. Always-on VPN is disabled in the manifest for this nonfunctional scaffold.
- Simple black-and-white UI, EN/RU/KK/AR Android resource catalogs, Android 13+ OS app language preferences and RTL.
- Pure JVM negative tests cover permission replay, grant/revoke races, engine callback replay, failure recovery, observer lifetimes and process reset. No runtime third-party libraries, analytics, traffic inspection or credentials.

## Reproducible build proposal

Official AGP 8.9.2 requires Gradle **8.11.1** and JDK **17**. Android SDK platform **35** and Build Tools **35.0.0** are required. The build entrypoint enforces versions and fails rather than skipping tests:

```sh
bash apps/vpn/android/ci/android-check.sh
```

When those prerequisites are installed, it runs Gradle `:app:testDebugUnitTest`, `:app:lintDebug`, and `:app:assembleDebug`.

Pure Kotlin local smoke (independent of Android SDK):

```sh
cd apps/vpn/android
kotlinc app/src/main/java/com/ihsansoft/wexumvpn/ConnectionStateMachine.kt tests/StateMachineSmoke.kt -include-runtime -d /tmp/wexumvpn-state-tests.jar
java -jar /tmp/wexumvpn-state-tests.jar
```

**GitHub Actions is not active.** The proposed minimal-permission SHA-pinned workflow is under `ci/android-workflow.proposal.yml`, which GitHub will not execute at that path. Only the integrator may create a workflow at repository-root `.github/workflows/android.yml`, via a separate independently reviewed PR. No binary Gradle wrapper is included because its provenance could not be verified; the pinned `setup-gradle` action installs Gradle 8.11.1 in the proposed runner.

Without local Android SDK + Gradle, Android compilation, JUnit execution, lint and runtime/emulator verification remain **NOT VERIFIED**. Smoke tests are not equivalent to Android tests or a CI result.

## Trust boundaries and blockers

Client-side consent cannot substitute for server-side identity/entitlement authorization. Future integration must use independently reviewed engine and service contracts and real verification of TUN ownership, gateway handshake, protected sockets, credentials, DNS/IP leaks, network switching, always-on lockdown, Android foreground-service requirements and cancellation. No `PROTECTED` event is available until these conditions are designed, implemented and verified.

Foundation PR #1, audit #41, review governance #38, VPN Control Plane #2, Entitlements #3, Nodes #4, Identity #34 and i18n draft #50 remain dependencies. Android store/legal/privacy/religious review is pending. Never merge on a green smoke test alone.

Rollback: close draft PR #66 or remove only `apps/vpn/android/`; there are no deployments, migrations, billing records, credentials or user data.
