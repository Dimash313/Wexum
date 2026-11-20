# Wexum Storefront Localization & ASO Preflight

Status: **PROPOSED / DRAFT ONLY**. Owner: issue #51. This work depends on internationalization PR #45, design PR #42 and foundation PR #1. It does not publish to stores, create developer accounts, or imply WexumVPN is functional or released.

## Separate three language systems

1. **UI locales**: the 102 planned regional entries / 81 languages in the Wexum i18n registry. These are NOT shipped UI translations.
2. **Google Play listing locales**: a separately managed set in Play Console, including localized title, short and long description, and in-language screenshots. Google may provide automated translations when approved versions are missing.
3. **App Store Connect metadata localizations**: a separately supported vendor set. Apple announced **50** store metadata localizations on March 31, 2026, not 102. What customers see may also depend on the local storefront and OS language settings.

Internal uiLocale and storeLocale values in draft manifests are NOT verified store API shortcodes. A human publisher must check every locale against the current platform console/API before export. There is no one-to-one mapping from planned Wexum app locales to store listings.

## Vendor limits, checked 2026-11-21

| Field | Google Play | App Store |
| --- | --- | --- |
| Localized app title | 30 characters | 2–30 characters |
| Short description / subtitle | 80 characters | 30 characters |
| Full description | 4,000 characters | 4,000 characters, plain text |
| Promotional text | Not modeled | 170 characters |
| Dedicated keywords | Not modeled | **100 UTF-8 bytes**, comma-separated; terms longer than 2 characters |
| Screenshots | Localized, based on real app | Localized, based on real app |

For conservative validation, character-limited fields use UTF-16 code unit count. The live storefront counter is authoritative and may differ for complex grapheme clusters.

Official vendor references:
- Google Play setup and field limits: https://support.google.com/googleplay/android-developer/answer/9859152?hl=en
- Google Play localization/automated translations: https://support.google.com/googleplay/android-developer/answer/9844778?hl=en
- Google Play metadata policy: https://support.google.com/googleplay/android-developer/answer/9898842
- Apple name and subtitle: https://developer.apple.com/help/app-store-connect/reference/app-information/app-and-compliance-information
- Apple description, keywords, promotional text: https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/
- Apple store localization list: https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations
- Apple 50-localization announcement: https://developer.apple.com/news/?id=97t4mt64
- Apple app review rules: https://developer.apple.com/app-store/review/guidelines/

## Draft examples and validation

The example at docs/storefront/examples/wexumvpn-drafts.json includes 8 **unapproved internal samples**: 2 stores × English, Spanish, Russian and Arabic. They explicitly state WexumVPN is under development and do not assert working features. No real screenshot, translated application, reviewed copy, verified store-localization shortcode, support website or privacy link is attached. DO NOT upload these samples to stores.

From repository root, run:

    python docs/storefront/validate_metadata.py docs/storefront/examples/wexumvpn-drafts.json
    python -m unittest discover -s docs/storefront -p 'test_*.py' -v

This next command **must fail for the draft samples**, since no review/asset evidence exists:

    python docs/storefront/validate_metadata.py docs/storefront/examples/wexumvpn-drafts.json --preflight

Manifest publicationStatus must remain draft; individual listings can be draft or reviewed, but never published by this tool. An approved/published locale requires independently reviewed translation and verified product behavior.

The stricter preflight gate checks declared reviewers, feature evidence, actual local screenshot file paths and SHA256 hashes, locale documentation references, secure support/privacy URLs and Play contact email. Passing it **does not prove** copy accuracy, real screenshot capture, ownership, language quality or policy compliance. Human verification is mandatory.

## Marketplace launch checklist — per product × locale × store

1. Confirm current store language support, the actual store API shortcode, geographic app availability and relevant local legal restrictions. Distinguish store locale from UI locale.
2. Verify the UI translation exists and passes app tests. Metadata translations alone do not localize the app.
3. Draft truthful names/descriptions and market-specific search terms. Never claim impossible or untested functionality, fastest speed, unconditional zero logs, rank awards, privacy promises or unsupported subscriptions. Human reviewers check trademarks, competitors, keyword relevance and copy.
4. Capture real device screenshots from a functioning approved build in that locale. Never fabricate a protected VPN state. Check crop, text, font shaping, RTL, scaling, accessibility, asset rights and privacy-safe test data. No music or living-being imagery in the default Wexum assets; unresolved ethical issues block release.
5. Publish verified support/privacy URLs, review store age ratings, commerce, export, VPN and jurisdiction requirements. Never invent contact addresses.
6. Review copies with native-language experts, independently verify claims/legal/ethical evidence, recheck vendor limits, inspect actual marketplace previews, and obtain a human publishing decision. Language count is not a promise of proportional traffic growth.

## Ownership and blockers

Scope limited to docs/storefront/ for issue #51. All files are pre-release contracts, tests and draft examples. There is no marketplace API integration, live account, credential, paid service, product runtime change or shared CI modification. Separate issues and independent review must precede any publication or platform integration. PR #45, #42 and #1 remain upstream dependencies.
