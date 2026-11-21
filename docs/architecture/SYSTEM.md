# Wexum system architecture

## Target
Twenty-two independent standalone products, Wexum Hub for integrated workflows, and a shared Wexum Core. This is a **target architecture**, not a claim of implemented functionality.

## Planes
- **Data plane:** serves product traffic and must not synchronously depend on unrelated products or Hub. VPN traffic uses isolated VPN nodes; files use their product data paths.
- **Control plane:** identity, permission grants, configurations, entitlement distribution, billing state. Expensive or failure-prone tasks are not on every packet/request path.
- **Management plane:** deployment, telemetry, observability and recovery; isolation from customer traffic.

## Boundary rules
1. Each product owns its write model and schemas. No cross-product database reads. Use typed API contracts and domain events.
2. Prefer modular services with strong code boundaries before splitting every module into a microservice.
3. Treat Hub as a client, not a central mandatory gateway. Product applications and APIs must work when Hub is down.
4. Fail closed for new privileged actions when permission state cannot be verified. Bounded offline behavior for previously authorized operations requires a documented risk assessment, expiration and revocation plan.
5. For asynchronous workflows, use transactional outbox, idempotent consumers, bounded retries, dead-letter inspection and documented eventual-consistency contracts.
6. No user data flows to AI, search or another product without explicit, scoped authorization.
7. Encrypt at rest and in transit as appropriate; encrypted vault secrets must not be exposed to search/AI by default.
8. Operationally independent failure domains evolve with measured load. Never introduce an unnecessary shared chokepoint.
9. Auth, VPN tunneling, payment processing and user secrets use separate threat models.

## Interfaces
- Explicit API schemas; tenant-scoped authorization checked on the server on every request.
- Domain event envelope has event ID, event type, schema revision, tenant ID, and timezone-aware timestamp.
- Public contracts change by additive compatible migrations first. Never silently reinterpret an existing field.
- API/DB compatibility requires tests across producers, consumers, and mixed deployments.

## Anti-goals
- Universal shared database with unrestricted module access.
- One giant superapp binary as the only functional entry point.
- Pushing all packets through Wexum Core.
- Premature Kubernetes/microservice sprawl.
- Claiming impossible zero-failure or zero-vulnerability guarantees.

See BOUNDARIES.md, vpn/ARCHITECTURE.md, engineering/QUALITY.md and operations/RELIABILITY.md.

