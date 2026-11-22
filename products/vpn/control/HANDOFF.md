# HANDOFF — WexumVPN Control Plane / Device Management

## 1. Scope and ownership
- GitHub Issue #2, `products/vpn/control/` only. This is a non-deployed Python standard-library SQLite prototype, not a functioning VPN or integrated authentication service.
- Existing owned Draft PR #55 is stacked on unmerged foundation PR #1. Do not merge without required exact-head CI and independent review.
- Backend Engineering left an issue #2 coordination comment on 2026-11-22 for CTO confirmation of the narrow SQLite open-error remediation. A comment does not constitute CTO approval. Do not touch shared CI, Identity, Node Registry, Entitlements, Billing or client lanes without CTO/integrator agreement.

## 2. Architecture and current decisions
- `src/wexum_vpn_control/service.py`: `DeviceControlService` enforces trusted actor tenant/subject/scope/issuer/audience/freshness and checks a server-supplied authoritative entitlement before enrollment. `AuthenticatedActor` is only a trust-boundary input, NOT verified by this module.
- `src/wexum_vpn_control/store.py`: SQLiteDeviceStore; WAL, owner-scoped persistent rows, hashed idempotency keys, BEGIN IMMEDIATE for atomic device cap, and owner-scoped revocation. Device rows do NOT authorize a VPN tunnel, provide device proof or issue signed grants.
- Store connect/open/PRAGMA failures are now normalized to `StoreBusy('device store unavailable')` inside `_connect` (including cleanup of an already opened connection). Service maps StoreBusy for enroll/list/revoke to `EnrollmentUnavailable('device store unavailable')`.
- `README.md`, `THREAT_MODEL.md`, `openapi-proposal.yaml` remain proposals and explicit non-production limits.

## 3. Issue, branch and review
- Issue: https://github.com/Dimash313/Wexum/issues/2
- Branch: `feat/vpn/2-control-plane` (base `architecture/foundation-and-agent-operating-system`); Draft PR: https://github.com/Dimash313/Wexum/pull/55
- Source fix commit: https://github.com/Dimash313/Wexum/commit/36493b0c11f5e041a38b955732fe15e813afda17
- Final corrected test commit: https://github.com/Dimash313/Wexum/commit/c914b1dc592a8faa729ccbf25480d44b24100fbb
- A malformed intermediate test edit (`2d16c29574515586c222648a47551af20b8762ad`) was superseded by the corrected entire-file restoration in c914b1d; review the latest head, not the intermediate change.
- This HANDOFF was first added after c914b1d. Recheck live PR head SHA each session.

## 4. Implemented code and tests
- `_connect` catches sqlite3.Error raised by `sqlite3.connect()` and PRAGMA setup, closes a partially opened connection, then raises stable StoreBusy.
- One `DeviceServiceTests.test_database_open_failure_maps_to_service_unavailable` tests fail-closed behavior for list, revoke and enroll with an unavailable database parent, restores the store path and verifies the original device record remains unchanged.
- New test and source code were written through GitHub, then read back at final blob SHA. No shared code/CI changed.

## 5. Actual verification (do not conflate)
- Previous code baseline on PR #55: author reported 20/20 local tests, but these were not rerun for this patch.
- PR #67 original combined candidate SHA `ea882455a788dd76e07fee106409c2c33654ad77`: GitHub Actions run https://github.com/Dimash313/Wexum/actions/runs/44873727876 failed on 4 negative cases (3 opening errors, 1 >200 history visibility). This is evidence for OLD PR #55 SHA `66532b4df984c091b46e53697218b82557bb4bbd`, not an outcome for the corrected code.
- Current cycle local focused Python smoke mirror of changed `_connect` function (NOT full code mirror): 3/3 tests PASS; `python -m py_compile` on the focused harness PASS. Tested sqlite open failure, partial-connection PRAGMA exception cleanup, and valid connection.
- Actual full repo command `PYTHONPATH=products/vpn/control/src python -m unittest discover -s products/vpn/control/tests -v`: NOT RUN (git clone failed due DNS `Could not resolve host: github.com`); actual full-source compileall: NOT RUN.
- New-head GitHub Actions required core + CodeQL: NOT VERIFIED until exact new PR SHA is tested. No independent approval; do not report green CI from PR #67 baseline.

## 6. Known blockers and risks
- **P1 unresolved:** list_for_owner orders the oldest 200 historical rows, hiding newer active device after >200 revoked history; negative test PR #67 remains a confirmed failure. Requires a careful bounded deterministic active-first/owner-scoped query and tests, coordinated under issue #2.
- PR #67 integration candidate copied OLD issue #2 source and must NOT be treated as testing the corrected commit. Shared workflow edits and PR #67 are integrator-owned issue #56.
- Signed grants, real identity/OIDC verification, authoritative external entitlements, device proof, node revocation, VPN tunnel and production payments are absent; this is not production-ready.
- Foundation PR #1 and its independent audit #41 / release rules issue #38 still block integration. CTO approval of cross-lane contracts is still required.
- Raw sqlite errors remain available via Python exception context; future HTTP/logging adapters must sanitize error responses and avoid logging secrets or filesystem paths.

## 7. Next concrete steps
1. CTO/integrator confirms scope and coordinates #2 source correction with issue #56 CI owner.
2. Run full Control Plane 21-method unit suite, compileall, PR #67 exact-source negative tests (including >200 history), and CodeQL against the latest corrected head; make the required job blocking.
3. Resolve the separate >200-history defect under issue #2, add an owner-scoped regression test, rerun full suite and independent audit.
4. Review data retention, DB lifecycle and future auth/entitlement contracts before any service exposure.

## 8. References
- PR #55: https://github.com/Dimash313/Wexum/pull/55
- PR #67: https://github.com/Dimash313/Wexum/pull/67
- Reproducing GitHub CI: https://github.com/Dimash313/Wexum/actions/runs/44873727876
- Independent QA: https://github.com/Dimash313/Wexum/pull/74
- Foundation: https://github.com/Dimash313/Wexum/pull/1
- Issue #56 (integrator CI): https://github.com/Dimash313/Wexum/issues/56
