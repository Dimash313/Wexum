import test from 'node:test';
import assert from 'node:assert/strict';
import {createI18n} from '../src/index.mjs';

const registry = {
  defaultLocale: 'en-US',
  locales: [
    {tag:'en-US', direction:'ltr', fallback:null},
    {tag:'es-ES', direction:'ltr', fallback:'en-US'},
    {tag:'es-MX', direction:'ltr', fallback:'es-ES'},
    {tag:'ar-SA', direction:'rtl', fallback:'en-US'},
    {tag:'zh-Hans-CN', direction:'ltr', fallback:'en-US'},
    {tag:'zh-Hant-TW', direction:'ltr', fallback:'en-US'},
  ],
  languageDefaults: {en:'en-US', es:'es-ES', ar:'ar-SA', zh:'zh-Hans-CN'},
  scriptDefaults: {'zh-Hans':'zh-Hans-CN', 'zh-Hant':'zh-Hant-TW'},
};
const en = {
  'vpn.hello': {kind:'text',value:'Hello, {name}!',params:['name']},
  'vpn.count': {kind:'plural',argument:'count',params:['count'],forms:{one:'{count} device',other:'{count} devices'}},
  'vpn.state': {kind:'select',argument:'status',params:['status'],forms:{connected:'Connected',disconnected:'Disconnected',other:'Unknown'}},
};
const es = {
  'vpn.hello': {kind:'text',value:'Hola, {name}!',params:['name']},
  'vpn.count': {kind:'plural',argument:'count',params:['count'],forms:{one:'{count} dispositivo',other:'{count} dispositivos'}},
  'vpn.state': {kind:'select',argument:'status',params:['status'],forms:{connected:'Conectado',disconnected:'Desconectado',other:'Desconocido'}},
};
const ar = {
  'vpn.hello': {kind:'text',value:'أهلاً، {name}!',params:['name']},
  'vpn.count': {kind:'plural',argument:'count',params:['count'],forms:{zero:'لا أجهزة',one:'جهاز واحد',two:'جهازان',few:'{count} أجهزة',many:'{count} جهازًا',other:'{count} جهاز'}},
  'vpn.state': {kind:'select',argument:'status',params:['status'],forms:{connected:'متصل',disconnected:'غير متصل',other:'غير معروف'}},
};
const configs = (locale, published=['en-US'], extra={}) => ({registry, catalogs:{'en-US':en,'es-ES':es,'es-MX':es,'ar-SA':ar, 'zh-Hans-CN':en, 'zh-Hant-TW':en},publishedLocales:published,preferredLocale:locale,...extra});
const runtime = (locale, published) => createI18n(configs(locale, published));

