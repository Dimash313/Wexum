# WexumVPN product requirements

## Primary user journeys
- Sign in via an eligible Wexum account; register and revoke devices.
- View transparent plans and limits; know whether a subscription is active.
- Connect/disconnect using OS-approved native capabilities.
- See actual state: connecting / protected / interrupted / disconnected / error; never fake a successful connection.
- Choose available locations from real node health, not decorative country labels.
- Handle network switching, app backgrounding, expiring grants, server outage and offline management API.
- Understand the honest privacy policy and data-removal behavior.

## Initial acceptance
- Document supported OS and API permissions.
- Validate device ownership and subscription on control-plane mutations.
- Test replay, expiry, clock skew, revocation and cross-tenant access.
- Test real connection continuity and DNS/IP leak scenarios on each target OS.
- Provide deterministic integration test rigs with no production credentials.
- Measure node throughput, egress cost, failure behavior and restoration.
- Receive store, legal and religious review before customer-facing release.

Unimplemented items are requirements, not delivered features.

