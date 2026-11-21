# Wexum planning catalog — current validated contract

The source of truth is `products.json`. `scripts/validate_catalog.py` checks the current pre-release planning representation, not the eventual product lifecycle.

- Root: `organization` = `IhsanSoft`, `ecosystem` = `Wexum`, `hub`, `products`. No other root keys are accepted by the current validator.
- Hub: `name` = `Wexum Hub`; `status` = `planned`.
- Products: exactly 22 entries with distinct, nonempty, lowercase ASCII slug IDs (`[a-z][a-z0-9]*(?:-[a-z0-9]+)*`), a nonempty `Wexum`-prefixed display name, nonempty `category`, `summary`, and `code_owner` strings, strictly boolean `standalone: true`, and `status` and `hub_integration` both `planned`. Every listed field is required; unspecified metadata is rejected rather than silently ignored.

Only `planned` is currently approved as a lifecycle state because no Wexum app has been released. Adding other states, schema fields, non-ASCII IDs or changing the number of products needs an explicit reviewed architecture/catalog decision and corresponding negative tests. This contract does not certify that the product, VPN, Hub or integration is operational.

## Immutable identity baseline

The 22 existing `id` → `name` bindings from the reviewed initial planning catalog are explicitly pinned as `_APPROVED_PRODUCT_IDENTITIES` in `scripts/validate_catalog.py`. Normal edits to descriptions/categories/owners do not reassign product identity, and changing the order of the catalog is allowed. Editing an existing ID, removing it or swapping IDs/names is rejected even if all slugs remain syntactically valid.

Any deliberate future ID migration requires an explicit compatibility ADR, consumer/reference migration and rollback plan, approved updates to both catalog and validator, and independent review with regression tests. Neither editing `products.json` nor changing this validator alone constitutes approval for an ID migration. This gate prevents accidental edits, not malicious changes to both files by an authorized writer.
