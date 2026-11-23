# Wexum internal AI review and release-gate policy

**Owner policy decision:** 2026-11-22. Applies to **internal, pre-release development** in `Dimash313/Wexum`. Tracked under [Issue #38](https://github.com/Dimash313/Wexum/issues/38); this proposal does not become the integrated rule until reviewed and merged through its own PR chain.

## Internal PR integration: separate human GitHub approval is not mandatory

Wexum may use the existing five AI engineering centers without creating a sixth automation, a fictitious GitHub identity, or engaging a human reviewer for every internal PR. A formal GitHub `APPROVED` review by a second account is **not a universal policy prerequisite** unless the saved, live GitHub ruleset actually requires one.

Internal code must still satisfy all of the following:

1. A dedicated GitHub issue, owned paths, non-overlapping source branch, and reviewable PR. No direct pushes or force pushes to `main`.
2. Actual **required** GitHub Actions on the reviewed integrated source/merge candidate: syntax, positive/negative regression tests, relevant platform compile/lint/build, security analysis and contracts as applicable. Red, absent, skipped or stale required checks block integration. No path-filter blind spots or `continue-on-error` loopholes.
3. A recorded verdict by the **Independent Audit AI center**, distinct from the implementing AI engineering lane. The auditor must inspect the exact current source HEAD + base/target, relevant diff, user/tenant boundaries, privacy/security issues, test coverage, actual check logs and known limitations. Accepted verdict = `ACCEPTED FOR INTEGRATION`; negative states = `BLOCKED` or `CHANGES REQUIRED`, which prohibit integration. Any source change invalidates the prior verdict.
4. All blocking audit findings, review threads and cross-team contract issues must be resolved on the final code; no invented approvals or false claims of operational security.
5. CTO/integrator makes and documents the integration decision and may integrate only when **all actual repository rules** allow it. The change author must not self-approve or self-merge. AI role separation on one connected GitHub identity is a *process boundary*, not independent GitHub-account authorization.

The repository's `required_approving_review_count=0` can remain in place for internal development; it does not substitute for the above independent AI technical audit. If GitHub is configured to demand more approvals, its **live technical requirements still apply** until deliberately and safely reconfigured. Never bypass a protective rule to implement this policy.

## Higher-risk changes

Changes affecting actual VPN tunnel traffic, key material, crypto/protocol selection, identity and authorization, production entitlements/payments, sensitive user data, cross-tenant isolation, node trust, network privacy or deployment require more demanding threat review, fail-closed negative tests, independent source analysis and evidence-based acceptance. A serious unresolved risk is a blocker even if CI is green.

External specialist review is strongly recommended for critical VPN/security trust boundaries before **public production launch**, and should be considered an explicit launch risk item rather than an approval bottleneck for every internal prototype commit. A decision to proceed to public release without the recommended external review requires the founder's **specific informed authorization**, documented residual risk assessment, and satisfaction of all applicable legal, store, privacy, security and religious gates. AI-only internal review is never described as a professional security certification.

## Integration vs launch

- **Internal PR accepted for integration**: code may be reviewed/merged to `main` if all mandatory technical and live GitHub gates pass; no claim of working VPN, production readiness or regulatory compliance.
- **Public production release**: a separate founder-controlled decision after real-device/tunnel tests, measured security and privacy behavior, infrastructure/reliability testing, applicable legal/store obligations and substantive risk review. CI green does not authorize deployment.

## Procedure for CTO and Independent Audit

The five existing hourly agents coordinate through GitHub. The CTO must track exact-sha source, CI candidate equivalence, required checks, independent AI verdict, open blockers and next action on existing issues/PRs; avoid new duplicate task streams. Independent Audit may issue its conclusion through existing issues/PR comments; it cannot masquerade as a separate-account formal GitHub Review. Where the live repository ruleset cannot enforce the AI verdict automatically, CTO must verify and record that verdict before any allowed merge, and must not represent procedural checks as GitHub-enforced controls.

Historical comments or draft documents that required a distinct human reviewer for **every internal PR** are superseded by this owner decision once this governance change is accepted. Past CI failures and independent technical findings remain valid until retested/resolved. Only the latest integrated policy and live GitHub protections govern actual integration.

**Out of scope:** retroactive merge of Draft PRs, changes to the ruleset, public VPN deployment, spending money, creating additional agents/automations, or relaxing mandatory CI.
