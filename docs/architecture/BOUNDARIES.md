# Domain ownership and trust boundaries

| Domain | Owns | Must not directly own |
| --- | --- | --- |
| Identity | User identities, sessions, authenticators | VPN packet traffic, vault plaintext |
| Access | Organization membership, permission grants | Raw documents and files |
| Billing | Payment-provider references, subscription entitlements | Network payloads and private content |
| VPN | Network node configuration, allowed devices and connection policy | Cross-product personal files |
| Cloud | File metadata, objects, share permissions | Credentials of unrelated products |
| Work | Document state, edit permissions and collaboration | Direct writes to Cloud internals |
| Hub | UI composition, explicit client consents | Authoritative product state |
| Search | Permission-aware indexed copies with deletion hooks | Unconsented data or vault secrets |
| AI | User-approved tasks and ephemeral contexts | Silent access to unrelated resources |

## Data contracts
- Request authentication establishes who the subject is; authorization establishes what they can do to the target tenant/resource.
- Personal resources and organization resources are distinct; no global administrator bypass in shared libraries.
- Service-to-service tokens are scoped to purpose, tenant, audience and short lifetimes.
- Access revocation, account deletion and legal retention requirements must propagate through outbox events and reconcile jobs.
- Strongly consistent operations stay within one owning transaction; cross-domain workflows are explicit and compensatable.
- A user may have standalone apps, yet has one Wexum identity across Wexum-owned products. FileShape does NOT share this identity automatically.

## Handoff
Every new endpoint or event must define: owner, caller, actor, tenant, scopes, input validation, idempotency, errors, privacy data class and migration behavior. Unknown authority always denies.

