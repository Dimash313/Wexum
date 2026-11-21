# Identity & Authentication — threat model and isolated implementation

Status: **Draft, unapproved, not production-ready.** Owner #34. Dependent on unmerged foundation PR #1, its independent audit #41 and CTO interface approval. No deployed account login or VPN access is implemented.

## User journey and trust/data flow

1. The server selects an approved OIDC issuer, client ID and exact redirect URI and binds the login attempt to a server-owned browser session. WexumVPN and Hub are separate clients. FileShape has separate identities and storage.
2. A future OIDC adapter redirects a browser to the trusted authorization endpoint with randomized state, nonce and PKCE S256 code challenge. The code verifier stays on the server.
3. On authorization callback, the server checks state against its server session binding, configured issuer/client/redirect and RFC 9207 authorization-response issuer (iss). This package atomically consumes the transaction before any token exchange. Failed exchange requires a fresh login attempt.
4. **Not implemented:** exchange code only at the configured provider token endpoint; validate OIDC ID-token signature against trusted JWKS, allowed algorithms, issuer, audience, time claims and nonce; map verified identity to an internal principal; rotate session on login; validate access token scope/audience/revocation and authoritative organization membership on every owning-product operation. Only then may the VPN issue an authenticated actor. Hub is never a shared superuser.
5. Cross-product sharing requires explicit scoped grants. Product databases are separate. Audit only justified administrative events with minimization, deletion policy and no raw tokens, credentials or traffic history.

The isolated package at apps/platform/identity/src/wexum_identity/transactions.py provides a bounded in-memory OAuth state/PKCE/nonce transaction, **not an identity service**. It hashes a high-entropy server browser-session binding and state lookup key, retains verifier/nonce until consumption or timeout, and uses a mutex for atomic single-use processing. Monotonic clock expiry defaults to 300 seconds (hard maximum 900); capacity defaults to 1024 pending attempts per process and the smaller of 4 or global capacity per browser session (atomic under the process lock). Restart loses pending attempts, failing closed; multiple service replicas require an approved shared atomic store. Pending attempts can be discarded atomically by trusted browser-session binding, but this never revokes the actual browser session: upstream must revoke/rotate that session and block fresh attempts against it. No user personal records, external APIs, secrets or paid dependencies are added.

**Caller obligations:** browser cookie is Secure, HttpOnly, appropriately SameSite, rotated after successful login, and protected by CSRF/XSS controls. Caller must supply trusted server-side issuer/client/registered redirect, not values from a request query. HTTP callback must reject duplicate/invalid parameters, unsolicited OAuth errors and oversized requests. The current component requires RFC 9207 iss; provider compatibility must be checked before choosing an issuer. In-memory verifier is sensitive and must not appear in telemetry, logs or debug dumps. Default dataclass `repr` hides state, nonce, PKCE verifier and stored session digest, but direct attribute access and serialized requests still expose values; redact at every caller/logging boundary.

## Threat assessment and acceptance checks

| Threat | Current scope and required next control |
| --- | --- |
| Login CSRF/session swapping | Server session binding + unguessable state; wrong browser negative test. Browser/HTTP cookie work pending. |
| PKCE downgrade/code interception | S256 code challenge, server-held verifier; provider must enforce code verifier and expiration. |
| Authorization-server mix-up | Configured issuer equals untrusted callback iss; provider discovery, HTTP parsing and token endpoint binding pending. |
| Replay/parallel callbacks | Mutex and one-time state consumption; 12-thread race test requires exactly one winner. Distributed replay store pending. |
| Cross-tenant and cross-app access | Wrong client/redirect rejected locally; authoritative membership/scope/audience adapter and integration tests pending. |
| JWT signature/key confusion/JWKS rollover | No JWT acceptance implemented; audited standards-compliant OIDC token verifier, key rollover and unknown-kid policy pending. |
| Stale sessions/recovery/MFA/credential stuffing | Provider, rotation, revocation, MFA, rate-limits and account recovery require architecture approval. |
| Flood of login starts | Per-process capacity, per-browser-session capacity and TTL fail-closed; distributed throttling, proxy/app IP controls, bounded HTTP size and capacity/load measurements pending. |
| Crash and partial outage | Unknown or expired state denied, fresh login required. Real product session outage policy and alerting pending. |
| Personal-data leakage | No stored email/password/organization membership. Logs must exclude codes, state, verifier, nonce, session IDs and VPN destinations. Retention/deletion policy still open. |

