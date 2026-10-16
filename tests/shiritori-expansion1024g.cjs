const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-10-16-expansion1024g',out=path.join(root,'data/image-coverage',name);
const json=p=>JSON.parse(fs.readFileSync(p,'utf8')),plan=json(path.join(out,'plan.json')),summary=json(path.join(out,'summary.json'));
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split(/\r?\n/),header=lines.shift().split(',');
const rows=lines.map(s=>Object.fromEntries(s.split(',').map((v,i)=>[header[i],v])));
const baseline=fs.readFileSync(path.join(out,'registration-baseline.csv'));
assert.ok(Buffer.from(text).subarray(0,baseline.length).equals(baseline),'Preserve every column and ID of all preceding rows');
assert.equal(plan.items.length,1024);assert.equal(new Set(plan.items.map(x=>x.reading)).size,1024);
const oldReadings=new Set(lines.slice(0,plan.baselineRows).map(s=>s.split(',')[0]));
const gas=json(path.join(root,'data/dictionary-imports/2026-10-16-gas-vocabulary.review.json'));
assert.ok(!plan.items.some(x=>gas.some(y=>x.reading===y.reading)),'Keep the concurrent GAS batch disjoint');
const assets=json(path.join(root,'assets/shiritori/manifest.json')).assets,byfile=new Map(assets.map(a=>[a.file,a]));
assert.equal(byfile.size,assets.length);
for(const x of plan.items){
 assert.ok(!oldReadings.has(x.reading));assert.ok(!x.reading.endsWith('ん'));
 const r=rows[x.id-1];for(const k of ['word','reading','meaning','level'])assert.equal(r[k],String(x[k]));
 assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.imageReason);
 assert.equal(r.image_mode,'asset');assert.equal(r.image_asset,'assets/shiritori/'+x.filename);
 const a=byfile.get(x.filename);assert.ok(a);assert.ok(a.aliases.some(y=>y.id===x.id&&y.meaning===x.meaning));
 const b=fs.readFileSync(path.join(root,r.image_asset));assert.equal(b.readUInt32BE(16),256);assert.equal(b.readUInt32BE(20),256);
 if(x.assignment==='new')assert.ok(x.cropValidation&&x.sourceSheet&&a.cropValidation===x.cropValidation);
 else assert.equal(r.image_asset,rows[x.sourceId-1].image_asset);
}
assert.equal(summary.addedWords,1024);assert.equal(summary.newReadings,1024);assert.equal(summary.generatedImages,1018);assert.equal(summary.missingImages,0);
const history=json(path.join(root,'data/dictionary-imports/history.json'));assert.equal(history.at(-1).afterSha256,crypto.createHash('sha256').update(text).digest('hex'));
console.log(JSON.stringify({passed:true,added:1024,newReadings:1024,images:1018,reused:6,precedingRowsPreserved:plan.baselineRows}));
