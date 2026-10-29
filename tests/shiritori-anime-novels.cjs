const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-29-anime-novels');
const read=f=>JSON.parse(fs.readFileSync(f,'utf8')),items=read(base+'.review.json'),s=read(base+'.summary.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift();
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
assert(s.registered);assert(items.length>=1000);assert.equal(items.length,s.added);
assert.equal(hash([header,...lines.slice(0,s.baselineRows)].join('\n')+'\n'),s.beforeSha256,'Retain every prior byte and ID');
assert.equal(hash([header,...lines.slice(0,s.baselineRows+items.length)].join('\n')+'\n'),s.afterSha256);
const coverage=read(path.join(root,'data/image-coverage/review-2026-10-10.json')),grades=read(path.join(root,'data/shiritori-grade-review.json')),updates=read(path.join(root,'data/image-coverage/review-updates.json'));
assert.equal(coverage.length,lines.length);assert.equal(grades.length,lines.length);assert.equal(updates.entries.length,lines.length);assert.equal(updates.csvSha256,hash(csv));
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),map=new Map(rows.map(r=>[r.reading,r]));
const ids=new Set(),keys=new Set(),identities=new Set(),counts={};
for(const x of items){
 assert(!ids.has(x.id));ids.add(x.id);assert(!identities.has(x.identity));identities.add(x.identity);
 const key=[x.reading,x.word,x.meaning].join('\t');assert(!keys.has(key));keys.add(key);
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(x.lexicalSource.startsWith('https://'));assert(x.meaningReason&&x.ageReason&&x.distinctSenseReason&&x.evidence);
 const actual=lines[x.id-1].split(',');assert.equal(actual.length,9);assert.deepEqual(actual.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(actual[6],'');assert.equal(actual[7],'none');
 assert.equal(grades[x.id-1].level,5);assert.equal(coverage[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,actual.slice(0,3));
 const r=map.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'fiction',x.word);assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);
 if(x.category==='作品略称'){assert(x.aliasOf);assert.equal(x.evidence.verified,true);assert(x.evidence.evidence.includes(x.word));}
 if(x.category==='著者・原作者'){assert(x.evidence.creditSource.startsWith('https://cal.syoboi.jp/tid/'));assert(x.evidence.readingLead);}
 counts[x.category]=(counts[x.category]||0)+1;
}
assert(counts['ラノベ・小説原作タイトル']>=100);assert(counts['著者・原作者']>=50);assert(counts['作品略称']>=10);
for(const word of ['このすば','転スラ','俺ガイル','青ブタ','はがない','冴えカノ','リゼロ','ごちうさ'])assert(items.some(x=>x.word===word)||read(base+'.reused.json').some(x=>x.word===word),word);
const report={passed:true,added:items.length,newReadings:s.newReadings,categories:counts,totalRows:lines.length,stableBaseline:true,allLevel5:true,allExplanationOnly:true,allSourceLinked:true,allFiction:true};
fs.writeFileSync(base+'.validation.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
