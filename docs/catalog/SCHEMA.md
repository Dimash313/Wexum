# Wexum planning catalog — current validated contract

The source of truth is `products.json`. `scripts/validate_catalog.py` checks the current pre-release planning representation, not the eventual product lifecycle.

- Root: `organization` = `IhsanSoft`, `ecosystem` = `Wexum`, `hub`, `products`. No other root keys are accepted by the current validator.
- Hub: `name` = `Wexum Hub`; `status` = `planned`.
- Products: exactly 22 entries with distinct, nonempty, lowercase ASCII slug IDs (`[a-z][a-z0-9]*(?:-[a-z0-9]+)*`), a nonempty `Wexum`-prefixed display name, nonempty `category`, `summary`, and `code_owner` strings, strictly boolean `standalone: true`, and `status` and `hub_integration` both `planned`. Every listed field is required; unspecified metadata is rejected rather than silently ignored.

Only `planned` is currently approved as a lifecycle state because no Wexum app has been released. Adding other states, schema fields, non-ASCII IDs or changing the number of products needs an explicit reviewed architecture/catalog decision and corresponding negative tests. This contract does not certify that the product, VPN, Hub or integration is operational.
