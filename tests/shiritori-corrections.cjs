const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
require('../scripts/shiritori-correction-ledger.cjs').historicalRows();
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ledger=read('data/corrections/2026-10-11-ledger.json');
const lines=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/);const heads=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((x,i)=>[heads[i],x])));
const history=read('data/dictionary-imports/history.json');
const correction=history.findLastIndex(r=>r.type==='vocabulary-corrections');
const previousText=correction<0?fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'):require('../scripts/shiritori-correction-ledger.cjs').undoImports(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),history.slice(correction));
const previousRows=previousText.trim().split(/\r?\n/).slice(1).map(l=>Object.fromEntries(l.split(',').map((x,i)=>[heads[i],x])));
const byOrigin=new Map(ledger.currentOriginalIds.map((id,i)=>[id,previousRows[i]]));
const changes=new Map(ledger.changes.map(c=>[c.originalId,c]));
const ordered=[59,287,291,70,72,75,76,93,96,99,100,423,150,152,169,172,174,214,215,224,240,290,298,305,307,308,318,321,325,361,372,374,391,420,421,424,425,435,478,489,524,531,539,548,572,580,588,612,654,655,658,659,711,720,722,737,752,754,756,761,765,801,810,811];
assert.equal(ordered.length,64);for(const id of ordered)assert.ok(changes.has(id),'Every requested ID resolved: '+id);
for(const [a,b] of [[70,3205],[99,4361],[99,423],[240,3388],[290,1277],[307,3137],[372,1971],[489,4798],[539,4385]])assert.notEqual(byOrigin.get(a).image_asset,byOrigin.get(b).image_asset,'Different scenes split: '+a+'/'+b);
assert.equal(byOrigin.get(655).word,'液');assert.equal(byOrigin.get(658).word,'液体');
assert.equal(byOrigin.get(653).word,'駅');assert.ok(!byOrigin.has(654)&&!byOrigin.has(659));
assert.equal(byOrigin.get(290).word,'いじらしい');assert.match(byOrigin.get(152).meaning,/ひく/);
assert.match(byOrigin.get(374).meaning,/3.03/);assert.ok(!byOrigin.get(361).meaning.includes('いっき'));
assert.equal(byOrigin.get(317).reading,'いたずらっこ');assert.equal(byOrigin.get(812).reading,'だいず');
assert.equal(byOrigin.get(438).word,'居留守');assert.match(byOrigin.get(5367).meaning,/任天堂/);
for(const r of rows){assert.match(r.reading,/^[ぁ-ゖー]+$/);assert.ok(r.meaning&&!/[,\r\n]/.test(r.meaning));}
const assets=read('assets/shiritori/manifest.json').assets;
for(const a of assets){
  const uses=rows.map((r,i)=>({r,id:i+1})).filter(({r})=>r.image_asset==='assets/shiritori/'+a.file);
  assert.equal(a.aliases.length,uses.length,'Complete current alias list '+a.file);
  for(const {r,id} of uses)assert.ok(a.aliases.some(x=>x.id===id&&x.reading===r.reading&&x.word===r.word&&x.meaning===r.meaning),'Alias matches CSV');
}
// App parser must keep genuine homonyms and eliminate spelling-only duplicates.
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');const context=vm.createContext({});
vm.runInContext(html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST =')),context);
context.csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');const parsed=vm.runInContext('parseCSV(csv)',context);
for(const [reading,words] of [['あつい',['暑い','厚い']],['えき',['駅','液']],['えんじ',['臙脂','園児']],['やきもち',['焼き餅','やきもち']]]){
  const r=parsed.find(r=>r.reading===reading);for(const w of words)assert.ok(r.words.includes(w));
}
assert.equal(parsed.find(r=>r.reading==='えきたい').meanings.length,1);
assert.equal(parsed.find(r=>r.reading==='うさぎ').meanings.length,1);
console.log(JSON.stringify({passed:true,requestedOrders:ordered.length,rows:rows.length,images:ledger.replacedImages.length}));
