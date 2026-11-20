/**
 * Provisional i18n core. A registry entry is NEVER evidence of a published translation.
 * Applications supply an independently approved set of published locales and catalogs.
 * All formatted messages are plain strings; render as text, never as HTML.
 */
const KEY = /^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)+$/;
const ARG = /^[a-zA-Z_][a-zA-Z_0-9]*$/;
const PLURAL_FORMS = new Set(['zero', 'one', 'two', 'few', 'many', 'other']);
const PLACEHOLDER = /\{([a-zA-Z_][a-zA-Z_0-9]*)\}/g;

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function keysEqual(a, b) {
  return a.length === b.length && a.every(k => b.includes(k));
}

function fail(message) {
  throw new TypeError(`Invalid Wexum translation catalog: ${message}`);
}

function checkPattern(value, parameters, key) {
  if (typeof value !== 'string' || value.length > 6000 || /[<>]/.test(value)) {
    fail(`${key}: raw markup, invalid text or oversized pattern`);
  }
  const placeholders = [...value.matchAll(PLACEHOLDER)];
  for (const hit of placeholders) {
    if (!parameters.includes(hit[1])) fail(`${key}: undeclared placeholder ${hit[1]}`);
  }
  if (value.replace(PLACEHOLDER, '').includes('{') || value.replace(PLACEHOLDER, '').includes('}')) {
    fail(`${key}: malformed placeholder syntax`);
  }
}

function validateMessage(key, msg) {
  if (!KEY.test(key) || !isRecord(msg)) fail(`${key}: invalid key/message`);
  const {kind, params = [], argument} = msg;
  if (!Array.isArray(params) || !params.every(p => typeof p === 'string' && ARG.test(p)) || new Set(params).size !== params.length) {
    fail(`${key}: invalid placeholder declaration`);
  }
  if (kind === 'text') {
    if (Object.hasOwn(msg, 'argument') || Object.hasOwn(msg, 'forms')) fail(`${key}: unsupported text message fields`);
    checkPattern(msg.value, params, key);
    return;
  }
  if (!['plural', 'select'].includes(kind) || typeof argument !== 'string' || !params.includes(argument)) {
    fail(`${key}: invalid variant message`);
  }
  if (!isRecord(msg.forms) || !Object.hasOwn(msg.forms, 'other') || Object.keys(msg.forms).length > 30) {
    fail(`${key}: missing other branch or too many branches`);
  }
  for (const [form, pattern] of Object.entries(msg.forms)) {
    if (kind === 'plural' && !PLURAL_FORMS.has(form)) fail(`${key}: invalid plural category ${form}`);
    if (kind === 'select' && !ARG.test(form)) fail(`${key}: invalid select option ${form}`);
    checkPattern(pattern, params, key);
  }
}

function validateCatalogs(catalogs, publishedLocales, registry) {
  if (!isRecord(catalogs) || !Array.isArray(publishedLocales) || publishedLocales.length === 0) {
    fail('published inventory and catalogs are required');
  }
  const supported = new Set(registry.locales.map(l => l.tag));
  if (!publishedLocales.includes(registry.defaultLocale)) fail('default-language catalog must be published');
  if (new Set(publishedLocales).size !== publishedLocales.length) fail('duplicate published locale');
  for (const locale of publishedLocales) {
    if (!supported.has(locale) || !isRecord(catalogs[locale])) fail(`unknown or missing published catalog ${locale}`);
  }
  const base = catalogs[registry.defaultLocale];
  const baseKeys = Object.keys(base);
  if (!baseKeys.length) fail('empty default-language catalog');
  for (const key of baseKeys) validateMessage(key, base[key]);
  for (const locale of publishedLocales) {
    const candidate = catalogs[locale];
    if (!keysEqual(baseKeys, Object.keys(candidate))) fail(`${locale}: catalog keys differ from default`);
    for (const key of baseKeys) {
      const src = base[key], target = candidate[key];
      validateMessage(key, target);
      if (src.kind !== target.kind || src.argument !== target.argument || !keysEqual(src.params, target.params)) {
        fail(`${locale}:${key}: incompatible message signature`);
      }
      if (src.kind === 'select' && !keysEqual(Object.keys(src.forms), Object.keys(target.forms))) {
        fail(`${locale}:${key}: select branches differ`);
      }
    }
  }
}

