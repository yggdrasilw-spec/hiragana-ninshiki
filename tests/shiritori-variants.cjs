const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ledger=read('data/corrections/2026-10-12-variants.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
const lines=csv.trimEnd().split('\n'),heads=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
for(const merge of ledger.merged){
  const canonical=rows.find(r=>r.reading===merge.canonical.reading&&r.word===merge.canonical.word&&r.meaning===merge.canonical.meaning);
  assert.ok(canonical,'Canonical sense survives '+merge.canonical.word);
  assert.equal(canonical.level,merge.canonical.level,'Lowest difficulty survives');
  assert.ok(!rows.some(r=>r.reading===merge.variant.reading&&r.word===merge.variant.word&&r.meaning===merge.variant.meaning),'Merged spelling is not a duplicate sense');
}
for(const [reading,words] of [['いか',['イカ','以下']],['かえる',['カエル','帰る']],['くも',['雲','クモ']],['はるさめ',['春雨','春雨']],['うに',['ウニ','海胆']],['つき',['月','月（時）']]]){
  const group=rows.filter(r=>r.reading===reading);for(const word of words)assert.ok(group.some(r=>r.word===word),reading+' retains '+word);
  if(reading==='はるさめ')assert.equal(group.length,2);
}
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');const context=vm.createContext({csv});
vm.runInContext(html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST =')),context);
const parsed=vm.runInContext('parseCSV(csv)',context);
assert.equal(parsed.find(r=>r.reading==='あり').words.length,1);
assert.equal(parsed.find(r=>r.reading==='いか').words.length,2);
const manifest=read('assets/shiritori/manifest.json');
for(const asset of manifest.assets)for(const alias of asset.aliases||[]){
 const row=rows[alias.id-1];assert.ok(row);for(const k of ['word','reading','meaning'])assert.equal(row[k],alias[k]);assert.equal(row.image_asset,'assets/shiritori/'+asset.file);
}
require('../scripts/shiritori-correction-ledger.cjs').historicalRows();
// A reviewed variant cannot be resurrected by re-importing an old batch.
const os=require('node:os'),cp=require('node:child_process');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'shiritori-variants-'));
try{
  fs.mkdirSync(path.join(temp,'scripts'));fs.mkdirSync(path.join(temp,'data/dictionary-imports'),{recursive:true});
  fs.copyFileSync(path.join(root,'scripts/import-shiritori-words.cjs'),path.join(temp,'scripts/import-shiritori-words.cjs'));
  fs.writeFileSync(path.join(temp,'whitelist.csv'),csv);
  fs.writeFileSync(path.join(temp,'data/dictionary-imports/history.json'),JSON.stringify([ledger.history]));
  const variant=ledger.merged.find(m=>m.variant.word==='蟻').variant;
  const batch=path.join(temp,'old.csv');fs.writeFileSync(batch,heads.join(',')+'\n'+heads.map(k=>variant[k]).join(',')+'\n');
  const result=cp.spawnSync(process.execPath,[path.join(temp,'scripts/import-shiritori-words.cjs'),batch,'--append'],{encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).added,0);
  assert.equal(fs.readFileSync(path.join(temp,'whitelist.csv'),'utf8'),csv);
}finally{fs.rmSync(temp,{recursive:true,force:true});}
console.log(JSON.stringify({passed:true,merged:ledger.merged.length,homonyms:true,liveAliases:true,reversibleHistory:true}));
