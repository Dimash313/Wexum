# Preliminary threat model (to expand per product)

Assets: user authentication factors, organization memberships, private files, network access grants, VPN node credentials, payments and recovery backups.

Trust boundaries: browser/mobile ↔ public API; API ↔ internal service; customer ↔ organization; Hub ↔ product; control plane ↔ VPN data plane; service ↔ external provider; CI runner ↔ deployment.

Threat categories: stolen session/keys; cross-tenant access; SSRF or unsafe uploads; supply-chain compromise; permission escalation; replay of events; double billing; backup exfiltration; logs containing secrets; abusive traffic; single-region outages.

Required mitigations: deny-by-default checks; authenticated callers; explicit tenancy; bounded timeouts/retries; idempotency and concurrency control; secret rotation; safe logging; tested restore; dependency updates and vulnerability triage; rate limits; isolated privileged hosts; manual emergency revocation.

Open questions: actual identity provider, device attestation, hardware-backed keys, legal retention, cross-region data residency, incident notifications and external penetration testing. None is claimed implemented.

