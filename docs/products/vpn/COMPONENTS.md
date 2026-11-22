# WexumVPN components and trust transitions

**Proposed.** Arrows describe the proposed producer and consumer. Solid arrows in the component view carry requests or evidence. Dashed arrows carry asynchronous events or telemetry. The letters match [interfaces A–K](INTERFACES.md). A protected UI state requires native, engine, policy and network evidence for the same attempt. The signed-permit profile and the existing-session outage rule await [CTO and Security decisions](ADR-control-data-plane-trust.md).

## 1. Component and privilege boundaries

```mermaid
flowchart TB
  subgraph Client["Client device"]
    UI["Unprivileged native UI"]
    Native["Privileged native adapter and OS engine"]
    UI -->|scoped command| Native
    Native -->|I authenticated status| UI
  end
  Hub["Optional Hub client"]
  IdP["Trusted issuer candidate"]
  Provider["Provider evidence or approved isolated lab authority"]
  subgraph CP["Control Plane"]
    ID["Verified Identity edge"]
    Ctrl["Tenant authorization and device lifecycle"]
    Bill["Subscription authority"]
    Ent["Entitlements precheck"]
    Sign["Isolated signing authority"]
    ID -->|A verified actor| Ctrl
    Ctrl -->|B enrollment eligibility| Ent
    Bill -->|authoritative subscription| Ent
    Ent -->|D internal candidate| Ctrl
    Ctrl -->|E candidate, admission intent and revisions| Sign
  end
  subgraph MP["Management Plane"]
    Reg["Registry and trusted node enrollment"]
    Obs["Authenticated probe adapter"]
    Dist["Config, revocation and verifier-key distribution"]
    Ops["Aggregate telemetry and incidents"]
    Obs -->|G scoped observations| Reg
  end
  subgraph DP["Isolated Data Plane"]
    Verify["Gateway identity, verifier and admission state"]
    Worker["VPN packet engine"]
    Verify -->|local admitted session| Worker
  end
  Rig["Independent lab observers and QA"]
  Audit["Independent Audit and CTO"]
  IdP -->|verified identity evidence| ID
  Hub -->|optional scoped request| Ctrl
  Native -->|verified session and key proof| Ctrl
  Provider -->|C provider evidence or private lab decision| Bill
  Ctrl -->|discovery| Reg
  Reg -->|H advisory selection| Ctrl
  Sign -->|bounded permit via Control| Native
  Native -->|F permit and live peer proof| Verify
  Verify -->|fresh admission check| Ctrl
  Native <-->|encrypted lab traffic| Worker
  Ctrl -.->|J durable revoke| Dist
  Dist -.->|versioned change and receipt| Verify
  Verify -.->|aggregate counters| Ops
  Rig -->|K sanitized measurements| Audit
```

The lab fixture alternative feeds a private synthetic subscription authority. Its evidence cannot enter the real provider-ingestion interface. Gateway-to-Control interaction ends at admission, renewal or reconciliation. The packet worker has no Identity, Billing or Hub dependency.

## 2. Login, verified actor and enrollment

```mermaid
sequenceDiagram
  participant C as Native client
  participant I as Identity edge
  participant P as Configured issuer
  participant D as Device Control
  participant E as Eligibility authority
  C->>I: Begin login with server-bound attempt
  I->>P: Authorization code flow with PKCE
  P-->>I: One-time response bound to issuer and nonce
  I->>I: Exchange and verify token, session and membership
  alt Unknown issuer, invalid nonce or timeout
    I-->>C: Deny login and retire attempt
  else Verified actor
    I-->>D: A authenticated scoped actor with session reference
    C->>D: Request enrollment and owner-scoped idempotency key
    D->>E: B may this subject enroll another device
    E-->>D: Decision, limit, revision and freshness
    D-->>C: Single-use challenge bound to this enrollment
    C->>D: Device key proof for same challenge and session
    D->>D: Verify proof, limit and current revisions atomically
    D-->>C: Active device reference or stable denial
    Note over C,D: Lost reply uses same intent. A consumed challenge cannot bind a second key.
  end
```

## 3. Eligibility, candidate and signing

```mermaid
sequenceDiagram
  participant C as Control
  participant E as Entitlements
  participant A as Account, subscription and device authorities
  participant R as Registry
  participant S as Isolated signer
  C->>E: D verified actor and requested connection scope
  E->>A: Authenticated fresh reads with bounded deadlines
  A-->>E: Owner-scoped decisions and revisions
  alt Unavailable, stale, denied or mismatched
    E-->>C: Deny or unavailable, no candidate
  else Eligible
    E-->>C: D unsigned internal GrantCandidate
    C->>R: H select node for requested capability
    R-->>C: Advisory peer, generation and observation
    C->>S: E candidate and bound intent, target and revisions
    S->>A: Confirm current authority and revocation revisions
    alt Changed state, ambiguous timeout or unknown trust
      S-->>C: Deny or reconcile issuance by intent
    else Current and authorized
      S->>S: Record idempotent issuance decision
      S-->>C: Scoped signed permit for one target and device proof
    end
  end
```

## 4. Selection, admission and tunnel evidence

