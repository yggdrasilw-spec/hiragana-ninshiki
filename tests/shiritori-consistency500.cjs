const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8');
const review=JSON.parse(read('data/meaning-review/source-check-20261118-batch0001.json'));
const lineage=require('../scripts/shiritori-correction-ledger.cjs');
const parse=text=>text.trimEnd().split('\n').slice(1).map(line=>line.split(','));
const before=parse(lineage.dictionaryAtHash(review.baselineSha256)),after=parse(read('whitelist.csv'));
assert.equal(review.changes.length,50);assert.equal(review.unresolved.length,0);
assert.equal(after.length,before.length+review.additions.length);
const edited=new Set(review.changes.map(r=>r.id-1));
for(let i=0;i<before.length;i++)if(!edited.has(i))assert.deepEqual(after[i],before[i],`Unrelated row ${i+1}`);
const ctx=vm.createContext({});ctx.window=ctx;
for(const f of ['shiritori-image-policy.js','shiritori-grade-policy.js','shiritori-mrs-details.js','shiritori-meaning-sources.js'])vm.runInContext(read(f),ctx);
vm.runInContext(read('shiritori.html').match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)[0],ctx);
const fallback=ctx.parseCSV(read('whitelist.csv'),true);
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root);
let checked=0;
for(const r of [...review.changes,...review.additions]){
 const exact=[r.reading,r.word,r.meaning].join('\t');
 for(const list of [fallback,rows]){
  const group=list.find(x=>x.reading===r.reading),i=group.words.findIndex((w,i)=>w===r.word&&group.meanings[i]===r.meaning);
  assert.ok(i>=0,exact);assert.equal(group.meaningLevels[i],r.effectiveLevel,exact);
  assert.equal(group.imagequeries[i].source.url,r.sources[0],exact);
  assert.equal(group.imagequeries[i].source.title,r.sourceTitles[0],exact);
 }
 assert.equal(ctx.ShiritoriMeaningSources.get(r.reading,r.word,r.meaning+'別義'),null,'No word-only source leakage');
 if(r.id){
  const a=after[r.id-1],b=before[r.id-1];
  assert.deepEqual(a.slice(0,3),[r.reading,r.word,r.meaning]);
  assert.equal(a[4],b[4],'CSV legacy level preserved');
  if(r.id!==354)assert.deepEqual(a.slice(3),b.slice(3),'Images and search metadata preserved');
 }else{
  const a=after.find(a=>a.slice(0,3).join('\t')===exact);assert.equal(a[6],'');assert.equal(a[7],'none');
 }
 checked++;
}
assert.equal(after[353][6],'');assert.equal(after[353][7],'none','Mismatched cycle image detached');
assert.equal(ctx.ShiritoriMeaningSources.get('いぐにす','イグニス','スズキの、小型SUVの名前。'),null);
assert.equal(rows.find(r=>r.reading==='いっかん').meanings.filter(m=>m==='密接につながった全体のうちの一部分。').length,1);
const catalog=JSON.parse(read('data/image-coverage/review-updates.json'));
assert.equal(catalog.entries.length,after.length);
after.forEach((r,i)=>{assert.deepEqual(catalog.entries[i].text,r.slice(0,3));assert.equal(catalog.entries[i].image_asset,r[6]);});
console.log(JSON.stringify({passed:true,researched:review.changes.length,added:review.additions.length,sourcePairsChecked:checked*2,unrelatedRowsPreserved:before.length-edited.size,priorityEntries:catalog.entries.length}));
