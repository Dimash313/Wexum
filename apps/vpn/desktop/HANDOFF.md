# WexumVPN Desktop — engineering handoff

**Last inspected:** 2026-11-21 (GitHub issue #7, draft PR #70, and its branch).
**Status:** draft, non-connecting prototype only; no desktop OS is verified as a working VPN client.
**Source of truth:** live GitHub issue, PR, branch and repository instructions take precedence over this snapshot.

## 1. Direction and exclusive responsibility

- Product: **WexumVPN Desktop**, intended as a standalone desktop client for Windows, macOS and Linux.
- Exclusive owned path: `apps/vpn/desktop/`.
- Scope: unprivileged desktop UI, native-client integration boundary, connection lifecycle presentation, platform adapters, desktop-local tests and build documentation.
- Out of scope without integrator-approved coordination: shared API/contracts, identity, entitlements, nodes, billing, security-team docs, root CI, sibling mobile apps and privileged-server components.
- **Ownership conflict noted:** issue #7 contains two claims from separate sessions. The earlier claim specified C++20/Qt6; a subsequent Electron claim was withdrawn and **did not publish code**. The live branch and PR #70 use C++20/Qt6. Do not replace that work with the competing local prototype. Integrator/CTO arbitrates ownership and architecture decisions.

## 2. Architecture and technical decisions (proposed, not production-approved)

- C++20 standard-library core: deterministic `ConnectionMachine` and locale selection, compilable/testable without Qt or a network.
- CMake >= 3.20 with CTest; optional Qt >= 6.5 Widgets presentation layer (build flag `WEXUM_DESKTOP_BUILD_UI=ON`, default OFF).
- UI is **unprivileged**, non-connecting and explicitly displays a disconnected state; connect/disconnect controls are disabled. The shell must never infer protection from optimistic UI state.
- A future OS-managed, signed privileged component must own actual VPN tunneling, route/DNS configuration and cleanup. The IPC transport, peer authentication, helpers, native OS integrations and tunnel protocol are **not implemented or approved**.
- `TrustedPolicy` and `VerifiedEngineEvent` data types are **not evidence of authenticated origin**; future adapters must verify OS peer identity, message schema, authorization, attempt IDs, generation and monotonic sequence before passing events to the state model.
- UI language: ordered OS preferences on first launch; explicit System default / English / Russian override. Qt `QSettings` stores locale preference only. Do not persist credentials, grants or tunnel keys there.
- Qt licensing/packaging, dynamic-link compliance, accessibility, platform UX and adoption of shared i18n (PR #50) require review. No invented VPN protocol, custom crypto, elevated shell command or paid service.

## 3. Live GitHub work items

- Issue: [#7 — VPN client-desktop](https://github.com/Dimash313/Wexum/issues/7).
- Working branch: [`feat/vpn/7-client-desktop`](https://github.com/Dimash313/Wexum/tree/feat/vpn/7-client-desktop).
- Draft PR: [#70 — isolated Qt shell and connection state core](https://github.com/Dimash313/Wexum/pull/70), base `main`, **open, not merged** as inspected on 2026-11-21.
- Foundation dependency: [PR #1](https://github.com/Dimash313/Wexum/pull/1), still open/unmerged at inspection.
- Shared localization dependency: [PR #50](https://github.com/Dimash313/Wexum/pull/50), draft.
- The app has **no release**; do not assign a product release number.

## 4. Implemented components in PR #70

- `CMakeLists.txt`: strict C++20 core build, test target, opt-in Qt Widgets UI.
- `include/wexum/desktop/connection.hpp` and `src/connection.cpp`: state machine with disconnected/connecting/protected/interrupted/disconnecting/error, stale-event and attempt/sequence rejection, explicit disconnect confirmation and failure handling. It has no real VPN engine.
- `include/wexum/desktop/locale.hpp` and `src/locale.cpp`: local published-language selection behavior.
- `src/main.cpp`: minimalist monochrome Qt UI with connection action disabled until a verified native backend exists.
- `tests/test_main.cpp` and `scripts/test.sh`: dependency-light C++ core tests and scoped runner.
- `README.md` and `docs/SECURITY.md`: architecture, limitations, platform verification gates, threat model, recovery and licensing considerations.

## 5. Test evidence and platform status

**Reported by the author of Draft PR #70, not independently rerun in this handoff update:**

- `cd apps/vpn/desktop && bash scripts/test.sh` — reported **PASS** on Linux using GCC 14.2.0. One CTest executable with **71 assertions**.
- `cmake -S . -B build-clang -DCMAKE_CXX_COMPILER=clang++ -DBUILD_TESTING=ON -DWEXUM_DESKTOP_BUILD_UI=OFF && cmake --build build-clang --parallel 2 && ctest --test-dir build-clang --output-on-failure` — reported **PASS** on Linux Clang.
- These are local test claims in the PR; **not** GitHub Actions runs, not GUI or VPN validation. No tests executed specifically for this documentation update.
- Windows: no native build, GUI run, privileged service or VPN tests verified.
- macOS: no native build, GUI run, privileged service or VPN tests verified.
- Linux: C++ non-GUI core reportedly tested; Qt GUI not built (Qt missing on test host); no privileged service, VPN, DNS/IP leak or installer tests verified.

## 6. Known blockers and risks

1. Foundation PR #1 not integrated; shared cross-team contracts must not be assumed stable.
2. Native privileged VPN component, OS IPC peer authentication and narrow privilege grants not implemented. Do not enable `Connect` until an independently reviewed verified backend exists.
3. Actual entitlement validation, device identity, binding, signed grants, clock skew, expiry, revocation and server API handling remain unresolved cross-team dependencies.
4. No secure storage adapter (Windows Credential Manager, macOS Keychain or Linux Secret Service); no credentials are stored in this scaffold.
5. Platform-specific tunnel, DNS/routes, kill-switch, offline behavior, sleep/wake, recovery, uninstall and leak tests absent.
6. Qt license/distribution, Windows/macOS/Linux packaging, accessibility/RTL and legal/security/religious review pending.
7. No required root GitHub Actions Desktop job: shared CI is integrator-owned and must not be edited from this lane without approval.
8. Competing agent claim for the same lane was reported in issue #7; integrator should explicitly resolve ownership to avoid concurrent edits.

## 7. Next concrete actions (in priority order)

1. Before editing, reread `AGENTS.md` from the current integrated base (or PR #1 branch while not merged), issue #7, this file, branch HEAD, PR #70 diff/reviews/CI and related PRs. Verify the issue is still assigned to the same lane and no other agent is writing the same paths.
2. CTO/integrator: resolve the documented ownership collision and confirm Qt6/C++20 direction or publish an approved ADR before replacing the stack.
3. Independently run `bash apps/vpn/desktop/scripts/test.sh` on an approved Linux runner; add a scoped CI proposal to the integrator, not an unauthorized root workflow edit.
4. Set up a Qt 6.5+ build environment and validate the GUI starts, stays disconnected and has disabled connect actions; add UI tests and record exact host/toolchain results.
5. Test C++ core and Qt builds on Windows and macOS runners, document accessibility, platform behavior and packaging. Do **not** call any OS supported merely because it builds.
6. Coordinate service/API/entitlement/identity/node interfaces with their owners; produce an integrator-reviewed design for OS-specific privileged helper, authenticated IPC, secret storage and revocation. Continue to fail closed until approved.
7. With security/testing teams, construct native end-to-end tests for real tunnel state, revocation, DNS/IP leaks, network change, sleep/wake, forced crash, uninstall and restoration before any release claim.
8. Update this `HANDOFF.md` after substantive changes, tests, reviews and before ending each milestone. Include evidence rather than assumptions. Do not self-merge or mark production-ready.

## 8. Linked documents and neighboring work

- [AGENTS.md in foundation PR branch](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md)
- [VPN Architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/ARCHITECTURE.md)
- [VPN Product Requirements](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/vpn/PRODUCT_REQUIREMENTS.md)
- [Quality gates](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/engineering/QUALITY.md)
- [Religious review policy](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/policy/RELIGIOUS_REVIEW.md)
- [Desktop README](README.md) and [Desktop security gates](docs/SECURITY.md)
- Related work: [VPN security #11](https://github.com/Dimash313/Wexum/issues/11), [VPN testing #10](https://github.com/Dimash313/Wexum/issues/10), [UX specification #39](https://github.com/Dimash313/Wexum/issues/39), [shared localization #50](https://github.com/Dimash313/Wexum/pull/50).

**Handoff rule:** treat GitHub as the live source of truth, keep all changes within `apps/vpn/desktop/`, record only observed test results, and ask the integrator to resolve conflicts involving shared interfaces, release policy, infrastructure, or another agent's branch.
