/** Draft public contract. TypeScript static keys require a later catalog generator. */
export type LanguageDirection = 'ltr' | 'rtl';
export interface LocaleEntry {
  tag: string;
  fallback: string | null;
  direction: LanguageDirection;
}
export interface LocaleRegistry {
  defaultLocale: string;
  locales: LocaleEntry[];
  languageDefaults: Record<string, string>;
  scriptDefaults: Record<string, string>;
}
export type Message =
  | {kind: 'text'; value: string; params: string[]}
  | {kind: 'plural' | 'select'; argument: string; forms: Record<string, string>; params: string[]};
export type Catalog = Record<string, Message>;
export interface I18nRuntime {
  readonly locale: string;
  readonly direction: LanguageDirection;
  t(key: string, args?: Record<string, string | number | boolean>): string;
  number(value: number | bigint, options?: Intl.NumberFormatOptions): string;
  date(value: Date | number, options?: Intl.DateTimeFormatOptions): string;
}
export function createI18n(config: {
  registry: LocaleRegistry;
  catalogs: Record<string, Catalog>;
  publishedLocales: string[];
  preferredLocale?: string;
}): I18nRuntime;
