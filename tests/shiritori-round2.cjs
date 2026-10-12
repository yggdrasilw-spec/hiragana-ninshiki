const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const ledger=read('data/corrections/round2/ledger.json'),plan=read('data/corrections/round2/plan.json');
const liveText=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),history=read('data/dictionary-imports/history.json');
const later=history.findIndex(r=>r.ledger==='data/corrections/review93-2026-10-11/ledger.json');
const text=later<0?liveText:require('../scripts/shiritori-correction-ledger.cjs').undoImports(liveText,history.slice(later));
const lines=text.trimEnd().split('\n'),heads=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
const liveRows=liveText.trimEnd().split('\n').slice(1).map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
assert.equal(crypto.createHash('sha256').update(text).digest('hex'),ledger.afterSha256);
assert.equal(ledger.requestedOrders.length,83);assert.equal(ledger.sourceImages,76);
assert.equal(rows.length,ledger.sourceRows-1);assert.equal(ledger.currentRows,rows.length);
assert.equal(new Set(ledger.requestedOrders.map(o=>o.orderId)).size,83);
const byOrigin=new Map(ledger.currentOriginalIds.map((oid,i)=>[oid,rows[i]]));
const word=(oid,w,r)=>{assert.equal(byOrigin.get(oid).word,w);assert.equal(byOrigin.get(oid).reading,r);};
word(311,'痛い','いたい');word(1034,'筆算','ひっさん');word(1105,'割り込む','わりこむ');word(1372,'コーディネート','こーでぃねーと');word(1374,'居合わせる','いあわせる');
assert.ok(!byOrigin.has(1173));assert.ok(!rows.some(r=>['痛','書き算','割入','噛みやん','着合う','居合わせ'].includes(r.word)));
for(const [a,b] of [[417,416],[1432,608],[872,4363],[888,5223],[911,3458],[1065,472],[1175,472],[1220,1215],[1248,4153],[1271,48],[1273,214],[1307,4544],[1375,1871],[1942,979]])assert.notEqual(byOrigin.get(a).image_asset,byOrigin.get(b).image_asset);
for(const ids of [[645,648],[829,1567,1574,2187],[911,4312],[937,2974],[920,3615,3620],[1309,2014,3373,4215],[1056,2024,3503]])assert.equal(new Set(ids.map(id=>byOrigin.get(id).image_asset)).size,1);
assert.equal(byOrigin.get(1175).image_asset,'assets/shiritori/complete-1199.png');
assert.match(byOrigin.get(364).meaning,/一本の指/);assert.match(byOrigin.get(864).meaning,/頼まれて/);assert.match(byOrigin.get(984).meaning,/自然/);assert.ok(!byOrigin.get(1195).meaning.includes('通う'));
for(const o of ledger.requestedOrders){assert.deepEqual(byOrigin.get(o.orderId)||null,o.after);if(o.id)assert.deepEqual(rows[o.id-1],o.after);}
const coverage=read('data/image-coverage/review-2026-10-10.json');assert.equal(coverage.length,liveRows.length);
liveRows.forEach((r,i)=>{assert.match(r.reading,/^[ぁ-ゖー]+$/);assert.ok(r.meaning&&!/[\r\n,]/.test(r.meaning));assert.equal(coverage[i].id,i+1);for(const k of ['word','reading','meaning','image_asset'])assert.equal(coverage[i][k],r[k]);});
const manifest=read('assets/shiritori/manifest.json'),assets=manifest.assets;
for(const a of assets){const expected=liveRows.flatMap((r,i)=>r.image_asset==='assets/shiritori/'+a.file?[{id:i+1,reading:r.reading,word:r.word,meaning:r.meaning}]:[]);assert.ok(expected.length);assert.deepEqual(a.aliases.map(({id,reading,word,meaning})=>({id,reading,word,meaning})),expected);}
for(const file of ledger.replacedImages){const a=(manifest.previousRound2Assets||assets).find(a=>a.file===file);assert.ok(a.prompt&&a.review&&a.scenePrompt&&a.cropBox&&a.cropMethod);assert.ok(fs.existsSync(path.join(root,'assets/shiritori',a.sourceSheet)));assert.equal(a.status,'reviewed');assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'assets/shiritori',a.archivedFile||file))).digest('hex'),a.sha256);}
require('../scripts/shiritori-correction-ledger.cjs').historicalRows();
console.log(JSON.stringify({passed:true,orders:83,sourceImages:76,updatedImages:ledger.replacedImages.length,rows:rows.length,historicalRestore:true}));