## Proposed measurable acceptance targets (not measured SLA)

The local component: validate S256 proof against verifier; unique state/nonce, one-time callback; deny invalid state/session/issuer/client/redirect, expiry and replay; preserve valid attempt after unrelated mismatches; support scoped pending-attempt discard on session rotation, deny replay and keep other sessions intact; recover global and per-browser capacity after consumption/expiry; concurrent starts cannot bypass per-session cap; fail closed on restart; one winner under concurrent callbacks. Run:

    PYTHONPATH=apps/platform/identity/src python -m unittest discover -s apps/platform/identity/tests -v
    python -m compileall -q apps/platform/identity/src apps/platform/identity/tests

For a future full service, measure p95 handshake start/callback latency, failure/retry rates, memory growth, cross-node replay behavior, JWKS rotation, revocation propagation delay, account recovery abuse, HTTP CSRF and identity/deletion audits. Define tenant policy budgets from product usage before signoff. No availability or security guarantee is claimed.

## CTO/integrator decisions and issue-owned lanes

- **This PR:** provider-neutral temporary transaction store with tests; no shared contract change.
- **Architecture approval:** chosen issuer/OIDC provider, RFC 9207 compatibility, native redirect registration, recovery/MFA, token/session TTL, audit retention and privacy residency, accessibility and local laws.
- **Follow-up identity issue(s):** verified token exchange and OIDC/JWKS adapter, server sessions/refresh/revocation, user/organization membership authority, constrained service tokens and audited principal constructors.
- **Cross-domain proposal to CTO:** product-specific audience/scope and VPN AuthenticatedActor adapter, Core contract, shared CI, multi-replica atomic state store. No edits to src/wexum_core, VPN code or common API until approved.

Costs: zero new runtime dependencies or services for this isolated prototype; future OIDC provider, transactional session storage, HA, email/MFA and operational costs remain unresolved. Failure mode: deny new logins on full/expired/unknown state; never grant identity by assumption. Rollout: **none**. Rollback: close the unmerged Draft PR or omit this isolated module from assembly. Religious/ethical review: no media, betting, interest-bearing financial feature or social discovery added; future tracking and identity sharing need independent privacy and ethical review, not an unsupported religious certification.

## Strict callback parameter boundary (isolated draft)

`apps/platform/identity/src/wexum_identity/callback.py` accepts only a bounded sequence of already decoded `(name, value)` pairs. It rejects duplicates (including unfamiliar extensions), malformed shapes, control characters, excessive input, OAuth errors and code/error ambiguity; success requires a nonempty `code`, `state`, and RFC 9207 HTTPS `iss` with no query/fragment. Returned state and code are hidden from default repr, not from direct access or logging. The parser **does not** consume state, validate issuer against the trusted stored issuer, exchange tokens or authenticate; caller must call the existing transaction consume method with trusted server configuration before exchanging the untrusted authorization code.

**HTTP integration boundary remains unimplemented:** select exactly one approved response mode and transport (query or form body), reject duplicate parameters across transports, preserve duplicate parameter occurrences when decoding, reject ambiguous/invalid encodings, bound network request size before decoding and never log callback secrets. Verify RFC 9207 issuer exactly against provider metadata as part of the existing state transaction. Native-app and full OIDC JARM/form-post policies remain CTO decisions. Standards references: https://www.rfc-editor.org/rfc/rfc6749.html and https://www.rfc-editor.org/rfc/rfc9207.html. No public HTTP endpoint is added.

## Composed callback-to-PKCE handoff (local-only boundary)

The isolated `exchange.py` composes the strict authorization-response parser and atomic, browser-session-bound `AuthorizationTransactions.consume`. Only a callback containing a valid unique code/state/iss can reach the one-time state consumption. Returned `UnverifiedCodeExchange` carries code, verifier, expected nonce and *trusted* issuer/client/redirect for a later token-verification adapter. It is **not authenticated**, and no HTTP endpoint, token request, JWT verifier, session cookie, user account or VPN permission is created. After a successful consume, any exchange failure requires a new authorization attempt; a malformed callback does not destroy the valid attempt. Tests cover replay, parameter ambiguity, cross-browser, cross-client, mix-up issuer, expiration, session discard and concurrency. Network transport and size enforcement, token endpoint trust, JWKS/algorithm selection, token claims and revocation still need separate CTO approval and independent audit.
