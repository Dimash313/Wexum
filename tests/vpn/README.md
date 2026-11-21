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
`products/vpn/control/src` in the checkout. Otherwise these tests are **skipped** by default:
check the final test summary, not just exit status. Use
\`WEXUM_VPN_REQUIRE_CONTRACTS=1\` for mandatory CI/integration runs to turn a
missing import into a **hard failure**, never silent skipped coverage. To run against a separate
checkout of the Control Plane proposal, pass an explicit source directory:

```bash
WEXUM_VPN_REQUIRE_CONTRACTS=1 \
WEXUM_VPN_CONTROL_SRC=/absolute/reviewed/control/src \
  python -m unittest discover -s tests/vpn -p 'test_control_contract.py' -v
```

An invalid explicitly set source path **fails**, not skips. The provider callback
is a synthetic in-memory decision; real OIDC/JWT, real entitlements, HTTP, and
network/gateway behavior are not covered. The 16 contract checks include regressions for newest active device visibility
and for SQLite connection-open failures on enrollment, listing and revocation.
On PR #55 head \`66532b4df984c091b46e53697218b82557bb4bbd\`, those four
checks are known to fail until owner #2 corrects the implementation. Do not
mark failing tests as expected success or hide them in CI.

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

## Independent exact-source regression replay (2026-11-21)

Isolated Python 3.13.5 local checkout with exact GitHub blob SHAs:

- PR #55 \`service.py\`: \`de329886873e1cb3a26672b8786712f86df747a4\`
- PR #55 \`store.py\`: \`d00b0427f60ce46ccf049a808e9a692e6db34146\`
- PR #55 \`__init__.py\`: \`8469816eb7c4cd2c6b39a3f28e1ff4426a4216be\`
- QA \`test_control_contract.py\`: \`82d66ac38908fc9edcec3642705f3d8b0bcf0fb2\`
- QA \`test_leak_evidence.py\`: \`6c66ab5fe1ce0cc8b8d906c70595999bec7b5296\`
- QA \`leak_evidence.py\`: \`a5c29c87abdd605422d3cd27de2d303019e0f8ca\`

Ran \`python -m compileall -q tests/vpn\` successfully and
\`PYTHONPATH=products/vpn/control/src python -m unittest discover -s tests/vpn -p 'test_*.py' -v\`:
**27 executed; 23 passed, 1 assertion failure, 3 unexpected exceptions, 0 skipped.**
These are expected **red tests against unfixed code**, not an accepted build
or a green suite. Three SQLite open-failure cases leak \`sqlite3.OperationalError\`
instead of \`EnrollmentUnavailable\`; the fourth assertion detects hidden
active device after 200 expired historical records. Re-run on a corrected,
independently reviewed source head before any integration decision. No tunnel
or physical DNS/IP probe was executed.
