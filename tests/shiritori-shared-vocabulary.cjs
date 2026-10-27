const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.env.SHARED_VOCAB_ROOT||path.resolve(__dirname,'..'),name='2026-10-27-shared-vocabulary';
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split('\n'),heads=lines.shift().split(','),rows=lines.map(l=>Object.fromEntries(heads.map((h,i)=>[h,l.split(',')[i]])));
const review=read('data/dictionary-imports/'+name+'.review.json'),summary=read('data/dictionary-imports/'+name+'.summary.json');
assert.equal(crypto.createHash('sha256').update(text).digest('hex'),summary.afterSha256);
assert.equal(rows.length,summary.afterRows);assert.equal(review.length,summary.addedRows);
assert.equal(crypto.createHash('sha256').update(heads.join(',')+'\n'+lines.slice(0,summary.baselineRows).join('\n')+'\n').digest('hex'),summary.beforeSha256,'Every existing row preserved byte for byte');
const assets=new Map(read('assets/shiritori/manifest.json').assets.map(a=>[a.file,a])),catalog=read('data/image-coverage/review-2026-10-10.json'),update=read('data/image-coverage/review-updates.json'),grade=read('data/shiritori-grade-review.json');
const beforeReadings=new Set(rows.slice(0,summary.baselineRows).map(r=>r.reading)),seen=new Set();
const live=process.env.SHARED_VOCAB_ASSET_ROOT||root;
for(const r of review){
 const row=rows[r.id-1],src=rows[r.sourceId-1];for(const k of ['reading','word','meaning','image_asset'])assert.equal(row[k],r[k]);
 assert.ok(!beforeReadings.has(row.reading)&&!seen.has(row.reading),'Only distinct new readings');seen.add(row.reading);
 assert.ok(fs.existsSync(path.join(live,row.image_asset)));assert.equal(row.image_asset,src.image_asset);
 assert.ok(assets.get(path.basename(row.image_asset)).aliases.some(a=>a.id===r.id&&a.reading===row.reading&&a.meaning===row.meaning),'Manifest includes exact meaning');
 assert.equal(catalog[r.id-1].assignment,'reused');assert.equal(catalog[r.id-1].meaning,row.meaning);
 assert.deepEqual(update.entries[r.id-1].text,[row.reading,row.word,row.meaning]);assert.equal(grade[r.id-1].level,r.meaningLevel);
}
const lacto=rows.find(r=>r.reading==='らくとあいす'),milk=rows.find(r=>r.reading==='あいすみるく');
assert.notEqual(lacto.meaning,milk.meaning);assert.ok(lacto.meaning.includes('3%'));assert.ok(milk.meaning.includes('10%'));
assert.equal(lacto.image_asset,rows.find(r=>r.reading==='あいす').image_asset);
assert.ok(!review.some(r=>['かなりや','ぶるーまー','ねーる','でーじー','うぃぐる','うぃんぐ','じんずうりき','とおせんぼ'].includes(r.reading)),'Homonyms must not acquire unrelated art');
assert.equal(update.csvSha256,summary.afterSha256);console.log(JSON.stringify({passed:true,rows:rows.length,added:review.length,stableExistingRows:true,manifest:true,catalog:true,grades:true,newReadings:seen.size}));
