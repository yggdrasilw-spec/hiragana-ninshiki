const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-28-entertainment');
const items=JSON.parse(fs.readFileSync(base+'.review.json','utf8')),summary=JSON.parse(fs.readFileSync(base+'.summary.json','utf8'));
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift().split(',');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert(summary.registered);assert.equal(hash([header.join(','),...lines.slice(0,summary.baselineRows+items.length)].join('\n')+'\n'),summary.afterSha256);assert(lines.length>=summary.baselineRows+items.length);assert(items.length>4000);
assert.equal(hash([header.join(','),...lines.slice(0,summary.baselineRows)].join('\n')+'\n'),summary.beforeSha256,'All pre-existing meanings and IDs retained byte-for-byte');
const coverage=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-2026-10-10.json'),'utf8'));
const grades=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-grade-review.json'),'utf8'));
const updates=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-updates.json'),'utf8'));
assert.equal(coverage.length,lines.length);assert.equal(grades.length,lines.length);assert.equal(updates.entries.length,lines.length);assert.equal(updates.csvSha256,hash(csv));
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),map=new Map(rows.map(r=>[r.reading,r]));
const policy=require('../shiritori-vocabulary.js');assert.equal(policy.categories.entertainment,'芸能・映画・番組');
const ids=new Set(),identities=new Set(),triples=new Set();
for(const x of items){
 assert(!ids.has(x.id));ids.add(x.id);assert(!identities.has(x.identity));identities.add(x.identity);
 const triple=[x.reading,x.word,x.meaning].join('\t');assert(!triples.has(triple));triples.add(triple);
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(x.lexicalSource.startsWith('https://'));assert(x.ageReason&&x.meaningReason&&x.distinctSenseReason);
 const actual=lines[x.id-1].split(',');assert.equal(actual.length,9);assert.deepEqual(actual.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(actual[6],'');assert.equal(actual[7],'none');
 assert.equal(grades[x.id-1].level,5);assert.equal(coverage[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,actual.slice(0,3));
 const r=map.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'entertainment',x.word);assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);
}
// Homonyms must keep their separate meanings and genre/level assignments.
for(const [word,reading] of [['French','ふれんち'],['Midnight','みっどないと'],['Mrs. GREEN APPLE','みせすぐりーんあっぷる']]){
 const r=map.get(reading);assert(r.meanings.length>=2,word);assert(r.genres.includes('entertainment'));
}
assert.equal(policy.category('ライス','食べ物のご飯。'),'food');
assert.equal(policy.category('ライス','お笑いグループ。吉本興業の公式プロフィールに掲載されている。'),'entertainment');
for(const word of ['Mrs. GREEN APPLE','大森元貴','若井滉斗','藤澤涼架','ライラック','青と夏','我逢人','POPS','OITOMA','0.2mm','French','Midnight','ゼンジン未到とイ/ミュータブル～間奏編～','ダウンタウン','明石家さんま','千と千尋の神隠し','ミュージックステーション'])assert(items.some(x=>x.word===word),word);
assert.equal(items.find(x=>x.word==='0.2mm').reading,'れーてんにみり');
assert.equal(items.filter(x=>x.word==='French').length,2,'Song and EP are distinct senses, not alternate spellings');
assert.equal(items.filter(x=>x.word==='POPS').length,1,'Format/SKU differences never inflate counts');
console.log(JSON.stringify({passed:true,added:items.length,newReadings:summary.newReadings,total:lines.length,allSourceLinked:true,allLevel5:true,allExplanationOnly:true,allEntertainment:true,stableBaseline:true}));
