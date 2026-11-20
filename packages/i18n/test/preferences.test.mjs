import test from 'node:test';
import assert from 'node:assert/strict';
import {
  browserLanguagePreferences,
  browserPreferenceStore,
  createLanguageController,
  resolveLanguage,
} from '../src/preferences.mjs';

const registry = {
  defaultLocale: 'en-US',
  locales: [
    {tag: 'en-US', direction: 'ltr', fallback: null},
    {tag: 'es-ES', direction: 'ltr', fallback: 'en-US'},
    {tag: 'es-MX', direction: 'ltr', fallback: 'es-ES'},
    {tag: 'fr-FR', direction: 'ltr', fallback: 'en-US'},
    {tag: 'fr-CA', direction: 'ltr', fallback: 'fr-FR'},
    {tag: 'ar-SA', direction: 'rtl', fallback: 'en-US'},
    {tag: 'zh-Hans-CN', direction: 'ltr', fallback: 'en-US'},
    {tag: 'zh-Hant-TW', direction: 'ltr', fallback: 'en-US'},
    {tag: 'pa-Guru-IN', direction: 'ltr', fallback: 'en-US'},
    {tag: 'pa-Arab-PK', direction: 'rtl', fallback: 'en-US'},
    {tag: 'sr-Cyrl-RS', direction: 'ltr', fallback: 'en-US'},
    {tag: 'sr-Latn-RS', direction: 'ltr', fallback: 'en-US'},
    {tag: 'sw-KE', direction: 'ltr', fallback: 'en-US'},
  ],
  languageDefaults: {
    en:'en-US', es:'es-ES', fr:'fr-FR', ar:'ar-SA',
    zh:'zh-Hans-CN', pa:'pa-Guru-IN', sr:'sr-Cyrl-RS',
  },
  scriptDefaults: {
    'zh-Hans':'zh-Hans-CN', 'zh-Hant':'zh-Hant-TW',
    'pa-Guru':'pa-Guru-IN', 'pa-Arab':'pa-Arab-PK',
    'sr-Cyrl':'sr-Cyrl-RS', 'sr-Latn':'sr-Latn-RS',
  },
};
const published = ['en-US', 'es-ES', 'ar-SA', 'zh-Hant-TW'];
const choose = (systemLanguages, override=null, available=published) =>
  resolveLanguage({registry, publishedLocales:available, override, systemLanguages});

function memoryStore(initial=null) {
  let stored = initial;
  const operations = [];
  return {
    operations,
    load: async () => stored,
    save: async locale => { operations.push(['save',locale]); stored=locale; },
    clear: async () => { operations.push(['clear']); stored=null; },
    get stored() { return stored; },
  };
}

