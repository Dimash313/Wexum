/**
 * Platform-neutral language selection. Host apps inject OS/browser preferences
 * and durable storage; this package never accesses the device or network itself.
 * A planned locale is not a published translation.
 */

function normalize(tag) {
  if (typeof tag !== 'string' || tag.length > 80) return null;
  try {
    return Intl.getCanonicalLocales(tag.trim().replaceAll('_', '-'))[0] ?? null;
  } catch (error) {
    if (error instanceof RangeError) return null;
    throw error;
  }
}

export function browserLanguagePreferences(navigatorLike) {
  if (!navigatorLike) return [];
  const list = Array.isArray(navigatorLike.languages) ? navigatorLike.languages : [];
  const candidates = [...list.slice(0, 20), navigatorLike.language];
  const output = [];
  const seen = new Set();
  for (const item of candidates) {
    const tag = normalize(item);
    if (tag && !seen.has(tag.toLowerCase())) {
      output.push(tag);
      seen.add(tag.toLowerCase());
    }
    if (output.length === 12) break;
  }
  return output;
}

function findCandidate(preference, registry, entries, published) {
  const tag = normalize(preference);
  if (!tag) return null;
  const parts = tag.split('-');
  const language = parts[0];
  const byLower = new Map([...entries.keys()].map(key => [key.toLowerCase(), key]));
  let candidate = byLower.get(tag.toLowerCase());

  if (!candidate) {
    const scriptMappings = Object.keys(registry.scriptDefaults ?? {})
      .filter(key => key.startsWith(language + '-'));
    if (scriptMappings.length) {
      // CLDR likely-subtags resolves zh-HK to Hant, pa-PK to Arab, etc.
      const script = new Intl.Locale(tag).maximize().script;
      candidate = registry.scriptDefaults[language + '-' + script];
      // Do not substitute an unrelated script when no script match exists.
      if (!candidate) return null;
    } else {
      candidate = registry.languageDefaults?.[language];
      if (!candidate) {
        const matches = [...entries.keys()].filter(key => key.split('-')[0] === language);
        if (matches.length === 1) candidate = matches[0];
      }
    }
  }
  if (!candidate) return null;

  const visited = new Set();
  while (candidate && !visited.has(candidate)) {
    // Delay an unrelated English fallback until all system languages were tried.
    if (candidate === registry.defaultLocale && language !== registry.defaultLocale.split('-')[0]) return null;
    if (published.has(candidate)) return candidate;
    visited.add(candidate);
    candidate = entries.get(candidate)?.fallback;
  }
  return null;
}

export function resolveLanguage({registry, publishedLocales, override = null, systemLanguages = []}) {
  if (!registry || !Array.isArray(registry.locales) || !Array.isArray(publishedLocales) || !Array.isArray(systemLanguages)) {
    throw new TypeError('Invalid locale selection input');
  }
  const published = new Set(publishedLocales);
  const entries = new Map(registry.locales.map(entry => [entry.tag, entry]));
  if (!published.has(registry.defaultLocale) || !entries.has(registry.defaultLocale)) {
    throw new RangeError('Published default locale is required');
  }
  for (const tag of published) {
    if (!entries.has(tag)) throw new RangeError('Unknown published locale');
  }
  const overridden = normalize(override);
  if (overridden) {
    const selected = findCandidate(overridden, registry, entries, published);
    if (selected) return Object.freeze({locale: selected, direction: entries.get(selected).direction, mode: 'manual'});
  }
  for (const preference of systemLanguages.slice(0, 20)) {
    const selected = findCandidate(preference, registry, entries, published);
    if (selected) return Object.freeze({locale: selected, direction: entries.get(selected).direction, mode: 'system'});
  }
  const fallback = registry.defaultLocale;
  return Object.freeze({locale: fallback, direction: entries.get(fallback).direction, mode: 'system'});
}

export function browserPreferenceStore(storage, key = 'wexum.ui.language') {
  if (!storage || !['getItem', 'setItem', 'removeItem'].every(method => typeof storage[method] === 'function')) {
    throw new TypeError('Provide a compatible browser storage adapter');
  }
  if (typeof key !== 'string' || !/^[a-z0-9._-]{1,96}$/.test(key)) {
    throw new TypeError('Invalid preference key');
  }
  return Object.freeze({
    load: () => storage.getItem(key),
    save: value => storage.setItem(key, value),
    clear: () => storage.removeItem(key),
  });
}

/**
 * Explicitly asynchronous controller for browser and native host adapters.
 * Native hosts should supply their ordered per-app OS language preferences.
 * System language changes are applied by calling refresh(), e.g. on app resume.
 */
export function createLanguageController({registry, publishedLocales, getSystemLanguages, store}) {
  if (!Array.isArray(publishedLocales) || typeof getSystemLanguages !== 'function' || !store ||
      !['load', 'save', 'clear'].every(method => typeof store[method] === 'function')) {
    throw new TypeError('Language controller requires system and durable preference adapters');
  }
  // Snapshot catalog inventory: the caller cannot silently enable an unreviewed translation.
  const trustedLocales = Object.freeze([...publishedLocales]);
  let override = null;
  let snapshot = null;
  let queue = Promise.resolve();
  const subscribers = new Set();

  function commit(next) {
    const changed = !snapshot || snapshot.locale !== next.locale ||
      snapshot.direction !== next.direction || snapshot.mode !== next.mode;
    snapshot = next;
    if (changed) for (const subscriber of subscribers) subscriber(next);
    return next;
  }

  function enqueue(task) {
    const next = queue.then(task);
    queue = next.then(() => undefined, () => undefined);
    return next;
  }

  function calculate(systemLanguages) {
    return resolveLanguage({registry, publishedLocales: trustedLocales, override, systemLanguages});
  }

  function readSystem() {
    return Promise.resolve().then(getSystemLanguages).then(languages => {
      if (!Array.isArray(languages)) throw new TypeError('System language adapter must return an array');
      return languages;
    });
  }

  return Object.freeze({
    get current() { return snapshot; },
    subscribe(listener) {
      if (typeof listener !== 'function') throw new TypeError('Listener must be a function');
      subscribers.add(listener);
      return () => subscribers.delete(listener);
    },
    initialize() {
      return enqueue(async () => {
        const saved = await store.load();
        if (saved !== null && saved !== undefined && typeof saved !== 'string') {
          throw new TypeError('Invalid stored language preference');
        }
        override = saved;
        return commit(calculate(await readSystem()));
      });
    },
    refresh() {
      return enqueue(async () => {
        if (!snapshot) throw new Error('Initialize language controller first');
        // A manual choice stays stable without querying an unrelated OS source.
        if (override) return snapshot;
        return commit(calculate(await readSystem()));
      });
    },
    setLanguage(language) {
      return enqueue(async () => {
        if (!snapshot) throw new Error('Initialize language controller first');
        const canonical = normalize(language);
        if (!canonical || !trustedLocales.includes(canonical)) {
          throw new RangeError('Only a published language may be selected manually');
        }
        // Persist before changing the in-memory state; report storage failures.
        await store.save(canonical);
        override = canonical;
        const entry = registry.locales.find(item => item.tag === canonical);
        return commit(Object.freeze({locale: canonical, direction: entry.direction, mode: 'manual'}));
      });
    },
    useSystemLanguage() {
      return enqueue(async () => {
        if (!snapshot) throw new Error('Initialize language controller first');
        const languages = await readSystem();
        await store.clear();
        override = null;
        return commit(calculate(languages));
      });
    },
  });
}
