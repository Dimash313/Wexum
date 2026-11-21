# WexumVPN — Node Registry (issue #4)

This is a **standalone, in-memory, standard-library-only implementation** for the node-registry ownership lane. It is **not deployed**. It has no real servers, probes, VPN gateway addresses, geolocation validation, tunnel configuration, public discovery endpoint, persistent database, or access-grant behavior. Every identifier in the unit tests is synthetic (prefixed test-).

## Trust boundary

- NodeRegistry.register(Node), set_enabled(node_id, enabled), remove(node_id): **trusted management-plane only**. An adapter must authenticate and authorize operators, check provenance, and log changes. Never feed user-submitted JSON directly into these methods.
- record_health(HealthObservation, now=...): accepts only authenticated health observations from a trusted monitoring adapter. The library does not verify probe identity or cryptographic signatures.
- select(now=..., region_id=..., required_capabilities=...): returns an **advisory snapshot**, not a signed entitlement, gateway credential, or capacity reservation. Control Plane must independently verify identity, tenant/device entitlement, and current node suitability.
- snapshot(now=..., limit=...): bounded inventory status intended for privileged services. Client visibility requires a separately approved policy.

## Domain contract — internal proposal; CTO review required before API adoption

| Object / operation | Fields and invariants |
| --- | --- |
| Node | immutable node_id, region_id (lowercase ASCII 1–64 characters), capabilities (immutable set, at most 16), max_sessions (1–100000), enabled (boolean) |
| HealthObservation | node_id, status enum healthy/down, UTC-aware observed_at, bounded active_sessions; caller supplies trusted observation |
| NodeAvailability | immutable node_id, region_id, status disabled/unreported/stale/down/saturated/healthy, observed and expiry timestamps |
| NodeSelection | immutable node_id, region_id, observed/expiry timestamps and sampled active/max sessions; not a reservation or permission |
| record_health | rejects future/expired reports and repeated/older timestamps; thread-safe |
| select | deterministic lowest active_sessions/max_sessions, then lexicographically smallest node_id; returns None without an eligible fresh, healthy node |
| revalidate_selection | local, lock-protected equality check of previously selected registration/observation/capacity and current health; returns false on stale, changed or disabled node. It is not an entitlement check or capacity reservation |

An operator-declared region label does **not** prove physical geography or legal eligibility. No country, latency, or uptime claims are made.

### Selection freshness and concurrency limits

`select(...)` returns a snapshot; its state can become obsolete before Control Plane acts on it. `revalidate_selection(selection, now=trusted_utc)` atomically checks the same registration ID, region, max session cap, observed timestamp, sample load and expiry against current in-memory healthy status. It fails closed when the node has been disabled, removed, recreated, expired, reported DOWN/saturated, or received a newer observation. Invalid input types are rejected.

**This is not a guarantee of available capacity at connection time:** revalidation may race with a later change after its lock is released, and it does not reserve sessions or authenticate clients. The future Control Plane must check authorization, node eligibility and capacity in an approved atomic/grant allocation workflow. The method is only an internal proposal and its cross-lane use requires CTO approval.

### Registration lifecycle and replay protection

- `register(Node(...))` allocates and returns a new random 128-bit `registration_id` (32 lowercase hexadecimal characters). The trusted inventory adapter must retain this ID and associate it with its **authenticated, actual node instance**. Do not accept a registration ID from the public client as proof of a trusted probe.
- `HealthObservation` requires that `registration_id`, and `record_health` rejects observations when the stored registration differs — even if the observation timestamp is recent or newer than the last accepted timestamp. Removing and re-registering the same stable `node_id` always generates a different registration ID.
- `set_enabled(node_id, False)` clears live health and returns `None`; `set_enabled(node_id, True)` after a disabled state generates a new registration ID and returns it. Repeated no-op calls preserve the ID. An adapter must update the authenticated probe binding after re-enabling; otherwise discovery remains fail-closed.
- `NodeSelection.registration_id` identifies the exact sampled registration so the control plane can **compare it against the current generation** before using the selection. This ID is **not** a credential, grant, authentication mechanism, or concurrency-safe capacity reservation.
- Process restart clears all registrations and observations (no persistent inventory), so newly registered nodes require fresh matching health. Production needs transactional persistence and a separately trusted lifecycle sequence/probe identity system. The in-memory mechanism is only a local safety primitive; it cannot authenticate its inputs.


**Fail-closed:** Unknown, expired, disabled, down, saturated, or unreported nodes are never selected. A disabled/reenabled node requires a fresh health report. Health TTL 1–300 seconds (default 30); inventory maximum 1–10000 (default 2048); snapshot limit 1–200. No external I/O, background workers or retries. The trusted caller injects UTC time.

Invalid inputs raise ValueError or TypeError; missing inventory raises KeyError; expired/replayed/out-of-order observations raise StaleObservationError. HTTP adapters must map these to safe responses and enforce caller-specific rate limits.

## Run local checks

From repository root with Python 3.11+ (no dependencies beyond stdlib):

    python -m unittest discover -s products/vpn/nodes -p 'test_*.py' -v
    python -m compileall -q products/vpn/nodes

The tests cover stale health, TTL, down/over-capacity exclusion, region/capability filters, resource bounds, out-of-order reports, invalid input, deterministic selection and concurrent mutations.

## Blockers and integration handoff

1. Foundation PR #1 is pending independent audit. This code imports none of its unpublished contracts. Leave this PR draft until the foundation and common interface are approved, and current-head CI passes.
2. No persistence or multi-worker coordination: restarting loses all health/inventory and therefore fails closed. Production needs approved authoritative storage, authenticated monitoring, cache invalidation, report generation/sequence proof, capacity/load tests and recovery drills.
3. No integrated authorization or connection API. CTO must approve actor/tenant/scope, visibility, errors, freshness and selection handoff with Control Plane (#2), Entitlements (#3), Identity (#34) and deployment/observability owners.
4. No live node data or benchmarks. Measure availability, capacity, network latency, egress cost and geography only after real infrastructure exists.
5. No browsing history, packet contents, user IDs, device IDs or secrets handled. No paid services or external dependencies introduced. Independent security, legal, store and religious reviews remain release gates.

Rollout: none. Rollback: close/revert the draft branch. No migrations or production data.
