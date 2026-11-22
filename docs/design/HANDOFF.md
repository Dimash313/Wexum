# Wexum Experience — implementation handoff

1. Review the proposed decision and token schema in issue #40. Record approval/rejection before moving code to `packages/design-system/`.
2. After acceptance, create separate narrowly scoped issues for web token export, React Native integration and native Android/iOS/Desktop adaptations. Do not create one gigantic app framework.
3. Central component package must be passive UI code: no product data access, no implicit API calls, no global superuser auth.
4. Set up isolated visual regression cases and accessibility checks per component. Measure font scaling, RTL and locale truncation.
5. Track tokens and component API compatibility; product teams own application-specific UX flows and data integrity.
6. For WexumVPN, do not replace OS tunnel status with a simulated connection indicator. Product UX issue #39 coordinates details.
7. New features touching public content, image generators or media follow the religious-review gate before product inclusion.

## Reproducible local proposal checks
```sh
python docs/design/validate_tokens.py
python -m unittest discover -s docs/design -p "test_*.py" -v
```

These validations check **only** machine-readable token constraints. They are not a live UI, production security assessment or accessibility certificate.
