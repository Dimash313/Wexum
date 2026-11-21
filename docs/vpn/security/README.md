# WexumVPN Security & Privacy Engineering

**Issue:** [#11](https://github.com/Dimash313/Wexum/issues/11)  
**Scope owner:** `docs/vpn/security/` only  
**Status:** draft security design and review evidence; **NOT** an implemented VPN, accreditation, independent audit, or production approval.

## Baseline and dependency discipline

As inspected on 2026-11-21, `main` contains only repository bootstrap files and does **not** contain the architecture, production VPN or CI assumed by the proposed [foundation PR #1](https://github.com/Dimash313/Wexum/pull/1). Source documents read from PR #1 are **proposals** until independently reviewed and integrated. Security reviews of other draft PRs refer to their exact heads, not to `main` implementation. Nothing here grants permission to modify shared API contracts, platform code or other lanes.

**Agent continuity:** always begin with [HANDOFF.md](HANDOFF.md), verify its GitHub references and update it after each significant change.

Read in order:
1. [Threat model](THREAT_MODEL.md): assets, STRIDE, confirmed findings, unresolved design threats.
2. [Authorization and key requirements](ACCESS_AND_KEY_SECURITY.md): trust boundaries, grant authorization, revocation and rotation.
3. [Privacy and recovery](PRIVACY_AND_OPERATIONS.md): data inventory, collection limits, recovery/incident controls.
4. [Release gate manifest](release_gates.json) and [gate evaluator](gate_check.py): **metadata-only** completeness linter. Passing it is never proof of real security, legitimate review, or successful network testing.
5. [Cross-lane security contract proposal](CROSS_LANE_CONTRACT_PROPOSAL.md): specific CTO decisions for authentic principals, signed grants, revocation, probes, payments and trustworthy leak evidence.

**Critical CLI distinction:** `gate_check.py` without flags validates only supplied manifest metadata (exit 0 on valid structure). `--require-attested` intentionally **never returns a release-green success code**, even if the supplied manifest claims all gates are attested, because this offline linter cannot authenticate review/test evidence. External independently verified approval is required before deployment. Three negative CLI regression cases were added to `test_gate_check.py`; see HANDOFF for exact test execution status.

## Observed implementation defects (not speculation)

- **SEC-CTRL-001 (HIGH, proposed severity):** draft [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55), at head `66532b4df984c091b46e53697218b82557bb4bbd`, uses oldest-first `LIMIT 200` across both revoked and active devices in `SQLiteDeviceStore.list_for_owner`. After 200 historical revoked entries a newly enrolled active device can disappear from owner listings. This is a device-management/revocation visibility hazard, **not evidence of actual unauthorized VPN access**. Owner: issue #2.
- **SEC-CTRL-002 (MEDIUM):** the same PR opens SQLite connections before the `try` handlers in enrollment, listing and revocation. A failed open can escape as `sqlite3.OperationalError` instead of the stable service outage error. Owner: issue #2.

Evidence: [negative regression source](https://github.com/Dimash313/Wexum/blob/integration/56-vpn-control-ci-candidate/tests/integration/test_vpn_control_blockers.py) in [PR #67](https://github.com/Dimash313/Wexum/pull/67) and [Actions failure](https://github.com/Dimash313/Wexum/actions/runs/44873727876) on `ea882455a788dd76e07fee106409c2c33654ad77`: 1 failed assertion plus 3 errors. These are **not** vulnerabilities in a deployed VPN, which does not yet exist.

## Mandatory integration workflow

1. Defect owner fixes within their owned PR and supplies deterministic negative regression tests.
2. CTO coordinates shared contracts and mandatory CI and verifies corrected exact head.
3. Issue #11 verifies security requirements without changing another lane's code.
4. Independent auditor (#41 / chat #2) checks evidence independently. Security ownership does not substitute for audit.
5. Integration owner alone determines merge; release requires much more than a green documentation linter.

Never claim "no logs", "absolute anonymity", "10/10 security" or a working private tunnel from specs or mocked clients.