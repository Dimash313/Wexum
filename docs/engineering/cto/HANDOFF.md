# Wexum CTO / Integrator — HANDOFF

**Snapshot:** 2026-11-21 UTC (refresh GitHub before using).  
**Role:** CTO / integrator; **Issue:** [#76](https://github.com/Dimash313/Wexum/issues/76).  
**Branch:** `docs/engineering/76-cto-operating-protocol`.  
**Draft PR:** [#77](https://github.com/Dimash313/Wexum/pull/77), stacked on unmerged foundation PR #1. **Do not merge or assume this file is in main.**

## 1. Responsibility and boundaries

Own repository coordination: shared architecture/contracts, integrator-owned `AGENTS.md` and `docs/engineering/`, CI integration proposals, issue/PR dependency tracking, review gates and truthful verification reports. Direct product-source ownership remains with its assigned team (VPN Control Plane #2, Nodes #4, etc.). Do not overwrite another agent's work. No direct changes to `main`, no self-approval or self-merge.

Permanent user instruction: when the owner writes **«Продолжаем дальше»**, inspect live GitHub, select the highest-priority actionable blocker and **perform** the next safe engineering step without asking the owner for PR numbers or distribution. Escalate only owner-authority decisions. Full rules: [CTO_OPERATING_PROTOCOL.md](../CTO_OPERATING_PROTOCOL.md).

## 2. Current architecture and decisions

- Wexum is a *planned* IhsanSoft ecosystem with 22 standalone products plus Wexum Hub. FileShape is a separate product; no Wexum app or VPN tunnel is released or operational.
- Root [foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) is still unmerged. The proposed contracts and GitHub Actions on its branch are not integrated into `main`.
- The integrator can construct isolated **CI-only** drafts targeting `main` to exercise stacked code; **never merge those duplicate foundation candidates** or treat them as authorized source integration. Actual intended code must be independently reviewed and adopted in the appropriate PR chain.
- GitHub Issues own work, Draft PRs own proposed code; review [AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md), [MULTI_AGENT.md](../MULTI_AGENT.md), [QUALITY.md](../QUALITY.md), [REVIEW_PROTOCOL.md](../REVIEW_PROTOCOL.md), and religious policy on their real current branch. `docs/engineering/STATE.md` describes **merged** work only.

## 3. Active CTO work items and branches

| Issue | Branch / PR | Purpose | Snapshot |
| --- | --- | --- | --- |
| [#76](https://github.com/Dimash313/Wexum/issues/76) | `docs/engineering/76-cto-operating-protocol` / [#77](https://github.com/Dimash313/Wexum/pull/77) | durable CTO rule and this handoff | draft, not merged |
| [#61](https://github.com/Dimash313/Wexum/issues/61) | `integration/61-foundation-audit-candidate` / [#63](https://github.com/Dimash313/Wexum/pull/63) | CI proof for source proposals #58 + #60 | `core`/CodeQL success on `e28194f`; DO NOT MERGE |
| [#56](https://github.com/Dimash313/Wexum/issues/56) | `integration/56-vpn-control-ci-candidate` / [#67](https://github.com/Dimash313/Wexum/pull/67) | reproduce two Control Plane SQLite defects | `core` RED on `ea88245`; CodeQL success |
| [#56](https://github.com/Dimash313/Wexum/issues/56) | `integration/80-node-registry-ci-candidate` / [#80](https://github.com/Dimash313/Wexum/pull/80) | test exact Node Registry #65 head + extra health replay regressions | `core` 28+22+3 tests and CodeQL **PASS** on candidate head `a1eb50b`; see logs below |
| [#38](https://github.com/Dimash313/Wexum/issues/38) / [#41](https://github.com/Dimash313/Wexum/issues/41) | foundation [PR #1](https://github.com/Dimash313/Wexum/pull/1) | independent review and governance | BLOCKED |

Repository baseline when this file was created: `main` `cc805a79b6dfc4e08e6866c1bc0653381755fb83`, unchanged; always refetch.

## 4. Completed/proposed artifacts

- [Issue #76](https://github.com/Dimash313/Wexum/issues/76) persists owner instruction immediately, even before PR merge. [PR #77](https://github.com/Dimash313/Wexum/pull/77) adds operating protocol and entry-point links in `AGENTS.md`, `README.md`, `AGENT_START.md` and `.github/copilot-instructions.md`. This HANDOFF is also proposed in that draft.
- Foundation fixes: [auth PR #58](https://github.com/Dimash313/Wexum/pull/58) handles invalid principal IDs; [catalog PR #60](https://github.com/Dimash313/Wexum/pull/60) validates catalog schema and pins the 22 existing ID/name identities. Their **exact source** was combined into CI-only PR #63, not into PR #1.
- [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55) remains unchanged at `66532b4`. PR #67 copies its seven product files unchanged and adds required `core` tests + four independent regression cases in integrator-owned test paths.
- [Node Registry PR #65](https://github.com/Dimash313/Wexum/pull/65) current inspected head `95145b5` contains generation-rotated health records and advisory selection revalidation. PR #80 copies its four files unchanged and adds three independent integration tests and required `core` job steps; no product-source edit was made by CTO.
- [Auditor handoff PR #79](https://github.com/Dimash313/Wexum/pull/79) and issue #78 are owned by the separate auditor lane. Do not edit auditor documents.

## 5. Tests actually observed (exact provenance)

| Evidence | Observed | Important qualification |
| --- | --- | --- |
| [PR #63 GitHub core #44872931012](https://github.com/Dimash313/Wexum/actions/runs/44872931012), `e28194f` | 28/28 Python tests, syntax, real catalog: PASS | CI-only foundation fixes candidate, not #1 head |
| [PR #63 CodeQL #44872931031](https://github.com/Dimash313/Wexum/actions/runs/44872931031), `e28194f` | SUCCESS | security scan ≠ independent signoff |
| [PR #67 core #44873727876](https://github.com/Dimash313/Wexum/actions/runs/44873727876), `ea88245` | 28/28 foundation + 20/20 existing VPN tests pass; **4 added tests fail** | 1 active device not listed after 200 revoked; 3 raw SQLite opening errors |
| [PR #67 CodeQL #44873727875](https://github.com/Dimash313/Wexum/actions/runs/44873727875), `ea88245` | SUCCESS | does not waive red core |
| [PR #80 core #44891614729](https://github.com/Dimash313/Wexum/actions/runs/44891614729), `a1eb50b` | **SUCCESS:** 28/28 foundation, 22/22 Node Registry, 3/3 independent health-replay regressions; syntax + catalog PASS | Verified full GitHub job log on test-only candidate; all four product files have identical Git blob SHAs to #65 |
| [PR #80 CodeQL #44891614667](https://github.com/Dimash313/Wexum/actions/runs/44891614667), `a1eb50b` | **SUCCESS** | CodeQL is not external review or proof of real gateway safety |
| [PR #77](https://github.com/Dimash313/Wexum/pull/77) | docs diff inspected only | stacked draft; zero current-head Actions when previously checked |

Author-reported local tests for #65 and other lane PRs are **not** independent or GitHub Actions evidence. The GitHub reviewer account in prior self-reported audit comments is the same account `Dimash313`; never treat these as distinct formal GitHub Approvals.

## 6. Blocking defects and dependencies

1. **HIGH triage, issue #2 / PR #55:** a LIMIT-200 oldest-device listing excludes newest active device after 200 revoked rows; raw `sqlite3.OperationalError` leaks from connection creation for enroll/list/revoke. Proven by four red tests in #67. Assigned Control Plane owner must fix in their own branch, update tests and signal new head. Re-copy exact blobs, rerun integrated tests and independent security review #11.
2. **Foundation review #41:** auditor technically confirmed fixes #57/#59 in combined candidate #63, but **PR #1 itself has not adopted them**. Need an accepted final merge candidate with latest-head checks. Do not merge PR #63 as workaround.
3. **Governance #38:** ruleset #27754912 last checked with **0 required approvals**, no distinct non-author formal approval. Admin/trusted reviewer action needed; owner-account comments cannot replace it.
4. **Node Registry #4:** an auditor reviewed PR #80 with byte-identical #65 source and confirmed the previous MEDIUM old-generation replay defect **resolved in the candidate**, with 53/53 tests and CodeQL success. Overall #65 remains blocked by external approval, trusted probe/management source, persistence and cross-lane interfaces. [GitHub Advanced Security inline finding](https://github.com/Dimash313/Wexum/pull/80#discussion_r4651871168) flags an unexplained `except StaleObservationError: pass` in **test-only** code; triage assigned back to owner #4 for source correction and new exact-head CI.
5. **Other dependent PRs:** i18n Runtime #50 had medium missing-`params` crash; design #42, i18n catalog #45 and storefront #52 have targeted audit findings. Many lane PRs lack executable current-head CI or trusted integration.
6. No deployed trusted Identity issuer, signed VPN permits, real gateway, network nodes, live native tunnel or operational security certification; no release claim is supported.

## 7. Next concrete tasks on «Продолжаем дальше»

1. **First refresh live GitHub**. CI for [PR #80](https://github.com/Dimash313/Wexum/pull/80) passed on `a1eb50b` (28+22+3 tests and CodeQL). Send evidence to owner issue #4, CI issue #56 and auditor #78/#41; require a **distinct** review before adopting the Node Registry source. Do not transfer this outcome to later source head changes without new checks.
2. Check issue #2 / PR #55 for a new repair head. If changed, compare source blobs, incorporate *only approved exact fix* into separate test-only candidate with same four negative regression cases, obtain full required `core` + CodeQL results, request non-author re-review. Otherwise do not spam duplicate comments.
3. Review audit disposition and reviewer identity for #41, and whether a distinct reviewer has actually been invited and approvals enforced under #38. Never self-approve or merge while blocked.
4. Track the newly reported Node Registry test-only CodeQL diagnostic and source owner #4 action, then request re-audit after revised #65 head. Keep this HANDOFF synced after material events, update PR #77 and request review; avoid documenting open PRs as integrated state.
5. Only then extend CI to other priority lane heads. No paid services or scope changes without owner authorization.


### CTO live verification at 2026-11-21 12:17 UTC

- New **active** hourly CTO automation was created from the current CTO chat, scheduled at minute **:55 Europe/Moscow** (first scheduled run 2026-11-21 15:55 +03:00). This is an external ChatGPT scheduler, not a GitHub Actions workflow; re-check actual automation state separately before relying on it.
- Live GitHub access confirmed with repository admin/write permission. Ruleset #27754912 remains active, but has **zero required approving reviews**. CTO clarified owner/admin acceptance criteria directly in [issue #38](https://github.com/Dimash313/Wexum/issues/38); adding an independent reviewer or changing saved ruleset remains uncompleted.
- Re-fetched current source heads: Control Plane [#55](https://github.com/Dimash313/Wexum/pull/55) `66532b4` (unchanged, P1 blockers), Node Registry [#65](https://github.com/Dimash313/Wexum/pull/65) `95145b5` (byte-identical to tested #80 product copy), QA [#74](https://github.com/Dimash313/Wexum/pull/74) `df1c9f9`, CI candidate [#67](https://github.com/Dimash313/Wexum/pull/67) `ea88245` (red core), Node candidate [#80](https://github.com/Dimash313/Wexum/pull/80) `a1eb50b` (core and CodeQL green). No code merges or VPN runtime tests performed in this CTO cycle.
- Priority order: **P1 #2 Control Plane blocker fixes** by code owner → rerun red #67 with exact corrected source; in parallel **P1 #38/#41** non-author approval and true foundation integration. **P2** cross-lane trusted health-probe/registration contracts for #4. Do not add duplicate comments while the source head is unchanged.


### CTO scheduled verification — 2026-11-21 12:55 UTC

- Read live AGENTS.md, architecture/quality/review/ethics contracts and this handoff; checked open PRs/issues and Control Plane/Node Registry heads. Control Plane PR #55 still `66532b4` with P1 failures reproduced by red PR #67; no owner fix or waiver.
- Node Registry source PR #65 advanced to `e91d734ac5306bf3605962078730f7746d235e3a`: owner replaced one test-only `except StaleObservationError: pass` with explicit `return` and refreshed its lane handoff. Source test blob is now `9279b96c26580ef0cd148082a3bad40d09bddf2e`; prior CI-only #80 had obsolete blob `b33c87ac9f12e775a0d6c7993fddf83d7e5aacb9`. No source PR #65 current-head CI statuses were reported.
- **Actual integration action:** synchronized exactly that one-line, owner-authored test cleanup into CI-only PR #80 branch `integration/80-node-registry-ci-candidate` via commit [`7e39bac`](https://github.com/Dimash313/Wexum/commit/7e39bacb19797f525deffcde65a505d931dc07bf). Product `registry.py` and all other files were untouched; candidate `test_registry.py` blob now equals #65 (`9279b96c`). **Do not merge #80**: duplicated foundation test candidate only.
- **Next:** check new PR #80 head Actions `core` (28 foundation + 22 Node Registry + 3 independent replay tests) and CodeQL, inspect actual logs, verify source blob identity and independent review at exact updated head. Old green runs #44891614729/#44891614667 were on earlier `a1eb50b` and do **not** certify the new test blob. Keep foundation #1 / #38 / #41 and Control Plane #2 blocked.

## 8. Related references

- [CTO operating protocol](../CTO_OPERATING_PROTOCOL.md), [Issue #76](https://github.com/Dimash313/Wexum/issues/76), [Draft PR #77](https://github.com/Dimash313/Wexum/pull/77)
- [Foundation issue #41](https://github.com/Dimash313/Wexum/issues/41), [PR #1](https://github.com/Dimash313/Wexum/pull/1), [Core PR #58](https://github.com/Dimash313/Wexum/pull/58), [Catalog PR #60](https://github.com/Dimash313/Wexum/pull/60), [CI-only #63](https://github.com/Dimash313/Wexum/pull/63)
- [VPN Control issue #2](https://github.com/Dimash313/Wexum/issues/2), [PR #55](https://github.com/Dimash313/Wexum/pull/55), [red CI-only PR #67](https://github.com/Dimash313/Wexum/pull/67)
- [VPN Nodes issue #4](https://github.com/Dimash313/Wexum/issues/4), [PR #65](https://github.com/Dimash313/Wexum/pull/65), [CI-only PR #80](https://github.com/Dimash313/Wexum/pull/80)
- [Security issue #11](https://github.com/Dimash313/Wexum/issues/11), [Auditor issue #78](https://github.com/Dimash313/Wexum/issues/78), [Auditor draft #79](https://github.com/Dimash313/Wexum/pull/79), [CI issue #56](https://github.com/Dimash313/Wexum/issues/56)

**This is a dated checkpoint, not a license to ignore fresher GitHub evidence.**


### CTO verification — 2026-11-21 13:55 UTC

- Re-read foundation-branch `AGENTS.md`, architecture boundaries, quality/review/ethics documents and open PR/issue queue. `AGENTS.md` is still not in `main`; PR #1 remains unmerged.
- Node Registry source PR #65 remains at `e91d734ac5306bf3605962078730f7746d235e3a`. CI-only PR #80 remains at `7e39bacb19797f525deffcde65a505d931dc07bf` with the synchronized owner-authored test cleanup.
- **New confirmed GitHub Actions result:** [foundation-checks #44906218376](https://github.com/Dimash313/Wexum/actions/runs/44906218376) completed **SUCCESS** and [CodeQL Python #44906218399](https://github.com/Dimash313/Wexum/actions/runs/44906218399) completed **SUCCESS** on PR #80 head `7e39bac`. Exact test counts on this head were **not** reverified from job logs in this cycle; prior 53-test log is for older `a1eb50b` only. These results are not source-PR #65 checks or independent approval.
- CTO left a new exact-head review request on [PR #80](https://github.com/Dimash313/Wexum/pull/80) for independent auditor to examine current #65/#80 SHA pair, CodeQL finding and residual trust boundaries. The review is requested, **not** completed.
- P1: Control Plane PR #55 still `66532b4` with four independently reproduced red tests in CI-only #67; owner must fix, then re-copy exact files and rerun required CI. Foundation #1, governance #38 and independent review #41 remain blocking. Do not merge any CI-only candidate or claim a live VPN tunnel.
- Next action: inspect actual logs for new #80 run and auditor verdict; follow up on owner repair for #55 without duplicating earlier comments. Keep product-owner files untouched.


### CTO verification — 2026-11-21 14:58 UTC

- Refreshed live open PR/issue queue and mandatory foundation-branch `AGENTS.md`, README, integrated STATE, SYSTEM/BOUNDARIES, QUALITY, REVIEW_PROTOCOL and RELIGIOUS_REVIEW. Root `AGENTS.md` is still absent on `main` (404); its instructions are present only on the unmerged foundation branch. No evidence supports treating draft code as integrated.
- [Control Plane PR #55](https://github.com/Dimash313/Wexum/pull/55) remains open/draft with no newer owner repair visible (last updated 2026-11-21 09:52:59 UTC). The four independent red regressions from [PR #67 core run 44873727876](https://github.com/Dimash313/Wexum/actions/runs/44873727876) remain P1 blockers. Do not mark them resolved or duplicate the existing owner-directed comments.
- [Node Registry PR #65](https://github.com/Dimash313/Wexum/pull/65) remains open/draft (last updated 2026-11-21 12:23:09 UTC). [CI-only PR #80](https://github.com/Dimash313/Wexum/pull/80) remains open/draft; its exact `7e39bacb19797f525deffcde65a505d931dc07bf` commit has two **completed SUCCESS** GitHub Actions: [foundation-checks #44906218376](https://github.com/Dimash313/Wexum/actions/runs/44906218376) and [CodeQL #44906218399](https://github.com/Dimash313/Wexum/actions/runs/44906218399). Test counts on this SHA were not independently re-read; prior 53/53 counts are from an earlier SHA. Neither CI-only PR #80 nor the unreviewed source PR #65 is authorized to merge.
- Checked [PR #80 discussion](https://github.com/Dimash313/Wexum/pull/80): most recent CTO request asks for independent exact-head audit of #65 `e91d734` against #80 `7e39bac`. No later auditor disposition appears in the retrieved discussion. [Auditor PR #79](https://github.com/Dimash313/Wexum/pull/79) remains draft, with no discussion comments returned. Comments posted under `Dimash313` are not independent formal non-author approvals.
- Priority remains **P1** Control Plane source fix by #2 owner, then exact-source integration CI and audit; **P1** foundation review/governance #38/#41; **P2** Node Registry trusted probe, persistence and cross-lane contracts. This checkpoint is a documentation-only CTO action; no product source edits, new test executions, PR merges or deployments were performed. Next: detect a genuinely new owner SHA or independent audit disposition before another review handoff; do not spam unchanged PRs.


### CTO verification — 2026-11-21 15:53 UTC

- Re-read foundation-branch `AGENTS.md`, README, STATE, SYSTEM, BOUNDARIES, QUALITY, REVIEW_PROTOCOL and RELIGIOUS_REVIEW; root `AGENTS.md` still returns 404 on default `main`. No open-PR code should be represented as merged baseline.
- Refetched live PR metadata: foundation #1 `6b072ca12f79f7a45c2220253069e0ab34d27c2f`; Control Plane #55 `66532b4df984c091b46e53697218b82557bb4bbd`; Node Registry source #65 `e91d734ac5306bf3605962078730f7746d235e3a`; CI-only candidate #80 `7e39bacb19797f525deffcde65a505d931dc07bf`; CTO handoff PR #77 `a614dda98e245560b233d201148da50079f7237b` (before this documentation commit). All remain open; #55/#65/#80/#77 remain drafts.
- Re-read PR #80 discussion: latest exact-head auditor request remains the CTO comment at 2026-11-21 13:54 UTC; no later independent disposition in retrieved comments. Prior reviewer discussion concerns older `95145b5`/`a1eb50b` heads and cannot be applied uncritically to newer heads. No formal independent approval established.
- **P1 unchanged:** Control Plane source head #55 has not advanced, so the four red regressions in #67 still block acceptance. Foundation #1 has not adopted validated remediation from #58/#60; governance #38/#41 still needs distinct approval and enforced rules. **P2:** Node Registry #65 still requires trusted-probe/management and cross-lane contract review despite green candidate #80 Actions at `7e39bac` (previously verified; not rerun in this cycle).
- **Action:** refreshed this CTO handoff only; no duplicate review requests or Issue/PR creations, no product code edits, no local tests, no new CI runs, no merges or deployment. Next: detect owner fix on #55 or new independent exact-head audit; then verify updated code and mandatory CI. If neither changes, continue checking high-priority shared integration contracts without spamming owners.


### CTO checkpoint — 2026-11-21 16:59 UTC

- Re-read live foundation-branch `AGENTS.md`, CTO protocol, quality/review rules, trust boundaries and ethical policy. Root `AGENTS.md` is still absent from `main` (404); all proposed governance remains unmerged.
- Rechecked current PR heads: foundation #1 `6b072ca12f79f7a45c2220253069e0ab34d27c2f`; Control Plane #55 `66532b4df984c091b46e53697218b82557bb4bbd`; Node Registry #65 `e91d734ac5306bf3605962078730f7746d235e3a`; CI-only #80 `7e39bacb19797f525deffcde65a505d931dc07bf`; CTO draft #77 before this checkpoint `dab189f680c12813763642127c1782247548b83d`. No changed source heads or new audit response were found in inspected PR #55/#80 discussions.
- Confirmed #55 still has the four red regressions demonstrated by [GitHub core run #44873727876](https://github.com/Dimash313/Wexum/actions/runs/44873727876); source repair remains P1 owner responsibility. The source head #65 still requires a distinct independent review despite successful CI-only #80 runs [#44906218376](https://github.com/Dimash313/Wexum/actions/runs/44906218376) and [#44906218399](https://github.com/Dimash313/Wexum/actions/runs/44906218399). The GitHub combined commit-status endpoint returned an empty legacy status list for #80; this is **not** a replacement for checking Actions/check-runs.
- Android source PR #66 `8b4474947861b2a22ebb86d721d24eb6c2e0423d` and QA PR #74 `df1c9f94f3a78d981e7de15e7efb7f1798d943eb` were sampled; integration issue [#68](https://github.com/Dimash313/Wexum/issues/68) remains the Android mandatory-CI tracking path. No new tests or live VPN trials were executed in this checkpoint.
- **Next actionable priority:** after the #55 owner supplies a new source SHA, compare exact product blobs against #67, rerun all four negative cases in required GitHub CI, then request non-author audit. In parallel, enforce independent approval for #1/#65 and review Android CI gap #68 without duplicating existing issues. Do not merge any candidate or edit product-owner code as CTO.
