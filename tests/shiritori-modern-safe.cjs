const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-11-16-modern-safe';
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8'));
const reviews=read(`data/dictionary-imports/${name}.review.json`),summary=read(`data/dictionary-imports/${name}.summary.json`),entries=read(`data/dictionary-imports/${name}.entries.json`),excluded=read(`data/dictionary-imports/${name}.excluded.json`);
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const history=read('data/dictionary-imports/history.json');
const idx=history.findIndex(x=>String(x.batch||'').replaceAll('\\','/')===`data/dictionary-imports/${name}.csv`);assert(idx>=0);
const {undoImports}=require('../scripts/shiritori-correction-ledger.cjs');
const snapshot=undoImports(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),history.slice(idx+1));
assert.equal(hash(snapshot),summary.afterSha256);
assert.equal(hash(snapshot.trimEnd().split('\n').slice(0,summary.baselineRows+1).join('\n')+'\n'),summary.baselineSha256);
assert.equal(reviews.length,summary.added);assert.equal(entries.length,summary.added);
const key=x=>[x.reading,x.word,x.meaning].join('\t');assert.equal(new Set(reviews.map(key)).size,reviews.length);
const built=require('../scripts/build-shiritori-delivery.cjs').build(root),byReading=new Map(built.rows.map(r=>[r.reading,r]));
const metadata=new Map(entries.map(x=>[key(x),x]));
for(const x of reviews){
 const row=byReading.get(x.reading),i=row?.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);assert(i>=0,x.word);
 assert.equal(row.meaningLevels[i],x.grade,x.word);assert.equal(row.genres[i],metadata.get(key(x)).genre,x.word);
 assert(row.imagequeries[i].source?.url.startsWith('https://'),x.word);
 assert.equal(x.safetyReview.decision,'include',x.word);assert(x.safetyReview.context&&x.ageReason&&x.imageReason);
 assert(x.lexicalSource.references.length>0);assert.equal(x.lexicalSource.expertReviewed,false);
}
for(const x of excluded.items)assert(!reviews.some(r=>r.word===x.term),'Excluded candidate must not enter this batch: '+x.term);
assert(history[idx].addedLines.every(line=>line.split(',')[6]===''&&line.split(',')[7]==='none'));
for(const [r,w,fragment,g] of [['くさ','草','笑った','other'],['ぽすと','ポスト','SNS','technology'],['ぬま','沼','趣味','entertainment'],['たいぱ','タイパ','時間','society'],['えっほえっほ','エッホエッホ','フクロウ','entertainment'],['ふぃじかるえーあい','フィジカルAI','現実','technology']]){
 const row=byReading.get(r),i=row.words.findIndex((word,i)=>word===w&&row.meanings[i].includes(fragment));assert(i>=0,w);assert.equal(row.genres[i],g);
}
const grass=byReading.get('くさ');assert(grass.meanings.some(m=>m.includes('植物')),'The ordinary grass sense stays present');
const post=byReading.get('ぽすと');assert(post.meanings.some(m=>m.includes('郵便')),'The mailbox sense stays present');
console.log(JSON.stringify({passed:true,added:reviews.length,oldRowsPreservedByImport:summary.baselineRows,safetyReviews:true,excludedCandidates:excluded.items.length,independentSenses:true,sourceAndGradePairing:true}));
