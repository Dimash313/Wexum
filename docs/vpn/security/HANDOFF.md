# HANDOFF — WexumVPN Security & Privacy Engineering

**Updated:** 2026-11-21 UTC (GitHub rechecked on command «Продолжаем дальше»; refresh head SHA before decisions)  
**Status:** active engineering documentation, **draft only**. No production VPN, privacy certification, independent security approval or release.  
**Next agent:** start here, but always re-fetch GitHub: snapshots and commits can become stale.

## 1. Direction, responsibilities and hard ownership

- **Direction:** WexumVPN / Security & Privacy Engineering.
- **Primary GitHub issue:** [#11](https://github.com/Dimash313/Wexum/issues/11) (open).
- **Only writable path:** `docs/vpn/security/`. Do **not** edit `products/vpn/`, `apps/vpn/`, `tests/vpn/`, `docs/engineering/`, shared `docs/vpn/` contract files, root `AGENTS.md` or other teams' HANDOFF.md without CTO/integrator approval.
- Responsible for STRIDE threat modeling, client/Identity/control-plane/node boundaries, customer-data minimization, grant/secret/key requirements, DNS/IP/privacy leak risks, incident/recovery specifications, adversarial evidence and objective release blockers.
- This lane **does not** implement another team's fixes and does **not** replace the independent auditor (#41 / chat #2). Route changes to owners **through CTO**; never approve/merge your own PR.
- Update **this file** whenever meaningful scope, branch/PR, threats, decisions, evidence or blockers change, and before completing a work phase. Persist cross-chat continuity here, not in a chat transcript.

## 2. Current architecture and accepted versus proposed decisions

**Integrated baseline as observed 2026-11-21:** default `main` has only bootstrap repository files; **[foundation PR #1](https://github.com/Dimash313/Wexum/pull/1)** (head `6b072ca12f79f7a45c2220253069e0ab34d27c2f`) remains open/unmerged. Its `AGENTS.md`, VPN architecture, entitlement design, quality and religious policy docs are **proposed**, not integrated authority. Fetch them directly from PR #1 head until integration. No working VPN tunnel or production identity/signing service has been verified.

**Security target architecture (not implemented):**
1. Public native VPN clients obtain consent via OS system APIs; user consent or mocked engine status never proves protection.
2. Identity adapter verifies authentic token/session/issuer/audience/scopes and supplies trusted actor, not client-supplied identity.
3. VPN Control Plane owns tenant+subject+device enrollment and revocation; Billing supplies verified, fresh subscription state.
4. Entitlement policy may produce a candidate but **only an isolated approved signer** can mint scoped, short-lived, asymmetric signed grants with tenant+device+node+session constraints.
5. Independently authenticated VPN node verifies grant, device/node audience, expiry, replay and revocation; no per-packet dependency on Hub or Billing.
6. VPN traffic (data plane) is separate from Control/Management planes. Operational telemetry defaults to aggregates; browsing destinations and raw secrets must not enter routine logs.
7. Recovery, retention, backup, node availability, revocation and DNS/IPv4/IPv6 protection require real-environment tests.

**Design principles agreed as requirements, not as proven runtime behavior:**
- Fail closed for *new privileged authorizations* on unavailable identity/subscription/device authority.
- Existing-session offline tolerance, signed-token TTL, clock skew, revocation SLA, proof-of-possession, canonical token format, key store and rotation windows **not approved**. The proposed metadata release gate has no approved offline grace, but actual enforcement does not yet exist. Request CTO ADR for any nonzero grace.
- Use reviewed standard crypto and asymmetric key separation; no secret in git, comments, logs or tests.
- Hub is not trusted issuer or mandatory VPN gateway; avoid cross-product identity/data leakage.
- Never claim absolute anonymity, zero logs or quality 10/10 without independent evidence.

## 3. Work identifiers

| Item | State | Link / ref |
| --- | --- | --- |
| GitHub repository | public | https://github.com/Dimash313/Wexum |
| Issue | **#11 open** | https://github.com/Dimash313/Wexum/issues/11 |
| Our branch | `feat/vpn/11-security-review` | https://github.com/Dimash313/Wexum/tree/feat/vpn/11-security-review |
| Our Draft PR | **#71 open, draft, base `main`** | https://github.com/Dimash313/Wexum/pull/71 |
| Our PR head | Changes with this handoff will move head; **query PR #71 live** | Do not trust a fixed SHA in this document |
| Foundational dependency | #1 open/unmerged | https://github.com/Dimash313/Wexum/pull/1 |
| Independent foundation audit | #41 open | https://github.com/Dimash313/Wexum/issues/41 |

**Do not merge #71.** Its base `main` currently does not yet have proposed foundational docs. Rebase/retest only on CTO-approved integrated foundation; preserve exclusive ownership and avoid silently editing shared contracts.

## 4. Implemented artifacts in our exclusive directory

| Path (relative to `docs/vpn/security/`) | Purpose |
| --- | --- |
| `README.md` | Mission, initial reviewed findings and integration policy |
| `THREAT_MODEL.md` | STRIDE risk register, trust boundaries, abuse scenarios and source evidence |
| `ACCESS_AND_KEY_SECURITY.md` | Proposed trusted actor → grant issuer → node verifier contract, key custody and negative access tests |
| `PRIVACY_AND_OPERATIONS.md` | Minimization matrix, provider/retention unknowns, outage response, incident and actual-device leak-testing gate |
| `release_gates.json` | 13 **blocked** mandatory evidence gates; SEC-CTRL-001 (HIGH) and SEC-CTRL-002 (MEDIUM) open |
| `gate_check.py` | Python stdlib metadata shape/readiness linter; checks only submitter-provided metadata, **not genuine evidence** |
| `test_gate_check.py` | 15 authored unit cases for missing gates, fake/inconsistent evidence, SHA mismatch, duplicates and open findings |
| `CROSS_LANE_CONTRACT_PROPOSAL.md` | CTO decision request D1–D8, actual cross-lane source refs and preliminary observability clock-regression scenario |
| `HANDOFF.md` | This canonical continuation document |

The linter's `attested` state is NOT an external verification; even a structurally passing manifest must not be interpreted as authorization to deploy.

## 5. Test and review evidence — distinguish observed from reported

**Current continuation (2026-11-21):**
- Re-fetched issue #11, main, proposed AGENTS.md and mandatory architecture/quality/policy docs, PR #1/#55/#64/#65/#66/#67/#71 and new PRs #62/#72/#73/#74. Foundation #1 and source defect PR #55 still unmerged/unfixed; #67 negative CI remains red.
- Source-reviewed #72 `health.py`/`probes.py`, #73 billing `core.py`, #74 leak-evidence classifier and their tests (not run here). New separate decision request `CROSS_LANE_CONTRACT_PROPOSAL.md` is scoped to our directory.
- **Fixed an unsafe future release-signal in own `gate_check.py`:** offline `--require-attested` can no longer exit 0 even for an entirely self-attested, internally consistent fabricated manifest; returns 1 until a separate external independent verification gate exists. The default metadata-lint command may return 0 only to mean valid **structure**.
- **Added 3 negative CLI tests** to `test_gate_check.py` for fabricated complete attestation, lint-vs-release distinction and open HIGH finding. Total **18 authored tests** (15 historical + 3 new). **NOT EXECUTED on changed exact GitHub source in this continuation; Python execution environment cannot fetch connected GitHub repository (DNS unavailable). No new GitHub Actions.** Do not report tests as passed.
- New modified code blobs: `gate_check.py` `2cdff042974fcf93468504a5367f578d9e26d1c9`; `test_gate_check.py` `26bc40d3441f8380920038d2ea56a95a264b9998`. These are GitHub-reported file blob hashes, **not local test parity checks**.
- `main` contains only repository bootstrap files; no verified deployment, tunnel traffic or real leak tests. Changes limited to `docs/vpn/security/`. No release clearance.


**Prior handoff evidence (historical):**
- Read live GitHub PR #71 metadata, issue #11, current main tree and the referenced security files. Checked that `HANDOFF.md` did not exist before creating it.
- PR #71 previous head `b465f0d22841524ccb754298aaf44735ee150bc6` had **0 PR-triggered Actions runs and 0 legacy combined statuses** by GitHub connector check. This is *not* a green CI result.
- No tests, packet captures or runtime tunnel tests were executed during **this handoff-only update**.
- An unauthenticated local Git clone attempt failed due to network DNS unavailable; this is environmental, not a test failure in the project.

**Earlier PR #71 report (historical evidence, not rerun in the current iteration):**
- Previous conversation/PR description reported **15/15 local Python 3.13.5 unittest tests passing**, syntax compilation passing, and local SHA match for three files:
  - `gate_check.py` Git blob `a8aad5a2c458eb8617be51275ed8ac89dbec3305`;
  - `test_gate_check.py` Git blob `2af6d886091c211d35f88975a1470cd440004ef0`;
  - `release_gates.json` Git blob `c6410b7b238989039a9501e466fe59d0a1cc1da1`.
- **A reproducible command transcript/CI artifact from that reported local run is not attached in this handoff session. Re-run to independently substantiate, then link exact evidence.** Do not inflate historical claims into current-head CI approval.
- Intended commands (from repository root):
  ```sh
  python -m unittest discover -s docs/vpn/security -p 'test_*.py' -v
  python -m compileall -q docs/vpn/security
  python docs/vpn/security/gate_check.py
  python docs/vpn/security/gate_check.py --require-attested
  ```
  Last command is **expected to exit 1** while 13 gates and open HIGH finding remain. Ordinary lint checks structure only; it is not a release test.

**Separate integration evidence:** candidate [PR #67](https://github.com/Dimash313/Wexum/pull/67), head `ea882455a788dd76e07fee106409c2c33654ad77`, [Actions run #44873727876](https://github.com/Dimash313/Wexum/actions/runs/44873727876) failed with **one assertion failure and three errors** for source defects in PR #55. The existing Control Plane tests passing alongside these does **not** override failed negative regressions. This is not our lane's own CI.

## 6. Confirmed findings, unverified risks and blockers

**Confirmed from Control Plane draft [PR #55](https://github.com/Dimash313/Wexum/pull/55)**, observed unchanged head `66532b4df984c091b46e53697218b82557bb4bbd`:
- `SEC-CTRL-001` **HIGH triage**: oldest-first `LIMIT 200` includes revoked history and can hide newly active devices from owner listing, undermining manage/revoke visibility. Not evidence of unauthorized access to a deployed VPN. Owner: **issue #2**. Fix active-first or bounded, tenant-scoped cursor pagination; test >200 history, revocation visibility and cross-tenant cursor handling.
- `SEC-CTRL-002` **MEDIUM**: SQLite `_connect()` before error handlers allows `sqlite3.OperationalError` to escape rather than stable `EnrollmentUnavailable` mapping. Information leakage through future HTTP adapter is a **possibility**, not demonstrated. Owner: **issue #2**. Normalize failures from open/enroll/list/revoke and exercise unavailable-path regressions. Reverify exact corrected head.
- `SEC-OBS-001` **preliminary LOW/MEDIUM, static only**: #8 `HealthMonitor.snapshot()` calculates `age=max(0, now-last_sample)`; an injected/provisioned clock rollback could retain a healthy state with future-dated samples. Production default is monotonic; **not independently reproduced** nor evidence of a deployed exploit. Request #8 owner negative clock-rollback test and CTO review of invalid telemetry policy. Source: [PR #72](https://github.com/Dimash313/Wexum/pull/72) head `bfff09382ab5b11df2366c77b67a9ac224ab1b38`.
- Reproducer is at `tests/integration/test_vpn_control_blockers.py` on PR #67; our lane does not modify it.

**Unimplemented/unverified blockers (do not label as observed vulnerabilities):**
- #34 verified Identity/OIDC edge; #3 currently unsigned precheck, no live signed grant issuer/verifier, #4 trusted live node registry, #9 verified billing/refunds, revocation delivery, replay/session binding.
- PR #1 foundation and independent audit #41 still pending; mandatory root CI/ruleset #38 governance needs verified integration.
- Real Android/iOS/Desktop protected tunnel; DNS/IP (IPv4, IPv6, DNS, route) leaks and kill-switch tests not performed.
- Precise retention/deletion/provider logging, hosting regulations, security incident restoration, app-store/legal and qualified religious policy review not done.
- Current issue #3 [PR #64](https://github.com/Dimash313/Wexum/pull/64) has since advanced to observed head `8acebae483a146c5adf68bd82ba4c440f01e3e7f` with 40 **reported** local Python tests; the module remains an unsigned precheck only, no live signed issuer or node verifier. Reinspect exact code/test diff before acceptance.
- Recent drafts inspected: [Nodes #65](https://github.com/Dimash313/Wexum/pull/65) `5103d986323767c4457a941a058c877ffd0083f1`, [Android #66](https://github.com/Dimash313/Wexum/pull/66) `fc1f7129bce5d29a7c1eae2a4974899010c1fec4`, [Observability #72](https://github.com/Dimash313/Wexum/pull/72) `bfff09382ab5b11df2366c77b67a9ac224ab1b38`, [Billing #73](https://github.com/Dimash313/Wexum/pull/73) `bff44a49fa024b2df4d87d4bf0ac557b3856bcd8` and [QA #74](https://github.com/Dimash313/Wexum/pull/74) `0404c3fa1d4f9023a1b03bb1e412c8555a4f0036`. All are Draft proposals; reported local tests do not establish active VPN protection, real vendor integration, or GitHub current-head CI.

Do not publish sensitive exploit detail, live secrets or user IPs in public PR comments.

## 7. Concrete next tasks on “Продолжаем дальше”

1. **Refresh GitHub first:** read `AGENTS.md` from integrated branch, or PR #1 if still unmerged; `docs/engineering/STATE.md`, `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/engineering/QUALITY.md`, `docs/policy/RELIGIOUS_REVIEW.md`; then this `HANDOFF.md`, issue #11, current #71, #1, #55, #64, #65, #66, #67 and other changed cross-lane PRs. Record exact heads and check any comments/decisions.
2. **Obtain current-head evidence:** run/re-run security directory **18** authored unit tests (previous 15 + 3 CLI cases) and compile check; capture commands, environment, exact commit SHA, outputs and any failures. Previous SHA parity and local tests are NOT proof for this changed source. Ask integrator to add required GitHub CI for owned security tests, without touching shared workflows directly.
3. **Review issue #2 fixes independently:** fetch corrected PR #55 when changed; verify scoped pagination/active visibility and SQLite outage normalization against PR #67 negatives, record security verdict and exact SHA, request owner/CTO fixes if still failing.
4. **Seek CTO review of [CROSS_LANE_CONTRACT_PROPOSAL.md](CROSS_LANE_CONTRACT_PROPOSAL.md):** approve or reject decisions D1–D8 before anyone implements shared grant/node/probe/identity interfaces. Independently inspect current Entitlements #3 / Nodes #4 source and tests for mismatched tenant, device, expiry, scope, freshness and nonce/replay properties.
5. **Verify SEC-OBS-001 and privacy requirements:** request #8 owner to run an explicit snapshot/render clock-rollback negative test; treat severity as preliminary. Obtain provider/observability data inventory and contractual logging/retention; draft allowlist/sanitization tests and deletion/restore scenarios, not unsupported “no logs” statements.
6. **Coordinate test-lab #10:** request real-device IPv4/IPv6/DNS/network-switch/permission-revocation results on exact client+node commits; do not mark gates attested from mocked status.
7. **Maintain issue #11/PR #71 and this file:** update findings, implemented components, real test evidence, blocker status, dependency URLs and handoff at each significant change; never merge or bypass independent audit.

## 8. References and communication

- [Security issue #11](https://github.com/Dimash313/Wexum/issues/11) and [our Draft PR #71](https://github.com/Dimash313/Wexum/pull/71).
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1), [independent audit #41](https://github.com/Dimash313/Wexum/issues/41), [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55), [negative CI PR #67](https://github.com/Dimash313/Wexum/pull/67).
- [Entitlements PR #64](https://github.com/Dimash313/Wexum/pull/64), [Node Registry PR #65](https://github.com/Dimash313/Wexum/pull/65), [Android PR #66](https://github.com/Dimash313/Wexum/pull/66).
- Proposed foundation instructions (PR #1 branch): `AGENTS.md`, `docs/engineering/STATE.md`, `docs/engineering/REVIEW_PROTOCOL.md`, `docs/vpn/ARCHITECTURE.md`, `docs/vpn/PRODUCT_REQUIREMENTS.md`, `docs/vpn/ENTITLEMENTS.md`, `docs/engineering/QUALITY.md`, `docs/policy/RELIGIOUS_REVIEW.md`.
- Our security docs: [README](README.md), [threat register](THREAT_MODEL.md), [authorization and keys](ACCESS_AND_KEY_SECURITY.md), [privacy and operations](PRIVACY_AND_OPERATIONS.md), [CTO decision proposal](CROSS_LANE_CONTRACT_PROPOSAL.md), [release manifest](release_gates.json).

**Operational rule:** GitHub issue/PR and repository documents, not an agent's previous assurances, determine current state. Use the existing branch and Draft PR until CTO directs otherwise; do not duplicate #11 work on a new branch without checking ownership.

## 2026-11-21 — automation security-gate verification checkpoint

- **One completed read-only verification:** re-fetched the current security manifest from the existing security branch (Git blob `c6410b7b238989039a9501e466fe59d0a1cc1da1`) and parsed its JSON directly. Observed **13/13 gates in `blocked` state**, `target_sha: null`, empty evidence arrays for every gate, and two open findings: `SEC-CTRL-001` (high) and `SEC-CTRL-002` (medium). This confirms that the recorded manifest does **not** claim release readiness; it is **not** an independent assessment of the underlying services.
- **PASS:** GitHub connector fetched and parsed the exact security manifest; all 13 declared gate records remain blocked. **FAIL:** container attempt to retrieve the raw GitHub Python sources returned `curl: (6) Could not resolve host: raw.githubusercontent.com` (environment DNS failure, not application test failure). **NOT RUN:** the 18 current-head Python security unit tests, compileall, release CLI and end-to-end VPN/privacy tests. **SKIP:** no source change or merge because code execution against exact GitHub source is unavailable and independent approval is outstanding.
- **Next step:** run `python -m unittest discover -s docs/vpn/security -p 'test_*.py' -v` and `python -m compileall -q docs/vpn/security` against a verifiably exact checkout, then exercise `gate_check.py --require-attested` (expected nonzero), record exact PR head and GitHub CI provenance. Do not promote metadata lint to a release gate. This checkpoint changes only the security-owned HANDOFF and does not resolve any release blocker.
