// Validate the actual registered senses and delivery, including the preserved prefix.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8'));
const base='data/dictionary-imports/2026-10-28-entrance-geohistory';
const summary=read(base+'.summary.json'),batch=read(base+'.review.json');
assert.ok(summary.registered);assert.equal(batch.length,summary.added);
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split('\n');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
// Restore only subsequent, explicitly reviewed edits for intake-time hashes.
const intakeLines=lines.slice(),keys=lines[0].split(',');
for(const c of read('data/dictionary-imports/2026-10-28-art-history.corrections.json')){
 assert.equal(c.action,'edit');
 const after=keys.map(k=>c.after[k]).join(',');assert.equal(intakeLines[c.beforeId],after);
 intakeLines[c.beforeId]=keys.map(k=>c.before[k]).join(',');
}
assert.equal(hash(intakeLines.slice(0,summary.baselineRows+1).join('\n')+'\n'),summary.beforeSha256,'All pre-existing bytes preserved');
assert.ok(lines.length-1>=summary.totalRows);
assert.equal(hash(intakeLines.slice(0,summary.totalRows+1).join('\n')+'\n'),summary.afterSha256);
const {rows,manifest}=require('../scripts/build-shiritori-delivery.cjs').build(root);
const byReading=new Map(rows.map(x=>[x.reading,x]));
const history=read('data/dictionary-imports/history.json');
assert.equal(history.at(-1).afterSha256,hash(text));
const imported=history.find(x=>x.batch?.replaceAll('\\','/')===base+'.csv');
assert.ok(imported);assert.equal(imported.addedLines.length,batch.length);
const seen=new Set();let homophones=0;
for(const x of batch){
 assert.ok(!seen.has(x.reading+'\t'+x.word));seen.add(x.reading+'\t'+x.word);
 assert.equal(lines[x.id].split(',').slice(0,3).join(','),[x.reading,x.word,x.meaning].join(','));
 const row=byReading.get(x.reading);assert.ok(row,x.word);
 const matches=row.words.flatMap((w,i)=>w===x.word&&row.meanings[i]===x.meaning?[i]:[]);assert.equal(matches.length,1,x.word);
 const i=matches[0];assert.equal(row.meaningLevels[i],5,x.word);assert.equal(row.imagequeries[i].mode,'none',x.word);assert.ok(!row.imagequeries[i].asset,x.word);
 if(row.words.length>1)homophones++;
 assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.topics.length);
}
const corpus=fs.readFileSync(path.join(root,'data/entrance-geohistory/entries.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
assert.equal(corpus.length,summary.catalogCandidates);
assert.equal(corpus.filter(x=>x.status==='add').length,batch.length);
assert.ok(corpus.every(x=>x.status==='add'||x.status==='existing-form'));
for(const x of corpus){const row=byReading.get(x.reading);assert.ok(row,x.word);if(x.status==='add')assert.ok(row.words.includes(x.word),x.word);else for(const id of x.existingIds)assert.equal(lines[id].split(',')[0],x.reading,x.word);}
const coverage=read('data/entrance-geohistory/coverage.json');assert.equal(coverage.dictionarySha256,hash(text));
const report={passed:true,added:batch.length,preservedRows:summary.baselineRows,totalRows:summary.totalRows,catalogTerms:corpus.length,indexedMeanings:coverage.indexedMeanings,homophoneReadings:homophones,topics:coverage.topics.length,chunks:manifest.chunks.length};
fs.writeFileSync(path.join(root,base+'.validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
