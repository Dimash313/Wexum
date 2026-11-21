# Wexum Identity: isolated OAuth transaction building block

**Prototype only.** No login service, token acceptance, organization membership, HTTP endpoint or production security assurance. Issue #34; independent of Wexum Core/VPN code and of the unmerged foundation integration.

Python 3.12+ / stdlib only. Run the local tests from the repository root:

    PYTHONPATH=apps/platform/identity/src python -m unittest discover -s apps/platform/identity/tests -v
    python -m compileall -q apps/platform/identity/src apps/platform/identity/tests

AuthorizationTransactions.begin(...) returns state, nonce, code_challenge and S256 for trusted server-side OIDC authorization initiation. The caller must provide a server-owned browser session binding and configured issuer/client/redirect. consume(...) requires the same trusted binding/configuration and matching authorization-response issuer (iss under RFC 9207), and yields server-only PKCE verifier and expected ID-token nonce once. It **does not** validate token responses. Do not create an authenticated actor from these values. Tokens, scopes, membership and sessions require independently reviewed implementations.

The store is process-local and intentionally loses outstanding attempts on restart; do not run multi-replica callback routing with this implementation. Capacity and expiry are bounded. Consult docs/platform/identity/THREAT_MODEL.md before integrating; requests for shared API changes go to the CTO/integrator.
