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

### Current-head CI evidence checkpoint — 2026-11-21 (22:25 Moscow)

- **Single P1 verification task:** queried GitHub PR #71 live: head `c0983a50fe484af17c76cb587e175e8665596570`, Draft/open, base `main`. GitHub connector returned **0 PR-triggered workflow runs** and **0 legacy combined commit statuses** on that exact SHA. The workflow-run API is PR-event filtered and the combined-status API does not cover every Check Runs API result; therefore this is **not proof that every possible GitHub check is absent**, and is certainly not test PASS.
- **PASS:** connected GitHub read, exact PR head retrieval, source blob read of `gate_check.py` (`c162393e40c2743b48afbdce758363bf6ad3a5cb`), `test_gate_check.py` (`c54f653ec3921873b3d95025e4327a3e7d094d8d`), manifest (`c6410b7b238989039a9501e466fe59d0a1cc1da1`); reviewed proposed `AGENTS.md` on unmerged PR #1 and QA #74 / Observability #72 HANDOFFs.
- **NOT RUN:** all **24 authored Python unittest methods**, Python `compileall`, actual VPN/DNS/IP tests, independent evidence verification. Source read is not execution. **SKIP:** merge, self-approval, and edits to integration-owned workflows.
- **Blocker and action:** #56 / CTO must create an exact-source, mandatory CI candidate for Security PR #71 with `python -m unittest discover -s docs/vpn/security -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/security`, and negative `python docs/vpn/security/gate_check.py --require-attested` (expected nonzero). Attach full job URLs, source SHA and counts; independent reviewer #41 must evaluate before integration. Existing #56 escalation already covers this; do not spam duplicate comments.
- No changes to code or release-gate status. 13 gates remain `blocked`; `SEC-CTRL-001` HIGH and `SEC-CTRL-002` MEDIUM remain `open` in manifest. No operational VPN or release clearance.

## 5. Test and review evidence — distinguish observed from reported

