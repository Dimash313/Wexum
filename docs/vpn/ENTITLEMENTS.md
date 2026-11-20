# WexumVPN entitlement and node access contract

Status: **proposed** — design input for issue #3, #2, #4, #9 and #11. No real signed permits or VPN node access enforcement is deployed.

## Trust boundaries
- Billing provider → Billing adapter → entitlement authority → VPN control plane → VPN node. Payment claims or client fields are never trusted directly.
- Signed grants are minted only after authenticated, tenant-scoped, authoritative entitlement checks. Verification lives in an isolated VPN node component.
- No per-packet calls to Wexum Core. Node verifies a bounded local authorization grant without reading payment tables, private user data or unrelated products.
- Hub may show subscription/device status but must not be the trusted issuer or VPN tunnel owner.

## Minimal permit claims (subject to security approval)
- Opaque permit ID and replay/session binding where needed.
- Subject and tenant identifiers with separate, opaque device identifier.
- Issuer, intended VPN-node audience, scope, issued-at, not-before, expiry and signing key ID.
- Scope restricts permitted operations and regions/capabilities where applicable.
- No browsing history, destination hostnames or payment card data in permits.

## Required behavior
- Signature/issuer/audience/scope invalid, revoked device, wrong tenant, expired or not-yet-valid permit: **deny** new authorization.
- Existing sessions may continue only for a **documented bounded** window while the control plane is offline; explicit revocation exposure must be acceptable to the security reviewer.
- Prevent signed-grant substitution across devices/nodes and uncontrolled replay across concurrent sessions.
- Support key rotation with explicit overlapping verification windows and emergency compromise procedures.
- Handle cancellation, refund, chargeback, account deletion and device removal through idempotent control-plane updates.
- No client-side modification to subscription status grants additional access; provider webhooks must be verified and reconciled.
- All expiration and clock-skew budgets are explicit and testable; never rely on indefinite cached membership.

## Cryptography requirement
Use a maintained, reviewed implementation of a suitable signed token format and key-management system; no homegrown cryptographic primitives. Keys are rotated and never stored in the public repository. Prefer asymmetric verification so a compromised node cannot mint valid grants.

## Testing matrix
- Happy path: valid scoped grant for registered device.
- Deny: wrong issuer, scope, audience, tenant, device, altered payload, invalid signature, missing fields, expired permit.
- Lifecycle: device revoked, account deleted, subscription inactive, refund/chargeback, duplicated webhook, concurrent sessions.
- Clock: near-expiry boundary, small clock drift, excessive skew and grace-window expiration.
- Operations: control-plane outage, node restart, signing key overlap, unknown KID and emergency key rotation.
- Privacy: verify logs/metrics exclude raw tokens, payment data and destination traffic.

No node gateway implementation, user subscription or store-compliance approval is represented by this document.