```mermaid
sequenceDiagram
  participant C as Privileged native adapter
  participant G as Authenticated Gateway
  participant M as Node management
  participant A as Control admission authority
  participant O as OS engine and local route observer
  participant U as Unprivileged UI
  C->>G: F bound permit and live device proof over authenticated peer channel
  G->>M: H confirm current peer generation and selection
  G->>G: Verify permit, binding and replay state then hold tentative capacity
  G->>A: Commit admission intent against current authority and revocation revision
  alt Stale, partition, invalid proof or no capacity
    G->>G: Release tentative slot on denial, reconcile uncertain intent
    G-->>C: Deny admission or report attempt pending
    C-->>U: No verified protection
  else Trusted and available
    G->>G: Finalize one lease for confirmed current intent
    G-->>C: Authenticated admission receipt and session generation
    C->>O: Establish engine session and install approved routes and DNS
    O-->>C: OS reports tunnel active
    C-->>U: connected_unverified
    O-->>C: Current engine, peer and local path evidence
    C->>C: Match attempt, generation, entitlement, device and route policy
    C-->>U: I verified_connected only when all evidence agrees
  end
```

## 5. Renewal and rekey

```mermaid
sequenceDiagram
  participant N as Native adapter
  participant C as Control and signer
  participant G as Gateway verifier
  N->>C: Renew current session with fresh proof and idempotent intent
  C->>C: Recheck authority, node target, revisions and signer health
  alt Outage, revoke, expiry or wrong peer
    C-->>N: No renewed permit
    N->>N: Apply approved existing-session policy, withdraw stale claim
  else Current authority
    C-->>N: Successor permit bound to intended session and generation
    N->>G: Present successor with current peer proof
    G->>C: Confirm current admission authority
    G->>G: Verify successor and atomically replace prior generation
    G-->>N: Replacement receipt or original result on identical retry
    Note over N,G: Engine rekey and policy renewal are distinct. Neither restores expired authority.
  end
```

## 6. Revocation, asynchronous propagation and safe disconnect

```mermaid
sequenceDiagram
  participant A as Device or subscription authority
  participant E as Outbox and delivery
  participant G as Gateway
  participant C as Privileged native adapter
  participant U as UI
  A->>A: Commit revoke and outbox record in one transaction
  A-->>E: J resource revision and event ID
  E-->>G: Authenticated asynchronous revoke
  alt Delivered or repeated
    G->>G: Persist monotonic deny revision and cut off matching session
    G-->>E: Applied receipt after enforcement
    G-->>C: Authenticated session cutoff
    C->>C: Stop engine and verify route cleanup
    C-->>U: Revoked or interrupted, clear verified claim
  else Receipt missing or Gateway restarted
    E->>E: Retry and reconcile from durable watermark
    G->>A: Recover current deny state before new admissions
    Note over A,G: Missing receipt means unknown enforcement. Escalate and isolate if required.
  end
```

## 7. Network loss, restore or fail closed

```mermaid
sequenceDiagram
  participant O as OS network path
  participant C as Privileged adapter
  participant U as UI
  participant A as Control authority
  participant G as Gateway
  O-->>C: Path change, captive portal or IPC loss
  C-->>U: Interrupted, clear verified status
  C->>C: Invalidate prior attempt evidence and apply approved routing policy
  Note over C,G: Existing-session outage policy awaits CTO and Security. Measure actual forwarding.
  O-->>C: Network available again
  C->>A: Resolve fresh actor, entitlement, peer and new attempt
  alt Timeout, partition or unknown trust
    A-->>C: Deny fresh admission
    C-->>U: Offline or access check unavailable
  else Current authority
    A-->>C: New bound permit
    C->>G: Fresh admission with peer proof
    G-->>C: Admit only after current checks
    C->>O: Revalidate routes, DNS and network generation
    C-->>U: Report verified only after all same-attempt evidence
  end
```

## 8. Dependency graph for the first laboratory connection

```mermaid
flowchart TD
  Gov["1 Foundation governance and approved boundaries"] --> Id["2 Verified lab identity and session"]
  Id --> Dev["3 Device enrollment and proof"]
  Dev --> Ent["4 Authoritative lab eligibility"]
  Ent --> Permit["5 Permit issuer and verifier agreement"]
  Permit --> Peer["6 Authenticated Gateway, registry and capacity"]
  Peer --> Engine["7 Approved protocol and maintained engine"]
  Engine --> Native["8 One native client and OS adapter"]
  Native --> Tunnel["9 Actual isolated tunnel and endpoints"]
  Tunnel --> Tests["10 Positive, deny, route and failure measurements"]
  Tests --> Audit["11 Independent review of exact evidence"]
  Policy["CTO and Security fixture, offline and routing decisions"] --> Ent
  Policy --> Tests
  Rig["QA independent observers and negative controls"] --> Tunnel
  Gov --> Rig
```

Stage 3 can prove device enrollment against an explicitly approved private enrollment decision. Stage 4 validates the separate right to connect. Run order, owners, gates, artifacts and cleanup are in the [lab migration plan](LAB_MIGRATION_AND_ACCEPTANCE.md).