test('browser reads ordered language preferences without using country or IP address', () => {
  const languages = browserLanguagePreferences({languages:['fr-CA','es-MX'],language:'en-US'});
  assert.deepEqual(languages,['fr-CA','es-MX','en-US']);
});
test('browser single language fallback and invalid inputs', () => {
  assert.deepEqual(browserLanguagePreferences({language:'ar-sa'}), ['ar-SA']);
  assert.deepEqual(browserLanguagePreferences(null), []);
  assert.deepEqual(browserLanguagePreferences({languages:['??','es_MX','es-mx',123],language:'es-MX'}),['es-MX']);
});
test('browser limits untrusted language preference list', () => {
  const list=Array.from({length:80},(_,i)=>'x'+i+'-ZZ');
  assert.equal(browserLanguagePreferences({languages:list,language:'en-US'}).length,1);
});
test('first available system preference wins, skipping unpublished alternatives', () => {
  assert.equal(choose(['fr-CA','es-MX']).locale,'es-ES');
  assert.equal(choose(['ar-SA','es-MX']).locale,'ar-SA');
});
test('an explicit English preference beats later published languages', () => {
  assert.equal(choose(['en-US','ar-SA']).locale,'en-US');
});
test('regional language fallback preserves language when available', () => {
  assert.equal(choose(['es-MX']).locale,'es-ES');
});
test('unknown language defaults to published English', () => {
  assert.deepEqual(choose(['xx-YY']),{locale:'en-US',direction:'ltr',mode:'system'});
});
test('explicit override wins over system language', () => {
  assert.deepEqual(choose(['ar-SA'],'es-ES'),{locale:'es-ES',direction:'ltr',mode:'manual'});
});
test('unavailable stale override follows system languages', () => {
  assert.deepEqual(choose(['ar-SA'],'fr-CA'),{locale:'ar-SA',direction:'rtl',mode:'system'});
});
test('Arabic RTL is based on selected published language, not requested unsupported one', () => {
  assert.equal(choose(['ar-SA'],null,['en-US']).direction,'ltr');
  assert.equal(choose(['ar-SA']).direction,'rtl');
});
test('Hong Kong Chinese defaults to Traditional script when published', () => {
  assert.equal(choose(['zh-HK']).locale,'zh-Hant-TW');
  assert.equal(choose(['zh-Hant-HK']).locale,'zh-Hant-TW');
});
test('a missing Traditional Chinese translation never silently switches to Simplified', () => {
  assert.equal(choose(['zh-HK'],null,['en-US','zh-Hans-CN']).locale,'en-US');
  assert.equal(choose(['zh-Hant-HK'],null,['en-US','zh-Hans-CN']).locale,'en-US');
});
test('Punjabi in Pakistan resolves to Arabic script and Serbian selects its script', () => {
  assert.equal(choose(['pa-PK'],null,['en-US','pa-Arab-PK','pa-Guru-IN']).locale,'pa-Arab-PK');
  assert.equal(choose(['sr-Latn-BA'],null,['en-US','sr-Latn-RS']).locale,'sr-Latn-RS');
});
test('missing Punjabi Arabic script does not select Gurmukhi', () => {
  assert.equal(choose(['pa-PK'],null,['en-US','pa-Guru-IN']).locale,'en-US');
});
test('unambiguous language with no default mapping is selected', () => {
  assert.equal(choose(['sw-TZ'],null,['en-US','sw-KE']).locale,'sw-KE');
});
test('selection cannot invent publication or proceed without English baseline', () => {
  assert.throws(()=>choose(['es-ES'],null,['es-ES']),/Published default/);
  assert.throws(()=>choose(['es-ES'],null,['en-US','xx-YY']),/Unknown published/);
  assert.throws(()=>resolveLanguage({registry,publishedLocales:[],systemLanguages:[]}),/Published default/);
});
test('language selection output cannot be mutated', () => {
  assert.ok(Object.isFrozen(choose(['ar-SA'])));
});
test('browser store maps to injected browser storage and persists only UI preference', async () => {
  const raw=new Map();
  const storage={
    getItem:key=>raw.get(key)??null,
    setItem:(key,value)=>raw.set(key,value),
    removeItem:key=>raw.delete(key),
  };
  const adapter=browserPreferenceStore(storage,'product.locale');
  assert.equal(adapter.load(),null);
  adapter.save('es-ES');
  assert.equal(adapter.load(),'es-ES');
  adapter.clear();
  assert.equal(adapter.load(),null);
});
test('rejects an invalid browser storage adapter or key',()=>{
  assert.throws(()=>browserPreferenceStore(null),TypeError);
  assert.throws(()=>browserPreferenceStore({}),TypeError);
  const store={getItem(){},setItem(){},removeItem(){}};
  assert.throws(()=>browserPreferenceStore(store,'../../secret'),TypeError);
});
test('initial launch uses system language without mandatory language picker',async()=>{
  const store=memoryStore();
  const controller=createLanguageController({
    registry,publishedLocales:published,store,getSystemLanguages:()=>['ar-SA','en-US'],
  });
  assert.equal(controller.current,null);
  assert.deepEqual(await controller.initialize(),{locale:'ar-SA',direction:'rtl',mode:'system'});
  assert.deepEqual(store.operations,[]);
});
test('saved manual choice has precedence and survives controller restart',async()=>{
  const store=memoryStore();
  const make=()=>createLanguageController({
    registry,publishedLocales:published,store,getSystemLanguages:()=>['ar-SA'],
  });
  const first=make();
  await first.initialize();
  await first.setLanguage('es-ES');
  assert.equal(store.stored,'es-ES');
  const second=make();
  assert.deepEqual(await second.initialize(),{locale:'es-ES',direction:'ltr',mode:'manual'});
});
test('following system-language changes only in system mode',async()=>{
  let languages=['ar-SA'];
  const controller=createLanguageController({
    registry,publishedLocales:published,store:memoryStore(),getSystemLanguages:()=>languages,
  });
  await controller.initialize();
  languages=['es-MX'];
  assert.equal((await controller.refresh()).locale,'es-ES');
  await controller.setLanguage('ar-SA');
  languages=['en-US'];
  assert.deepEqual(await controller.refresh(),{locale:'ar-SA',direction:'rtl',mode:'manual'});
});
test('resetting manual choice returns to current system language and deletes preference',async()=>{
  const store=memoryStore('ar-SA');
  const controller=createLanguageController({
    registry,publishedLocales:published,store,getSystemLanguages:()=>['es-MX'],
  });
  await controller.initialize();
  assert.equal((await controller.useSystemLanguage()).locale,'es-ES');
  assert.equal(store.stored,null);
  assert.equal(controller.current.mode,'system');
});
test('unpublished languages cannot be selected through settings',async()=>{
  const store=memoryStore();
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>['en-US']});
  await c.initialize();
  await assert.rejects(c.setLanguage('fr-FR'),RangeError);
  assert.equal(c.current.locale,'en-US');
  assert.deepEqual(store.operations,[]);
});
test('storage write failure leaves previous displayed language unchanged',async()=>{
  const store=memoryStore();
  store.save=async()=>{throw new Error('disk unavailable');};
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>['en-US']});
  await c.initialize();
  await assert.rejects(c.setLanguage('ar-SA'),/disk unavailable/);
  assert.equal(c.current.locale,'en-US');
});
test('storage clearing failure preserves manual selection',async()=>{
  const store=memoryStore('ar-SA');
  store.clear=async()=>{throw new Error('storage denied');};
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>['es-MX']});
  await c.initialize();
  await assert.rejects(c.useSystemLanguage(),/storage denied/);
  assert.equal(c.current.locale,'ar-SA');
});
test('concurrent preference writes are serialized to last explicit selection',async()=>{
  const store=memoryStore();
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>['en-US']});
  await c.initialize();
  await Promise.all([c.setLanguage('ar-SA'), c.setLanguage('es-ES')]);
  assert.equal(store.stored,'es-ES');
  assert.equal(c.current.locale,'es-ES');
});
test('change subscriptions notify on changes but not unchanged refresh',async()=>{
  const store=memoryStore();
  let language=['en-US'];
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>language});
  const notices=[];
  const unsubscribe=c.subscribe(v=>notices.push(v.locale));
  await c.initialize();
  await c.refresh();
  language=['ar-SA'];
  await c.refresh();
  unsubscribe();
  language=['es-MX'];
  await c.refresh();
  assert.deepEqual(notices,['en-US','ar-SA']);
});
test('invalid OS adapter data fails explicitly',async()=>{
  const store=memoryStore();
  const c=createLanguageController({registry,publishedLocales:published,store,getSystemLanguages:()=>null});
  await assert.rejects(c.initialize(),/must return an array/);
});
test('calls before initialization are rejected',async()=>{
  const c=createLanguageController({registry,publishedLocales:published,store:memoryStore(),getSystemLanguages:()=>['en-US']});
  await assert.rejects(c.refresh(),/Initialize/);
  await assert.rejects(c.setLanguage('es-ES'),/Initialize/);
  await assert.rejects(c.useSystemLanguage(),/Initialize/);
});
