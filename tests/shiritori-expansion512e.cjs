const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-10-15-expansion512e';
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const plan=json('data/image-coverage/'+name+'/plan.json'),summary=json('data/image-coverage/'+name+'/summary.json');
const snapshot=json('data/image-coverage/'+name+'/reservation-snapshot.json');
const text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=text.trimEnd().split(/\r?\n/),header=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
assert.equal(plan.items.length,512);assert.equal(new Set(plan.items.map(x=>x.reading)).size,512);
assert.equal(hash(header.join(',')+'\n'+lines.slice(0,summary.baselineRows).join('\n')+'\n'),summary.beforeSha256,'All preceding vocabulary/IDs/images preserved');
const reserved=new Set(snapshot.readings),old=new Set(rows.slice(0,summary.baselineRows).map(r=>r.reading));
const assets=new Map(json('assets/shiritori/manifest.json').assets.map(x=>[x.file,x]));
const coverage=json('data/image-coverage/review-2026-10-10.json');let cards=0,illustrations=0;
for(const x of plan.items){
 assert.ok(!reserved.has(x.reading),'Other batches reserved '+x.reading);
 assert.ok(!old.has(x.reading));assert.match(x.reading,/^[ぁ-ゖー]+$/);
 const row=rows[x.id-1];for(const k of ['reading','word','meaning'])assert.equal(row[k],x[k]);
 assert.equal(row.level,'3');assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.imageReason&&x.sources.length);
 const review=coverage[x.id-1];assert.equal(review.word,row.word);
 if(x.imageStatus==='name-card'){
  cards++;assert.equal(row.image_credit,'独自文字カード（外部検索なし）');assert.equal(row.image_mode,'asset');
  assert.equal(row.image_asset,'assets/shiritori/'+x.filename);const a=assets.get(x.filename);assert.ok(a);assert.ok(a.aliases.some(y=>y.id===x.id&&y.reading===x.reading));
  const b=fs.readFileSync(path.join(root,row.image_asset));assert.equal(b.readUInt32BE(16),256);assert.equal(b.readUInt32BE(20),256);
 }else{
  illustrations++;assert.equal(x.imageStatus,'illustration');assert.equal(row.image_credit,'AI生成イラスト');
  assert.equal(row.image_asset,'assets/shiritori/'+x.filename);assert.equal(row.image_mode,'asset');
  const a=assets.get(x.filename);assert.ok(a);assert.equal(a.cropValidation,x.cropValidation);
  assert.ok(a.aliases.some(y=>y.id===x.id&&y.reading===x.reading));assert.ok(review.target);assert.equal(review.status,'covered');
 }
}
assert.equal(cards,360);assert.equal(illustrations,152);assert.equal(summary.missingImages,0);assert.equal(summary.coveredWords,512);
assert.deepEqual(Object.fromEntries(Object.keys(plan.categories).map(c=>[c,plan.items.filter(x=>x.category===c).length])),plan.categories);
const source=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');assert.ok(source.includes("assetCredit === '独自文字カード（外部検索なし）'"),'Name cards never search externally, including broken assets');
console.log(JSON.stringify({passed:true,words:512,cards,illustrations,priorRowsPreserved:summary.baselineRows,reservedReadingCollisions:0}));
