# Wexum Experience — cross-product UX contract

Status: proposed. This policy is a handoff guide, not an implemented component library.

## Navigation and interface ownership
- Each product provides standalone routing; Hub is optional navigation and shared workspace.
- The Hub cannot claim an app is running, protected or synchronized based solely on decorative UI.
- Main actions occupy a consistent, discoverable location. Secondary/destructive actions must not resemble safe primary actions.
- Critical settings must be understandable without icon-only navigation; text labels required for security and money operations.

## Required interface states
| State | Behavior |
| --- | --- |
| initial/loading | Clear progress; no implied completion or fake data |
| success | Only after an authoritative operation result |
| empty | Say why content is empty; actionable next step |
| offline | Explain available local capabilities, clearly identify unavailable remote actions |
| degraded | Show which feature is impaired; allow unaffected features |
| authorization denied | Explain access problem without exposing another tenant's existence or private metadata |
| expired session | Protect unsaved work and prompt a safe re-authentication |
| rate limit | Explain retry policy without exposing infrastructure-sensitive details |
| destructive confirmation | Identify irreversible outcome and target; prevent accidental activation |
| security warning | Plain-language impact, trustworthy action, accessible to screen readers |
| error | No raw tracebacks, secrets or user identifiers; include a supportable reference when available |

## Accessibility and localization
- Target WCAG 2.2 AA for applicable web UI and platform-native accessibility guidance for Android/iOS/Desktop.
- Every interactive control: keyboard operation, visible focus, programmatic label and minimum 48 logical units target where feasible. Use an offset focus ring so it remains visually distinct from a filled primary button; test it in both color modes.
- Never convey success/error/connection state through color alone; combine labels and clear icons.
- Honor reduced-motion, zoom, font scaling, high-contrast preferences and OS control conventions.
- Plan RU, EN, KZ and AR. Do not hardcode text layout order; RTL flips logical layout but not universally meaningful icons or numeric content.
- Dates, numbers, money and plural forms use locale-aware presentation; do not infer the language from country alone.
- Persisted form drafts and autosave require trustworthy failure indication and no silent data loss.

## Shared component contract (proposed)
Buttons; form fields; toggles; dialogs; alert banners; status indicators; skeletons; empty states; navigation; permission prompts. Each component requires documented input, accessibility label, loading/disabled/error behavior and deterministic visual tests.

## Handoff to products
- VPN (#39) owns VPN-specific connection-state language; Android/iOS/Desktop engineers implement the native system APIs and state indicators.
- Product applications map the shared semantic tokens to their platform without bypassing the app's domain permissions.
- Review designs using actual small-screen, desktop, keyboard and assistive technology scenarios; illustrations alone are not adequate evidence.

## Religious/ethical and privacy constraints
Neutral geometry and typography only as default visual assets; no music, living-being depictions or disputed generators in default design. Unresolved features follow docs/policy/RELIGIOUS_REVIEW.md. Never display sensitive files, passwords, VPN destinations or private account identifiers in mock analytics/screenshots.
