const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-29-oricon1990-2025');
const get=s=>JSON.parse(fs.readFileSync(base+s,'utf8')),items=get('.review.json'),s=get('.summary.json'),coverage=get('.coverage.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift().split(',');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert(s.registered);assert.equal(items.length,s.added);assert.equal(items.length,5588);
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,s.baselineRows).join('\n')+'\n'),s.beforeSha256,'Existing rows and IDs retained byte-for-byte');
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,s.baselineRows+items.length).join('\n')+'\n'),s.afterSha256);
const grades=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-grade-review.json'),'utf8'));
const images=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-2026-10-10.json'),'utf8'));
const updates=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-updates.json'),'utf8'));
assert.equal(grades.length,lines.length);assert.equal(images.length,lines.length);assert.equal(updates.entries.length,lines.length);assert.equal(updates.csvSha256,hash(csv));
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),map=new Map(rows.map(x=>[x.reading,x]));
const triples=new Set(),keys=new Set();
for(const x of items){
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(x.lexicalSource.references.length&&x.ageReason&&x.meaningReason&&x.distinctSenseReason);
 assert(!keys.has(x.nodeKey));keys.add(x.nodeKey);const triple=[x.reading,x.word,x.meaning].join('\t');assert(!triples.has(triple));triples.add(triple);
 const actual=lines[x.id-1].split(',');assert.equal(actual.length,9);assert.deepEqual(actual,header.map(k=>String(x[k])));
 assert.equal(x.image_mode,'none');assert.equal(grades[x.id-1].level,5);assert.equal(images[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,actual.slice(0,3));
 const r=map.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'entertainment');assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);
}
assert.equal(coverage.length,3600);
for(let year=1990;year<=2025;year++){
 const list=coverage.filter(x=>x.year===year);assert.equal(list.length,100);assert.equal(new Set(list.map(x=>x.rank)).size,100);
 for(const c of list){assert(c.entryIds.length);for(const id of c.entryIds){assert(id>0&&id<=lines.length);assert(lines[id-1]);}assert.equal(c.rankVerification,year>=2024?'official':'secondary-list-position-not-certified-oricon-rank');}
}
for(const [word,reading] of [['1/2','にぶんのいち'],['1/3の純情な感情','さんぶんのいちのじゅんじょうなかんじょう'],['Doki it','どきっと'],['Pieces','ぴーしーず'],['PIECES OF A DREAM','ぴーしずおぶあどりーむ'],['Snow Man','すのーまん'],['SixTONES','すとーんず'],['京本大我','きょうもとたいが'],['池田瑛紗','いけだてれさ'],['七五三掛龍也','しめかけりゅうや']])assert(items.some(x=>x.word===word&&x.reading===reading),word);
assert(items.some(x=>x.word==='永遠に'&&x.artist==='KinKi Kids'&&x.reading==='えいえんに'));
assert(items.some(x=>x.word==='永遠に'&&x.artist==='ゴスペラーズ'&&x.reading==='とわに'));
assert.equal(items.filter(x=>x.word==='RYO'&&x.category.includes('メンバー')).length,2,'Same stage name must keep separate people');
assert(items.some(x=>x.word==='HIDE'&&x.meaning.includes('GReeeeN')));assert(items.some(x=>x.word==='hide'&&x.meaning.includes('X JAPAN')));
const naoto=items.filter(x=>x.word==='NAOTO');assert.equal(naoto.length,2);assert(naoto.some(x=>x.meaning.includes('EXILE')&&x.meaning.includes('三代目')));assert(naoto.some(x=>x.meaning.includes('ORANGE RANGE')));
for(const word of ['花','虹','嵐']){const x=items.find(x=>x.word===word);assert(map.get(x.reading).meanings.length>=2);}
console.log(JSON.stringify({passed:true,added:items.length,total:lines.length,chartSlots:coverage.length,years:36,allLevel5:true,allExplanationOnly:true,allEntertainment:true,stableBaseline:true,homonyms:true}));
