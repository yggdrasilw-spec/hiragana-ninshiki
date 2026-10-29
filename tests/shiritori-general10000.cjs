const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),read=f=>fs.readFileSync(path.join(root,f),'utf8'),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const summary=JSON.parse(read('data/dictionary-imports/2026-10-29-general10000.summary.json'));
const added=read('data/general10000/entries.jsonl').trim().split('\n').map(JSON.parse),csv=read('whitelist.csv'),lines=csv.trimEnd().split('\n');
assert.ok(summary.registered&&added.length>10000);assert.equal(added.length,summary.added);
assert.equal(hash(lines.slice(0,summary.baselineRows+1).join('\n')+'\n'),summary.beforeSha256,'Every original byte and row order is retained');
assert.equal(hash(lines.slice(0,summary.totalRows+1).join('\n')+'\n'),summary.afterSha256,'Later append-only imports retain this complete intake');
assert.equal(new Set(added.map(e=>e.reading+'\t'+e.word)).size,added.length);
const baseline=new Set(lines.slice(1,summary.baselineRows+1).map(l=>l.split(',').slice(0,2).join('\t')));
const delivery=JSON.parse(read('data/shiritori-delivery/index.json'));
const delivered=new Map(delivery.chunks.flatMap(c=>JSON.parse(read('data/shiritori-delivery/'+c.file))).map(r=>[r.reading,r]));
for(const e of added){
  assert.ok(!baseline.has(e.reading+'\t'+e.word));
  const row=delivered.get(e.reading),i=row.words.findIndex((w,i)=>w===e.word&&row.meanings[i]===e.meaning);assert.ok(i>=0,e.word);
  assert.equal(row.meaningLevels[i],e.grade);assert.equal(row.imagequeries[i].mode,'none');
  assert.deepEqual(row.imagequeries[i].source,e.source);assert.ok(e.source.jmdictIds.length);
  assert.ok(e.editorial||e.alignment.length,'Every unedited definition has an independently matching English sense');
  assert.ok(e.editorial||e.grade===4,'Unedited definitions never enter elementary CPU levels');
}
const strength=delivered.get('ちから');assert.ok(strength.words.includes('ちから'),'Existing entertainer meaning is retained');
const i=strength.words.indexOf('力');assert.ok(i>=0);assert.equal(strength.meaningLevels[i],1);assert.match(strength.meanings[i],/ものを うごかしたり/);
assert.ok(added.some(e=>e.reading==='もの'&&e.word==='物'));
assert.ok(added.some((e,i)=>added.findIndex(x=>x.reading===e.reading)<i),'Spelling variants are retained');
const history=JSON.parse(read('data/dictionary-imports/history.json')).find(h=>h.batch?.replaceAll('\\','/')==='data/dictionary-imports/2026-10-29-general10000.csv');
assert.equal(history.addedLines.length,added.length);assert.equal(history.beforeSha256,summary.beforeSha256);assert.equal(history.afterSha256,summary.afterSha256);
console.log(JSON.stringify({passed:true,added:added.length,newReadings:summary.newReadings,editorial:summary.editorial,preservedRows:summary.baselineRows}));
