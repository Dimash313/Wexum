# Security policy

Wexum is pre-release research and implementation. No application currently has a production security assurance claim.

## Reporting
Do not disclose security vulnerabilities or credentials in public issues, PRs or chat. Prefer GitHub's **Report a vulnerability** private security advisory workflow if enabled by repository administrators. If unavailable, request a private contact channel from the repository maintainer without posting exploit details.

## Maintainer responsibilities
- Triage reports privately and restrict access to evidence.
- Rotate leaked credentials immediately; removing a committed secret from the latest branch is insufficient.
- Assess affected code, users, environments and data-retention implications.
- Fix and test in an isolated branch, coordinate disclosure after mitigation.
- Document incident recovery and lessons learned without publishing user data.

## Not allowed
Never add real user data, live VPN node credentials, API tokens, payment secrets or private signing keys to tests or source code. Never promise "zero vulnerabilities" or a deployed no-logs policy without independent verification.

## Review focus
Authentication, cross-tenant authorization, VPN key distribution, cloud file ACLs, billing integrity, event replay, dependencies and supply chain.
