const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base='data/dictionary-imports/2026-10-29-geohistory5000';
const read=f=>fs.readFileSync(path.join(root,f),'utf8'),json=f=>JSON.parse(read(f)),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const summary=json(base+'.summary.json'),items=json(base+'.review.json'),sources=json(base+'.sources.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv')),lines=csv.toString('utf8').trimEnd().split('\n').slice(1);
assert.ok(summary.registered&&items.length>=5000);assert.equal(items.length,summary.added);
assert.deepEqual(Object.keys(summary.subjects).sort(),['世界史','地理','日本史'].sort());
assert.equal(hash(csv.subarray(0,summary.beforeBytes)),summary.beforeSha256,'All existing bytes preserved');
assert.equal(hash(csv.subarray(0,summary.beforeBytes+summary.batchBytes)),summary.afterSha256,'Registered batch is unchanged');
const entries=read('data/geohistory5000/entries.jsonl').trim().split('\n').map(JSON.parse),records=new Map();
assert.equal(entries.length,items.length);
for(const f of sources.files){
 const b=fs.readFileSync(path.join(root,'data/geohistory5000/sources',f.file));assert.equal(hash(b),f.sha256);
 const raw=JSON.parse(b);assert.equal(raw.results.bindings.length,f.bindings);
 for(const row of raw.results.bindings){const x=Object.fromEntries(Object.entries(row).map(([k,v])=>[k,v.value]));const q=x.item.split('/').at(-1);if(!records.has(q))records.set(q,[]);records.get(q).push(x);}
}
const old=lines.slice(0,summary.baselineRows),oldWords=new Set(old.map(l=>l.split(',')[1])),oldReadings=new Set(old.map(l=>l.split(',')[0]));
const uniqueReads=new Set(),uniqueWords=new Set(),uniqueIds=new Set();
const {rows,manifest}=require('../scripts/build-shiritori-delivery.cjs').build(root),delivered=new Map(rows.map(r=>[r.reading,r]));
for(let i=0;i<items.length;i++){
 const x=items[i],e=entries[i],cols=lines[x.id-1].split(',');
 assert.equal(x.id,summary.baselineRows+i+1);assert.equal(cols.length,9);assert.deepEqual(cols.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(cols[6],'');assert.equal(cols[7],'none');
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert.ok(!oldWords.has(x.word)&&!oldReadings.has(x.reading));
 assert.ok(!uniqueReads.has(x.reading)&&!uniqueWords.has(x.word)&&!uniqueIds.has(x.source.id));uniqueReads.add(x.reading);uniqueWords.add(x.word);uniqueIds.add(x.source.id);
 assert.ok(records.get(x.source.id)?.some(r=>JSON.stringify(r)===JSON.stringify(x.sourceRecord)),'Complete source record retained: '+x.word);
 assert.equal(x.source.license,'CC0');assert.equal(x.source.url,'https://www.wikidata.org/wiki/'+x.source.id);assert.equal(e.source.id,x.source.id);
 const d=delivered.get(x.reading),sense=d.words.indexOf(x.word);assert.ok(sense>=0);assert.equal(d.meanings[sense],x.meaning);assert.equal(d.meaningLevels[sense],5);assert.equal(d.genres[sense],x.genre);assert.equal(d.imagequeries[sense].source.url,x.source.url);assert.equal(d.imagequeries[sense].mode,'none');
}
const history=json('data/dictionary-imports/history.json').find(x=>x.batch?.replaceAll('\\','/')===base+'.csv');assert.ok(history);assert.equal(history.beforeSha256,summary.beforeSha256);assert.equal(history.afterSha256,summary.afterSha256);assert.equal(history.addedLines.length,items.length);
assert.equal(json('data/shiritori-grade-decisions.json').sourceSha256,hash(csv));assert.equal(json('data/image-coverage/review-updates.json').csvSha256,hash(csv));
assert.ok(manifest.chunks.every(c=>c.count<=128));
const result={passed:true,added:items.length,subjects:summary.subjects,oldRowsBytePreserved:summary.baselineRows,newReadings:uniqueReads.size,sourceChecked:items.length,explanationOnly:items.length};
fs.writeFileSync(path.join(root,base+'.validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
