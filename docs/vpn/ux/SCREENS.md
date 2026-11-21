# WexumVPN — screen specifications and flows

**Proposal for review; illustrative layouts are NOT a running VPN UI.** No example shows real speed, node availability, subscription, IP or protection. Only authoritative service data may populate live fields.

## S01 — Connection / home

**Purpose:** answer three questions within one glance: “Am I connected?”, “What can I do now?”, “Why can't I connect?”

Phone layout proposal (monochrome, logical start-to-end order; not a screenshot):

```text
WEXUMVPN                                    Help

Connection status
VPN unavailable
Engine is not integrated in this build.

[ Connect — unavailable ]

Location
No verified server data available
[ View locations ]

Account                          Settings
```

- The primary control is **disabled** and explains why whenever the runtime feature gate is absent. Do not provide a fake transition on tap or animate a success.
- Future operational states use one prominent status **text** line with descriptive secondary message. A monochrome icon may reinforce it, never replace the text.
- When `connecting`, show “Connecting” only while an actual request is in flight. Cancellation is a real service action, not an immediate UI-only disconnect.
- `connected_unverified`: “Connection status not verified”, not “Protected”; offer a safe disconnect action when there is a real service to stop.
- `verified_connected` is **reserved**. Only current-session authenticated engine evidence + native tunnel state + device/entitlement/network evidence described by `connection_states.json` may enter it. No existing WexumVPN scaffold has that producer.
- `interrupted`, `reconnecting`, `access_check_unavailable`, `offline` and `revoked` immediately cease showing verified appearance, irrespective of the last successful connection.
- Show last selected region only if it was genuinely persisted. Do not render an invented recommended location or latency.

**Dynamic announcements:** screen readers receive a polite status announcement on a real state transition; permission denial, revocation and loss of verifiable protection use an assertive announcement without repeatedly re-announcing on redraw. Do not steal focus when a delayed event arrives.

## S02 — Locations / server selection

```text
Locations                             Close
Search [                         ]

Available locations
No live server inventory is available.
[ Retry ]      [ Why this happens ]
```

