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
    Auth["Fenced VPN authority, journal and outbox"]
    Ctrl -->|scoped effective transitions| Auth
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
    Gate["Expiring packet-path gate"]
    Verify -->|fresh boot-bound allowance| Gate
    Gate -->|enable or stop| Worker
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
  Verify -->|F conditional admission and fresh activation| Auth
  Auth -->|challenge-bound confirmation| Verify
  Native <-->|encrypted lab traffic| Worker
  Auth -.->|J durable revoke| Dist
  Dist -.->|versioned change| Verify
  Verify -.->|boot-bound apply and enforcement receipt| Auth
  Worker -.->|synthetic path sampled outside host| Rig
  Verify -.->|aggregate counters| Ops
  Rig -->|K sanitized measurements| Audit
```

The lab fixture alternative feeds a private synthetic subscription authority. Its evidence cannot enter the real provider-ingestion interface. Gateway-to-Control traffic includes admission, activation, live authority challenges, renewal and reconciliation. The packet worker has no Identity, Billing or Hub dependency.

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
    A-->>G: Committed revision and one reserved slot
    G->>A: Fresh activation challenge for intent and current boot
    A-->>G: Current disposition and anchored deadline
    alt Positive fresh activation and matching local deny floor
      G->>G: Arm gate once under local deny lock
      G-->>C: Authenticated admission receipt and session generation
      C->>O: Establish engine session and install approved routes and DNS
      O-->>C: OS reports tunnel active
      C-->>U: connected_unverified
      O-->>C: Current engine, peer and local path evidence
      C->>C: Match attempt, generation, entitlement, device and route policy
      C-->>U: I verified_connected only when all evidence agrees
    else Revoked or confirmation uncertain
      G->>G: Leave gate closed and reconcile original allocation
      G-->>C: Denied or pending with no forwarding
    end
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
    G->>C: Commit successor against current floors and capacity
    C-->>G: Fresh activation confirmation for current boot
    G->>G: Verify successor and atomically replace prior generation
    G-->>N: Replacement receipt or original result on identical retry
    Note over N,G: Engine rekey and policy renewal are distinct. Neither restores expired authority.
  end
```

## 6. Revocation, asynchronous propagation and safe disconnect

```mermaid
sequenceDiagram
  participant A as Device or subscription authority
  participant E as VPN authority and outbox
  participant G as Gateway
  participant C as Privileged native adapter
  participant U as UI
  A->>E: Submit scoped effective VPN restriction
  E->>E: Serialize revoke at VPN authority with durable outbox
  E-->>A: Committed VPN revision and event ID
  E-->>G: Authenticated asynchronous revoke
  alt Delivered or repeated
    G->>G: Persist contiguous deny floor and mark session closing
    G-->>E: Applied receipt
    G->>G: Close packet gate and drain queued traffic
    G-->>E: Local enforced receipt if closure succeeded
    G-->>C: Authenticated local enforcement disposition or unknown on failure
    C->>C: Stop engine and verify route cleanup
    C-->>U: Revoked or interrupted, clear verified claim
  else Receipt missing or Gateway restarted
    E->>E: Retry and reconcile from durable watermark
    G->>E: Bootstrap from authoritative checkpoint and tail
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
  C->>A: Resolve any unknown prior intent and prove prior session fenced
  C->>A: Request fresh authority for reconnect after prior resolution
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

## 9. Race at the authority and recovery of a lost commit reply

```mermaid
sequenceDiagram
  participant D as Domain owner
  participant G as Gateway boot G
  participant A as Fenced VPN writer
  participant L as Durable authority store
  G->>A: Submit same tenant, intent, digest and prepared target
  D->>A: Restrict bound device or session
  alt Restriction takes writer first
    A->>L: Commit deny floor and outbox at R
    A->>L: Check admission against R and record denial
    A-->>G: Denied with no slot
  else Admission takes writer first
    A->>L: Commit intent, spend, one slot, revision and outbox at R
    A--xG: Admission response lost after commit
    G->>G: Keep gate closed and outcome unknown
    A->>L: Commit restriction and outbox at next revision
    G->>A: Authenticated lookup of original intent and digest
    A->>L: Linearizable read of outcome and present authority
    A-->>G: Historical grant R, now revoked, no activation
    G->>G: Persist deny and retire unused preparation
  end
  Note over G,L: If lookup is unavailable retain unknown. If still eligible obtain fresh activation for same allocation.
```

## 10. Active session during partition and independent cutoff evidence

```mermaid
sequenceDiagram
  participant A as VPN authority
  participant G as Gateway supervisor
  participant F as Independent expiring packet gate
  participant Q as QA ingress and egress observers
  participant U as Native adapter and UI
  G->>A: Fresh boot and session challenge at local send anchor
  A-->>G: Current authorized revision and immutable limit
  G->>F: Arm bounded deadline for current boot
  Q->>Q: Calibrate each path and observe live markers
  G--xA: Control partition while data path still forwards
  A->>A: Commit revoke and retain outbox
  G->>G: Detect loss by bounded deadline and refuse new work
  G-->>U: Withdraw stale verified state if status channel reachable
  alt A selected
    F->>F: Expire positive confirmation and stop without grace
  else B separately approved
    F->>F: Honor only remaining pre-issued active lease
    F->>F: Stop at fixed expiry or earlier explicit restriction
  end
  F-->>G: Report enforced if both directions closed
  Q->>Q: Continue ingress, bound last egress and verify sensor health
  alt Receipt and calibrated packet evidence match
    Q->>Q: Confirm stopped for measured session and paths
  else Missing observer or unreliable clock
    Q->>Q: Mark cutoff unverified and block acceptance
  end
  Note over A,Q: Decision, packet cutoff and receipt arrival have distinct times. Lost ACK leaves the authority uncertain.
```

## 11. Restart, missing revisions and restored management

```mermaid
sequenceDiagram
  participant G as Rebooted Gateway
  participant F as Packet gate
  participant M as Management
  participant A as Fenced VPN authority
  participant Q as QA observers
  G->>F: Default deny before network forwarding
  Q->>Q: Drive ingress and verify old traffic cannot resume
  G->>M: Authenticate new boot and reader capabilities
  M->>A: Fence prior peer generation and register successor
  G->>A: Request snapshot at certified checkpoint and scoped stream tail
  alt Unknown writer, old checkpoint, missing tail or incompatible reader
    A-->>G: Quarantine, no new grant or activation
  else Complete history and live authority
    A-->>G: Current keys, denies, stream digest and high-water barrier
    G->>G: Persist snapshot and contiguous suffix, reconcile old intents
    G-->>A: Applied watermark for current boot
    A->>A: Check fresh barrier, generation and retirement of prior paths
    A-->>G: Eligible for fresh admission only after reconciliation
  end
  Note over M,A: Either channel may return first. Neither alone can resume an old session.
```
