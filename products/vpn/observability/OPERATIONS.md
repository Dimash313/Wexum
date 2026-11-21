# Observability — operations runbook (not deployed)

## First-response checks

1. Check management-plane scheduler, trusted probe adapter and expected scrape cadence. Missing samples are UNKNOWN or STALE, never success.
2. Verify trusted operator endpoint configuration using independent management tools; TCP probe success is NOT proof of a functional VPN tunnel.
3. Correlate only aggregate health and local resource pressure; do not collect user traffic destinations, account IDs, raw IPs or packet contents for diagnosis.
4. Confirm access restrictions on Prometheus text exposure, TLS and telemetry storage separately. This module starts no listener.

## Alert interpretation

- telemetry_missing: no recent/sufficient checks. Investigate scheduler, network isolation, process restarts and scrape pipeline before attributing outage to gateway.
- probe_failures: consecutive technical TCP failures observed. Ask Node Registry/Control Plane owner to validate independently; do not bypass authorization or auto-route clients using untrusted samples.
- sample_error_budget_exhausted: observed sample failures exceed target. Verify sample count, cadence and estimator bias; not a measured customer SLA breach.
- local resource read: evaluate CPU seconds, current process RSS (Linux only if available) and local mount disk. No predefined alarm threshold or remote-node promise.

## Recovery / rollback

1. Disable malfunctioning authorized probes or adapter; status must become stale/unknown instead of falsely green.
2. Validate node and control-plane behavior through owning components and independent evidence.
3. Restart only if necessary. All samples and counters reset; treat reset as a measurement gap.
4. Roll back by not integrating or reverting the isolated Draft PR; there are no migrations, secrets or persistent telemetry here.
5. Audit surrounding host/proxy/cloud logging and retention independently before marking privacy incident resolved.

## CTO + auditor approval gates

Approval required for management API auth, probe target allowlist and node identity/generation (PR #65), service boundaries, metrics transport security, exact retention, CI integration, scheduler deadlines and concurrency, false-positive controls, SLO, egress-cost measurement and actual recovery drills.
Legal/religious/privacy review and independent infrastructure testing are still required before operations.
