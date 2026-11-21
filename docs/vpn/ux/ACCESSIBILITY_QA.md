# WexumVPN — cross-platform accessibility, RTL and responsive acceptance plan

**Status: proposed test plan, NOT executed usability evidence.** Implementers are Android #5, iOS #6 and Desktop #7. Test-case references point to [SCREENS.md](SCREENS.md) and [STATE_COPY.md](STATE_COPY.md); shared tokens and locale publication require #40/#44 integration review.

## Required evidence format

For **each** executed case, record: `case_id`, date, platform + OS build, tested app commit SHA, language + script, assistive technology/version, viewport/window dimensions, font/zoom level, **actual observed behavior**, PASS/FAIL/BLOCKED, tester, and a sanitized proof artifact when permitted. Do not attach account identifiers, subscription receipts, DNS destinations, private IPs, physical location or other sensitive screenshots/voice recordings. Do not replace actual results with expected results.

A test is **BLOCKED**, not passed, if the underlying native VPN/identity/billing capability is unavailable. Nonoperational shells can still be tested for honest disconnected and disabled-state behavior.

## Test environments

- **Android (issue #5):** API 26+ baseline, Android 13+ per-app language, small 320dp available width (if supported), landscape, split-screen; TalkBack, hardware keyboard and increased system font/display size.
- **iOS (issue #6):** iPhone iOS 16+ with Dynamic Type including accessibility categories, VoiceOver, small screens, rotation and OS permission sheets; large iPad layout only when a supported target/build exists.
- **Desktop (issue #7):** Windows, macOS and Linux as individually supported/tested, resizable window and 200% UI zoom; keyboard-only, appropriate native screen readers (e.g. NVDA, VoiceOver, Orca), high contrast where supported.
- **Locales (not guaranteed published):** test the **available reviewed** en-US/ru-RU/kk-KZ/ar-SA catalog sets; use pseudo-expanded and pseudo-RTL *test-only* fixtures from i18n owners for layouts before publication. An untranslated locale is BLOCKED, never silently certified.
- **Visual configurations:** light/dark/system mode, reduced motion, focus ring, high contrast, dynamic theme updates; use approved Experience PR #42 tokens only after adoption. No new VPN-specific colors in this lane.

## Scenario acceptance matrix

| Case | Screen / fault input | Device-specific action | PASS criteria | Current status |
| --- | --- | --- | --- | --- |
| UX-A11Y-001 | Home with no engine | Launch fresh install and read screen with AT | First status is unambiguously unavailable; no enabled Connect; no implied protection | NOT RUN |
| UX-A11Y-002 | OS VPN consent | Trigger consent only on explicit user action; decline then grant when native shell supports it | UI never equates permission with connection; native OS dialog remains recognizable | NOT RUN |
| UX-A11Y-003 | Home async transitions | Inject deterministic state changes from owning test adapter; read with AT | Exactly meaningful state change announced, no runaway repetitions, no focus hijacking | NOT RUN |
| UX-A11Y-004 | Verification loss | From approved test harness only, simulate revoked entitlement/lost provider/offline after verified state | Status immediately loses verified claim; alert is announced; never reload cached protection | BLOCKED: verified engine unavailable |
| UX-A11Y-005 | Busy connecting/disconnecting | Trigger real request once, then rapid double tap and interruption | Action disabled while pending; cancellation only when implemented; no premature success/stop | BLOCKED: functional engine unavailable |
| UX-A11Y-006 | Server inventory empty/unreachable | Inject empty/expired/error server responses | Appropriate empty/error copy; no fabricated nodes, countries or latency; retry has real handler | BLOCKED: live registry adapter unavailable |
| UX-A11Y-007 | Account & subscription | Signed out, unknown, expired, revoked and unavailable entitlement | No invented price, plan, date, or payment success; keyboard and AT labels accurate | BLOCKED: authoritative billing adapter unavailable |
| UX-A11Y-008 | Compact phone / landscape | Fit actual screens to 320dp available width and rotate | No clipped text/primary action, no horizontal scroll for essential flow, safe-area compliant | NOT RUN |
| UX-A11Y-009 | Dynamic type / zoom | Increase iOS/Android text to 200% equivalent and desktop app zoom to 200% | Status, reason and recovery remain readable and reachable without overflow | NOT RUN |
| UX-A11Y-010 | TalkBack / VoiceOver / desktop reader | Navigate entire enabled UI including dialogs | Role/name/state of controls and current VPN status announced in correct order | NOT RUN |
| UX-A11Y-011 | Keyboard and switches | Tab/Shift+Tab, Enter/Space, Esc; focus through modal & return | Full enabled flow reachable; visible focus in dark/light; no unintended activation | NOT RUN |
| UX-A11Y-012 | RTL text and mixed-direction content | Arabic layout; use neutral fixture hostname/IP/email if reviewed safe | Natural reading order; bidi isolation for LTR tokens; no reversed IP digits or incorrect navigation | NOT RUN |
| UX-A11Y-013 | Kazakh/Russian expansion | Reviewed strings, 50% pseudo-expansion, large fonts | Labels wrap/reflow, buttons and status retain meaning; no overlapping text | NOT RUN |
| UX-A11Y-014 | Reduced motion | Enable OS reduce-motion and trigger pending/status transitions | No looping fake tunnel pulse, no essential state conveyed by motion alone | NOT RUN |
| UX-A11Y-015 | Contrast & monochrome | Review actual snapshots in both themes and high-contrast setting | WCAG 2.2 AA targets where applicable: text ≥4.5:1 (large ≥3:1), essential nontext/focus ≥3:1; status also textual | NOT RUN |
| UX-A11Y-016 | Recover from restart/resume | Background/terminate/restore while OS state changes | Fresh native and trusted source used; no stale verified text, focus/state remain comprehensible | NOT RUN |
| UX-A11Y-017 | Privacy/error copy | Inject safe error and open diagnostics disclosure | No secrets, identifiers, traffic destinations or tracebacks; opt-in before sharing data | NOT RUN |
| UX-A11Y-018 | Notifications / widgets | Trigger only when a separately approved feature exists | Same trusted status gate as app; no lock-screen PII/false protection | BLOCKED: feature not implemented |

The default NOT RUN/BLOCKED statuses are **the specification's starting inventory**, not claims of results. The platform owners must replace them with executed evidence in their own reports; this UX document is not an autonomous CI gate.

## RTL and layout decisions requiring explicit acceptance

1. **Logical direction:** container edges, navigation rows, leading actions and separators follow logical start/end; only directional icons whose meaning changes with navigation can be mirrored. Do not flip logos, network topology meaning, numerals or physical-device directions indiscriminately.
2. **Mixed-script values:** IP addresses, hosts, domains, URLs, email and opaque identifiers use the platform-native isolation API. Do not concatenate untranslated LTR tokens into Arabic sentences manually.
3. **State priority:** visual structure does not depend on English text length; titles/details can wrap while preserving one primary decision and full accessibility semantics.
4. **Keyboard focus:** RTL visual ordering and focus order follow the actual logical navigation hierarchy. Screen-reader language applies to the spoken span rather than inferred region.
5. **Fallback:** never silently show unchecked Arabic or Kazakh security copy; locale owner must publish and verify product-specific catalogs or explicitly use an approved fallback, with truthful translation status.
6. **Pseudolocales:** test-only fixtures must not become public language picker options; the i18n owner controls their exact tags and formatting.

## Manual review workflow

1. Platform owner supplies a build identifier, tested device and fixture/test adapter source. Explicitly label prototype/unavailable states.
2. UX reviewer executes the screen flow with input device and assistive technology, records failures and reproduction **without** private data.
3. Security owner validates protection-status semantics, revocation and stale-event handling separately; experience design owner reviews token/contrast usage; i18n owner validates language and RTL.
4. Retest after correction on the **new commit SHA**. Only a documented independent review supports acceptance; the absence of complaints is not a PASS.
5. CTO/integrator controls cross-team contract changes, required CI and eventual merge. No mobile/store launch implied.

## Current limitations

No mobile screenshots, real device builds, native screen-reader checks, keyboard sessions, colorimeter evidence or independently translated security strings were collected by UX #39. Foundation and design/i18n PRs are unmerged. The VPN is not operational; engine-dependent cases remain blocked until trustworthy native adapters exist. Future tester reports may link here but must not overwrite sibling teams' evidence without permission.
