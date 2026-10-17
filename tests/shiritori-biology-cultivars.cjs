const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const root=process.env.SHIRITORI_ROOT||path.resolve(__dirname,'..');
const name='2026-10-17-biology-cultivars';
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const plan=json('data/dictionary-imports/'+name+'.coverage.json'),review=json('data/dictionary-imports/'+name+'.review.json'),summary=json('data/dictionary-imports/'+name+'.summary.json'),source=json('data/dictionary-imports/'+name+'.source.json');
const bytes=fs.readFileSync(path.join(root,'whitelist.csv')),text=bytes.toString('utf8'),lines=text.trimEnd().split('\n'),header=lines[0].split(',');
const rows=lines.slice(1).map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(hash(lines.slice(0,plan.baselineRows+1).join('\n')+'\n'),plan.baselineSha256,'All preceding IDs and fields stay unchanged');
assert.ok(rows.length>=plan.baselineRows+review.length);
assert.equal(summary.addedWords,review.length);
assert.ok(json('data/dictionary-imports/history.json').some(x=>x.afterSha256===summary.afterSha256),'Original vocabulary import hash stays in history');
assert.equal(new Set(review.map(x=>x.reading)).size,review.length,'Every added row has a separate input reading');
const runtime={window:{}};vm.createContext(runtime);
for(const f of ['shiritori-grade-policy.js','shiritori-image-policy.js','shiritori-vocabulary.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),runtime);
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
vm.runInContext(html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST =')),runtime);
runtime.csv=text;const parsed=vm.runInContext('parseCSV(csv,true)',runtime),byreading=new Map(parsed.map(r=>[r.reading,r]));
const grades=json('data/shiritori-grade-review.json'),manifest=json('assets/shiritori/manifest.json');
const coreVegetables=plan.items.filter(x=>x.category==='野菜'&&!x.aliasOfReading);
assert.equal(coreVegetables.length,118);
for(const x of plan.items){
 const matches=x.status==='existing'?x.existingIds.map(id=>rows[id-1]):[rows[x.id-1]];
 assert.ok(matches.some(r=>r.reading===x.reading&&r.meaning),'Coverage checklist item must have a real row: '+x.word);
}
const gradeCounts={},categories={};
for(const x of review){
 const r=rows[x.id-1];
 for(const k of ['reading','word','meaning','level','imagequery','imagequery_en','image_mode','image_asset','image_credit'])assert.equal(r[k],String(x[k]),x.word+' '+k);
 assert.ok(x.sources.length&&x.lexicalSource&&x.meaningReason&&x.ageReason);
 assert.ok(x.sources.every(e=>/^https:\/\//.test(e.url)));
 const g=byreading.get(x.reading),i=g?.words.findIndex((w,i)=>w===x.word&&g.meanings[i]===x.meaning);
 assert.ok(i>=0,'App parser must preserve this exact meaning: '+x.word);
 assert.equal(g.meaningLevels[i],x.grade);
 assert.equal(grades[x.id-1].level,x.grade);
 assert.equal(grades[x.id-1].meaning,x.meaning);
 const kind=runtime.window.ShiritoriImagePolicy.category(r.word,r.meaning,r.imagequery);
 if(x.sourceExistingId){const parent=rows[x.sourceExistingId-1];assert.equal(kind,runtime.window.ShiritoriImagePolicy.category(parent.word,parent.meaning,parent.imagequery),'Same-sense alias retains image classification');}
 else if(['犬種','猫種','鳥類','爬虫類','その他生物'].includes(x.category))assert.equal(kind,'animal',x.word+' animal settings');
 else assert.ok(['plant','fungi'].includes(kind),x.word+' plant/fungi settings: '+kind);
 if(x.aliasOfReading){
  const other=plan.items.find(y=>y.reading===x.aliasOfReading);
  assert.ok(other&&other.reading!==x.reading);
  assert.equal(x.meaning,other.status==='existing'?rows[other.existingIds[0]-1].meaning:other.meaning);
 }
 if(x.sourceExistingId){
  const original=rows[x.sourceExistingId-1];assert.equal(r.meaning,original.meaning);
  for(const k of ['image_asset','image_mode','image_credit'])assert.equal(r[k],original[k]);
 }
 if(r.image_asset){
  assert.ok(fs.existsSync(path.join(root,r.image_asset)));
  const asset=manifest.assets.find(a=>a.file===path.basename(r.image_asset));
  assert.ok(asset.aliases.some(a=>a.id===x.id&&a.meaning===x.meaning));
 }
 if(x.distinctSenseReason){
  assert.ok(g.words.length>=2,'Homonym must retain old meanings: '+x.word);
 }
 categories[x.category]=(categories[x.category]||0)+1;gradeCounts[x.grade]=(gradeCounts[x.grade]||0)+1;
}
const normalize=s=>s.normalize('NFKC');
const riceNames=new Set(plan.items.filter(x=>x.category==='コメ').map(x=>normalize(x.word)));
for(const names of Object.values(source.hiroshima.table))for(const word of names)assert.ok(riceNames.has(normalize(word)),'Every Hiroshima brand in the 2026 source is registered: '+word);
assert.equal(source.hiroshima.coverageCount,38);
assert.ok(plan.items.some(x=>x.reading==='もえいぶき'&&x.meaning.includes('広系酒４５号')));
assert.ok(plan.items.some(x=>x.reading==='ひろけいしゅよんじゅうごごう'&&x.aliasOfReading==='もえいぶき'));
assert.equal(byreading.get('ぶろっこりー').meaningLevels[0],1);
assert.equal(byreading.get('せんぼんにしき').meaningLevels[0],4);
const history=json('data/dictionary-imports/history.json');assert.equal(history.at(-1).afterSha256,hash(bytes));
assert.equal(json('data/image-coverage/review-updates.json').entries.length,rows.length);
console.log(JSON.stringify({passed:true,added:review.length,precedingRowsPreserved:plan.baselineRows,coreVegetables:coreVegetables.length,hiroshimaRice:38,categories,gradeCounts}));
