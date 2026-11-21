# WexumVPN — Subscriptions & Billing (issue #9)

**Status: isolated accounting prototype; NOT a payment product or VPN access authority.** This module neither contacts stores/payment gateways nor processes cards. It has no live provider implementation. It is based on `main`, independent of pending foundation PR #1.

## Behavior

- A **trusted server** creates an opaque order bound to an authenticated tenant + account, selected plan snapshot, and approved provider. This code does not authenticate callers and MUST NOT be published as a client API by itself.
- A provider adapter verifies webhook authenticity before constructing a typed event. `TestHmacAdapter` is a **synthetic test harness only**; it is explicitly disabled by default and cannot silently substitute for an actual store verification/reconciliation flow.
- Verified events are applied atomically with SQLite `BEGIN IMMEDIATE`, uniqueness for provider event IDs and transaction IDs, and per-transaction refund/chargeback tombstones (including refunds received before paid events). Replays and collisions fail closed.
- Cancellation disables future renewal intent while preserving already paid access. Failed payment does not grant access and cannot erase a valid earlier period. Expiry is evaluated at query time; refunds/chargebacks revoke only the affected transaction. Later valid, distinct renewals can retain access.
- A server-only tenant/account-scoped `Snapshot` can be queried by the Entitlements service **after** approved integration. It is NOT a signed grant, never authenticates the user, and MUST NOT be trusted if supplied by a client.

## Test (Python standard library only)

From repository root:

```sh
PYTHONPATH=products/vpn/subscriptions/src python -m unittest discover -s products/vpn/subscriptions/tests -v
python -m compileall -q products/vpn/subscriptions/src products/vpn/subscriptions/tests
```

Tests use only synthetic events/secret and a temporary SQLite DB. No third-party dependency, cloud API, paid endpoint, card data, app store account, or real payment is used.

## Data and operational boundary

Persisted fields: opaque order/tenant/account IDs; plan code, ISO currency and amount in integer minor units; provider/event/transaction opaque identifiers; SHA-256 digest of the received webhook; paid-through timestamps; cancellation state; refund markers and monotonically advancing ledger revision. **No raw webhook body, payment credential, bank card, IP, browsing destination or customer email is stored.** Identifiers must remain opaque in upstream adapters. Restrict database file access and backups; define deletion/retention and encrypted storage policies before any deployment. This prototype includes no audit export, reconciliation job, outbox, distributed entitlement revocation propagation, data-migration system or operational monitoring. SQLite WAL requires correct backup/restore handling.

Store timestamps are integer UTC epoch seconds supplied by trusted server clocks. The adapter's synthetic timestamp tolerance is 300 seconds; this is **not** a claim about any real vendor's signature algorithm, retry semantics or event ordering.

## Dependencies and integration blockers

1. **PR #1**: foundation/quality/identity contracts are not integrated. This directory changes no cross-lane files.
2. **Issues #3 and #34**: independently reviewed trusted authentication and Entitlements integration, transactional outbox / revision consumption, refund-to-revocation latency, account deletion and tenancy authorization. No access grant is minted here.
3. **Provider selection**: real store/payment providers require vendor-specific signed webhook/receipt verification, merchant/account binding, app-store server-side transaction APIs, subscription reconciliation and documented outage handling. All live providers remain unavailable until a separately approved implementation and end-to-end tests.
4. **Store/legal/religious gate**: eligibility in target jurisdictions, platform purchase rules, taxes/receipts, cooling-off/refund rules, consent for auto-renewal, honest price disclosure, lawful age/merchant account requirements and a qualified religious review for monetization. No interest, deceptive defaults, silent renewals, gambling or doubtful monetization is authorized by this prototype.
5. **Operations**: secure DB permissions and backups; migrations; GDPR/local data-retention review; limits/rate limiting at HTTP ingress; independent security, failure and concurrency tests using real vendor fixtures and provider callbacks. Shared API/event changes require integrator-approved ADR.

## Rollback

No deployment or remote side effects. Close the Draft PR or remove only `products/vpn/subscriptions/`. Never merge as production billing without blockers above being resolved.
