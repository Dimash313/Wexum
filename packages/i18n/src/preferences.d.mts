/** Platform-neutral proposed language preference API. No automatic OS access. */
export type LocaleDirection = 'ltr' | 'rtl';
export type LocaleMode = 'system' | 'manual';
export type SelectedLanguage = Readonly<{
  locale: string;
  direction: LocaleDirection;
  mode: LocaleMode;
}>;
export interface LocaleRegistry {
  defaultLocale: string;
  locales: Array<{tag: string; direction: LocaleDirection; fallback: string | null}>;
  languageDefaults: Record<string, string>;
  scriptDefaults: Record<string, string>;
}
export interface PreferenceStore {
  load(): Promise<string | null> | string | null;
  save(language: string): Promise<void> | void;
  clear(): Promise<void> | void;
}
export interface LanguageController {
  readonly current: SelectedLanguage | null;
  subscribe(listener: (selection: SelectedLanguage) => void): () => void;
  initialize(): Promise<SelectedLanguage>;
  refresh(): Promise<SelectedLanguage>;
  setLanguage(language: string): Promise<SelectedLanguage>;
  useSystemLanguage(): Promise<SelectedLanguage>;
}
export function browserLanguagePreferences(navigatorLike: {
  readonly languages?: readonly string[];
  readonly language?: string;
} | null | undefined): string[];
export function browserPreferenceStore(storage: {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}, key?: string): PreferenceStore;
export function resolveLanguage(config: {
  registry: LocaleRegistry;
  publishedLocales: string[];
  override?: string | null;
  systemLanguages?: string[];
}): SelectedLanguage;
export function createLanguageController(config: {
  registry: LocaleRegistry;
  publishedLocales: string[];
  getSystemLanguages: () => string[] | Promise<string[]>;
  store: PreferenceStore;
}): LanguageController;
