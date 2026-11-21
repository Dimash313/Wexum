# WexumVPN — safety-first state and copy matrix

**Proposed product UX text for independent security, i18n and native review; NOT published translations or a live VPN UI.** Source IDs and primary-action identifiers are defined in [connection_states.json](connection_states.json). The table below is **English review-source wording**, not an approved locale catalog; localization belongs to #44/#46. Do not duplicate these messages into production or enable prototype controls without owner approval.

## State-to-copy / action contract

Each row specifies the proposed visible title and supporting text, the *source of authority* the adapter must check before displaying it, how a valid action should behave, and which accessibility announcement to send on a state **change** (not on every render).

| State ID | Proposed visible title | Meaning / safe detail | Authority / primary-action contract | SR announcement |
| --- | --- | --- | --- | --- |
| `prototype_unavailable` | VPN not available | This build has no operational VPN engine. Your traffic is **not claimed** to be protected. | Application capability metadata, checked locally; **no action**, Connect disabled with explanation | Polite on entry |
| `signed_out` | Sign in required | Sign in to check whether VPN access is available; signing in alone won't connect. | Trusted identity session; `sign_in` only if reviewed sign-in flow exists | Polite |
| `permission_required` | VPN permission needed | Your operating system will ask before this app can manage a VPN configuration. Permission is not connection. | Fresh OS permission check; `request_permission` only after explicit tap | Polite |
| `permission_denied` | Permission not granted | The requested OS permission was not granted. No connection was made. | Native OS callback **and** fresh recheck; `open_settings` only where supported | Polite |
| `disconnected` | Not connected | There is no verified active VPN session. This does not prove that the device has no other VPN or networking configuration. | Fresh native/service session snapshot; `connect` only when real engine, valid grant and eligible node are ready | Polite |
| `connecting` | Connecting | A connection request is in progress. Traffic protection is not yet verified. | Current request generation + native and trusted service status; `cancel` only if real cancellation is supported | Polite |
| `connected_unverified` | Connection not verified | The OS reports a VPN connection, but traffic protection has not been independently verified. | Native OS status **without** sufficient authenticated engine, entitlement and route/DNS evidence; `disconnect` only through real service | Assertive: uncertain protection |
| `verified_connected` | VPN connected and verified | Required tunnel and policy checks passed for the **current** session. Not a guarantee of anonymity or future leak-free operation. | Fresh authenticated native+engine+entitlement/device+network/DNS/route evidence, same session; `disconnect` through service. **No current client may enter this state.** | Polite; no repeated success chime |
| `reconnecting` | Reconnecting | The previous connection cannot be treated as protected while service status is being re-established. | Service attempt/generation + new native observations; `disconnect` only when supported | Assertive: previous state no longer verified |
| `disconnecting` | Disconnecting | Disconnect requested. Do not assume the tunnel has stopped until the service confirms it. | Trusted service stop acknowledgement needed; **no new action** | Polite, then separate completion notice |
| `interrupted` | Connection interrupted | Connection status is not verified. Review your device VPN status if the service is unavailable. | OS path change, provider mismatch, revoked/lost IPC or stale event; `disconnect` only if an actual stop route remains | Assertive: connection changed |
| `offline` | Device offline | Network access appears unavailable. The app cannot confirm a working VPN connection. | Fresh OS network monitor; `retry` only if it triggers a new check | Polite |
| `subscription_expired` | Subscription expired | Access is reported expired by the authoritative service. Existing tunnel shutdown must be confirmed separately. | Fresh trusted entitlement result; `manage_subscription` only when a real reviewed billing destination exists | Assertive |
| `access_check_unavailable` | Access status unavailable | The service cannot verify your eligibility right now. Do not assume your plan is active or expired. | Authenticated entitlement request failure/timeout; `retry` must actually repeat verification with bounded backoff | Polite |
| `revoked` | Access revoked | This account/device has lost access. Request a trusted disconnect; never claim tunnel stopped without confirmation. | Authenticated revocation/device event; `sign_in` only for genuinely recoverable session cases | Assertive |
| `no_nodes` | No available locations | No eligible current server inventory was returned. A preferred country is not a usable node. | Fresh authenticated registry eligibility check; `retry` must re-fetch | Polite |
| `error` | Connection could not be completed | A connection error occurred; details can be provided safely without revealing secrets. | Actual native/service failure; `retry` only if retriable and safe, with bounded repeat policy | Polite or assertive if protection was lost |

