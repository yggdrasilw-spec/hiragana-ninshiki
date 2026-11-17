const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8');
const lineage=require('../scripts/shiritori-correction-ledger.cjs');
const parse=text=>text.trimEnd().split('\n').slice(1).map(line=>line.split(','));
const reviews=['0001','0002','0002-followup'].map(id=>JSON.parse(read(`data/meaning-review/source-check-20261118-batch${id}.json`)));
const first=reviews[0];
assert.equal(first.changes.length,50);assert.equal(first.unresolved.length,0);
const ctx=vm.createContext({});ctx.window=ctx;
for(const f of ['shiritori-image-policy.js','shiritori-grade-policy.js','shiritori-mrs-details.js','shiritori-meaning-sources.js'])vm.runInContext(read(f),ctx);
vm.runInContext(read('shiritori.html').match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)[0],ctx);
const fallback=ctx.parseCSV(read('whitelist.csv'),true);
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root);
for(const review of reviews){
 const application=JSON.parse(read(review.applicationRecord||'data/meaning-review/consistency500-application.json'));
 const before=parse(lineage.dictionaryAtHash(review.baselineSha256));
 const after=parse(lineage.dictionaryAtHash(application.afterSha256));
 const edited=new Set(review.changes.map(r=>r.id-1));
 const detached=new Set(application.imageLinksRemoved);
 assert.equal(application.corrected,edited.size);
 assert.equal(after.length,before.length+review.additions.length);
 for(let i=0;i<before.length;i++)if(!edited.has(i))assert.deepEqual(after[i],before[i],`Unrelated row ${i+1}`);
 if(review.rowRange){
  const [start,end]=review.rowRange;
  const fixed=parse(lineage.dictionaryAtHash(review.fixedScopeSha256));
  assert.equal(review.rowDecisions.length,end-start+1);
  review.rowDecisions.forEach((decision,i)=>{
   const id=start+i;
   assert.equal(decision.id,id);
   assert.deepEqual(decision.baselineKey,fixed[id-1].slice(0,3));
   assert.deepEqual(decision.baselineKey,before[id-1].slice(0,3));
   assert.equal(decision.decision==='corrected',edited.has(id-1));
  });
  assert.deepEqual(review.rowDecisions.filter(r=>r.decision==='pending').map(r=>r.id),review.unresolved.map(r=>r.id));
  assert.equal(review.nextRow,end+1);
 }
 for(const record of review.exclusions||[]){
  const [reading,word,meaning]=record.baselineKey;
  assert.deepEqual(before[record.id-1].slice(0,3),record.baselineKey);
  assert.equal(ctx.ShiritoriMeaningSources.isExcluded(reading,word,meaning),true);
  assert.equal(ctx.ShiritoriMeaningSources.isExcluded(reading,word,meaning+'別義'),false);
  for(const list of [fallback,rows]){
   const group=list.find(row=>row.reading===reading);
   assert.ok(!group?.words.some((item,i)=>item===word&&group.meanings[i]===meaning));
  }
 }
 const scopeRows=review.rowDecisions?.length||500;
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
   if(detached.has(r.id)){
    assert.equal(a[6],'');assert.equal(a[7],'none');assert.equal(a[8],'');
   }else assert.deepEqual(a.slice(3),b.slice(3),'Images and search metadata preserved');
  }else{
   const a=after.find(a=>a.slice(0,3).join('\t')===exact);assert.equal(a[6],'');assert.equal(a[7],'none');
  }
 }
 console.log(JSON.stringify({scopeRows,corrected:edited.size,added:review.additions.length,
  unresolved:review.unresolved.length,sourcePairsChecked:(edited.size+review.additions.length)*2}));
}
const second=reviews[1],followup=reviews[2];
assert.equal(followup.unresolved.length,0);
assert.ok(second.changes.every(row=>row.senseCoverageReview==='checked'));
assert.equal(followup.coverageDecisions.length,47);
assert.deepEqual([...followup.changes,...followup.exclusions].map(row=>row.id).sort((a,b)=>a-b),second.unresolved.map(row=>row.id));
assert.equal(ctx.ShiritoriMeaningSources.get('いぐにす','イグニス','スズキの、小型SUVの名前。'),null);
assert.equal(rows.find(r=>r.reading==='いっかん').meanings.filter(m=>m==='密接につながった全体のうちの一部分。').length,1);
const catalog=JSON.parse(read('data/image-coverage/review-updates.json'));
const after=parse(read('whitelist.csv'));
assert.equal(catalog.entries.length,after.length);
after.forEach((r,i)=>{assert.deepEqual(catalog.entries[i].text,r.slice(0,3));assert.equal(catalog.entries[i].image_asset,r[6]);});
console.log(JSON.stringify({passed:true,priorityEntries:catalog.entries.length}));
