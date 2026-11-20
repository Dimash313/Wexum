# Wexum i18n runtime — experimental / blocked on upstream review

Issue #46. This isolated, dependency-free ECMAScript module implements basic text messages, structured CLDR-driven plural choice via `Intl.PluralRules`, select branches, number/date formatting, script-aware locale selection and catalog validation. It is **NOT** a complete ICU MessageFormat implementation and has **not** been approved as a product runtime.

Catalog keys are dot-separated, e.g. `vpn.status`. A message is one of:

```json
{
  "vpn.greeting": {"kind":"text","value":"Hello, {name}","params":["name"]},
  "vpn.devices": {"kind":"plural","argument":"count","params":["count"],"forms":{"one":"{count} device","other":"{count} devices"}}
}
```

`createI18n({registry, catalogs, publishedLocales, preferredLocale})` requires a **trusted, independently approved** published-locale allowlist; the 102 planned locales in `docs/i18n/locales.json` do not make any translation available. The default locale must have a complete catalog. All published catalogs require matching keys and argument signatures. Regional/script fallbacks always resolve only into published locales.

```sh
cd packages/i18n
npm test
```

The module returns **plain text**, not trusted HTML. Render using `textContent`, React text nodes or native text widgets; **never** pass the output to `innerHTML` or an HTML parser. Translation patterns reject angle brackets and arbitrary JS templates, but interpolated user input is not HTML-escaped. Apps must use a trustworthy source for connection/protection state. Do not put secrets in localization metadata.

**Limitations:** full ICU MessageFormat parsing, CLDR data packaging and licensing, production token/format interpolation, named-key type generation, pseudolocale coverage, visual regression, accessibility tests, translation verification, and release approvals all remain separate tasks. Node.js `Intl` support must be confirmed on the supported mobile browsers and native JS runtimes. No paid dependencies or services are introduced.

## Automatic language selection — prototype API

Apps should default to the OS **per-app language** (when supported), then the OS/browser ordered preferred languages, with no mandatory first-run language picker. An explicit Wexum in-app selection is persisted until the user selects **System Default** again. No IP, SIM, server, VPN exit-node, billing country or physical location detection is used.

Browser integration can inject `navigator` and `localStorage` (in a browser context only), without accessing globals from the i18n package:

```js
import {
  browserLanguagePreferences, browserPreferenceStore, createLanguageController,
  createI18n
} from '@wexum/i18n';

const language = createLanguageController({
  registry,
  publishedLocales, // authenticated, reviewed per-product release inventory
  getSystemLanguages: () => browserLanguagePreferences(navigator),
  store: browserPreferenceStore(localStorage, 'wexum.ui.language'),
});
const selected = await language.initialize();
const translator = createI18n({
  registry, catalogs, publishedLocales, preferredLocale: selected.locale
});
// Render only through safe text nodes; use selected.direction for the view.
```

`language.setLanguage('es-ES')` persists an explicit published locale. `language.useSystemLanguage()` clears it. `language.refresh()` reads OS settings again; call it when the app resumes or when the host reports a language change, and rerender on `language.subscribe(callback)`. This package **does not install OS listeners or access storage automatically**.

For Android/iOS/desktop, the host must inject the platform's ordered **per-app language** preferences and a durable, product-scoped preference store. Web storage is origin-scoped; it does not provide cross-domain or cross-device synchronization. Storage failures are reported rather than falsely claiming a choice was saved. Server-side rendering must use request-provided preferences and must not access browser globals.

System locale preference and manual override are **display preferences**, never authorization inputs. The registry is a plan; the runtime only exposes locales present in the independently approved `publishedLocales` catalog inventory. Do not mistake these APIs for completed UI integration, platform QA, or 102 finished translations.
