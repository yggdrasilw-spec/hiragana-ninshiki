const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'data/image-coverage/2026-10-18-expansion1024h');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),plan=read(path.join(out,'plan.json')),summary=read(path.join(out,'summary.json'));
const csv=fs.readFileSync(path.join(root,'whitelist.csv')),baseline=fs.readFileSync(path.join(out,'registration-baseline.csv'));
assert(csv.subarray(0,baseline.length).equals(baseline),'Preserve every preceding row and ID');
const lines=csv.toString('utf8').trimEnd().split('\n'),head=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((x,i)=>[head[i],x]))),oldReadings=new Set(rows.slice(0,plan.baselineRows).map(x=>x.reading));
assert.equal(plan.items.length,1024);assert.equal(new Set(plan.items.map(x=>x.reading)).size,1024);
assert.equal(rows.length,plan.baselineRows+1024);
const manifest=read(path.join(root,'assets/shiritori/manifest.json')).assets,byfile=new Map(manifest.map(x=>[x.file,x]));
const grade=read(path.join(root,'data/shiritori-grade-review.json')),inventory=read(path.join(root,'data/image-coverage/r2-assets.json'));
const entries=new Map(inventory.entries.map(x=>[x.key,x]));
for(const x of plan.items){
 assert(!oldReadings.has(x.reading));assert.equal(x.gameEndingN,x.reading.endsWith('ん'));
 const row=rows[x.id-1];for(const k of ['reading','word','meaning','level'])assert.equal(row[k],String(x[k]));
 assert(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.imageReason&&x.entryId);
 assert.equal(row.image_mode,'asset');assert.equal(row.image_asset,'assets/shiritori/'+x.filename);
 assert.equal(grade[x.id-1].level,x.grade);assert.equal(grade[x.id-1].meaning,x.meaning);
 const a=byfile.get(x.filename);assert(a);assert(a.aliases.some(v=>v.id===x.id&&v.meaning===x.meaning));
 assert.equal(a.cropValidation,x.cropValidation);assert.equal(a.sourceSheet,x.sourceSheet);
 const bytes=fs.readFileSync(path.join(root,row.image_asset));assert.equal(bytes.readUInt32BE(16),256);assert.equal(bytes.readUInt32BE(20),256);
 const e=entries.get(row.image_asset);assert(e);assert.equal(e.bucket,'shiritori-images');assert.equal(e.sha256,crypto.createHash('sha256').update(bytes).digest('hex'));
 assert(entries.get('assets/shiritori/'+x.sourceSheet)?.bucket==='shiritori-image-archive');
}
assert.equal(summary.addedWords,1024);assert.equal(summary.generatedImages,1024);assert.equal(summary.sheets,64);assert.equal(summary.missingImages,0);
const hash=crypto.createHash('sha256').update(csv).digest('hex');assert.equal(summary.afterSha256,hash);
assert.equal(read(path.join(root,'data/dictionary-imports/history.json')).at(-1).afterSha256,hash);
assert.equal(read(path.join(root,'data/shiritori-grade-decisions.json')).sourceSha256,hash);
console.log(JSON.stringify({passed:true,words:1024,images:1024,sheets:64,gradeCounts:summary.gradeCounts,endingNWords:summary.endingNWords,precedingRowsPreserved:plan.baselineRows,r2Inventory:true}));
