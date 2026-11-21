# WexumVPN Android — isolated engineering scaffold

Scope: issue #5. All code is confined to apps/vpn/android/. This is NOT a working VPN, a protected session, or a deployable product.

## Included
- Standalone Android application (Kotlin + SDK, minSdk 26, targetSdk 35).
- System VPN permission request using VpnService.prepare and a service guarded by BIND_VPN_SERVICE.
- Explicit process-local connection state machine; no protection claim merely from permission approval.
- Neutral black-and-white status screen, explanatory safety text and OS app language settings.
- Published native Android resource catalogs: English, Russian, Kazakh, Arabic, with RTL enabled and Android 13+ app locale configuration.
- Unit tests and a Kotlin-only smoke harness. No network requests, VPN routing, SDK tunnelling, credentials or persistent connection flags.

## Security decision
The VpnService subclass stops itself immediately if started: no TUN interface is established, no network routes are changed and no "Connected" state is produced. Even the model's tunnelVerified function is INTERNAL and not called in the application. Its four booleans are hypothetical gating test inputs, NOT acceptable real-world proof. A future approved engine must implement actual protocol handshake, TUN ownership, socket protection, DNS/route testing, network handover, foreground service notifications, credential revocation and independent leakage testing BEFORE wiring this state. Never store a "protected" value across process restarts.

Android system VPN consent is not permission to claim protection. Users can grant and revoke VPN permission; granting changes state only to READY ("not connected"). No destination browsing history, credentials, PII, analytics, third-party SDKs, network traffic or user files are collected.

## How to check
From apps/vpn/android/:

- JVM smoke (requires Kotlin CLI and Java):
  kotlinc app/src/main/java/com/ihsansoft/wexumvpn/ConnectionStateMachine.kt tests/StateMachineSmoke.kt -include-runtime -d /tmp/wexumvpn-state-tests.jar
  java -jar /tmp/wexumvpn-state-tests.jar
- Android SDK + Gradle environment, when available:
  gradle :app:testDebugUnitTest :app:assembleDebug

No Gradle wrapper binary, APK, or CI workflow is included; the repo main branch currently lacks an approved Android build workflow. The build and Android runtime were NOT verified without the SDK. Gradle plugin AGP 8.9.2, Kotlin plugin 2.0.21, and JUnit test dependency 4.13.2 need dependency provenance and license checks during integration. Only JUnit is introduced for tests, no added third-party runtime library.

## Integration blockers
- Foundation #1, independent audit and integrator approval.
- Approved Android VPN protocol and transport implementation; validated Control Plane (#2), Entitlements (#3), Nodes (#4), Identity (#34), their contract schemas and failures.
- OS-specific end-to-end testing on real target devices (VPN consent/revoke, doze, network switch, DNS/IP leaks, always-on lockdown, foreground service requirements).
- Play VPN policy and country/legal/store approval, security/privacy and religious review.
- Approved shared i18n adapter contract (draft #50) before cross-product integration. Native Android only currently, no geolocation/IP-based language choice.

Deployment: none. Rollback: close this draft and remove isolated apps/vpn/android/ directory; no database, migration, user data, or live endpoints.
