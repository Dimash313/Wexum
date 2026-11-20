# Evidence-based engineering acceptance

"10/10" is an aspirational quality bar, **never a self-assigned score**. A PR is not accepted unless mandatory gates are met. No code can be promised free of all future bugs.

## Ten independent dimensions (0: absent, 1: credible evidence)
1. Correctness: acceptance tests cover all behaviors, negative and edge cases.
2. Security: threat assessment, input validation and least-privilege tests.
3. Privacy: data minimization, encryption and retention/deletion paths.
4. Reliability: timeouts, bounded retries, failure modes and recovery drills where applicable.
5. Consistency: concurrency, idempotency, migrations and rollback when applicable.
6. Interfaces: API/event compatibility and cross-product boundaries.
7. Performance: representative measurable budgets and capacity tests, where applicable.
8. Maintainability: simple typed code, limited dependencies, clear errors and reviewable diffs.
9. Operations: logging without secrets, metrics, alerts, runbooks and cost controls.
10. Compliance: store/legal licensing and ethical/religious review for affected features.

## Release blocker rules
- Any critical security flaw, secret leak, unresolved cross-tenant access, broken data integrity, red CI, missing required human review or unresolved religious restriction blocks release.
- "Not applicable" needs a documented explanation, not an automatic pass.
- A passing PR CI is necessary but not sufficient for production.
- Tests and reviewer conclusions must be independently verified. Never fabricate commands, benchmarks, vulnerability scans or approval.
- Product parity with a competitor is assessed by measured user workflows, reliability and audited scope, not branding.
- No product-release numbers until actual product launch.

## Code principles
Small, explicit, deterministic and minimal; no unused generalization; no dead code; no needless comments; no silent exception swallowing; no unbounded background tasks; no hidden external IO. Explain complexity at the boundary only.

