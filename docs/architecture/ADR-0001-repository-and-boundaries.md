# ADR-0001 — Shared repository, independent domain boundaries

Status: proposed; approval required before foundation merge.

## Context
The ecosystem targets dozens of independently useful apps and coordinated parallel agents. Starting with completely separate infrastructure per app makes early integration and consistency expensive.

## Decision
Use a repository with explicit product and platform directories. Shared code is limited to stable, small contracts, design tokens and client libraries. Deployment boundaries may differ from source directories. VPN data-plane infrastructure is isolated from the start. All changes use per-issue PRs, protected integration and owner-reviewed shared contracts.

## Alternatives
- Monolith without domain boundaries: simpler initially, but unacceptable cross-domain coupling.
- Many independent repositories/microservices immediately: higher operational and integration overhead.
- Single hub containing all product logic: unacceptable single point of failure.

## Consequences
Strong CI and ownership discipline are necessary. Split deployment/repositories only after measured security, operational or ownership needs justify them. Reassess when real traffic and team size provide evidence.

