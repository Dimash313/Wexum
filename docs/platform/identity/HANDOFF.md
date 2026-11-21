# Wexum Identity & Authentication — engineering handoff

**Status checked:** 2026-11-21. **This is a working-lane handoff, not an integrated-state declaration or production approval.** GitHub is the live source of truth: refresh issue, PR, branch and CI state before acting. Update this file when material work or blockers change and before ending an engineering stage.

## 1. Lane, ownership and hard boundaries

- Lane: **Platform / Identity & Authentication**, owning GitHub issue **#34**.
- Owned implementation: `apps/platform/identity/`; owned documentation: `docs/platform/identity/`.
- Responsibility: user authentication *design* and trust boundaries, provider-neutral OAuth/OIDC authorization transaction safety, secure callback/pre-exchange primitives, related tests and threat analysis. Future sessions, revocation, membership, service grants and token validation need approved contracts and separate review.
- **Do not edit** shared Core (`src/wexum_core/`), VPN, other product areas, `docs/engineering/STATE.md`, `AGENTS.md`, global CI or other lanes' docs without CTO/integrator coordination. **Do not merge**, force-push, self-approve or deploy.
- Wexum Hub is not a superuser; products retain isolated data/permission boundaries. FileShape is separate and does not implicitly share Wexum accounts.
- This is not a deployed identity server, real OAuth login, token checker, or production-safe multi-node state store. Never infer authenticated user identity from a callback or `UnverifiedCodeExchange`.

## 2. Architecture and decisions already implemented in this lane

- Python 3.12+ **standard library only**; isolated and provider-neutral; no secrets, paid APIs, network calls, new infrastructure or shared API changes.
- `AuthorizationTransactions`: bounded process-local in-memory pending state, cryptographically randomized OAuth `state`, PKCE S256 verifier/challenge and OIDC `nonce`; SHA-256 state lookup and browser-session binding, atomic single-use consumption with a mutex, issuer/client/redirect and RFC 9207 callback `iss` binding, monotonic expiry (default 300 seconds, max 900), capacity (default 1024 total and `min(4,max_pending)` per browser session). Scoped removal of pending attempts for session rotation/logout; this **does not revoke the actual browser session**. Restarts lose pending state; multiple replicas are unsupported. Invalid/nonfinite/regressing monotonic-clock readings and unrepresentable expiry now discard pending attempts under the lock with `AuthorizationClockUnavailable`; this does not revoke real browser sessions.
- `callback.py`: strict untrusted code-response parser receiving already-decoded ordered parameter pairs, preserving duplicate occurrence for rejection; requires `state`, `code`, HTTPS `iss`, disallows OAuth error/mixed error-success, invalid/oversized/control fields.
- `exchange.py`: `prepare_code_exchange` composes callback parsing with atomic session-bound transaction consumption; returns an **unverified** code, held PKCE verifier and expected nonce with trusted issuer/client/redirect. It neither exchanges code nor verifies tokens.
- `transport.py`: raw byte URL/form decoding with duplicate preservation and invalid UTF-8/percent-escape rejection. Trusted response mode must be `GET/query` or `POST/form_post`; mixed transports, invalid content types, oversized raw input and malformed fields fail closed. This is **not an HTTP endpoint**, and the future adapter must enforce request-body/header limits before passing bytes.
- `webclient.py`: immutable `ConfiguredWebOAuthClient` groups trusted HTTPS issuer/client/redirect and browser response mode; composes start/prepare operations; rejects unsafe URL syntax. It does not prove a provider is approved. **Native-app redirect URI support is outside this browser-only draft**.
- Dataclass default `repr` redacts sensitive fields; this **does not** make direct access, network traffic, debugging, exceptions or telemetry safe.
- Threat model: `docs/platform/identity/THREAT_MODEL.md`. Existing foundation contract (proposed, unmerged): `docs/architecture/IDENTITY_AND_ACCESS.md`.

## 3. GitHub identifiers and current branches

