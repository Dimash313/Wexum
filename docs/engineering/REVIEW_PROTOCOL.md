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
8. Publish an evidence-backed AI audit verdict on the exact current head SHA (`BLOCKED`, `CHANGES REQUIRED`, or `ACCEPTED FOR INTEGRATION`), and inform the integrator of accepted risks. Do not misrepresent this technical verdict as a formal GitHub `APPROVED` review from a distinct account.

## Merge authority
CTO/integrator alone may decide whether to integrate an internal PR after the distinct AI-auditor lane documents acceptance on the exact reviewed SHA, relevant required CI/CodeQL and negative tests pass, all blocking findings are resolved, and actual GitHub rules allow the merge. The implementing agent must not self-approve or self-merge. With one shared GitHub account, AI audit separation is procedural, not a distinct-account GitHub approval; record that limitation transparently. Requiring a second human reviewer for every internal PR is **not** a Wexum policy requirement, and `required_approving_review_count = 0` does not waive AI audit or mandatory CI. Public VPN deployment and other high-risk release decisions have a separate founder authorization and security review gate; see `INTERNAL_REVIEW_POLICY.md`.

## Independent AI audit scope
The auditor must not be the same coding agent that authored the change. It must inspect current diffs, trust boundaries, negative scenarios and actual check logs, track SHA/target/base, and report bounded evidence without inventing independent human identity. A changed source SHA requires re-review. A `BLOCKED` or `CHANGES REQUIRED` verdict prevents integration. No skipped test is treated as passing.

## Shared-file coordination
Only the integrator edits AGENTS.md, shared CI, shared API/event schemas, STATE.md, and CODEOWNERS directly. Product agents submit proposals/issues for these paths. PRs with overlapping owned paths are serialized; an issue comment is not a transactional lock.
