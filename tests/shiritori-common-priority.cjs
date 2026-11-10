const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),p=require('../shiritori-vocabulary.js');
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
const ctx=vm.createContext({ShiritoriVocabulary:p,window:{},Math,ST:{level:5},norm:x=>x});
vm.runInContext(html.match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)[0],ctx);
vm.runInContext(html.slice(html.indexOf('function rowForLevel('),html.indexOf('function lookupRow(')),ctx);
vm.runInContext(html.slice(html.indexOf('function chooseWeightedWord('),html.indexOf('function chooseCpuFromPool(')),ctx);
ctx.csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
const rows=vm.runInContext('parseCSV(csv)',ctx);let changed=0;
const catalog=require('../scripts/shiritori-named-senses.cjs'),names=catalog.load(root);
for(const row of rows)row.namedSenses=row.words.map((word,i)=>names.has(catalog.key({reading:row.reading,word,meaning:row.meanings[i]}))||p.isNamedSense(word,row.meanings[i]));
for(const r of JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-27-game512.review.json'),'utf8')))assert.ok(names.has(catalog.key(r)),'Game-title source records must be classified exactly');
for(const file of ['2026-10-28-entertainment','2026-10-29-anime-novels','2026-10-29-foreign-cinema','2026-10-29-manga1000','2026-10-29-music2026','2026-10-29-oricon1990-2025','2026-10-29-companies-brands','2026-10-28-characters1024']){
  const entries=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports',file+'.review.json'),'utf8'));
  for(const r of entries)assert.ok(p.isNamedSense(r.word,r.meaning),'Known title/name intake must be classified: '+r.word);
}
for(const row of rows){
  row.genres=row.words.map((w,i)=>'genre-'+i);
  const ordered=p.preferGeneral(row);
  if(ordered!==row)changed++;
  let sawNamed=false;
  ordered.words.forEach((w,i)=>{
    const key=JSON.stringify([w,ordered.meanings[i],ordered.meaningLevels[i],ordered.imagequeries[i],ordered.genres[i]]);
    assert.ok(row.words.some((v,j)=>key===JSON.stringify([v,row.meanings[j],row.meaningLevels[j],row.imagequeries[j],row.genres[j]])),'Word/meaning/image/grade/genre must stay together');
    const named=p.namedAt(ordered,i);assert.ok(!sawNamed||named,'General meanings must precede titles/names: '+row.reading);sawNamed||=named;
  });
  assert.equal(p.preferGeneral(ordered),ordered,'Ordering is idempotent');
}
for(const meaning of ['昔話や伝説などに登場する不思議な存在。','キャラクターをうごかしてあそぶゲーム。','野球チームのメンバーに選ばれた人。'])assert.equal(p.isNamedSense('一般語',meaning),false);
const named={reading:'きんぞくばっと',words:['金属バット'],meanings:['お笑いグループ：テスト。'],meaningLevels:[5],imagequeries:[{asset:null}],genres:['entertainment'],level:5};
const ordinary={reading:'こいる',words:['コイル'],meanings:['電線を巻いたもの。'],meaningLevels:[3],imagequeries:[{asset:'coil.png'}],genres:['technology'],level:3};
ctx.pool=[named,ordinary];
for(let i=0;i<100;i++)assert.equal(vm.runInContext('chooseWeightedWord(pool)',ctx),ordinary);
ctx.pool=[named];assert.equal(vm.runInContext('chooseWeightedWord(pool)',ctx),named,'Explicit named-only genre remains playable');
const mixed={...named,words:[...named.words,...ordinary.words],meanings:[...named.meanings,...ordinary.meanings],meaningLevels:[5,3],imagequeries:[...named.imagequeries,...ordinary.imagequeries],genres:['entertainment','technology']};
const projected=p.project(mixed,[1]);assert.deepEqual(projected.genres,['technology']);assert.equal(projected.imagequeries[0].asset,'coil.png');
const Dictionary=require('../shiritori-dictionary.js'),dictionary=new Dictionary();
const oldStyle={...named,meanings:['古い取り込みで名称の種別が書かれていない説明。'],namedSenses:[true]};
const merged=dictionary.merge(oldStyle,{...ordinary,reading:oldStyle.reading,namedSenses:[false]});
const orderedMerge=p.preferGeneral(merged);assert.equal(orderedMerge.meanings[0],ordinary.meanings[0]);assert.deepEqual(orderedMerge.namedSenses,[false,true]);
assert.equal(p.namedOnly(p.project(orderedMerge,[1])),true,'Metadata classification survives pack merge and genre projection');
ctx.row=mixed;const r=vm.runInContext('rowForLevel(row)',ctx);assert.equal(r.words[0],'コイル');assert.equal(r.imagequeries[0].asset,'coil.png');
assert.match(html,/sort\(ShiritoriVocabulary.compareGeneral\)\.slice\(0,12\)/,'Hint ordering must happen before limiting the list');
console.log(JSON.stringify({passed:true,readingsChecked:rows.length,reorderedReadings:changed}));