**Security negative-test expansion — 2026-11-21 (subsequent cycle):**
- Selected one P2 hardening task in owned `docs/vpn/security/` after reading live repo, PR #71/#74/#72/#1, issue #11/#41, foundation AGENTS.md and QA/Observability handoffs.
- Added **three** stdlib unittest regressions to `test_gate_check.py`: non-object evidence record, duplicate verification masquerading as independent review, and insecure HTTP evidence URL. Total **21 authored tests** (18 prior + 3); these assert metadata rejection only, not external proof of safety.
- GitHub commit [`8c1fe6cd8fdd3fcc873939794bd0d4f856f6f369`](https://github.com/Dimash313/Wexum/commit/8c1fe6cd8fdd3fcc873939794bd0d4f856f6f369); test file blob `c56ee68248b12dfd1ae228648bef41ea78e925ae`. Re-fetched exact prior blob before writing; only this owned file changed in that commit.
- **PASS** GitHub API read and SHA-guarded write; **FAIL** attempted direct `git ls-remote` from local container (DNS cannot resolve github.com, environmental access failure); **NOT RUN** all 21 Python tests, `compileall`, and current-head GitHub Actions verification; **SKIP** real VPN/OS leak testing and merge. Do not imply test PASS. Re-run against exact current PR head through CI or a container with source access.
- Existing HIGH `SEC-CTRL-001` and MEDIUM `SEC-CTRL-002` remain recorded as unresolved in `release_gates.json`; this cycle does not modify another team's Control Plane. All 13 release gates remain blocked.
- Next task: obtain exact-head CI execution of the 21 security tests via CTO-owned workflow, then verify negative cases and independent review. No self-approval or merge.



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

## 2026-11-21 — evidence URL authority hardening (one P2 cycle)

- Read live repository and open Issues/PRs, foundation-branch AGENTS.md, and Security/QA/Observability handoffs. Root main AGENTS.md remains absent because foundation PR #1 is unmerged. No independent release approval.
- In owned `gate_check.py`, strengthened submitted evidence URL metadata validation: require HTTPS with nonempty hostname; reject embedded userinfo credentials, control characters, invalid URL authority/port and explicit port zero. This is a metadata safeguard, **not** evidence authenticity, DNS or TLS verification.
- Added one parameterized negative unittest method (six malformed URL cases) in `test_gate_check.py`; total 22 authored test methods. Source commit `afeb75e6c19e9b0a60a139de73425ce73b7ba1e6`, test commit `c3dc4f592a3cdbca5e6858750ecbfe07f515c35b` in Draft PR #71.
- **PASS** GitHub connector read, guarded file writes with current blob SHAs and post-write commit confirmation. **NOT RUN** Python unittest, syntax compile, exact-head Actions checks and live VPN testing in this run. **SKIP** merge/independent signoff. 13 gates remain blocked; existing SEC-CTRL-001 HIGH and SEC-CTRL-002 MEDIUM remain unresolved.
- Next: execute `python -m unittest discover -s docs/vpn/security -p 'test_*.py' -v` and `python -m compileall -q docs/vpn/security` on exact PR #71 head in mandatory CI, independently review URL semantics, then obtain external evidence. Do not treat local metadata acceptance as security approval.

## Security cycle — 2026-11-21: ambiguous HTTPS authority

- **One scoped P2 security hardening task:** metadata evidence URL authority ambiguity. Python `urllib.parse.urlsplit` can interpret a backslash-containing URL differently from other URL consumers; e.g. `https://example.test\\@evil.test/proof` reports hostname `evil.test`. The metadata-only linter must reject such input, not normalize or trust it. This is input-validation defense in depth, **not evidence of a deployed exploit**.
- Changed only owned `docs/vpn/security/gate_check.py` and `test_gate_check.py`: reject any backslash in evidence URL and add a negative unittest method with two backslash ambiguity cases. The original 22 test methods become **23 authored methods**; no release gate is marked passed.
- GitHub commits: [validator](https://github.com/Dimash313/Wexum/commit/a27208b1951e4a05710036946cab7beee6e9563e), [regression test](https://github.com/Dimash313/Wexum/commit/3282fda3b2b482f11daea921c52471f57e40abd2). Exact GitHub blobs after write: validator `b433ffc35618ea9ec3b73386458cf6ce3afc6c8f`, test `d3e873ad8f91d302c3d7f975e6ab28040aaaf2c4`.
- **PASS:** GitHub current file read, SHA-guarded updates, local standard-library URL parser ambiguity reproduction. **NOT RUN:** complete 23-method unittest suite, Python compileall and exact-head GitHub Actions (no verified CI run). **SKIP:** live VPN leak testing, release approval and merge. Re-fetch current PR head and run full suite in controlled checkout/mandatory CI before any integration.
- Main AGENTS.md remains absent because foundation PR #1 is unmerged; read proposed AGENTS.md from #1 head. QA handoff is at `tests/vpn/HANDOFF.md` on PR #74 and Observability handoff at `products/vpn/observability/HANDOFF.md` on PR #72; both are separately owned. Current security PR remains Draft #71. Existing 13 release gates blocked; SEC-CTRL-001 and SEC-CTRL-002 remain open.


## Exact-head CI evidence checkpoint — 2026-11-21 19:28 Europe/Moscow

**Single P1 verification task:** confirm whether the current security evidence-gate test suite has actually run on PR #71 head, before any claims of validation or integration.

- Fetched live [PR #71](https://github.com/Dimash313/Wexum/pull/71): head `01c810d781c869a2c8c0de6333ad9f5a5d600ddb`, Draft, base `main`.
- GitHub Actions PR-triggered workflow runs for this **exact head**: **0** returned by GitHub connector. Legacy combined commit status contexts: **0**. These endpoints do not prove absence of all possible external checks, but provide **no CI evidence** for the current SHA.
- Latest security tests in the PR diff contain **23 authored unittest methods**; no exact-head test execution is substantiated. Earlier local test counts are historical, not current-head proof.
- **PASS:** live repository, PR metadata, handoff and proposed foundation AGENTS.md read; exact-head workflow/status queries completed; SHA-guarded HANDOFF update.
- **FAIL:** none of the test assertions executed in this checkpoint.
- **SKIP:** cross-lane CI workflow edits (CTO/integrator ownership); merge and release (independent review and required checks absent).
- **NOT RUN:** `python -m unittest discover -s docs/vpn/security -p 'test_*.py' -v`, `python -m compileall -q docs/vpn/security`, real VPN/DNS/IP leak tests.
- **Blocking action for CTO/integration:** arrange required GitHub Actions execution of the 23 security unittest methods and compileall on a reviewed integration candidate containing this exact security commit; link the workflow run and logs, then obtain non-author review. Until then release gates remain blocked and PR #71 must remain Draft.
- No changes to other teams' files or workflows; this is a documented CI-evidence check, not a claim of a passing test suite.


## 2026-11-21 — P1 exact-head Security CI escalation (single-cycle handoff)

- **Source of truth:** [Security Draft PR #71](https://github.com/Dimash313/Wexum/pull/71) inspected at head `62eb3da68276a77be03a3e08d1c14c09d629080a`; `docs/vpn/security/gate_check.py` blob `b433ffc35618ea9ec3b73386458cf6ce3afc6c8f`; `test_gate_check.py` blob `d3e873ad8f91d302c3d7f975e6ab28040aaaf2c4`. No sibling-owned files changed.
- **One P1 task:** verified absence of PR-triggered GitHub Actions runs (0) and combined commit statuses (0) on that exact head, then sent [actionable CTO/integration handoff to issue #56](https://github.com/Dimash313/Wexum/issues/56#issuecomment-7066492719). This is an **evidence gap**, not a test failure or VPN exploit.
- **PASS:** live GitHub repository/PR read; owned file blobs fetched; QA and Observability HANDOFFs reviewed; existing integration issue/comments checked; comment posted to existing issue #56, avoiding duplicate issue/PR. **FAIL:** direct local GitHub git fetch blocked by DNS `Could not resolve host: github.com`. **NOT RUN:** 23 authored Security unit methods, `compileall`, exact-source runtime CLI, OS VPN leak tests. **SKIP:** cross-lane workflow edits, independent approval and merge.
- **Next step for CTO/integrator:** prepare a safe main-targeting candidate with exact Security file blobs, run the 23 tests and compile, assert `gate_check.py` default lint exits 0 and `--require-attested` intentionally exits 1; record Actions run/job URLs, SHA equivalence, actual counts/logs. Recheck current PR head before using this snapshot. This document update itself advances the head and does not confer CI evidence on the new commit.
- **Release posture:** Draft/unmerged; 13 mandatory gates remain blocked and existing HIGH/MEDIUM findings unresolved. CI is not a substitute for external independent audit or authentic evidence.

## 2026-11-21 — whitespace-padded HTTPS evidence URL hardening

- **Scope:** one P2 defensive parser-hardening cycle, exclusively in `docs/vpn/security/`. Python `urllib.parse.urlsplit` may strip leading ASCII whitespace; evidence URLs must not be silently normalized. Reject leading/trailing whitespace before parsing, without interpreting metadata validation as external proof.
- Validator commit: [b9f67213](https://github.com/Dimash313/Wexum/commit/b9f672131f9d6e63daeaaeadda45b6970a19f60a), blob `c162393e40c2743b48afbdce758363bf6ad3a5cb`.
- Regression commit: [3f6f3018](https://github.com/Dimash313/Wexum/commit/3f6f30184723a760045f46531c4cd9ada3aac7fb), blob `c54f653ec3921873b3d95025e4327a3e7d094d8d`. Added one negative unittest method with three whitespace-padded HTTPS inputs; **24 authored test methods** total.
- **PASS:** GitHub SHA-guarded writes and exact-file re-fetch; **NOT RUN:** Python unittest, compileall, Actions at new HEAD; **SKIP:** real VPN leak testing and merge. No CI or independent review claimed.
- **Issue/branch/PR:** [#11](https://github.com/Dimash313/Wexum/issues/11), `feat/vpn/11-security-review`, [Draft #71](https://github.com/Dimash313/Wexum/pull/71). Existing findings SEC-CTRL-001/002 and all 13 release gates remain unresolved. Next: obtain current-head CI with all 24 methods and external independent review; integration workflow owned by CTO.


### CI evidence recheck — 2026-11-21 23:25 Europe/Moscow

- **One P1 verification cycle:** GitHub Actions commit-run query for previously recorded PR #71 head `edfe4c23f980c1a5f7c87bc926a4aa3db4698509` returned **zero PR-triggered workflow runs**. The API is PR-event filtered and first-page limited; it does not prove the absence of all check runs or other event types. No test PASS is inferred.
- **PASS:** connected GitHub read of Security validator and its 24 authored tests; GitHub commit-run query completed; existing integration blocker [#56](https://github.com/Dimash313/Wexum/issues/56) checked open, with 5 comments, so no duplicate issue or repeated escalation created.
- **NOT RUN:** 24 Python tests, compileall, exact-source runtime checks, VPN/DNS/IP leak tests, independent review. **SKIP:** merge and modifications to integration-owned workflows.
- **Blocker:** mandatory exact-candidate CI evidence remains unavailable for the queried commit. Integration owner #56 must supply job URLs, tested SHA and results; verify the actual current PR head and all check types before release decisions. This checkpoint does not claim that the previously recorded SHA is still current.
- **Repository visibility limitation:** root `AGENTS.md` returned 404 on default branch; QA and Observability HANDOFF paths attempted in this cycle were not found on the Security branch, and guessed independent branch refs returned 404. Their exact PR head refs must be resolved live before claiming a complete cross-lane review.


### 2026-11-22 — Security URL evidence syntax regression (P2)

- Scope: issue #11 / Draft PR #71, exclusively `docs/vpn/security/`; no changes to sibling lanes or shared CI.
- Finding: `urllib.parse.urlsplit('https://example.test:/proof')` yields hostname `example.test` and `port=None`, so the prior evidence URL predicate accepted an explicitly empty port. This is a metadata validation ambiguity, **not** evidence of a deployed VPN vulnerability.
- Fix: reject `parsed.netloc.endswith(':')` in `gate_check.py`; add `https://example.test:/proof` to negative evidence URL regression cases in `test_gate_check.py`.
- Source commits: [72947384](https://github.com/Dimash313/Wexum/commit/72947384ed744995975edd3ff0b681fdc458c4db) and [d04951aa](https://github.com/Dimash313/Wexum/commit/d04951aa5e1153d2c9475daf50e10a77e9f8899b).
- **PASS**: isolated Python 3.13 reproduction verified the old predicate accepts the malformed URL and the revised predicate rejects it; GitHub accepted source and test updates using current blob SHAs.
- **NOT RUN**: full Security unittest suite, compileall, real VPN/DNS/IP checks and current-head GitHub Actions; this isolated reproduction is not a substitute for those checks.
- **SKIP**: merge and independent approval; PR remains Draft and release gate must remain closed.
- Follow-up: run full Security suite and `python -m compileall -q docs/vpn/security` on an exact integrated candidate SHA; attach required CI run/check links and independent review before merge. Existing release blockers and Security findings remain unresolved pending fresh external evidence.

## Security cycle — 2026-11-22 UTC: C1 control-character URL hardening

- **Scope / priority:** one P2 metadata validation hardening task in owned `docs/vpn/security/`, issue [#11](https://github.com/Dimash313/Wexum/issues/11), Draft [PR #71](https://github.com/Dimash313/Wexum/pull/71), branch `feat/vpn/11-security-review`. No cross-lane implementation or merge.
- **Finding:** the old evidence URL predicate rejected C0 controls and DEL but not Unicode C1 controls U+0080–U+009F. Python `urlsplit` accepts `https://example.test/proof` followed by U+0085 or U+009F as an HTTPS URL; different downstream consumers may normalize control characters differently. This is a metadata-consistency hardening issue, **not evidence of VPN exploitation**.
- **Fix:** `gate_check.py` rejects codepoints 0–31 and 127–159. `test_gate_check.py` adds one unittest method with two negative subtests (U+0085, U+009F), using `chr()` to ensure real codepoints, not literal backslash escape sequences. 25 authored test methods now (previous 24 + 1).
- **GitHub commits:** [validator c3d7c764](https://github.com/Dimash313/Wexum/commit/c3d7c764a6dcb4926b36553a3a46dabc88242a5e), [test 59e06bac](https://github.com/Dimash313/Wexum/commit/59e06bac7e0849d5e8801c0b81406fc0ad692a3e), [test correction d8034a08](https://github.com/Dimash313/Wexum/commit/d8034a0832c2da28698e110d88e455150f3a120c). SHA-guarded GitHub contents writes, exact-file re-fetch after correction.
- **PASS:** local Python standard-library reproducer showed `urlsplit` accepts both C1 URLs while the new predicate rejects both; normal HTTPS URL remains accepted by predicate. **NOT RUN:** full 25-test suite on exact GitHub checkout, `compileall`, current-head GitHub Actions/Check Runs, real VPN/DNS/IP leak tests. **SKIP:** merge, self-approval and shared workflow changes.
- **Blockers:** foundation PR #1 remains proposed, issue #56 integration CI, independent audit #41, 13 blocked release gates and SEC-CTRL-001/002 remain. Recheck live PR head and run exact-source CI; do not infer release safety from metadata tests.

## Security checkpoint — 2026-11-22: Unicode format controls in evidence URLs

- **Single scoped task (P2):** Python urllib.parse.urlsplit accepts HTTPS paths with U+202E bidi override; prior URL validation rejected C0/C1 controls but not Unicode Cf format characters. This is metadata/link-display ambiguity, not evidence of a working VPN exploit.
- **Source change:** gate_check.py rejects Unicode Cf characters in evidence URLs; test_gate_check.py adds one negative method with U+202E, U+2066 and U+200D. Code commit: https://github.com/Dimash313/Wexum/commit/6d6abb4a0c3f831e3e538ceb098afe6ff7fe2160 ; test commit: https://github.com/Dimash313/Wexum/commit/508caeb15f8a93d5917ae768a1c02282674a0220
- **Evidence:** local Python urlsplit accepted U+202E in path (PASS reproduction). GitHub writes used current blob SHAs. Full 26-method unittest, compileall and Actions NOT RUN. Direct git checkout FAIL due to DNS: Could not resolve host github.com.
- **Blockers:** PR #71 draft; foundation #1 and Control Plane #55 unmerged; SEC-CTRL-001/002 unresolved; 13 release gates blocked. No shared CI or other lane files changed. Next: exact-head security tests + compileall in required CI, then independent audit.
