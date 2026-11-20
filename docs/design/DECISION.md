# Wexum Experience — proposed design system decision

Status: **PROPOSED, NOT APPROVED**. Owner: Wexum Experience, issue #40. Depends on foundation PR #1; downstream products must not assume this is integrated.

## Scope and visual identity

Create one coherent semantic design language for 22 standalone apps and Wexum Hub. Premium neutral grayscale, excellent legibility, minimal decoration, no decorative pictures of living beings and no musical assets. Product workflows may differ: we unify principles and semantic patterns, not every screen layout.

## Contract proposal

- One canonical, machine-readable token file: `docs/design/tokens.json`.
- Roles express intent (`background`, `textPrimary`, `action`, `danger`) rather than a specific UI framework.
- Separate light and dark themes must share identical role names. Text contrast >= 4.5:1; essential visible UI and focus >= 3:1 against immediate surfaces.
- Spaces/radii/type are ordered logical units. Web may render logical pixels; native uses reviewed mappings to density-independent units (dp/pt). Users can enlarge typography; avoid absolute fixed-height text containers.
- Localized text uses system font fallbacks with Arabic layout/ligature checks. Do not distribute proprietary font files.
- No dependency on a particular mobile/web framework in the tokens. Platform adapters are later, separately tested code.

## Alternatives rejected

1. Hard-coded CSS and styles in each app: inconsistent, hard to audit, makes future changes risky.
2. A single WebView as every native interface: poor system integration, accessibility and performance risks (especially WexumVPN).
3. Immediate adoption of a large proprietary design system dependency: license and maintenance exposure before requirements are proven.

## Acceptance and migration

- `python docs/design/validate_tokens.py` must pass.
- `python -m unittest discover -s docs/design -p 'test_*.py' -v` must pass.
- Human reviewers inspect device screenshots, accessibility behavior, truncation, RTL and native control states.
- Before publication, integrator approves the contract, ensures CI covers these tests and documents migration policy.
- Token additions are preferably additive; semantic renaming requires planned adapter migration. Never silently change an established semantic role.

## Known limitations

Contrast automation does not prove WCAG conformance, accessible screen flow, icon usability or correct native adaptation. This PR does not implement a user-facing application.
