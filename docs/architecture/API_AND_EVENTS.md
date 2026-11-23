# API and event contract rules

- Every published interface must have an owning team, schema, examples, error model and compatibility policy.
- Normalize authentication at entry, then authorize each resource operation in the owning domain. Never trust user-supplied tenant claims alone.
- Mutation endpoints require appropriate idempotency keys, concurrency-control strategy, rate limits and audit semantics.
- PII must not be placed in event names, event IDs, URLs or metrics labels.
- Use the event envelope in src/wexum_core/events.py as a **minimal local type contract**, not a delivery system.
- A real event transport requires transactional outbox, consumer deduplication, retries, ordering assumptions, isolation, replay and schema-compatibility tests.
- Shared Python authorization rules in src/wexum_core/authorization.py are an illustrative pure policy contract, not a substitute for authenticated request handling and a real authorization service.
- Contract updates affecting another team require an ADR or interface issue and integrator review before implementation.

