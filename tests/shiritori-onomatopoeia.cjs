const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base='data/dictionary-imports/2026-11-03-onomatopoeia2000';
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8')),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const summary=read(base+'.summary.json'),review=read(base+'.review.json'),csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n');
assert(summary.registered);assert(review.length>=2000);assert.equal(new Set(review.map(x=>x.reading)).size,review.length);
assert.equal(hash(lines.slice(0,summary.baselineRows+1).join('\n')+'\n'),summary.beforeSha256,'Preceding dictionary preserved byte for byte');
assert.equal(hash(csv),summary.afterSha256);
const existing=new Set(lines.slice(1,summary.baselineRows+1).map(l=>l.split(',')[0]));
const coverage=read('data/image-coverage/review-2026-10-10.json'),updates=read('data/image-coverage/review-updates.json');
const entries=fs.readFileSync(path.join(root,'data/onomatopoeia/entries.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const byId=new Map(entries.map(x=>[x.id,x]));
for(const x of review){
 assert(!existing.has(x.reading));assert.match(x.reading,/^[ぁ-ゖー]+$/);
 const row=lines[x.id].split(',');assert.deepEqual(row.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(row[7],'none');assert.equal(row[6],'');
 assert.deepEqual([coverage[x.id-1].reading,coverage[x.id-1].word,coverage[x.id-1].meaning],row.slice(0,3));
 assert.deepEqual(updates.entries[x.id-1].text,row.slice(0,3));
 const e=byId.get(x.id);assert(e);assert.equal(e.genre,'onomatopoeia');assert.equal(e.grade,x.grade);assert(e.source.title);assert.match(e.source.url,/^https:\/\//);
}
for(const absent of ['しゅわっしゅわ','ぱりんぱりん','ふくふく','いちゃいちゃ','うぞうぞ','ぎしぎしあんあん','あへあへ'])assert(!review.some(x=>x.reading===absent));
assert.equal(review.filter(x=>x.reading.endsWith('ん')).length,summary.endingN);
assert.equal(updates.csvSha256,summary.afterSha256);assert.equal(entries.length,review.length);
console.log(JSON.stringify({passed:true,newReadings:review.length,baselinePreserved:true,ledgers:true,sources:true,images:'none'}));
