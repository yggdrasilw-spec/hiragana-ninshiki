const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-28-characters1024');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),items=read(base+'.review.json'),summary=read(base+'.summary.json');
const bytes=fs.readFileSync(path.join(root,'whitelist.csv')),lines=bytes.toString('utf8').trimEnd().split('\n'),head=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[head[i],v]))),baseline=Buffer.from(lines.slice(0,summary.baselineRows).join('\n')+'\n');
const original=Buffer.concat([Buffer.from(head.join(',')+'\n'),baseline]);
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(original),summary.beforeSha256,'Every preceding row/ID must remain unchanged');
assert.equal(items.length,1024);assert.equal(new Set(items.map(x=>x.reading)).size,1024);
const existing=new Set(rows.slice(0,summary.baselineRows).map(x=>x.reading));
const {build}=require('../scripts/build-shiritori-delivery.cjs'),built=build(root),delivered=new Map(built.rows.map(x=>[x.reading,x]));
const grades=read(path.join(root,'data/shiritori-grade-review.json'));
for(const x of items){
 assert(!existing.has(x.reading));assert.match(x.reading,/^[ぁ-ゖー]+$/);
 const row=rows[x.id-1];for(const k of ['reading','word','meaning'])assert.equal(row[k],x[k]);
 assert.equal(row.image_mode,'none');for(const k of ['image_asset','imagequery','imagequery_en','image_credit'])assert.equal(row[k],'');
 assert(x.lexicalSource.url&&x.lexicalSource.method&&x.meaningReason&&x.ageReason&&x.imageReason);
 const d=delivered.get(x.reading);assert(d);const i=d.words.findIndex((w,i)=>w===x.word&&d.meanings[i]===x.meaning);assert(i>=0);
 assert.equal(d.genres[i],'fiction');assert.equal(d.meaningLevels[i],5);assert.equal(d.imagequeries[i].mode,'none');assert.equal(grades[x.id-1].level,5);
 assert.equal(x.gameEndingN,x.reading.endsWith('ん'));
}
assert(rows.length>=summary.baselineRows+1024);assert.equal(hash(Buffer.from([head.join(','),...lines.slice(0,summary.baselineRows+1024)].join('\n')+'\n')),summary.afterSha256);
console.log(JSON.stringify({passed:true,added:1024,precedingRowsPreserved:summary.baselineRows,allFiction:true,allExplanationOnly:true,categories:summary.categories}));
