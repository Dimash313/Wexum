# Resume a Wexum task in a new ChatGPT/Codex session

Paste this message to a fresh coding agent:

> Repository: https://github.com/Dimash313/Wexum
>
> Work item: GitHub issue #NUMBER (replace with the real issue).
>
> Inspect current main, open PRs, branches, issue acceptance criteria and dependency blockers. Read AGENTS.md, docs/engineering/STATE.md, docs/architecture/SYSTEM.md, docs/architecture/BOUNDARIES.md, docs/engineering/QUALITY.md, docs/engineering/MULTI_AGENT.md and docs/policy/RELIGIOUS_REVIEW.md. If the foundation PR is not merged, read approved documents from its branch but do not treat them as integrated.
>
> Take exclusive ownership of this issue only after checking no other agent has claimed it. Identify exact paths you own, share a short plan, work in a separate issue branch and open a draft PR. Never change main directly, self-merge, overwrite another worker or alter shared contracts without integrator review.
>
> Write minimal, readable and testable code. Add negative, tenant-isolation and failure tests where relevant. Report exact commands, observed results, unresolved security/privacy/legal/religious risks and a PR link. A passing CI run is not 10/10. If blocked, report the blocker and stop rather than fabricate progress. Do not invent product release labels before actual release.

## CTO continuation in a fresh chat

The owner may simply write **«Продолжаем дальше»**. For an agent acting as CTO / integrator, this is a directive to **take the next safe technical action now**, not to ask for a PR number or a fresh assignment. Read [the mandatory CTO protocol](CTO_OPERATING_PROTOCOL.md), [CTO HANDOFF](cto/HANDOFF.md), root `AGENTS.md`, current GitHub issues/PRs, dependencies and exact-head CI. Choose the highest-priority actionable blocker, carry out a scoped fix/test/integration/audit handoff, and report verifiable results. Escalate only owner-authority decisions. Do not skip release or independent review gates.

A product-lane agent remains bound to its explicitly assigned issue; the CTO protocol does not give all other agents unlimited file ownership.

## Roles
- **Product architect:** decomposes a product epic into independent, testable child issues and reviews interface decisions.
- **Subsystem engineer:** implements one issue within its owned files.
- **UX lead:** specifies workflows and design contracts; platform client engineers implement them.
- **Security reviewer:** threat-models, tests and reviews; does not certify their own implementation.
- **Integrator:** arbitrates conflicts, checks interfaces/CI, merges and updates the integrated state.

## Ready-to-code gate
An implementation issue needs: accepted design decisions; stable API contracts; non-overlapping owned files; clearly defined acceptance tests; a plan to validate privacy/security and unresolved requirements. If one is missing, design it first.
