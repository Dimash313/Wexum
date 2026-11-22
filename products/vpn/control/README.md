# WexumVPN Control Plane — first executable backend

**Status: prototype in issue #2, not deployed or approved.** Device registration, listing and revocation with SQLite persistence and deny-by-default policy are working local Python functions. This is not an HTTP server, authentication system, VPN node, payment processor or VPN tunnel. There is no false 'connected' status or claim of active service.

## Run

Python 3.12+; standard library only. From repo root:

~~~bash
cd products/vpn/control
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
~~~

The SQLiteDeviceStore(path) must be initialized with a **trusted server-owned file path**, never a client-supplied path. The constructor creates tables and WAL journal. A dedicated user and restrictive directory permissions are necessary before deployment; SQLite is not the chosen global-scale backend.

DeviceControlService requires an **injected** authenticated actor verified by another service, an authoritative **async** entitlement adapter, expected issuer and audience, and explicit timeouts. The prototype includes NO OIDC/JWT verification: an HTTP handler MUST NOT build AuthenticatedActor from JSON, headers or client-provided identity claims. No HTTP route is exposed yet.

## Implemented contract

- await enroll(actor, platform, idempotency_key) checks scope and session freshness, obtains a bounded-time authoritative entitlement decision, then atomically enforces device limits and inserts a server-generated opaque UUID.
- list_devices(actor) returns up to 200 rows for the authenticated tenant and subject. Unrevoked devices whose expiry is in the future come first. Revoked and expired devices fill the remaining slots. Each group is ordered by registration time from oldest to newest, then by device ID.
- revoke_device(actor, device_id) only affects the caller's own device and remains usable if the entitlement verifier is unavailable.
- Duplicated registration idempotency keys return the same device, not a new permit. Reusing the key for a different platform fails. The key is stored as a SHA-256 digest, not plaintext.
- A revoked device does not return to active state on a duplicate request; expired/revoked devices do not consume a new device slot.
- Records contain opaque tenant/user/device IDs, platform and lifecycle timestamps. **No** VPN destinations, IP traffic, browsing history, auth tokens, credentials or node private keys are stored.

## Boundaries and blockers

A device row is NOT a cryptographically authenticated device: actual proof-of-possession and per-node signed permits belong to issues #3 and #11. Revocation updates only the local control database; it does NOT revoke an existing VPN session on a node, send a push message or prove remote disconnect.

Identity issuer verification (#34), billing authority (#36/#3), durable entitlement revocation, HTTPS API adapter, rate limits, account deletion and retention, multi-instance database scaling, log/metric design, backup/restore, trusted filesystem configuration, and native VPN client testing are all **not implemented** and must block public deployment. Expiry is bounded by the trusted entitlement response and the configured 30-day maximum; a short-lived login access token does not itself prematurely expire a device row.

A signed token and device key will later be necessary for actual VPN node access. Use maintained reviewed protocols; never invent cryptography. Do not merge this draft without foundation PR #1 and independent security review.

See THREAT_MODEL.md and openapi-proposal.yaml (proposal only).