- The no-data screen is the **default** until the node-registry contract and authenticated API are connected. Never render placeholder countries as selectable real servers.
- Once operational: location/region text from the authoritative registry; eligibility and freshness checked at selection time; show latency only if a measurement actually exists, with timestamp and methodology; otherwise hide the metric.
- A disabled location gives a plain-language reason if safe to disclose (“Unavailable”; “Subscription doesn't include this location”), not private node details.
- Selecting a location records preference **only**. It does not claim a tunnel was switched. If an active tunnel exists, provide an explicit switch/reconnect consequence and rollback behavior agreed with each client owner.
- Empty search: “No matching locations”; fetch failure: “Locations unavailable”; no eligible node: “No location available for this account”. These outcomes must not share a deceptive spinner.

## S03 — Account & subscription

```text
Account
Sign in to see your subscription.

[ Sign in ]

Subscription
Not available — sign in and verify your account.
[ Manage subscription — unavailable ]
```

- Never invent subscription tiers, prices, active plan, remaining minutes, discount, next charge, expiry or payment success.
- Signed out: sign-in primary; no account identifier shown. Pending authentication: non-success loading.
- Signed in, entitlement not verified: explicit “Unable to verify access”; VPN start stays disabled on an unverified new grant. Explain offline uncertainty without displaying an expired plan as active.
- Expired/revoked: factual state from authoritative backend, prompt to check or manage; never auto-open a payment page without user intent.
- Payment confirmation, refunds, restore purchases and provider-specific management require Billing #9 and Entitlements #3 contracts. The app must not infer purchase success from a client-side callback.
- Mask account identifiers where practical; never show bearer tokens or debug payloads.

## S04 — Permission and onboarding

1. Explain in clear language why OS-level VPN configuration/permission is required; disclose actual metadata collection from approved privacy policy.
2. Offer explicit **Continue** and **Not now**. Do not call platform permission APIs in response to passive screen presentation.
3. The OS displays its own trusted consent UI. A dismissal or denial never counts as acceptance.
4. Returning to the app, refresh actual OS status. Permission granted means **permission ready**, NOT VPN connected.
5. If no real provider/engine is integrated, leave Connect unavailable even when OS permission exists.

**Error behavior:** refusal → `permission_denied`, with non-punitive explanation and the platform-supported route to settings where available. Do not instruct users to disable device security features.

## S05 — Interruptions, errors and diagnostics

| Situation | Headline | Next user action | Forbidden representation |
| --- | --- | --- | --- |
| Network lost | Connection interrupted | Show last *known* state as historical; wait for fresh path/evidence or disconnect | Keep “Protected” badge |
| VPN service inaccessible | Connection cannot be verified | Safely check current native state / stop when available | Assume connected from cached UI |
| Access service timeout | Unable to verify access | Retry after connectivity returns; explain new connections are blocked | Invent a valid subscription |
| Grant revoked | Access ended | Sign in / resolve access through account flow; ensure disconnect attempt | Keep active subscription indicator |
| No eligible nodes | No locations available | Retry inventory later, no fake fallback | Show an imaginary country |
| Provider error | Connection failed | Retry when safe; offer privacy-safe diagnostics | Raw stack trace, token, node key |
| Recovery after process restart | Not connected / verification required | Fresh trusted status collection | Restore last saved protected state |

Diagnostic disclosure: user-triggered only, explicit list of fields, opt-in sharing, redaction of secrets and routing destinations. No collection of browsing history, DNS queries or per-site traffic in UX analytics. Actual retention must be specified by observability/privacy owners before sending data. Support references may be shown only when actually generated and safe.

## S06 — Settings & help

Settings groups: **Language** (System default + independently published locales), **Appearance** (system/light/dark through approved tokens), **Privacy & permissions**, **Help & diagnostics**. Feature toggles such as auto-connect, kill switch or split tunneling must NOT appear active unless the underlying platform capability is implemented, verified and reviewed. Avoid adding nonfunctional controls to screenshots.

Locale selection follows #44/#46: BCP 47, `en-US`, `ru-RU`, `kk-KZ`, `ar-SA` are **candidate** locale IDs, not proof of translated/published product support. Default OS language detection must not be confused with country, server region or billing currency.

## Cross-screen behavior rules

| UX contract | Requirement |
| --- | --- |
| Truth source | Native OS + authenticated service/engine + current entitlement; UI cannot author connection facts |
| Rendering | Loading and pending states do not display success; if input provenance is unknown, downgrade safely |
| Async/replay | Ignore stale request IDs, old service generations and out-of-order status events |
| Accessibility | Semantic labels, visible focus, actionable text, no color-only status; text reflows at 200% scale without losing actions |
| Controls | Target ≥48 logical units where platform allows; no icon-only security-critical actions |
| Reduced motion | No status pulse that suggests a tunnel; respect OS reduced-motion and avoid flashing |
| Privacy | No private IP/user ID/destination or payment details in demo data, notifications or screenshots |
| Error | Plain-language reason and recovery, only known support IDs, no internal exception leakage |
| Data | Last selected region may be cached as a **preference**; protected connection state may not be persisted as fact |
| Keyboard | Tab/Shift+Tab, Enter/Space, Esc, predictable focus order; dialogs trap focus only while truly modal |
| RTL | Mirror layout/navigation order via logical properties; do not reverse numbers, IP addresses or semantically directional icons indiscriminately |

## Acceptance scenarios for platform teams

- **A01:** Install with no engine: Home shows “unavailable”; no tap can yield connected/protected.
- **A02:** Accept VPN OS permission: status remains disconnected/unavailable; no protection claim.
- **A03:** Receive OS-connected only: show `connected_unverified`, never `verified_connected`.
- **A04:** Receive genuinely fresh, authenticated combined evidence: only then may the future verified state be displayed.
- **A05:** Revoke grant, lose service channel, lose network or expire entitlement while verified: immediate downgrade; no stale verification after restart.
- **A06:** Restore network: request a new authoritative snapshot; never automatically resurrect prior verified badge.
- **A07:** Registry unreachable, empty or stale: location list has factual empty/unavailable state and no fabricated latency.
- **A08:** Billing callback without server verification: pending/unknown, not paid.
- **A09:** Screen reader and 200% text: complete flow works with no clipped status or unlabeled action.
- **A10:** RTL and pseudo-localized layout: content remains readable; errors, labels and security announcements use reviewed strings.
- **A11:** Keyboard-only desktop: full navigation with focus indication and no implicit VPN actions.
- **A12:** Client returns from background/restarts: retrieve current authoritative state; cache is not protection evidence.

**Device-testing gate:** A01–A12 are acceptance requirements, **not yet executed results**. Real Android/iPhone/Windows/macOS/Linux runs, color-contrast review, screen readers, and user task observations remain mandatory before approval.
