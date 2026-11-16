const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/dictionary-imports');
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8')),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),history=read('data/dictionary-imports/history.json');
const batches=fs.readdirSync(dir).filter(f=>/^2026-11-16-related-closure(?:-\d+)?\.summary\.json$/.test(f)).map(f=>f.replace('.summary.json','')).filter(b=>read(`data/dictionary-imports/${b}.summary.json`).registered);
const {undoImports}=require('../scripts/shiritori-correction-ledger.cjs'),{build}=require('../scripts/build-shiritori-delivery.cjs');
const built=build(root),byReading=new Map(built.rows.map(r=>[r.reading,r]));let checked=0;
for(const batch of batches){
 const s=read(`data/dictionary-imports/${batch}.summary.json`),items=read(`data/dictionary-imports/${batch}.review.json`);
 const n=history.findIndex(h=>String(h.batch||'').replaceAll('\\','/')===`data/dictionary-imports/${batch}.csv`);assert(n>=0);
 const snapshot=undoImports(csv,history.slice(n+1));assert.equal(hash(snapshot),s.afterSha256);
 const baseline=snapshot.trimEnd().split('\n').slice(0,s.baselineRows+1).join('\n')+'\n';assert.equal(hash(baseline),s.baselineSha256);
 assert.equal(history[n].addedLines.length,s.added);assert.equal(items.length,s.added);assert.equal(s.allIndividuallyReviewed,false);
 for(const x of items){
  const row=byReading.get(x.reading),i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);assert(i>=0,x.word);
  assert.equal(row.meaningLevels[i],4,x.word);assert.equal(row.genres[i],x.genre,x.word);assert.equal(row.imagequeries[i].mode,'none');
  assert(row.imagequeries[i].source?.url.startsWith('https://'));assert.equal(x.provisional,true);
  assert.equal(x.reviewStatus,'source-checked-provisional');assert(x.lexicalSource.entryId);
  assert(!/伊勢を扱う|旗艦などを扱う|最新について|反復がうまく|大人のおもちゃ|大人の玩具/.test(x.meaning),x.word);
  checked++;
 }
 const result=cp.spawnSync(process.execPath,['scripts/import-shiritori-words.cjs',`data/dictionary-imports/${batch}.csv`,'--append'],{cwd:root,encoding:'utf8'});
 assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).added,0);
}
assert.equal(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),csv);
assert(!csv.split('\n').some(line=>line.startsWith('しけんかん,しけんかん,少量の液体を入れて')),'Retired spelling stays retired');
console.log(JSON.stringify({passed:true,batches:batches.length,checkedSenses:checked,priorRowsPreserved:true,provisionalLevel4:true,idempotent:true}));
