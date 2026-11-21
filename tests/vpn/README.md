# WexumVPN — independent QA test lab (issue #10)

This directory is exclusively owned by VPN Testing & Quality Engineering. These
are **not** proof of a deployed or working VPN, production security, anonymous
traffic, or actual DNS/IP leak prevention. All fixtures use reserved example IP
ranges and synthetic opaque identifiers; no production credentials or network IO.

## Reproducible commands (Python 3.12+, stdlib only)

From repository root:

```bash
python -m compileall -q tests/vpn
python -m unittest discover -s tests/vpn -p 'test_*.py' -v
```

`test_leak_evidence.py` checks a deterministic **offline evidence classifier**.
`CONSISTENT` means only that supplied fields agree with an explicit expectation,
**not** that a VPN tunnel was inspected. `INCOMPLETE` never becomes success.

`test_control_contract.py` imports real `DeviceControlService` and
`SQLiteDeviceStore` (not surrogate implementations) if the source is present at
`products/vpn/control/src` in the checkout. Otherwise these tests are **skipped**:
check the final test summary, not just exit status. To run against a separate
checkout of the Control Plane proposal, pass an explicit source directory:

```bash
WEXUM_VPN_CONTROL_SRC=/absolute/reviewed/control/src \
  python -m unittest discover -s tests/vpn -p 'test_control_contract.py' -v
```

An invalid explicitly set source path **fails**, not skips. The provider callback
is a synthetic in-memory decision; real OIDC/JWT, real entitlements, HTTP, and
network/gateway behavior are not covered. The regression test for newest active
device visibility is expected to expose the known open issue #2 defect in the
current PR #55 until the implementation is corrected. Do not mark failing tests
as expected success or hide them in CI.

## CI and cross-team handoff

No shared workflow is changed from this lane. Integrator must run this suite in
required CI on an exact, reviewed **combined commit** containing Control Plane
and the final integration contracts, with skipped contract tests treated as
missing evidence. Source branches and issue numbers are not an integrated API.
Do not merge this candidate before foundation PR #1, independent review and
integrator approval.

## Real VPN DNS/IP testing: pending equipment and protocol

Actual leak evaluation requires an independently reviewed test setup and OS
permissions. Capture **before, during, after, reconnect and forced-disconnect**
observations on each supported OS, across IPv4-only, IPv6-only, dual-stack,
Wi-Fi/mobile switching and captive-portal scenarios. Verify with external
controlled egress endpoints, OS-level routes, DNS requests (including fallback),
packet capture and resolver policy; record timestamps and protocol configuration.
A hostname lookup or public-IP comparison alone does not prove no leak.

Test rigs must be disposable, isolated, and contain no real user traffic, real
accounts, credentials, browsing history or IP-to-user identifiers. Minimize
captures and redact addresses before sharing artifacts. Independent reviewers
must verify provenance, coverage and false-negative risks. Until actual probes
exist, mark all physical tunnel, reconnection, kill-switch, throughput,
latency, DNS and IPv6 leak claims **NOT TESTED**.

## Risks / rollback

- A matching synthetic snapshot can be forged or incomplete; classifier lacks
  trustworthy probe provenance and cannot certify tunnel security.
- Contract suite is opt-in until upstream source becomes available in an
  integration candidate; skipping is explicitly not a pass.
- SQLite tests exercise single-process/local-file behavior, not distributed
  consistency, data-plane revocation or real capacity.
- Rollback by reverting only files in `tests/vpn/`. No migrations or deployment.
