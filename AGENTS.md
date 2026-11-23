# Wexum agent operating instructions

This document is binding for every ChatGPT, Codex and other coding agent working anywhere in this repository. The repository, not a chat transcript or assumed memory, is the source of truth.

## CTO autonomous continuation — owner directive (issue #76)

When the owner writes **«Продолжаем дальше»**, an agent acting as Wexum CTO / integrator must inspect live GitHub and autonomously **execute** the highest-priority available engineering step. Do not request a PR list, task allocation or repeated requirements from the owner. Use issues, PRs and checks to coordinate and verify actual work; delegate code within issue ownership and obtain repeat non-author audit for remediations. Escalate only owner-authority decisions (budget, strategy, substantial compromises, exceptional permissions). **This never waives green required CI, independent approval, security/privacy/religious review, branch protection or no-self-merge rules.**

Mandatory CTO operating instructions: [`docs/engineering/CTO_OPERATING_PROTOCOL.md`](docs/engineering/CTO_OPERATING_PROTOCOL.md). New CTO sessions also read and maintain their owned [`docs/engineering/cto/HANDOFF.md`](docs/engineering/cto/HANDOFF.md) after checking the live repo; GitHub is the source of truth, not a previous chat transcript.

## Mandatory read order for every new session
1. Inspect current repository, branch, status, latest commits and open PRs/issues. Do not assume the task is unfinished.
2. Read this file, `README.md`, `docs/engineering/STATE.md`, `docs/architecture/SYSTEM.md`, `docs/architecture/BOUNDARIES.md`, `docs/engineering/QUALITY.md`, `docs/engineering/REVIEW_PROTOCOL.md`, and `docs/policy/RELIGIOUS_REVIEW.md`.
3. Read the relevant product specification and its assigned GitHub issue, dependencies and PRs.
4. Identify the smallest independently testable change; state the touched paths and risks before coding.
5. Read recent changes in touched files; never discard or overwrite another agent's work.

## Work protocol
- One GitHub issue = one independently owned change = one branch = one PR, unless the issue explicitly defines a different arrangement.
- Branch: `feat/<domain>/<issue-number>-<slug>`, `fix/<domain>/<issue-number>-<slug>`, or `docs/<domain>/<issue-number>-<slug>`.
- Before changing a shared interface or cross-team file, create an interface proposal/ADR and obtain integrator approval. Avoid editing `docs/engineering/STATE.md` in parallel; only the integrator updates that file.
- No direct commits to `main`, no force pushes, no author self-approval and no unreviewed merge. For internal PRs, the distinct Independent Audit AI lane provides a documented verdict on the exact source SHA; passing mandatory GitHub Actions and clearing blockers remain necessary. Formal GitHub approval from a second human account is not a universal prerequisite unless the live ruleset requires it. Only the CTO/integrator may perform an authorized integration after these gates; an implementer must not self-merge. See `docs/engineering/INTERNAL_REVIEW_POLICY.md`. Passing CI alone is not proof of production readiness.
- If blocked by unavailable API, dependency, tools or missing authority, report the blocker accurately; do not fabricate implementation or test results.
- Do not introduce runtime dependencies, paid third-party APIs, cloud services or new infrastructure without a documented rationale and cost/security review.
- No secrets, API tokens, credentials, private keys, user files or personal data in the repo, issues, test fixtures, logs or chat.
- Implement only the contracted behavior; code must be explicit, minimal, typed where useful, deterministic and readable. Avoid filler comments, speculative abstractions and dead features.
- Add relevant positive, negative, cross-tenant, concurrency and fault-injection tests. State exactly which tests ran and which did not.
- Follow `docs/engineering/QUALITY.md`. Never assert a "10/10" rating without an independent evidence-based review.
- Never imply full compliance with religious rulings from a generic principle: unresolved cases require qualified review, logged decision and explicit owner approval.
- Do not invent product release numbers before actual release.

## PR report
Summarize: issue and scope; files touched; behavior; security/privacy impact; interface impact; tests with commands and outcomes; remaining risks; rollout and rollback; dependent PRs. Use the PR template.

## Source of truth
GitHub issues track assignments and acceptance criteria; PRs track proposed code; ADRs track architectural decisions; `docs/engineering/STATE.md` tracks the integrated baseline, not aspirational work. Use cross-references instead of duplicating mutable progress reports.


## Agent onboarding and task intake
- Resume instructions: `docs/engineering/AGENT_START.md`. Use `.github/ISSUE_TEMPLATE/agent_task.yml` for coding tasks and `architecture_decision.yml` for cross-boundary changes.
- A claimed task is not permission to implement a missing security/ethical/legal precondition. Resolve blockers first.
- No direct `main` changes. An administrator must activate repository rules; a YAML document alone cannot enforce approvals or status checks.
- Security concerns must follow `SECURITY.md` and never be publicly exposed in issue bodies.
