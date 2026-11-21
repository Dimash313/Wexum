# WexumVPN — Network Observability & Operations

Owned scope: issue #8. Standalone Python management-plane module, not a deployed monitoring service.

## Measured values (only after an authorized operator runs them)

- The monitor accepts aggregate success/failure and elapsed seconds of trusted technical probes for five fixed service categories.
- A bounded 300-second rolling sample window with up to 1,000 outcomes per category calculates sampled success ratio, relative SLO error-budget consumption, and unknown / healthy / degraded / down / stale states.
- Global monotonic-clock rollback is rejected for recording, snapshots and exposition rather than silently yielding a healthy state. Non-finite accumulated probe duration is rejected before updating sample/counters; invalid sample limits are rejected at construction.
- A TCP probe performs only a socket connect to an operator-configured endpoint. Success proves no more than that TCP handshake; it does not prove VPN tunnel operation, user experience, DNS leak prevention, location or anonymity.
- Resource readings are this monitoring process's CPU seconds, optional Linux process RSS, and disk capacity for a specified local mount. They are NOT remote gateway resource use, user traffic or cloud costs.
- AlertEngine emits deduplicated state transitions for explicitly watched service categories. Prometheus exporter only returns formatted text. Neither network scheduler nor HTTP endpoint is started.

## Privacy and trust boundaries

- No raw packets, browsing destinations, domain histories, account/tenant/user/device/session identifiers, node IDs, IP addresses, hostnames or customer requests are stored in telemetry or exported as labels.
- Hard-coded service categories, result and state enum values only. Invalid service labels and invalid numeric observations raise errors.
- A probe endpoint lives only in operator configuration and the current call stack; no endpoint or exception details are added to observations.
- The caller must be a trusted/authenticated management adapter. This module does NOT authenticate incoming samples and MUST NOT be exposed to untrusted clients.
- No database or file logs. Rolling samples are in process memory, and cumulative counters are process-lifetime. A process restart resets state. This alone is NOT a zero-log privacy policy for the infrastructure.
- Inventory logs at gateway, reverse proxy, load balancer, cloud host, DNS, SIEM and VPN tunnel layers before making any external privacy claims.

## Usage

Import HealthMonitor, AlertEngine, ProbeTarget and tcp_probe from products.vpn.observability.
Create a HealthMonitor; configure an AlertEngine(monitor, watched_services=("gateway",)); create a ProbeTarget("gateway", "gateway.internal.example", 443).
Only an operator-owned scheduler may call tcp_probe(target, monitor). Use monitor.snapshot(), alerts.evaluate() and monitor.render_prometheus() locally.
Do not expose metrics over an unauthenticated/public HTTP endpoint.

## Tests

From repository root with Python 3.10+:

    python -X dev -m unittest discover -s products/vpn/observability/tests -v
    python -m compileall -q products/vpn/observability

Tests mock TCP connections and use a local resource read; no real VPN infrastructure was tested or probed.
Shared GitHub CI does not yet run these owned-path tests; CTO must approve any change to shared workflow configuration.

## Limits / dependencies

- Only sampled checks contribute to the estimated sample error budget (default target success ratio 99%, NOT customer SLA). No fake uptime claim; missing data remains unknown/stale.
- DNS lookups may exceed socket connect timeout. External orchestrator needs independently bounded concurrency, hard deadline, jitter/backoff and alert delivery.
- This is a single-process library, not cross-node durable state. No per-node resource, egress, billing, monitoring fleet, incident paging, tracing, automatic failover or customer telemetry yet.
- All future Node Registry PR #65 and Control Plane contract integration needs CTO approval, authenticated source and freshness/generation verification.
- Foundation PR #1 is unmerged. This branch is independent of its runtime contracts.

See OPERATIONS.md for incident response, rollback and production gates.