function snapshotCatalog(catalog) {
  const output = Object.create(null);
  for (const [key, message] of Object.entries(catalog)) {
    const copy = {...message, params: Object.freeze([...message.params])};
    if (message.kind !== 'text') copy.forms = Object.freeze({...message.forms});
    output[key] = Object.freeze(copy);
  }
  return Object.freeze(output);
}

function selectLocale(preferred, registry, published) {
  const entries = new Map(registry.locales.map(l => [l.tag, l]));
  const lowerTags = new Map([...entries.keys()].map(x => [x.toLowerCase(), x]));
  const original = typeof preferred === 'string' ? preferred.trim().replaceAll('_', '-') : '';
  const parts = original.split('-');
  let current = lowerTags.get(original.toLowerCase());
  if (!current && parts.length > 1 && /^[a-z]{4}$/i.test(parts[1])) {
    current = registry.scriptDefaults[`${parts[0].toLowerCase()}-${parts[1][0].toUpperCase()}${parts[1].slice(1).toLowerCase()}`];
  }
  if (!current) current = registry.languageDefaults[parts[0]?.toLowerCase()] || registry.defaultLocale;
  const seen = new Set();
  while (current && !seen.has(current)) {
    if (published.has(current)) return current;
    seen.add(current);
    current = entries.get(current)?.fallback;
  }
  return null;
}

function fill(pattern, args, declared, numberFormatter) {
  return pattern.replace(PLACEHOLDER, (_match, name) => {
    if (!declared.includes(name) || !Object.hasOwn(args, name)) throw new TypeError(`Missing message argument: ${name}`);
    const value = args[name];
    if (value === null || value === undefined || (typeof value !== 'string' && typeof value !== 'number' && typeof value !== 'boolean')) {
      throw new TypeError(`Invalid value for message argument: ${name}`);
    }
    if (typeof value === 'number') {
      if (!Number.isFinite(value)) throw new TypeError(`Invalid finite numeric argument: ${name}`);
      return numberFormatter.format(value);
    }
    return String(value);
  });
}

/**
 * @param {{registry: object, catalogs: Record<string, object>, publishedLocales: string[], preferredLocale?: string}} config
 */
export function createI18n(config) {
  if (!isRecord(config) || !isRecord(config.registry) || !Array.isArray(config.registry.locales) || !isRecord(config.registry.languageDefaults) || !isRecord(config.registry.scriptDefaults)) {
    fail('invalid locale registry');
  }
  const {registry, catalogs, publishedLocales, preferredLocale} = config;
  validateCatalogs(catalogs, publishedLocales, registry);
  const published = new Set(publishedLocales);
  const locale = selectLocale(preferredLocale, registry, published);
  if (!locale) fail('no published fallback catalog');
  const entry = registry.locales.find(x => x.tag === locale);
  if (!entry || !['ltr', 'rtl'].includes(entry.direction)) fail('locale direction missing');
  const catalog = snapshotCatalog(catalogs[locale]);
  const plural = new Intl.PluralRules(locale);
  const numberFormatter = new Intl.NumberFormat(locale);

  return Object.freeze({
    locale,
    direction: entry.direction,
    t(key, args = {}) {
      if (!Object.hasOwn(catalog, key)) throw new RangeError(`Missing translation key: ${key}`);
      const msg = catalog[key];
      if (!isRecord(args)) throw new TypeError('Message arguments must be an object');
      if (Object.keys(args).some(name => !msg.params.includes(name))) {
        throw new TypeError('Unexpected message arguments');
      }
      for (const name of msg.params) {
        if (!Object.hasOwn(args, name)) throw new TypeError(`Missing message argument: ${name}`);
      }
      let pattern;
      if (msg.kind === 'text') pattern = msg.value;
      else if (msg.kind === 'plural') {
        const count = args[msg.argument];
        if (typeof count !== 'number' || !Number.isFinite(count)) throw new TypeError('Plural count must be finite');
        pattern = msg.forms[plural.select(count)] ?? msg.forms.other;
      } else {
        const choice = args[msg.argument];
        if (typeof choice !== 'string') throw new TypeError('Select argument must be a string');
        pattern = Object.hasOwn(msg.forms, choice) ? msg.forms[choice] : msg.forms.other;
      }
      return fill(pattern, args, msg.params, numberFormatter);
    },
    number(value, options) { return new Intl.NumberFormat(locale, options).format(value); },
    date(value, options) { return new Intl.DateTimeFormat(locale, options).format(value); },
  });
}

export {browserLanguagePreferences, browserPreferenceStore, resolveLanguage, createLanguageController} from './preferences.mjs';
