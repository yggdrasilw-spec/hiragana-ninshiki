const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),name='2026-11-15-request-related';
const read=f=>JSON.parse(fs.readFileSync(path.join(root,f),'utf8'));
const summary=read(`data/dictionary-imports/${name}.summary.json`),reviews=read(`data/dictionary-imports/${name}.review.json`),entries=read(`data/dictionary-imports/${name}.entries.json`);
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),lines=csv.trimEnd().split('\n');
const history=read('data/dictionary-imports/history.json');
const importIndex=history.findIndex(h=>String(h.batch||'').replaceAll('\\','/')===`data/dictionary-imports/${name}.csv`);
assert(importIndex>=0);
const {undoImports}=require('../scripts/shiritori-correction-ledger.cjs');
const importedSnapshot=undoImports(csv,history.slice(importIndex+1));
assert.equal(hash(importedSnapshot.trimEnd().split('\n').slice(0,summary.baselineRows+1).join('\n')+'\n'),summary.baselineSha256,'Every pre-existing row was preserved by this import');
assert.equal(importedSnapshot.trimEnd().split('\n').length-1,summary.afterRows);
assert.equal(hash(importedSnapshot),summary.afterSha256);
assert.equal(reviews.length,summary.added);assert.equal(entries.length,summary.added);
const exact=x=>[x.reading,x.word,x.meaning].join('\t');
assert.equal(new Set(reviews.map(exact)).size,reviews.length);
const {build}=require('../scripts/build-shiritori-delivery.cjs');
const built=build(root),byReading=new Map(built.rows.map(r=>[r.reading,r]));
const genres=new Map(entries.map(x=>[exact(x),x.genre]));
for(const x of reviews){
 const row=byReading.get(x.reading);assert(row,`Missing reading ${x.reading}`);
 const i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
 assert(i>=0,`Missing exact sense ${x.word}`);
 assert.equal(row.meaningLevels[i],x.grade,x.word);
 assert.equal(row.genres[i],genres.get(exact(x)),x.word);
 assert(x.imageReason,'The batch records its image status without excluding future image work');
 assert(row.imagequeries[i].source?.url.startsWith('https://'));
}
// Ordinary meanings must coexist with earlier works, names and other senses.
for(const [reading,word,fragment,genre] of [
 ['さんだー','サンダー','研磨材','daily'],['たい','タイ','音符','arts'],
 ['かみふうせん','紙風船','薄い紙','sport'],['あとらす','アトラス','ゲーム','company'],
 ['こま','独楽','回転','sport'],['しー','C','アルファベット','school'],['しー','C','コード名','arts'],
 ['おさ','長','率いる','society'],['むろ','室','保存','daily'],['しーめじゃーせぶん','CM7','長七度','arts']]){
 const row=byReading.get(reading),i=row.words.findIndex((w,i)=>w===word&&row.meanings[i].includes(fragment));
 assert(i>=0,word+': '+fragment);assert.equal(row.genres[i],genre);
}
const imported=history[importIndex];
assert.equal(imported.afterSha256,summary.afterSha256);assert.equal(imported.addedLines.length,summary.added);
assert(imported.addedLines.every(line=>line.split(',')[6]===''&&line.split(',')[7]==='none'));
console.log(JSON.stringify({passed:true,checkedSenses:reviews.length,oldRowsPreservedByImport:summary.baselineRows,meaningSpecificGenres:true,grades:true,initialImageModeRecorded:true}));
