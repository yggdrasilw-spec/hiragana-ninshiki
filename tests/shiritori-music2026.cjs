const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-29-music2026');
const get=s=>JSON.parse(fs.readFileSync(base+s,'utf8')),items=get('.review.json'),s=get('.summary.json'),coverage=get('.coverage.json'),sources=get('.sources.json');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n'),header=lines.shift().split(',');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert(s.registered);assert.equal(items.length,s.added);assert(items.length>500);
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,s.baselineRows).join('\n')+'\n'),s.beforeSha256);
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,s.baselineRows+items.length).join('\n')+'\n'),s.afterSha256);
const grades=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-grade-review.json'),'utf8'));
const images=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-2026-10-10.json'),'utf8'));
const updates=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-updates.json'),'utf8'));
assert.equal(grades.length,lines.length);assert.equal(images.length,lines.length);assert.equal(updates.entries.length,lines.length);assert.equal(updates.csvSha256,hash(csv));
const {rows}=require('../scripts/build-shiritori-delivery.cjs').build(root),map=new Map(rows.map(x=>[x.reading,x]));
const keys=new Set();
for(const x of items){
 assert.match(x.reading,/^[ぁ-ゖー]+$/);assert(x.lexicalSource.references.length&&x.ageReason&&x.meaningReason&&x.distinctSenseReason);
 assert(!keys.has(x.nodeKey));keys.add(x.nodeKey);
 const actual=lines[x.id-1].split(',');assert.equal(actual.length,9);assert.deepEqual(actual,header.map(k=>String(x[k])));
 assert.equal(x.image_mode,'none');assert.equal(grades[x.id-1].level,5);assert.equal(images[x.id-1].status,'explanation-only');assert.deepEqual(updates.entries[x.id-1].text,actual.slice(0,3));
 const r=map.get(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'entertainment');assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);
}
assert.equal(coverage.length,s.coverageRecords);for(const c of coverage){assert(c.entryIds.length);for(const id of c.entryIds)assert(id>0&&id<=lines.length);}
assert.equal(sources.monthlyCoverage.length,12);assert.equal(s.monthlyTop100Complete,false);
for(const c of sources.monthlyCoverage){assert.equal(c.verifiedRanks.length+c.missingRanks.length,100);assert.equal(c.complete,false);}
for(const kind of ['oricon-monthly-cd','oricon-weekly-cd','oricon-download','oricon-streaming','oricon-tiktok','tiktok-summer-announcement'])assert(coverage.some(x=>x.kind===kind),kind);
for(const [word,reading] of [['章','しるし'],['REBON','りぼん'],['小野寺梓','おのでらあずさ'],['桜庭遥花','さくらばはるか'],['藤井風','ふじいかぜ'],['星街すいせい','ほしまちすいせい'],['宮本佳林','みやもとかりん'],['STARGLOW','すたーぐろう'],['CHIKA','ちか'],['JISOO','じす']])assert(items.some(x=>x.word===word&&x.reading===reading),word);
assert.equal(items.filter(x=>x.word==='人誑し'||x.word==='ひとたらし').length,1);
assert.equal(items.filter(x=>x.word==='櫻井優衣').length,1);
console.log(JSON.stringify({passed:true,added:items.length,categories:s.categories,total:lines.length,coverageRecords:coverage.length,meaningLevel:5,imageMode:'none',stableBaseline:true,publicSourcesOnly:true,monthlyTop100Complete:false}));
