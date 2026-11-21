# WexumVPN — architecture and task boundaries

## Objective
Standalone native VPN clients with user-controlled protective connectivity. Competition targets product reliability, honest privacy and usability; competitor marketing is not engineering evidence.

## Hard boundaries
- **Data plane**: isolated VPN gateway nodes, independent from Hub and unrelated platform APIs. No per-packet billing/identity lookup.
- **Control plane**: account-based enrollment, signed short-lived entitlements, device limits, node discovery and revocation policy.
- **Management plane**: health, deployment, abuse response, safe metrics, cost controls and disaster recovery.
- Native clients use system VPN APIs and only permissions allowed by the relevant OS/store. Hub is an account/subscription console and may deep-link to the standalone VPN app.
- Initial protocol selection must use maintained, independently reviewed implementations. Do not invent cryptography.
- DNS leak prevention, disconnect handling and network switching require platform-specific tests, not design promises.
- Privacy policy must disclose exact collected fields and retention; do not claim "no logs" before measurement and external review.
- VPN availability does not guarantee anonymity; limit misleading claims.

## Open decisions
Eligible operating company and store accounts; target countries and server placement; provider agreements; node protocol choices; deployment topology; lawful abuse response; independent security review; entitlement revocation latency and renewal; mobile data usage estimates.

## First contracts
Node: stable node ID, region, capability, advertised health and expiry.
Device: opaque device ID, owner identity, enrollment/expiry, revocation.
Entitlement: signed subject, audience, scopes, time bounds, device binding and key rotation.
Connection telemetry: aggregate availability metrics only by default; no destination browsing histories.

See MULTI_AGENT.md for ten non-overlapping VPN work lanes. Product security review is mandatory before deployment.

