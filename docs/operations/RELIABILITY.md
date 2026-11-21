# Reliability and operational requirements

SLOs are provisional targets, **not achieved performance**:
- Mature core API monthly availability target: 99.9%.
- Mature VPN data-plane monthly availability target: 99.95%.
- Critical transactional RPO target: 15 minutes; RTO target: 60 minutes, subject to drills and funded redundancy.

Each service must document:
1. Critical dependencies and graceful degradation.
2. Timeouts, quotas, queue bounds, retry budget, backpressure and circuit breaking.
3. Monitoring, privacy-safe logs, alerts and on-call ownership.
4. Backup schedule, restore runbook and measured restore exercises.
5. Multi-region or single-region failure envelope, incident severity and communications.
6. Unit economics and scaling triggers.
7. Test plan: dependency outage, corrupted messages, partial DB outage, revoked credentials, connection drops and old-client compatibility.

Fail closed on privileged **new** actions; any bounded grace window for existing entitlements requires written revocation trade-off and short expiry. Monitor for abuse without promising zero logs of every type.