**Avoid ambiguous claims:** “Not connected” means *the WexumVPN session is not verified active*, not a claim about all device network traffic. “VPN connected and verified” is **reserved** and depends on a trust contract the existing product does not yet implement. Even a verified state does not establish anonymity, censorship resistance, privacy perfection or absence of future leaks.

## Action enablement — critical distinction

- A state table describes a **candidate primary action**, not authorization to enable it. Runtime feature support, OS capability, current identity/grant, eligible node, request freshness and actual callback presence must all be verified.
- Render a disabled action with a visible plain-language reason when the capability is absent; do not make a disabled CTA look like a clickable button. When no meaningful action exists (`none`), show text rather than an interactive fake button.
- `disconnect` can be shown only when there is a **real** stop mechanism, not a UI-only toggle. The truthful interim state is `disconnecting`; success requires authenticated stop confirmation.
- `retry` calls the relevant genuine check, never just changes the displayed message or starts a cosmetic spinner. Prevent duplicate attempts while in flight.
- `open_settings` must use appropriate OS app settings affordances; never coach the user to weaken device protections.
- `manage_subscription` must be provider-authoritative, with prices and renewal terms presented only from reviewed source data.
- For simultaneous events, prioritize revoke/expiry/engine-channel loss/network interruption over stale success snapshots; ensure stale callbacks from old attempts cannot reassert a verified status.

## Accessibility event rules

- Announce **state changes**, not redraws, pointer hover or animation loops. Use short, meaningful messages plus optional accessible description for what users can do next.
- **Assertive** announcement is appropriate on a *new* loss of verifiable protection, revocation or other immediately relevant status; do not repeatedly interrupt users while a network flap is occurring. Use platform-appropriate accessibility live-region/announcement APIs.
- Do not move keyboard/VoiceOver focus as a result of ordinary asynchronous status updates. After a true modal closes, restore focus to the invoking control if it still exists.
- The connection label must be selectable/readable in every supported text size, visible in both themes and not distinguishable solely by icon color/animation.
- Avoid sound-only alerts or music. Haptic feedback, if any, is an optional platform decision and cannot replace textual disclosure.
- Wording in screen-reader labels, push notifications and lock-screen widgets must follow **the same trust gate** as visible UI.

## Content gaps / pending owners

- No approved translations or final translator glossary exist; **do not market** any of the 102 proposed global locales as available based on this document.
- Exact accessibility phrasing in English/Russian/Kazakh/Arabic and RTL punctuation/isolates need #44/#46 and device/natural-language review.
- No live integration for sign-in, actual connection, server location, entitlement or payment is present here. Owners must review capability gates and state names before implementing.
- The proposed `verified_connected` evidence is not a cryptographic protocol and must be reviewed by Security #11 and native teams before any operational mapping.

## Repeatable documentation acceptance

1. Every ID from `connection_states.json` appears **exactly once** in the matrix and has a visible title, detail, authority and screen-reader policy.
2. No nonverified state uses “Protected” as its title; even the reserved verified state is conditioned on current authenticated evidence.
3. `permission_required`, `permission_denied` and `connected_unverified` never imply working tunnel or traffic verification.
4. Each action follows a genuine platform/service callback; an unavailable feature stays disabled.
5. Revocation, network loss, channel loss, expiration and restart remove earlier verified claims, with asynchronous replay guarded.
6. Native screen-reader and RTL checks must be executed and independently recorded before this copy can be approved.

**Not executed as device tests.** This is an engineering handoff specification, not user-tested wording.
