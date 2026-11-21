# WexumVPN Desktop — isolated application scaffold

GitHub issue: [#7](https://github.com/Dimash313/Wexum/issues/7).
Owned path: `apps/vpn/desktop/`. This is not a working VPN.

## Stack decision

- **C++20 standard-library core:** deterministic state transitions and locale
  resolution; tests compile without Qt or network access.
- **Qt 6 Widgets shell (optional build):** native desktop windowing available
  for Windows/macOS/Linux in principle. A single lean C++ build, no embedded
  browser, and accessible platform widgets favor straightforward auditing.
- **Future privileged service:** a separate, signed, OS-native helper or system
  VPN provider. Its design/IPC and backends need independent review before use.

Qt offers a common desktop abstraction without combining the UI and network
privileges. Tradeoffs: platform packaging still differs, GUI binaries require
Qt 6, and Qt licensing must be reviewed; cross-platform source does **not**
mean cross-platform validation. No new root/shared dependencies are introduced.

## Current behavior

The UI shows `Disconnected`, explicitly states that VPN integration is absent,
and disables both connection buttons. The user can choose System default,
English or Russian; only UI language choice is stored by `QSettings`.
System language ordering is used on first launch. The non-UI `ConnectionMachine`
models connection attempts, trusted policy changes, stale events, interrupted
channels, and explicit stop-confirmation. Neither model nor tests are an
operational VPN or authenticated service.

## Build and tests

Requirement: CMake >= 3.20 and a C++20 compiler.

```sh
cd apps/vpn/desktop
bash scripts/test.sh
```

To *attempt* the UI build, install compatible Qt6 Widgets development files:

```sh
cmake -S . -B build-ui -DBUILD_TESTING=ON -DWEXUM_DESKTOP_BUILD_UI=ON
cmake --build build-ui
ctest --test-dir build-ui --output-on-failure
```

A successful build does not prove native VPN operation or supported OS coverage.
For reproducible CI, integration owner may call `bash apps/vpn/desktop/scripts/test.sh`
from a pinned Linux C++ toolchain job. A root `.github/workflows/` edit requires
integrator approval and is deliberately absent here.

## Dependencies / rollout

- Foundation [PR #1](https://github.com/Dimash313/Wexum/pull/1) must be reviewed
  and merged before consuming its shared contracts.
- Global localization [PR #50](https://github.com/Dimash313/Wexum/pull/50)
  is only a draft; the local two-language UI is an interim, honest fallback.
- Identity, Entitlements, Control Plane and Node Registry require accepted,
  interoperable, device-bound and revocable contracts before real connections.
- Security model, platform gates, privacy and rollback: [docs/SECURITY.md](docs/SECURITY.md).

No deployment, secrets, privileged helper or service has been introduced.
Rollback: close this draft PR; no deployed assets or migrations exist.
