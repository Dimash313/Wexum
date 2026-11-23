# WEXUM Brand & Motion — HANDOFF

**Direction:** corporate identity and proposed cross-product motion semantics; documentation only.  
**Scope:** `docs/brand/`; do not change `docs/design/`, `docs/vpn/ux/` or native product code without the relevant owner and CTO review.  
**Work item:** existing [Draft PR #90](https://github.com/Dimash313/Wexum/pull/90), branch `docs/wexum-brand-reference-20261123`, base `main` (foundation PR #1 not yet integrated). Read the live PR head SHA before continuing; do not treat SHA printed in earlier reports as current.

## Sources and decisions

- The founder supplied the visual mark. The four traced SVGs in `assets/` provide full/symbol, black/white variants. Treat traced geometry as the chosen **brand reference**, not an original designer-authored vector master. Do not redraw or silently change paths.
- `WEXUM_BRAND_GUIDELINES.md`: brand asset constraints, typography proposals and corporate layout examples.
- `motion/WEXUM_MOTION_SYSTEM.md`: five proposed motion primitives (`W-Trace`, `Precision Shift`, `Lock Pulse`, `Panel Reveal`, `Ambient Edge`), state-safe animation rules and adaptive viewport conditions.
- Shared Experience [Issue #40 / Draft PR #42](https://github.com/Dimash313/Wexum/pull/42) owns **proposed** semantic product UI tokens; it currently differs from brand examples for font, neutral colors, spacing and motion timing. **Neither proposal is an automatically approved native API.** CTO must approve a single mapping before production adapters.
- VPN UX [Issue #39 / Draft PR #75](https://github.com/Dimash313/Wexum/pull/75) owns VPN-specific states, foldable/tablet acceptance and native handoff. Android #5, iOS #6 and Desktop #7 own their source.

## Review findings addressed in this branch

- Scoped illustrative corporate CSS vs shared product UI semantic tokens; clarified owner approval and no hidden parallel design-system dependency.
- Namespaced proposed brand motion tokens; documented the divergent values in #42 and required a reviewed mapping.
- Added immediate verified-state copy, cancellation of stale confirmation effects upon revocation/interruption, reduced-motion changes during animation, foldable/tablet/multiwindow behaviors and acceptance conditions.
- Original four logo paths/colors and layout geometry are unchanged.

## Evidence and outstanding verification

- Directly inspected all four GitHub SVG source blobs at the prior PR head. Textual checks confirmed black/white pairs contain identical path geometry (8 paths full, 3 paths symbol), expected monochrome fill colors, viewBox/size, image role and absence of external image/script references. **This is not an SVG-rendering or small-size visual test.**
- **NOT RUN:** font licensing verification; in-app CSS implementation; PNG exports; actual 24/32px optical comparisons; browser/native logo rasterisation; native animations, accessibility, foldable/tablet/RTL device tests; product CI, VPN/engine or security tests. Do not claim success based on these docs.
- **BLOCKED/NEEDS REVIEW:** brand-to-#42 token decision, CTO/UX cross-lane approval, independent accessibility review, approval of native motion adapters, actual-device evidence. Foundation integration and store gates are handled separately.

## Next bounded steps

1. CTO + Experience owner #40 review conflicting timing/color/font proposals and record one explicit token mapping without editing another team's owned paths.
2. VPN UX #39 and platform client owners translate **approved** primitives into nondeceptive prototype behavior; obtain fold/unfold, tablet/multiwindow, RTL, reduced-motion and stale-status regression evidence.
3. Export necessary real PNGs from the reviewed SVG geometry, verify alpha channels, sizes, platforms, license/brand-source provenance. The four SVGs **are not** PNG downloads.
4. Re-fetch the final Draft head, inspect all changed blobs/diff, run any available automated checks, record actual results and request independent audit; merge only through CTO after required protections.

**Rollback:** close/revert Draft PR #90; no runtime product files, network behavior or releases changed by this brand documentation.
