const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-29-companies-brands');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const items=read(base+'.review.json'),s=read(base+'.summary.json'),csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift();
assert(s.registered);assert(items.length>=3000);assert.equal(items.length,s.added);assert.equal(hash([header,...lines.slice(0,s.baselineRows)].join('\n')+'\n'),s.beforeSha256);
assert.equal(hash([header,...lines.slice(0,s.baselineRows+items.length)].join('\n')+'\n'),s.afterSha256);
const coverage=read(path.join(root,'data/image-coverage/review-2026-10-10.json')),grades=read(path.join(root,'data/shiritori-grade-review.json')),updates=read(path.join(root,'data/image-coverage/review-updates.json'));
assert.equal(coverage.length,lines.length);assert.equal(grades.length,lines.length);assert.equal(updates.csvSha256,hash(csv));assert.equal(updates.entries.length,lines.length);
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),byReading=new Map(rows.map(r=>[r.reading,r]));
const seen=new Set(),ids=new Set();
for(const x of items){
 assert(!seen.has(x.identity));seen.add(x.identity);assert(!ids.has(x.id));ids.add(x.id);
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(!x.reading.includes('かぶしき'),x.word);assert(x.lexicalSource.startsWith('https://'));assert(x.meaningReason&&x.ageReason&&x.distinctSenseReason&&x.sourceEvidence);
 const cols=lines[x.id-1].split(',');assert.equal(cols.length,9);assert.deepEqual(cols.slice(0,3),[x.reading,x.word,x.meaning]);assert.equal(cols[6],'');assert.equal(cols[7],'none');
 assert.equal(grades[x.id-1].level,5);assert.equal(coverage[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,cols.slice(0,3));
 const r=byReading.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],x.genre);assert.equal(r.imagequeries[i].mode,'none');assert(r.imagequeries[i].source.url.startsWith('https://'));assert(r.imagequeries[i].source.title);
}
for(const word of ['ガスト','バーミヤン','しゃぶ葉','すき家','はま寿司','ココス','牛角','サンマルクカフェ','コメダ珈琲店','竹中工務店','東芝','ライオン','ビオレ','白くまくん','クルトガ','プラレール'])assert(items.some(x=>x.word===word),word);
for(const [reading,word] of [['ぽっきー','ポッキー'],['じゃがりこ','じゃがりこ']])assert(byReading.get(reading).words.includes(word));
assert(byReading.get('がすと').meanings.some(m=>m.includes('Minecraft')));assert(byReading.get('がすと').meanings.some(m=>m.startsWith('店名・ブランド。')));
assert(byReading.get('らいおん').meaningLevels.includes(1));assert(byReading.get('らいおん').genres.includes('company'));
const p=require('../shiritori-vocabulary.js');assert.equal(p.category('北海道','店名・ブランド。和食を提供する店。'),'company');assert.equal(p.category('ビオレ','商品ブランド。花王の日用品ブランド。'),'brand');
assert(byReading.get('らいおん').genres.includes('animal'));
assert.equal(items.find(x=>x.word==='長谷川香料').reading,'はせがわこうりょう');assert.equal(items.find(x=>x.word==='NJS').reading,'えぬじぇーえす');
console.log(JSON.stringify({passed:true,added:items.length,newReadings:s.newReadings,byKind:s.byKind,allSourceLinked:true,allExplanationOnly:true,stableBaseline:true,total:lines.length}));
