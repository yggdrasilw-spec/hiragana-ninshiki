const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-10-16-expansion1024f',dir='data/image-coverage/'+name;
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const summary=json(dir+'/summary.json'),plan=json(dir+'/plan.json'),reviews=json('data/dictionary-imports/'+name+'.review.json');
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split(/\r?\n/),header=lines.shift().split(',');
const rows=lines.map(s=>Object.fromEntries(s.split(',').map((v,i)=>[header[i],v])));
const before=fs.readFileSync(path.join(root,dir,'baseline.csv'),'utf8').trimEnd().split(/\r?\n/).slice(1);
assert.ok(plan.items.length>=1024);assert.ok(summary.distinctNewReadings>=1024);assert.equal(reviews.length,plan.items.length);
const keys=plan.items.map(x=>[x.reading,x.word,x.meaning].join(','));assert.equal(new Set(keys).size,keys.length);
const oldkeys=new Set(before.map(x=>x.split(',').slice(0,3).join(',')));for(const k of keys)assert.ok(!oldkeys.has(k));
before.forEach((line,i)=>{const now=lines[i].split(','),old=line.split(',');assert.deepEqual(now.slice(0,7),old.slice(0,7),'Preserve prior vocabulary, levels, IDs and assets');if(old[1]!=='チロルチョコ')assert.deepEqual(now,old);});
const assets=json('assets/shiritori/manifest.json').assets,byfile=new Map(assets.map(a=>[a.file,a]));assert.equal(byfile.size,assets.length);
let none=0,illustrated=0;
for(const x of reviews){
 const r=rows[x.id-1];for(const k of ['word','reading','meaning'])assert.equal(r[k],x[k]);assert.match(r.reading,/^[ぁ-ゖー]+$/);
 assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.imageReason);
 if(x.imagePolicy==='none'){none++;assert.equal(r.image_mode,'none');assert.equal(r.image_asset,'');assert.equal(x.imageStatus,'intentionally-omitted');}
 else{illustrated++;assert.equal(r.image_mode,'asset');assert.ok(r.image_asset);const a=byfile.get(path.basename(r.image_asset));assert.ok(a);assert.ok(a.aliases.some(y=>y.id===x.id&&y.meaning===x.meaning));const png=fs.readFileSync(path.join(root,r.image_asset));assert.equal(png.readUInt32BE(16),256);assert.equal(png.readUInt32BE(20),256);if(x.reuseSlot){const target=plan.items.find(y=>y.slot===x.reuseSlot);assert.equal(rows[target.id-1].image_asset,r.image_asset);}}
}
assert.equal(none,summary.explanationOnly);assert.equal(illustrated,summary.newIllustrations+summary.reusedIllustrations);assert.equal(summary.missingRequiredImages,0);
for(const word of ['コカ・コーラ','ペプシ','ファンタ','CCレモン','アクエリアス','ポカリスエット','NSX','ポッキー','うまい棒'])assert.equal(reviews.find(x=>x.word===word).imagePolicy,'none');
for(const word of ['タイタン','カペラ','ミラ','アトラス','ゴルフ','トッポ','エリーゼ','コースター'])assert.ok(reviews.filter(x=>x.word===word).length>=2,'Keep distinct homonyms: '+word);
assert.ok(reviews.find(x=>x.word==='水星').distinctSenseReason);assert.equal(json(dir+'/core-coverage.json').missing.length,0);
const hist=json('data/dictionary-imports/history.json');assert.equal(hist.at(-1).afterSha256,crypto.createHash('sha256').update(text).digest('hex'));
console.log(JSON.stringify({passed:true,added:reviews.length,distinctNewReadings:summary.distinctNewReadings,explanationOnly:none,illustrated,oldRowsPreserved:before.length}));
