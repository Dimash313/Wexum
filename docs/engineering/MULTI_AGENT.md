# Multi-agent factory workflow

GitHub is the coordination mechanism. More chats do not imply unlimited shared infrastructure, writes or human review bandwidth.

## Admission
- Integrator opens a scoped issue with owned paths, acceptance criteria, interface dependencies, test plan and risks.
- Agent claims the issue by a visible issue comment and checks no other agent owns it. Concurrent claim collision is resolved by the integrator; comments are not an atomic lock.
- Agent creates one issue branch based on the latest accepted integration branch.
- No agent edits another agent's branch or shares working directories. Never modify main directly.
- Shared contracts, CI, lockfiles, policy and root AGENTS.md are integrator-owned. Product agents submit proposals before modifying them.
- Agent opens a **draft PR** early, links issue and records blocked dependencies. Do not merge without green checks and independent review.
- An integration agent serializes shared changes, verifies current base, resolves conflicts and updates STATE.md after merge only.

## Dependency order
Contract decisions → platform and test harness → independent modules → integrated workflows → fault testing → release review. Each task must specify which upstream interface it consumes.

## Example VPN work split (10 parallel ownership lanes)
1. control-plane: tenancy and VPN enrollment API (`products/vpn/control/`)
2. entitlements: scoped access grants and revocation (`products/vpn/entitlements/`)
3. node-registry: node health and region metadata (`products/vpn/nodes/`)
4. client-android: VPN Android native boundary (`apps/vpn/android/`)
5. client-ios: Apple Network Extension boundary (`apps/vpn/ios/`)
6. client-desktop: desktop app shell and native integration (`apps/vpn/desktop/`)
7. network-observability: privacy-safe metrics and alerts (`products/vpn/observability/`)
8. subscription-adapter: payment integration boundary (`products/vpn/subscriptions/`)
9. test-lab: simulations and reproducible integration/failure tests (`tests/vpn/`)
10. security-review: threat model, adversarial tests and verification (`docs/vpn/security/`)

These lanes can be active simultaneously only after shared contracts and cross-platform review are approved. Avoid assigning two agents the same files; e.g. all VPN contracts are integrator-owned in `docs/vpn/`.

## Agent startup prompt
"Open Dimash313/Wexum. Read AGENTS.md and the mandatory architecture/quality/policy documents. Fetch current main, open issues and PRs. Work ONLY on GitHub issue #<number> within its owned paths in a dedicated branch. Provide tests and PR; do not merge or claim unverified readiness. Report blockers rather than guessing."

## Shared resources
Limited Actions minutes, review throughput, cloud quotas, database access and runner capacity impose concurrency limits. Prefer path-filtered CI and explicit ownership; escalate cross-domain changes rather than creating PR races.

