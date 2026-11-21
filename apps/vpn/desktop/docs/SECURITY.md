# Desktop threat model and platform rollout gates

## Trust boundary

The Qt UI is an **unprivileged process**. `ConnectionMachine` is a deterministic,
non-networking model, not a VPN implementation. No subprocess with elevated
privileges is started. There is **no IPC transport** or tunnel backend here.

A future, independently reviewed privileged service must own OS VPN integration,
routes, DNS changes, rollback and service lifecycle. Candidate integration uses
well-maintained, platform-accepted VPN technologies; no custom crypto or protocol.

**Never** treat `TrustedPolicy` or `VerifiedEngineEvent` names or boolean flags
as proof of authentication. A future adapter may call the core event functions
only after validating the OS peer identity and IPC channel, authorization,
monotonic event sequence, attempt identifier and failure cases. The current
Qt shell has **no adapter** and never invokes these entrypoints or enables Connect.

A privileged service must re-check server-issued device-bound grants (including
audience, expiry, revocation and clock skew), not trust UI authorization flags.
The control plane remains authoritative for registration and entitlement;
fail closed for new connections when offline. Specify bounded continuity for
already-open tunnels only after a cross-team threat review.

## Failure cases and mitigations

| Risk | Current behavior | Required before real connections |
| --- | --- | --- |
| UI forged `Connected` | Shell has no engine event source | Authenticated OS IPC, strict message schema/peer verification |
| Stale engine success | Attempt and sequence checked in reducer | Authenticated generation binding across service restarts |
| Expired or revoked grant | Reducer leaves `Protected`, suggests `Stop` | Privileged service must enforce expiry, confirm stop and verify actual interface state |
| Lost helper/channel | UI state becomes `Interrupted` | OS-managed cleanup, safe kill switch and recovery drills |
| DNS/IP leak | No tunnel is launched | Per-platform route/DNS/leak tests, network switching and sleep/wake |
| Malicious helper install | No helper installed | Signed installer/service, restricted IPC ACL, updates and uninstall cleanup |
| Credential theft | No credentials or tokens are stored | OS secrets vault (Windows Credential Manager, macOS Keychain, Linux Secret Service); no plaintext fallback |
| Logging sensitive data | Core emits no telemetry | Redacted error identifiers, no VPN destinations or credentials in logs |

## Platform gates

| OS | Core | Qt GUI | Privileged service / VPN | E2E tunnel, DNS/leak and uninstall |
| --- | --- | --- | --- | --- |
| Windows | Not yet run on Windows | Not built | Not implemented | Not tested |
| macOS | Not yet run on macOS | Not built | Not implemented | Not tested |
| Linux | C++ core unit-tested on Linux build host | Not built; Qt unavailable on build host | Not implemented | Not tested |

Do not interpret a Linux core compilation as a validated Linux VPN client.

## OS integration to design and review separately

- Windows: prefer OS-approved VPN platform services / maintained tunnel backend;
  privileged Windows service with authenticated named pipe and limited ACL;
  installer/uninstaller, wake/network interface changes and route rollback.
- macOS: network extension entitlement, signing and notarization requirements;
  supervised system extension approval, XPC peer identity and kill-switch policy.
- Linux: supported NetworkManager/systemd-managed backend as applicable;
  D-Bus policy/peer checks or restricted Unix domain sockets, polkit policy only
  when justified, per-distribution packaging and uninstall restoration.
- Privileged helper must not accept arbitrary shell commands, file paths,
  route changes or unsigned VPN configurations from the UI.
- No user-supplied endpoint/tunnel configuration until server APIs, entitlement
  grants, node registry and signed configuration schema are approved.

## Storage and localization

Qt `QSettings` stores **only** the interface language preference (system/en/ru).
No session keys, tokens or VPN secrets are persisted. English and Russian are
currently the only implemented local catalogs; other OS languages fall back to
another published preference or English, never an invented translated UI.
Desktop adapter must eventually adopt approved shared i18n contract (draft PR
#50) and validate RTL, accessibility and pluralization before publishing more.

## Licensing and governance

Qt 6 Widgets is proposed as an optional dynamic dependency. Review chosen Qt
modules' actual licensing, dynamic-linking obligations, notices, redistribution,
security updates and commercial viability before shipping. No paid Qt plan or
other paid dependency is authorized by this draft. This is not a legal opinion.
Foundation PR #1 is a dependency for shared contracts. Legal/store eligibility,
independent security and religious review remain open. No production release.
