# WexumVPN — interface and UX workstream

**New agent / new chat:** start with [HANDOFF.md](HANDOFF.md), then read the current GitHub Issue #39, Draft PR #75, project AGENTS.md and the files linked in the handoff. On «Продолжаем дальше», inspect current GitHub and autonomously continue the highest-priority unblocked work inside `docs/vpn/ux/`; update HANDOFF.md after meaningful changes. Do not edit other teams' documentation or merge without CTO/integrator approval.

**Status: proposed specification, not an operational VPN or an approved design.** Owner: [issue #39](https://github.com/Dimash313/Wexum/issues/39). This directory owns product-facing UX flows, safe state copy, acceptance cases and native handoff only. No shared UI package or native app implementation is authorized here.

## Sources and precedence

1. [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1), `AGENTS.md`, `docs/vpn/ARCHITECTURE.md`, `docs/engineering/QUALITY.md` (the foundation is **unmerged and audit-blocked**).
2. [Wexum Experience PR #42](https://github.com/Dimash313/Wexum/pull/42) owns **proposed** cross-product semantic tokens and accessible components. Do not create divergent VPN colors, type scales, or a duplicate design system.
3. [i18n PR #45](https://github.com/Dimash313/Wexum/pull/45) and [adapter PR #50](https://github.com/Dimash313/Wexum/pull/50) own locale registry, fallback and language selection. `kk-KZ` is Kazakh, `ar-SA` is Arabic; neither is automatically published.
4. Native implementations and engine truth belong to [Android #66](https://github.com/Dimash313/Wexum/pull/66), [iOS #69](https://github.com/Dimash313/Wexum/pull/69) and [Desktop #70](https://github.com/Dimash313/Wexum/pull/70). Their current shells **do not establish a usable VPN tunnel**. UX must not upgrade their permission/configuration status to protection.
5. Legal, privacy and religious review: `docs/policy/RELIGIOUS_REVIEW.md`; no music or depictions of living beings.

The integration owner/CTO must approve changes to shared packages, localization catalogs and API contracts first.

## User jobs — research hypotheses, not verified personas

| Hypothesis / context | Job to accomplish | Success observation |
| --- | --- | --- |
| New mobile user | Understand what VPN does, the data disclosure, OS permission and whether it is *actually* connected | Can correctly distinguish **permission granted** from **connection established** |
| Returning mobile user | See trusted live status and reconnect or stop with a single discoverable action | Can correctly interpret interruption and current connectivity |
| Multi-region traveler | Select an actual eligible reachable region without assuming availability | No fabricated node, time, latency or country; inaccessible choices are explained |
| Desktop keyboard / assistive tech user | Operate full flow via keyboard and screen reader | Focus, labels and dynamic announcements function without color-only cues |
| Paying user | Understand entitlement availability, expiry, renew/cancel flows and charges | No fictional price, active plan or restored access while verification is unavailable |

These are **untested** assumptions. Validate with consenting participants before calling them evidence-based personas. Never use identifying customer data in research fixtures.

## Information architecture

- **Connection (primary):** clear verified state, one context-appropriate primary action, previous selection only if genuinely saved; no fictional server or counter.
- **Locations:** list real returned eligible nodes with freshness/unavailability information; default empty state if registry is not integrated.
- **Account & subscription:** authoritative signed-in and entitlement state, no placeholder plan/price/renewal date. Provider-managed billing journeys require separate approval.
- **Settings:** language via approved i18n adapter, appearance via approved Experience design tokens, privacy and diagnostics disclosure.
- **Help:** explain permissions, interruptions, privacy limitations and support; never dump raw errors/secrets.

Read [SCREENS.md](SCREENS.md), [STATE_COPY.md](STATE_COPY.md), [ACCESSIBILITY_QA.md](ACCESSIBILITY_QA.md), [NATIVE_HANDOFF.md](NATIVE_HANDOFF.md) and the [machine-readable state contract](connection_states.json). The state contract is a UX **proposal**, not an executable VPN engine or API schema.

## Core safety rules

- The app **never** shows “Protected”/“Защищено” for permission acceptance, animation completion, mere OS-connected status, unverified provider callback, cached session, timer or server metadata.
- A future verified connected state is conditional on *fresh*, trusted OS tunnel evidence **and** independently authenticated engine evidence **and** valid grant/device/policy. The guard is described for future integration; it has **no producer today**.
- If any trusted input expires or disappears, remove verified claims immediately; on network restoration, request fresh evidence rather than revive a previous protected appearance.
- No bandwidth, latency, encryption, uptime, IP address, user count, renewal deadline or billable price is invented. Missing observability yields “Not available”, never `0 ms` or `100%`.
- Do not promise anonymity, no leaks, or no logs without measured and reviewed evidence. Avoid recommending risky device changes in recovery copy.
- Privacy disclosures must explain actual collected data and retention from their service owners, not inferred marketing text. Screen text, accessibility labels and errors are localized together.
- No person/animal illustrations, music or autoplay sounds. Motion follows system reduced-motion preferences; animations are never connection evidence.

## Verification

Optional stdlib contract checks, scoped to this directory:

```sh
python docs/vpn/ux/validate_contract.py
python -m unittest discover -s docs/vpn/ux -p 'test_*.py' -v
```

Passing these checks validates the **proposed document contract**, not native UI usability, tunnel security, i18n correctness, any store review or release readiness. Physical-device, assistive-technology, real-node and DNS/IP leak checks remain open.
