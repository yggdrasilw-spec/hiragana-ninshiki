const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),batch='2026-11-16-life-family';
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8'));
const summary=read(`data/dictionary-imports/${batch}.summary.json`),items=read(`data/dictionary-imports/${batch}.review.json`);
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const history=read('data/dictionary-imports/history.json'),n=history.findIndex(h=>String(h.batch||'').replaceAll('\\','/')===`data/dictionary-imports/${batch}.csv`);
assert(n>=0);const {undoImports}=require('../scripts/shiritori-correction-ledger.cjs');
const snapshot=undoImports(csv,history.slice(n+1));
assert.equal(hash(snapshot),summary.afterSha256);
const baseline=snapshot.trimEnd().split('\n').slice(0,summary.baselineRows+1).join('\n')+'\n';
assert.equal(hash(baseline),summary.baselineSha256,'All previous rows remain byte-identical');
assert.equal(summary.baselineRows,92254,'The obsolete 89747-row checkout must not be the baseline');
assert.equal(items.length,178);assert.equal(summary.newReadings,170);assert.equal(summary.existingReadings,8);
assert.equal(summary.skippedExisting,12);assert.equal(summary.held,2);
const oldReadings=new Set(baseline.trimEnd().split('\n').slice(1).map(line=>line.split(',')[0]));
assert.equal(new Set(items.filter(x=>!oldReadings.has(x.reading)).map(x=>x.reading)).size,170);
assert.equal(new Set(items.map(x=>[x.reading,x.word,x.meaning].join('\t'))).size,items.length);
const {build}=require('../scripts/build-shiritori-delivery.cjs');
const built=build(root),index=new Map(built.rows.map(r=>[r.reading,r]));
for(const x of items){
 const row=index.get(x.reading),i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
 assert(i>=0,x.word);assert.equal(row.meaningLevels[i],x.grade,x.word);assert.equal(row.genres[i],x.genre,x.word);
 assert.equal(row.imagequeries[i].mode,'none');assert(row.imagequeries[i].source?.url.startsWith('https://'));
 assert.equal(row.namedSenses?.[i],false,x.word+' is an ordinary sense');
 assert(x.evidence.length&&x.evidence.every(e=>e.senseNumbers.length));assert.equal(x.imageEligible,true);
}
for(const reading of ['こぶくろ','しふく']){
 const row=index.get(reading);assert(row.words.length>=2,'Earlier homonyms are preserved');
}
assert(index.get('こぶくろ').words.includes('コブクロ'));assert(index.get('こぶくろ').words.includes('小袋'));
assert.equal(index.get('おりたたみがさ').meaningLevels[0],1);
assert.equal(history[n].addedLines.length,178);
const extra=read('data/dictionary-imports/2026-11-16-life-family-02.review.json');assert.equal(extra.length,219);
for(const x of extra){const row=index.get(x.reading),i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
 assert(i>=0,x.word);assert.equal(row.meaningLevels[i],x.grade);assert.equal(row.genres[i],x.genre);assert.equal(row.namedSenses?.[i],false);assert.equal(row.imagequeries[i].mode,'none');}
for(const word of ['夜空','庭木','寝不足','炊飯器','乳製品','花火大会'])assert(extra.some(x=>x.word===word));
const noImageChanges=['assets/shiritori/manifest.json','data/image-coverage/review-2026-10-10.json','data/image-coverage/review-updates.json'];
for(const file of noImageChanges)assert.equal(cp.execFileSync('git',['diff','--numstat','HEAD','--',file],{cwd:root,encoding:'utf8'}),'',file+' was preserved');
const result=cp.spawnSync(process.execPath,['scripts/import-shiritori-words.cjs',`data/dictionary-imports/${batch}.csv`,'--append'],{cwd:root,encoding:'utf8'});
assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).added,0,'Import is idempotent');
assert.equal(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),csv);
console.log(JSON.stringify({passed:true,checkedSenses:items.length+extra.length,baselineRows:summary.baselineRows,newReadings:389,previousImagesPreserved:true,idempotent:true}));
