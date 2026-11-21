# WexumVPN iOS — candidate shell (issue #6)

**Not a functioning VPN.** This isolated iOS target reads system status but neither creates a VPN configuration nor initiates a tunnel. A system-reported `connected` state displays **protection not verified**. It cannot be used as a security or anonymity guarantee.

## Project
- Open `WexumVPN.xcodeproj` with Xcode 16+ on macOS; set a valid Apple Developer signing team and Network Extensions capability. Intended deployment target: iOS 16+.
- `WexumVPNApp/`: SwiftUI status view, OS NetworkExtension configuration/status observer, path monitoring, localized strings (en/ru/kk/ar).
- `Sources/WexumVPNCore/`: dependency-free, testable fail-closed UI reducer and observation-epoch gate. Stale configuration results/status after refresh or network changes are rejected. The app target references this source directly; Swift package allows non-macOS tests.
- `Tests/WexumVPNCoreTests/`: 16 pure Swift XCTest state, stale-callback and failure tests.

## Verified locally
2026-11-21, Swift 6.2.1 / Linux: `swift test` — **16/16 pass**; `swiftc -frontend -parse WexumVPNApp/*.swift`, `bash -n ci/ios-check.sh` and `plutil -lint` on Xcode project/entitlements — passed syntax checks. `bash ci/ios-check.sh` executes tests and then correctly **exits 78 (BLOCKED)** without Xcode. **No Xcode, Apple signing, iOS Simulator or device test executed.** The Xcode project and Apple framework bindings require macOS compilation. `ci/macos-workflow.proposal.yml` is an inert proposal for the integrator, not an active GitHub Actions workflow.

## Deliberate unavailable features
Connect/disconnect actions, packet tunnel extension, device enrollment, identity, grants, node selection, subscriptions, server calls, secrets and credential storage **are not implemented**. Never add fake nodes, sample production credentials, or an unverified "protected" UI. Network Extensions entitlement in source does not mean the installed app is signed with this capability.

Before implementing start/stop, integrator must approve native provider and API contracts, then verify real authenticated entitlement/device scope and expiry; choose a maintained protocol engine; independently test packet, DNS, IPv4/IPv6, background, Wi-Fi/cellular switch, reconnection, revocation, and cross-account failures. Apple's organization/store eligibility, VPN privacy disclosure and country-specific legal compliance also gate release. See `Docs/APPLE_GATES.md`.

Language defaults to iOS per-app/device preferences. Manual persisted language overrides and approved shared i18n adapter depend on PR #50; no language is inferred from IP, VPN exit node, billing or device location. UI strings require native-speaker review and VoiceOver/RTL device tests.

## Stacking and ownership
This branch is stacked on unmerged foundation PR #1; only `apps/vpn/ios/` is modified. Rebase onto the integrated foundation after approved merge. Do not merge this draft independently.
