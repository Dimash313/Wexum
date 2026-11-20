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
