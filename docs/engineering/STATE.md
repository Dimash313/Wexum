# Current integrated state

This document describes only committed, reviewed, integrated work. It is maintained by the **integrator only** to prevent parallel-edit conflicts.

## Baseline
- Repo: Dimash313/Wexum; primary integration branch: main.
- Catalog: 22 planned standalone products and Wexum Hub.
- FileShape: separate IhsanSoft product with its own accounts; a potential external integration.
- Products: no released Wexum applications.
- Foundation PR: pending review and integration; contains planning contracts, basic pure authorization/event code and foundational CI.
- No deployed VPN, identity server, billing system or enterprise readiness claim.

## Mandatory next integrations
1. Review/merge foundation PR only after required current-head CI and an independent documented AI audit accepted by CTO; formal second-human GitHub approval is not mandatory for an internal PR unless the active ruleset requires it. Do not treat the foundation as integrated until the actual merge occurs.
2. Define product trust boundaries and identity threat model.
3. Implement isolated WexumVPN control-plane primitives and test harness.
4. Build approved product architecture through separate issues and PRs.

## How to update
Integrator updates this file only after the relevant PR is merged and its evidence checked. Do not record open PR code as integrated. GitHub issues and PRs are the authoritative live task queue.

