# WexumVPN — native implementation handoff and review gate

**Status: proposed; not an API contract, shared package or release approval.** Issue [#39](https://github.com/Dimash313/Wexum/issues/39) owns UX semantics; client teams own native implementation and engine interactions.

## State provenance and precedence

UX renderers should be **read-only consumers** of authoritative, fresh snapshots. A button press means only “request sent”; it is never evidence that a tunnel has started or stopped. State-machine details and protocol fields are for the owning native/security/entitlement teams to define with CTO review.

Priority when multiple events disagree (highest first):

1. Confirmed revocation/expiry, deleted configuration or lack of authenticated service: **remove any verified claim**; attempt safe disconnect where supported.
2. Network loss, engine IPC failure, stale status or OS provider mismatch: **interrupted / status unverified**.
3. Pending connect/disconnect/reassertion: pending copy, no success state.
4. Native OS connection alone: **connected but not verified**.
5. Fresh, authenticated native+engine+entitlement+device+network evidence from the same session and generation: only then candidate `verified_connected`. Current shells **do not** implement this verification. Permission acceptance, cached event or framework status never meets this gate.

Authentication, source identity, replay protection and revocation latency require separate service-side review. A UI-side boolean never constitutes an authoritative verification port.

## Adapter mapping — current independent drafts

| Platform | Existing draft behavior | UX alignment | Ownership |
| --- | --- | --- | --- |
| [Android PR #66](https://github.com/Dimash313/Wexum/pull/66) | Permission-only `VpnService.prepare` shell with `PERMISSION_READY`; no tunnel and no reachable `PROTECTED` | Permission ready → informational `disconnected` if real engine exists, otherwise `prototype_unavailable`; never claim protection | Android #5 |
| [iOS PR #69](https://github.com/Dimash313/Wexum/pull/69) | Read-only `NETunnelProviderManager`; `connectedUnverified`, no packet provider | OS connected → `connected_unverified`; no verified state without audited engine | iOS #6 |
| [Desktop PR #70](https://github.com/Dimash313/Wexum/pull/70) | Nonoperational Qt shell; reducer enum includes `Protected` but actions disabled, no authenticated privileged helper | Reserve protected-like semantics pending reviewed helper/IPC and independent trust validation; UI stays unavailable now | Desktop #7 |

Do **not** change those teams' state enums or source code from this branch; the table is a handoff for their own review. Future field naming, service IPC/API schema, connection status provider and signed-grant cache policy require CTO and domain owners' agreement. No import from `connection_states.json` into production code until a reviewed compatibility plan exists.

## Visual system: reuse, do not fork

- Use the semantic theme roles from **proposed** [PR #42](https://github.com/Dimash313/Wexum/pull/42) when approved; never copy colors or instantiate `packages/vpn-design/` without review.
- Black/white, strong hierarchy: status text as a primary visual element; one primary CTA; subdued secondary actions; generous whitespace; consistent system-native navigation. Avoid gradients, 3D power buttons, invented traffic charts or looping faux-connected animations.
- Use platform-safe typography and script shaping; approved token spacing/radii and type scales need native dp/pt translation tests. Honor system appearance, high contrast and reduced motion. Text and control contrast: WCAG 2.2 AA targets as described by Experience PR #42; contrast checker alone is not usability proof.
- Focus rings and disabled controls must remain visible in light/dark; never rely on grayscale alone for error/success meaning.

## Responsive and interaction matrix

| Device context | Proposed layout | Input / focus checks |
| --- | --- | --- |
| Small Android / iPhone | Single-column home; connection status and action before secondary locations/account; safe areas; scroll at large type | One-handed primary placement, TalkBack/VoiceOver, Android font scale / iOS Dynamic Type, OS VPN consent |
| Phone landscape / tablet | Wider single or two-column composition depending on actual available width; preserve content order | Rotation, split-screen/multiwindow, hardware keyboard, 200% text |
| Windows / macOS / Linux desktop | Status/action primary pane, optional real location list secondary pane, visible account/settings navigation | Keyboard-only, NVDA/VoiceOver/Orca as platform permits, 200% zoom, window resizing, system high contrast |
| RTL languages/scripts | Logical start/end, reversible flow and focus order; native bidi-isolated IP/address/identifier if actually present | Arabic shaping, combined LTR/RLT spans, punctuation, tab order, screen-reader language |

Breakpoints are **not** independently hard-coded here: adapt the proposed PR #42 breakpoints after approval and test 320dp-width phones plus constrained desktop windows. Do not give a fake 1:1 px/dp/pt conversion.

## Locale / security copy ownership

- Shared locale registry, negotiation, publishing gates: [issue #44 / PR #45](https://github.com/Dimash313/Wexum/pull/45). Client-side language adapter: [PR #50](https://github.com/Dimash313/Wexum/pull/50).
- This lane proposes namespaced UX message IDs `vpn.status.*` and `vpn.detail.*`; **not** a published translation catalog. i18n owner approves their final names/schema and translator workflow.
- RU/EN/Kazakh/Arabic are priority *candidates*; support must be declared per platform after complete human-reviewed catalogs and native-device tests. Project's 102 planned regional locales are not 102 shipped translations.
- Arabic RTL: localize numerals, date/units with CLDR/ICU as appropriate; bidi-isolate IPs, hostnames, email, device IDs, URLs. Do not mirror the meaning of a directional back arrow without platform-native RTL guidance.
- Have native speakers review exact security terms including “connected”, “not verified”, “revoked”, “interrupted”, “permission”, and “payment pending” before any store release; never substitute fallback that materially changes protection claims.

## Privacy, security, product and accessibility review

- **Privacy:** connection screen never shows browsing destinations, DNS query names or traffic history. Diagnostics have explicit consent, safe redaction, limited fields and owner-defined retention. No marketing “zero logs” until verified.
- **Security:** no remote grant authority in a visual component, no durable `isProtected` cache, no automatic reconnect from stale UI state. Revocation, peer authentication and routing are owned by backend/native/security teams.
- **Religious/ethical:** neutral geometry/typography only, no music and no depiction of living beings; no speculative premium billing or disputed content.
- **Accessibility:** real focus, semantic descriptions, state change announcements, screen-reader language, keyboard paths, text resizing and reduced motion. Platform owners must test native dialogs rather than substituting mock permission screens.
- **Performance/reliability:** native owners measure actual status-to-render propagation and degraded behavior on real devices; don't invent a response-time guarantee before test environment and measurement plan are agreed.
- **Safe account data:** entitlement identity, node data, prices and expiration must come from authenticated authoritative endpoints, not inferred from locale, last billing receipt or fake preview.

## Integration dependencies and sign-off

| Dependency | Needed before implementing/claiming | Owner |
| --- | --- | --- |
| Foundation PR #1 and independent audit #41 | Accepted, integrated architecture/governance | Integrator, auditor |
| Experience PR #42 | Approved semantic tokens and responsive/component API boundary | Design #40 / CTO |
| i18n PRs #45/#50 | Approved message/RTL contract and published per-product translations | i18n #44/#46 |
| VPN backend, Identity, Entitlements, Nodes | Authenticated, current connection eligibility and actual server inventory | VPN #2/#3/#4; Identity #34 |
| Native clients #66/#69/#70 | OS-specific status and audited real tunnel adapters, trust boundaries | Android/iOS/Desktop |
| Billing #9 | Real plans, purchase, renewal, refund and authoritative entitlement update | Billing |
| VPN security / testing #10/#11 | Threat model, real device tests, IP/DNS leak and revocation tests | QA/Security |
| Policy/legal/store checks | Verified disclosures and supported launch regions | Owner / independent reviewers |

**CTO decision requested:** accept `docs/vpn/ux/` as specification-only until PR #42 and i18n contract are approved. Do not create `packages/vpn-design/` now. If future native teams need shared status DTOs, require a separately reviewed ADR defining source authentication, versioning, privacy, bounded staleness, migration and rollback.

## Verification and rollback

Run `python docs/vpn/ux/validate_contract.py` and `python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v` for the *proposal*. Platform-level review must execute acceptance cases in [SCREENS.md](SCREENS.md) on physical devices and report failures with non-sensitive evidence. A final check on the integration head is mandatory; stacked draft PR results do not certify the merged code.

Documentation-only rollback: close this Draft PR or revert its changes within `docs/vpn/ux/`; no deployed user data or migrations are affected. Do not merge until blockers are resolved and independently reviewed.
