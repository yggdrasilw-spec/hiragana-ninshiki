const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-29-manga1000');
const items=JSON.parse(fs.readFileSync(base+'.review.json','utf8')),summary=JSON.parse(fs.readFileSync(base+'.summary.json','utf8'));
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift().split(',');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert(summary.registered);assert(items.length>=1000);
assert.equal(hash([header.join(','),...lines.slice(0,summary.baselineRows)].join('\n')+'\n'),summary.beforeSha256,'Existing rows preserved byte for byte');
assert.equal(hash([header.join(','),...lines.slice(0,summary.baselineRows+items.length)].join('\n')+'\n'),summary.afterSha256);
const coverage=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-2026-10-10.json'),'utf8'));
const grades=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-grade-review.json'),'utf8'));
const updates=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-updates.json'),'utf8'));
assert.equal(coverage.length,lines.length);assert.equal(grades.length,lines.length);assert.equal(updates.entries.length,lines.length);assert.equal(updates.csvSha256,hash(csv));
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),map=new Map(rows.map(r=>[r.reading,r]));
const sources=JSON.parse(fs.readFileSync(base+'.sources.json','utf8')).flatMap(s=>s.records),sourceMap=new Map(sources.map(s=>[s.url,s]));
const words=new Set(),triples=new Set();
for(const x of items){
 const key=[x.reading,x.word,x.meaning].join('\t');assert(!triples.has(key));triples.add(key);
 // Unicode letters are retained in normalized identities.
 const spelling=x.word.normalize('NFKC').replace(/[\p{P}\p{S}\s]/gu,'').toLowerCase();assert(!words.has(spelling),x.word);words.add(spelling);
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(x.ageReason&&x.meaningReason&&x.readingBasis);
 assert(sourceMap.has(x.lexicalSource));
 const actual=lines[x.id-1].split(',');assert.equal(actual.length,9);assert.deepEqual(actual.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(actual[6],'');assert.equal(actual[7],'none');
 assert.equal(grades[x.id-1].level,5);assert.equal(coverage[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,actual.slice(0,3));
 const r=map.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'fiction',x.word);assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);assert.equal(r.imagequeries[i].source.url,x.lexicalSource);
 if(x.category==='漫画タイトル')assert.equal(x.sourceRecord.url,x.lexicalSource);
 else{assert(x.works.length);assert(x.works.every(w=>sourceMap.has(w.source)));assert(!/株式会社|講談社|小学館|集英社/.test(x.word));if(x.category==='漫画原作者')assert(x.works.every(w=>w.role==='原作者'));}
}
for(const [word,reading] of [['茜部先生は照れ知らず','あかなべせんせいはてれしらず'],['黒い羊は迷わない','くろいひつじはまよわない']]){const x=items.find(x=>x.word===word);if(x)assert.equal(x.reading,reading);}
assert(items.filter(x=>x.category==='漫画タイトル').length>=500);assert(items.filter(x=>x.category==='漫画原作者').length>=20);
console.log(JSON.stringify({passed:true,added:items.length,categories:summary.categories,total:lines.length,stableBaseline:true,allSourceLinked:true,allLevel5:true,allFiction:true,allExplanationOnly:true}));
