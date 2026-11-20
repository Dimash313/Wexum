# Localization Engineer Handoff

## One team, reusable across the ecosystem
The owner of issue #44 maintains the planned registry, fallback policy, testing and approved terminology framework. Product engineers must consume approved i18n adapters, not re-create language settings per product.

## Build order
1. Approve BCP 47 registry, script metadata, language selection and fallback design.
2. Select CLDR/ICU-compatible production translation stack for TS/React Native/native clients, with license/security review.
3. Add the shared `packages/i18n/` API and typed translation catalogs in a separate PR after contracts are approved.
4. Implement per-product bundles and mark locales *available only by product* after human review.
5. Add CI for unused/missing keys, placeholders, RTL/pseudolocales, plural branches and format correctness.
6. Run device screenshot, screen-reader and native-speaker QA before marketing any locale.

## Reference checks (not automatically enforced yet)
```sh
python docs/i18n/validate_locales.py
python -m unittest discover -s docs/i18n -p "test_*.py" -v
```

A passing registry validator does not constitute a completed translation or global store launch.
