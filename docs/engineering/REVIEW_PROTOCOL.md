# Independent review and evidence protocol

## Decision states
- **Blocked**: red mandatory CI; missing evidence; open critical/high security defect; cross-tenant access; uncontrolled data loss; unresolved religious/legal restrictions on the affected feature.
- **Changes requested**: scope, tests, rollout, maintainability or backwards-compatibility defects remain.
- **Accepted for integration**: independently reviewed code and documented checks meet task acceptance criteria.
- **Operationally verified**: additional real-environment load, failure, security and recovery tests completed. PR integration does NOT imply this state.

## Quality scoring
Quality dimensions are defined in QUALITY.md. Each dimension is pass / fail / not-applicable, with evidence required for pass or not-applicable. A 10/10 summary is only possible when all ten are independently verified; it is never inferred from CI alone. This process does not guarantee zero defects.

## Reviewer protocol
1. Establish intended scope from the issue and compare changes against main.
2. Review identity, access and data boundaries before functional happy paths.
3. Validate dependency licenses, secrets, logging, resource limits and migrations.
4. Confirm CI on the latest integration base. Inspect tests; don't merely count them.
5. Run independent negative tests or review supplied reproducible evidence.
6. Record severity, exact reproduction and requested fixes. Never leak sensitive details in public comments.
7. Check religious-policy gate and legal/store obligations for relevant functionality.
8. Approve only after fixes are verified; inform the integrator of remaining accepted risks.

## Merge authority
Integration owner alone decides whether to merge once ruleset and required checks allow it. An AI author must not approve its own work or silently merge. With only one human collaborator, Required approvals = 0 is a temporary GitHub constraint, not a substitute for independent audit.

## Shared-file coordination
Only the integrator edits AGENTS.md, shared CI, shared API/event schemas, STATE.md, and CODEOWNERS directly. Product agents submit proposals/issues for these paths. PRs with overlapping owned paths are serialized; an issue comment is not a transactional lock.