- Main task: [issue #34](https://github.com/Dimash313/Wexum/issues/34) — **open**.
- Working branch: `feat/identity/34-pkce-transaction-boundary`.
- Working review: [Draft PR #62](https://github.com/Dimash313/Wexum/pull/62) — **open, unmerged**; stacked on foundation branch `architecture/foundation-and-agent-operating-system`.
- **Prior stable code head before clock fault fix:** `c9bca6f41d095f5fbe592e05cc1c2d4c40c48197`; later handoff-only head `76de9d8e803ec206ab0d6abbd5ca9fff63ff222a`. The clock change is in the same Draft PR; inspect fresh GitHub SHA rather than reusing either.
- Base foundation [PR #1](https://github.com/Dimash313/Wexum/pull/1) is **open and unmerged**, head observed `6b072ca12f79f7a45c2220253069e0ab34d27c2f`. Proposed combined foundation/audit [Draft PR #63](https://github.com/Dimash313/Wexum/pull/63) exists; it does **not** mean #1 was integrated into main.

## 4. Implemented components / exact owned files

- `apps/platform/identity/src/wexum_identity/transactions.py`: state, PKCE S256, one-time and session-bound pending store; fail-closed clock fault guard.
- `apps/platform/identity/src/wexum_identity/callback.py`: untrusted decoded callback pair parser.
- `apps/platform/identity/src/wexum_identity/exchange.py`: unverified pre-exchange handoff composer.
- `apps/platform/identity/src/wexum_identity/transport.py`: strict decoded raw HTTP query/form parameter boundary.
- `apps/platform/identity/src/wexum_identity/webclient.py`: immutable pinned browser OAuth settings.
- `apps/platform/identity/src/wexum_identity/__init__.py`: public exports.
- `apps/platform/identity/tests/test_transactions.py`, `test_callback.py`, `test_exchange.py`, `test_transport.py`, `test_webclient.py`, `test_clock_faults.py`: positive, negative, replay, session/client/issuer mismatch, expiry, concurrency and clock fault-injection checks.
- `apps/platform/identity/README.md`: local usage and explicit non-goals.
- `docs/platform/identity/THREAT_MODEL.md`: trust flow, threats, constraints and CTO decisions.
- This file: `docs/platform/identity/HANDOFF.md`. **All work is Draft PR work, not integrated main.**

## 5. Tests: executed evidence vs. missing evidence

**Prior recorded successful tests (not rerun with the clock change):**

```sh
PYTHONPATH=apps/platform/identity/src python -m unittest discover -s apps/platform/identity/tests -v
# 77 / 77 passed in a locally reconstructed byte-verified module mirror, Python 3.13
python -m compileall -q apps/platform/identity/src apps/platform/identity/tests
# passed for that mirror
```

- Composition: 21 transaction + 10 callback + 15 pre-exchange + 17 raw transport + 14 pinned web-client tests = **77**.
- PR #62 prior author evidence: 20 additional complete **77-test** repetitions passed in the local mirror; tests are not independent external approval.
- Published SHA-1 Git blobs for final new source/test at pre-handoff head were checked against exercised bytes:
  - `webclient.py`: `4b286e3d3b19e6c430c1bb7096799adac6611d9d`.
  - `test_webclient.py`: `ebdd6b8982679200c3531d6b354b9e5514745728`.
  - See [PR #62 test report](https://github.com/Dimash313/Wexum/pull/62#issuecomment-7058495386) for details and the other recorded blobs.
- **New targeted test evidence, 2026-11-21, local Python runtime:** `PYTHONPATH=apps/platform/identity/src python -m unittest discover -s apps/platform/identity/tests -v` on a focused mirror containing the byte-verified changed `transactions.py` and 7 new `test_clock_faults.py` methods: **7/7 passed**, and `python -m compileall -q apps/platform/identity/src apps/platform/identity/tests` passed. This **was not** a combined run of previous 77 tests; do not report 84/84 passed. Git object SHA matches the locally exercised files: updated `transactions.py` `8fb73beee5ee3a9d48b6af23bad0647305b213d8`, new `test_clock_faults.py` `8a320d475e02fd7b45927e8d7a3f65763d56f3aa`.
- **GitHub Actions on pre-clock-change head:** 0 check runs, 0 workflow runs, 0 statuses. Check latest SHA afresh; do **not** describe CI as green without evidence.
- **Not run / not built:** complete foundation checkout CI on Identity head; real HTTP/cookie/session tests; real OIDC provider, HTTPS network, code exchange, signed JWT/JWKS, tenant authorization, revocation, distributed replay tests or load/SLA measurements. A docs-only handoff commit does not change this evidence.

## 6. Known risks, audit and blocking dependencies

- Foundation PR #1 must be independently reviewed/integrated before consuming shared Core contracts; issue [#41 audit](https://github.com/Dimash313/Wexum/issues/41) raised corrective work [#57 / PR #58](https://github.com/Dimash313/Wexum/pull/58), [#59 / PR #60](https://github.com/Dimash313/Wexum/pull/60), CI [#61](https://github.com/Dimash313/Wexum/issues/61) and independent review settings [#38](https://github.com/Dimash313/Wexum/issues/38). Latest combined candidate PR #63 / CI must be assessed by integrator and independent auditor; **do not self-integrate**.
- [Independent Identity audit note](https://github.com/Dimash313/Wexum/pull/62#issuecomment-7058343622): static review of older `813fe0e` head was **INCOMPLETE / BLOCKED**; no independently executed suite or formal approval. Later `transport.py` and `webclient.py` changes need review against **their exact new head**, not inherited acceptance.
- Identity provider/issuer, RFC 9207 and response-mode support, OIDC discovery/JWKS/key rollover/token claim verification (signature/iss/aud/exp/nbf/nonce), token endpoint and algorithm policy, browser cookie/session rotation/revocation, recovery/MFA, authoritative memberships/tenancy, audit/privacy/retention/residency and native redirects require **CTO/integrator decisions**.
- Clock faults purge all pending attempts (fail closed), which can interrupt logins; actual session revocation, alerts and distributed clock/replay policy remain external. New exception `AuthorizationClockUnavailable` must be handled by upstream HTTP adapters as an untrusted, no-auth, retry-with-fresh-login condition.
- Process-local state loses valid attempts on restart, cannot handle multi-instance callback routing or cross-node replay; caller-supplied `browser_session` must come from trusted authentic server session middleware. `discard_pending_for_session` does not revoke a real session; caller must invalidate it.
- Callback parser and raw transport have strict feature/encoding policy and must be tested against approved provider; no public HTTP middleware has been audited.
- No deployment or user data migration; rollback: leave draft unmerged or close PR #62. No claim of a production login.

## 7. Specific next actions (resume without asking the owner to repeat context)

1. **Every new session / on “Продолжаем дальше”:** inspect actual GitHub branch/PR #62/issue #34 and comments, latest PR #1/#41/#63 and dependencies; read `AGENTS.md`, `README.md`, `docs/engineering/STATE.md`, `docs/architecture/SYSTEM.md`, `docs/architecture/BOUNDARIES.md`, `docs/engineering/QUALITY.md`, `docs/engineering/REVIEW_PROTOCOL.md`, `docs/policy/RELIGIOUS_REVIEW.md`, `docs/architecture/IDENTITY_AND_ACCESS.md`, this `HANDOFF.md`, threat model and current owned source/tests. Do not assume SHA or status is unchanged.
2. Request **fresh independent review of all current #62 changes** including the new transport/web-client layer; address any confirmed defects with narrowly scoped tests. Never self-approve.
3. Coordinate final-head CI coverage with integrator (#61 or an approved lane-scoped action); execute and report exactly what ran, including negative/security suites. No changes to global CI without approval.
4. In owned scope, rerun **all 84 module tests together** on byte-exact latest source and compare GitHub blobs, then extend trust-boundary tests and document browser-session rotation/revocation handshake and error ordering; treat untrusted callback code and the `UnverifiedCodeExchange` as unverified. Avoid implementing fake JWT verification or granting permissions.
5. Propose the **minimal approved interface** for provider allowlist, real OIDC/JWKS verifier, durable atomic state/session store and application-specific audience/scope/membership to CTO. Implement shared/production integration only after approval and foundation merge.
6. Re-run suite on exact candidate head, check CI/approval status; refresh this handoff after every material change, with accurate SHA, actual test counts, blockers and links. Keep PR in Draft until approved. No merges to `main`.

## 8. Reference links

- [Issue #34](https://github.com/Dimash313/Wexum/issues/34)
- [Draft PR #62](https://github.com/Dimash313/Wexum/pull/62)
- [Previous baseline code head](https://github.com/Dimash313/Wexum/commit/c9bca6f41d095f5fbe592e05cc1c2d4c40c48197); [Current Draft PR #62](https://github.com/Dimash313/Wexum/pull/62) resolves the newest head
- [Current lane threat model](https://github.com/Dimash313/Wexum/blob/feat/identity/34-pkce-transaction-boundary/docs/platform/identity/THREAT_MODEL.md)
- [Current module README](https://github.com/Dimash313/Wexum/blob/feat/identity/34-pkce-transaction-boundary/apps/platform/identity/README.md)
- [Foundation AGENTS.md](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/AGENTS.md)
- [Proposed identity architecture](https://github.com/Dimash313/Wexum/blob/architecture/foundation-and-agent-operating-system/docs/architecture/IDENTITY_AND_ACCESS.md)
- [Foundation PR #1](https://github.com/Dimash313/Wexum/pull/1) / [combined audit candidate #63](https://github.com/Dimash313/Wexum/pull/63)
- [Independent Identity audit](https://github.com/Dimash313/Wexum/pull/62#issuecomment-7058343622) / [latest Identity checkpoint](https://github.com/Dimash313/Wexum/pull/62#issuecomment-7058495386)

**Maintenance rule:** only this Identity lane's `HANDOFF.md` is maintained here; no modification of other lanes' documentation without CTO coordination. This handoff is a resumption index and must never override actual GitHub evidence or governance gates.
