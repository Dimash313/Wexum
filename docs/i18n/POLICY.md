# Wexum Global Localization Architecture

Status: **PLANNED**. Owner: issue #44. Depends on Wexum Experience PR #42 and foundation PR #1.

## International scope
The machine-readable registry includes **102 planned regional locales spanning 81 languages**. This is a planning catalog, **not 102 completed translations**. Launch order is subject to market research, security/legal reviews, translation budgets and native speaker verification. All entries are currently `translationStatus: planned`.

- **Priority candidates (20)**: English US/UK; Russian; Kazakh; Arabic (Saudi Arabia); Spanish Spain/Mexico; Portuguese Brazil/Portugal; French; German; Italian; Turkish; Hindi; Indonesian; Simplified and Traditional Chinese; Japanese; Korean; Urdu.
- **Growth candidates (62)**: European, Southeast and South Asian, Middle Eastern, Caucasus, Central Asian and African languages and regional alternatives.
- **Later candidates (20)**: additional regional Spanish/French/German/Arabic variants, other scripts for Punjabi and Uzbek, Sorani Kurdish, Uyghur, Dhivehi, Tajik and regional European languages.

The priority tier does not promise simultaneous release. A locale is publicly selectable only after its actual message catalog, formatting and QA pass.

## Foundations
1. Use canonical **BCP 47** language-script-region identifiers (e.g., `zh-Hant-TW`, `sr-Latn-RS`, `pa-Arab-PK`). Registry validator checks only the restricted tag shapes in our current catalog, **not** the entire BCP 47 grammar. Adopt CLDR/ICU for production locale data and canonicalization.
2. User-selected display language is separate from account country, purchase region, billing currency, server location and device timezone. No IP-based language assumptions.
3. Maintain separate `lang` and `dir` metadata. Some languages use multiple scripts; **do not infer writing direction solely from a language tag**. Require RTL review for Arabic, Persian, Hebrew, Urdu, Pashto, Arabic-script Punjabi, Central Kurdish, Uyghur and Dhivehi.
4. Explicit fallback by script and region; never silently substitute Simplified Chinese for Traditional Chinese or Latin for Arabic/Cyrillic scripts. Bidi isolate embedded emails, URLs, phone numbers, numeric IDs, IP addresses and passwords with platform-correct APIs.
5. Format dates/time, timezone, number grouping, currencies, units, names and grammatical plural categories via CLDR/ICU and `Intl` / native platform equivalents. Never manually concatenate strings or hard-code word order.

## Translation contract
- Message keys are stable and namespaced by product. All user-facing strings, accessibility labels, validation errors, security alerts and onboarding instructions use keys rather than inline literal text.
- Use a plural/select-capable ICU MessageFormat-compatible representation with structured arguments. Parameter placeholders are typed; untranslated or extra placeholders fail CI.
- Zero, one, two, few, many and other plural behavior depends on language data; do not assume English plural rules.
- No raw HTML or executable templates in translation strings. Enforce escaping, length budgets, interpolation checks and translator-safe markup.
- Pseudolocales such as `en-XA` and `ar-XB` are **test-only fixtures**, not actual supported languages or public selections.
- Test at least 35–50% text expansion, line breaks, typography and keyboard navigation with localized scripts. Support dynamic text scaling; avoid fixed-height labels.
- For VPN, payment, privacy, account recovery, permission dialogs and legal terms, require human reviews by competent native speakers before shipping. Machine translation can assist drafts but not substitute for final verification.
- Maintain a glossary and locked terminology for network/security/UI states. The string "Protected" may only display when authoritative native tunnel status confirms it.

## International product release gate
A planned locale becomes available per product only after:
- Translation completeness for its required message namespaces, validated placeholders and plural branches.
- Human review and sign-off for high-impact security, legal, subscription and recovery text.
- Native device tests for font shaping, script direction, punctuation, bidi isolation, truncation, focus/navigation, screen readers, large text and locale-specific formats.
- Store listing metadata, support and privacy/legal coverage for launch country, where required.
- An approved, authenticated **published catalog inventory**. Registry's `planned` records do **not** grant availability. Avoid false "102 languages supported" marketing.
- Religious/ethical review for affected product content and commercial terms remains a separate gate.

## Explicit dependencies and backlog
- Proposed registry: `docs/i18n/locales.json`.
- Validator and fallback test examples: `docs/i18n/validate_locales.py` and `docs/i18n/test_locales.py`. These are **reference tooling**, not production clients.
- Next implementation: approved `packages/i18n/` shared library, web/native adapters, translation pipeline, per-product message catalogs, telemetry without PII and staged locale acceptance.
- Shared CI wiring must be handled by an integration issue after PR #1 and PR #42 are approved; do not edit shared CI in this independent i18n PR.

## Sources and standards
- Unicode CLDR/UTS #35: https://www.unicode.org/reports/tr35/
- W3C Language Tags and Locale Identifiers: https://www.w3.org/International/articles/language-tags/
- W3C Strings on the Web / direction metadata: https://www.w3.org/TR/string-meta/

Decisions about actual market priority, translations and app store offerings require independent evidence.
