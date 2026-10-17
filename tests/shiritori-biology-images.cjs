const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=process.env.SHIRITORI_ROOT||path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split('\n'),fields=lines.shift().split(','),rows=lines.map(line=>Object.fromEntries(line.split(',').map((x,i)=>[fields[i],x])));
const name='data/image-coverage/2026-10-17-biology-generated/',plan=read(name+'plan.json'),summary=read(name+'summary.json'),manifest=read('assets/shiritori/manifest.json'),byfile=new Map(manifest.assets.map(x=>[x.file,x]));
const a=read('data/dictionary-imports/2026-10-17-biology-cultivars.review.json'),b=read('data/dictionary-imports/2026-10-17-snakes-danger.review.json');
const coverage=read('data/image-coverage/review-2026-10-10.json');
assert.equal(a.length,501);assert.equal(b.length,93);assert.equal(b.filter(x=>x.category==='ヘビ').length,76);assert.equal(rows.length,12894);assert.equal(plan.items.length,594);assert.equal(summary.generatedImages,578);assert.equal(summary.sharedImages,16);
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');assert.equal(summary.afterSha256,sha(text));
const generated=new Set(),sheets=new Set();
for(const x of [...a,...b]){
 const r=rows[x.id-1];for(const k of fields)assert.equal(String(x[k]),r[k],x.word+' '+k);
 assert.ok(r.image_asset&&r.image_mode==='asset');const asset=byfile.get(path.basename(r.image_asset));assert.ok(asset,x.word);
 assert.ok(['new','reused'].includes(coverage[x.id-1].assignment),'New-image catalog must include '+x.word);
 assert.ok(asset.aliases.some(y=>y.id===x.id&&y.meaning===r.meaning&&y.reading===r.reading),x.word+' exact sense alias');
 assert.ok(fs.existsSync(path.join(root,r.image_asset)));
 if(asset.file.startsWith('biology20261017-')){generated.add(asset.file);sheets.add(asset.sourceSheet);assert.ok(asset.cropValidation&&asset.sha256&&asset.status==='reviewed');assert.equal(asset.sha256,sha(fs.readFileSync(path.join(root,r.image_asset))));}
 if(x.aliasOfReading){const parent=rows.filter(y=>y.reading===x.aliasOfReading&&y.meaning===x.meaning);assert.equal(parent.length,1);assert.equal(r.image_asset,parent[0].image_asset);}
 if(b.includes(x)){assert.equal(x.grade,4);assert.ok(x.taxon&&x.sources.length>=2);}
}
assert.equal(generated.size,578);assert.equal(sheets.size,37);
const ids=new Set();
for(const sheet of plan.sheets){
 const n=String(sheet.sheet).padStart(2,'0'),v2=path.join(root,name+'sheet'+n+'-v2-staged.json'),s=read(name+'sheet'+n+(fs.existsSync(v2)?'-v2':'')+'-staged.json');
 assert.equal(s.semanticPassed,true);assert.equal(s.mechanicalPassed,true);assert.ok(s.semanticReview);
 const real=s.tiles.filter(x=>!x.filler);assert.deepEqual(s.approvedIds,real.map(x=>x.id));
 for(const tile of real){assert.ok(!ids.has(tile.id));ids.add(tile.id);const asset=byfile.get(tile.filename);assert.equal(asset.sourceSheet,s.sourceSheet);assert.equal(asset.tileIndex,tile.tileIndex);assert.equal(asset.prompt,s.prompt);assert.equal(asset.cropValidation,s.cropValidation);}
}
assert.equal(ids.size,578);
for(const [word,scientific] of [['ハイ','Sinomicrurus boettgeri'],['ヒャン','Sinomicrurus japonicus'],['ミルクヘビ','Lampropeltis triangulum']])assert.equal(b.find(x=>x.word===word).imagequery_en,scientific);
console.log(JSON.stringify({passed:true,addedWords:594,snakes:76,generatedImages:generated.size,sharedWords:16,approvedSheets:sheets.size,totalRows:rows.length}));