test('English text rendering and declared interpolation', () => {
  const i18n=runtime('en-US');
  assert.equal(i18n.t('vpn.hello',{name:'Alex'}),'Hello, Alex!');
});
test('untranslated regional candidate resolves only to independently published base', () => {
  assert.equal(runtime('es-MX',['en-US','es-ES']).locale,'es-ES');
  assert.equal(runtime('es-MX',['en-US']).locale,'en-US');
  assert.equal(runtime('es-MX',['en-US','es-ES','es-MX']).locale,'es-MX');
});
test('script-preserving Chinese fallback avoids another script', () => {
  assert.equal(runtime('zh-Hant-HK',['en-US']).locale,'en-US');
  assert.equal(runtime('zh-Hant-TW',['en-US','zh-Hans-CN']).locale,'en-US');
  const x=runtime('zh-Hant-HK',['en-US','zh-Hant-TW']);
  assert.equal(x.locale,'zh-Hant-TW');
});
test('Arabic sets RTL only when the selected catalog is published', () => {
  assert.equal(runtime('ar-SA',['en-US']).direction,'ltr');
  assert.equal(runtime('ar-SA',['en-US','ar-SA']).direction,'rtl');
});
test('CLDR plural choices for English', () => {
  assert.equal(runtime('en-US').t('vpn.count',{count:1}),'1 device');
  assert.equal(runtime('en-US').t('vpn.count',{count:3}),'3 devices');
});
test('CLDR plural choices for Arabic zero, two and few', () => {
  const t=runtime('ar-SA',['en-US','ar-SA']);
  assert.equal(t.t('vpn.count',{count:0}),'لا أجهزة');
  assert.equal(t.t('vpn.count',{count:2}),'جهازان');
  assert.equal(t.t('vpn.count',{count:3}),'3 أجهزة');
});
test('select branch and fallback', () => {
  assert.equal(runtime('en-US').t('vpn.state',{status:'connected'}),'Connected');
  assert.equal(runtime('en-US').t('vpn.state',{status:'unexpected'}),'Unknown');
});
test('reject missing key and missing/invalid message parameters', () => {
  const t=runtime('en-US');
  assert.throws(()=>t.t('missing.key'),RangeError);
  assert.throws(()=>t.t('vpn.hello'),TypeError);
  assert.throws(()=>t.t('vpn.count',{count:NaN}),TypeError);
  assert.throws(()=>t.t('vpn.count',{count:Infinity}),TypeError);
  assert.throws(()=>t.t('vpn.state',{status:1}),TypeError);
});
test('rendering plain text preserves user input without interpreting as markup',()=> {
  const out=runtime('en-US').t('vpn.hello',{name:'<script>alert(1)</script>'});
  assert.equal(out,'Hello, <script>alert(1)</script>!');
});
test('reject HTML or unbalanced markup in translation source',()=> {
  const bad=structuredClone(en);
  bad['vpn.hello'].value='<b>Hi</b>';
  assert.throws(()=>createI18n(configs('en-US',['en-US'],{catalogs:{'en-US':bad}})),/raw markup/);
  bad['vpn.hello'].value='Hello {name';
  assert.throws(()=>createI18n(configs('en-US',['en-US'],{catalogs:{'en-US':bad}})),/malformed/);
});
test('reject inconsistent translation keys and undeclared placeholders',()=> {
  const bad=structuredClone(es);
  delete bad['vpn.state'];
  assert.throws(()=>createI18n(configs('es-ES',['en-US','es-ES'],{catalogs:{'en-US':en,'es-ES':bad}})),/keys differ/);
  bad['vpn.state']=structuredClone(es['vpn.state']);
  bad['vpn.hello'].value='Hola {hacker}';
  assert.throws(()=>createI18n(configs('es-ES',['en-US','es-ES'],{catalogs:{'en-US':en,'es-ES':bad}})),/undeclared placeholder/);
});
test('reject changes to message signatures or select branches',()=> {
  const bad=structuredClone(es);
  bad['vpn.count'].argument='amount';
  assert.throws(()=>createI18n(configs('es-ES',['en-US','es-ES'],{catalogs:{'en-US':en,'es-ES':bad}})),TypeError);
  bad['vpn.count']=structuredClone(es['vpn.count']);
  delete bad['vpn.state'].forms.connected;
  assert.throws(()=>createI18n(configs('es-ES',['en-US','es-ES'],{catalogs:{'en-US':en,'es-ES':bad}})),/select branches/);
});
test('do not infer publication from planned locale metadata', () => {
  assert.throws(()=>createI18n(configs('ar-SA',['ar-SA'])),/default-language/);
  assert.throws(()=>createI18n(configs('ar-SA',['en-US','ar-SA'],{catalogs:{'en-US':en}})),/missing published/);
  assert.throws(()=>createI18n(configs('xx-ZZ',['en-US','xx-ZZ'])),/unknown or missing/);
});
test('language-only locale, casing, and unknown locale fallback', () => {
  assert.equal(runtime('es',['en-US','es-ES']).locale,'es-ES');
  assert.equal(runtime('es_mx',['en-US','es-ES']).locale,'es-ES');
  assert.equal(runtime('XX-YY').locale,'en-US');
});
test('Intl number and date formatting delegate to CLDR environment', () => {
  const i18n=runtime('en-US');
  assert.equal(i18n.number(5000),new Intl.NumberFormat('en-US').format(5000));
  const t=new Date('2024-01-02T12:00:00Z');
  assert.equal(i18n.date(t,{timeZone:'UTC',year:'numeric'}),'2024');
});
test('unexpected parameters do not bypass the declared translation interface', () => {
  assert.throws(() => runtime('en-US').t('vpn.hello', {name:'Alex', secret:'token'}), /Unexpected/);
});
test('catalog mutations after runtime construction cannot change reviewed text', () => {
  const input=structuredClone(en);
  const i18n=createI18n(configs('en-US', ['en-US'], {catalogs:{'en-US':input}}));
  input['vpn.hello'].value='<h1>changed</h1>';
  input['vpn.count'].forms.one='tampered';
  input['vpn.hello'].params.push('secret');
  assert.equal(i18n.t('vpn.hello',{name:'Alex'}),'Hello, Alex!');
  assert.equal(i18n.t('vpn.count',{count:1}),'1 device');
});
test('compiled runtime is immutable at the public API level',()=>{
  const i18n=runtime('en-US');
  assert.ok(Object.isFrozen(i18n));
  assert.throws(()=>{i18n.direction='rtl';},TypeError);
});
