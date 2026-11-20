# Wexum identity and access architecture

Status: **proposed** — implementation requires issue #34 threat review and interface approval. No deployed identity server exists.

## Identity boundary
- One Wexum account can access independently usable Wexum products. FileShape remains a separate product and does not inherit Wexum identity or accounts.
- Public clients must authenticate through a trusted issuer. Never accept client-provided `user_id`, organization membership, roles or scopes as authority.
- Product services must validate token signature, issuer, audience, expiry, not-before and revocation policy, then authorize the exact resource action within its tenant.
- Prefer a standards-compliant OpenID Connect implementation, Authorization Code + PKCE for public clients and platform-backed passkeys when eligible. Do not invent cryptography or custom authentication protocols.
- Use per-service short-lived tokens with narrow audiences and scopes. Browser sessions require secure HttpOnly cookies, CSRF and XSS defenses appropriate to the chosen architecture.
- MFA for privileged operations, strong recovery with abuse/rate-limit protections, and no indefinite session tokens. Avoid SMS as the only administrative recovery mechanism.

## Product permissions
- An authenticated user may have personal resources, many organization memberships and product-specific entitlements. None implies cross-product access.
- `authorize` in `src/wexum_core/authorization.py` is a **pure, illustrative policy contract**. It is not authentication, token verification, trusted membership loading or a production authorization service.
- Authoritative membership and revocation state are maintained by an owning service. Cache policies must specify staleness limits; sensitive operations fail closed on indeterminate decisions.
- A product may call another product only with scoped service-to-service authentication and an explicit consent or organizational authorization. Hub is an optional UI client, not a superuser.
- Store audit trails of *administrative actions* without passwords, raw tokens, private documents or VPN destinations.

## Failure and revocation semantics
- New login and privileged grants may fail if Identity is unavailable; existing product sessions can continue only within valid local token expiry and documented risk budgets.
- Disable/revoke devices, rotate compromised keys and support emergency expiry/re-authentication flows.
- Offline or cached permissions must not create uncontrolled indefinite access; sensitive revocations require shorter bounds or online checks.
- Clock skew tolerance, token refresh, device theft, account deletion and multi-tenant migrations need explicit integration tests.

## First acceptance gate
1. Threat model for account takeover, cross-tenant authorization, stale membership, session fixation, replay, credential stuffing and account recovery abuse.
2. Contract tests for issuer/audience/expiry/claims and negative authorization under mismatched tenants.
3. Reproducible key rotation and revocation test cases, including partial outages.
4. Data ownership/deletion plan and audit event minimization; legal/privacy review.
5. Document latency, availability, limits and safe failure modes before production integration.

Unresolved: OIDC provider, storage residency, recovery factors, service authentication, token lifetimes and emergency revocation design. These are decisions to review, not existing features.
