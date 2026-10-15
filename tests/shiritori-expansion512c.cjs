const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-10-15-expansion512c';
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const plan=json('data/image-coverage/'+name+'/plan.json'),summary=json('data/image-coverage/'+name+'/summary.json');
const review=json('data/dictionary-imports/'+name+'.review.json'),pairs=json('data/image-coverage/'+name+'/abbreviation-pairs.json');
const manifest=json('assets/shiritori/manifest.json'),text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
const lines=text.trimEnd().split(/\r?\n/),header=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert.equal(review.length,553);assert.equal(plan.items.length,553);assert.equal(summary.addedWords,553);
assert.equal(summary.newReadings,553);assert.equal(summary.singleCharacterWords,12);assert.equal(summary.missingImages,0);
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,summary.baselineRows).join('\n')+'\n'),summary.beforeSha256,'Existing data and IDs remain unchanged');
const oldReadings=new Set(rows.slice(0,summary.baselineRows).map(r=>r.reading));
const assets=new Map(manifest.assets.map(a=>[a.file,a]));assert.equal(assets.size,manifest.assets.length,'Manifest filenames are unique');
const readings=new Set(rows.map(r=>r.reading));
const batchLines=fs.readFileSync(path.join(root,'data/dictionary-imports/'+name+'.csv'),'utf8').trimEnd().split(/\r?\n/).slice(1);
assert.deepEqual(batchLines,review.map(x=>lines[x.id-1]),'The batch includes final image assignments and matches every live column');
for(const pair of pairs){
 assert.ok(readings.has(pair.abbreviation),'Short form exists: '+pair.abbreviation);
 assert.ok(readings.has(pair.fullReading),'Original exists: '+pair.fullReading);
 assert.ok(rows.some(r=>r.reading===pair.fullReading&&r.word===pair.fullWord),'Original spelling matches: '+pair.fullWord);
}
for(const item of review){
 const row=rows[item.id-1],p=plan.items.find(x=>x.id===item.id);
 assert.ok(!oldReadings.has(item.reading));assert.match(item.reading,/^[ぁ-ゖー]+$/);
 for(const k of ['reading','word','meaning'])assert.equal(row[k],item[k]);
 assert.equal(Number(row.level),item.level);assert.ok(item.lexicalSource&&item.meaningReason&&item.ageReason&&item.imageReason);
 assert.equal(row.image_asset,'assets/shiritori/'+p.filename);assert.equal(row.image_mode,'asset');
 const asset=assets.get(p.filename);assert.ok(asset);assert.ok(asset.aliases.some(a=>a.id===item.id&&a.reading===item.reading&&a.word===item.word&&a.meaning===item.meaning));
 const bytes=fs.readFileSync(path.join(root,row.image_asset));assert.equal(bytes.readUInt32BE(16),256);assert.equal(bytes.readUInt32BE(20),256);
 assert.equal(row.image_credit,p.credit);assert.equal(item.imageStatus,'covered');
}
const qr=pairs.find(p=>p.abbreviation==='きゅーあーるこーど');assert.equal(qr.relation,'origin');
assert.ok(!rows.some(r=>r.word==='クイックレスポンスコード'),'Do not invent an expanded official QR Code name');
for(const rd of ['えいちぴー','えむぴー'])assert.ok(review.find(r=>r.reading===rd).senseEvidenceIndexes.length,'Game-specific dictionary sense');
assert.equal(plan.newImages.length,302);assert.equal(plan.diagrams.length,161);
console.log(JSON.stringify({passed:true,words:553,originalWordsPresent:pairs.length,singleCharacterWords:12,allImages:553,originalRowsPreserved:summary.baselineRows}));
