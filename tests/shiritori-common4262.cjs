const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/dictionary-imports'),batch='2026-11-16-common4262';
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8')),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const summary=read(`data/dictionary-imports/${batch}.summary.json`),items=read(`data/dictionary-imports/${batch}.review.json`);
const decisions=fs.readFileSync(path.join(root,'data/vocabulary-gap/common4262/decisions.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
assert.equal(decisions.length,4262);assert.equal(new Set(decisions.map(x=>x.reading)).size,4262);
assert.equal(items.length,summary.added);assert.equal(items.length+decisions.filter(x=>x.status!=='approved-source-provisional').length,4262);
assert.equal(summary.individuallyEdited+summary.inheritedJapaneseDefinitions,items.length);
const history=read('data/dictionary-imports/history.json'),record=history.find(x=>String(x.batch).replaceAll('\\','/')===`data/dictionary-imports/${batch}.csv`);
assert.equal(record.beforeSha256,summary.baselineSha256);assert.equal(record.addedLines.length,items.length);
const raw=fs.readFileSync(path.join(root,'whitelist.csv')),baseline=raw.toString('utf8').split('\n').slice(0,summary.baselineRows+1).join('\n')+'\n';
assert.equal(hash(baseline),summary.baselineSha256);assert.equal(hash(raw),summary.afterSha256);
const {build}=require('../scripts/build-shiritori-delivery.cjs'),built=build(root),byReading=new Map(built.rows.map(x=>[x.reading,x]));
for(const x of items){
 const row=byReading.get(x.reading),i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
 assert(i>=0,x.word);assert.equal(row.meaningLevels[i],4,x.word);assert.equal(row.imagequeries[i].mode,'none');
 assert(row.imagequeries[i].source?.url.startsWith('https://'),x.word);assert(x.lexicalSource.jmdict.length);
 if(!x.definitionIndividuallyEdited){
  const evidence=x.lexicalSource.japaneseDefinitionSource;assert(evidence.originalDefinition&&evidence.url);
  // Same reading alone cannot justify borrowing a definition from 民法 for 民放.
  assert(evidence.word===x.word||evidence.word===x.reading||evidence.aliasTrail.includes(x.word),x.word);
 }
}
const meanings=new Map(items.map(x=>[x.word,x.meaning]));
assert.match(meanings.get('民放'),/放送/);assert(!meanings.get('民放').includes('私法'));
assert.match(meanings.get('英蘭'),/イングランド/);assert(!meanings.get('英蘭').includes('オランダ'));
assert.match(meanings.get('幕下'),/大相撲/);assert(!meanings.get('幕下').includes('陣営'));
assert.match(meanings.get('シルエッター'),/装置/);assert.match(meanings.get('テレスキャン'),/文字情報/);
assert.match(meanings.get('フレッシュ'),/クリーム/);assert.match(meanings.get('ボーン'),/骨/);
assert.equal(decisions.find(x=>x.word==='バムバム').status,'held-source-meaning');
assert(decisions.filter(x=>x.status!=='approved-source-provisional').every(x=>x.reason));
assert.equal(items.filter(x=>x.endsWithN).length,summary.endingN);
console.log(JSON.stringify({passed:true,scopeReadings:4262,checkedMeanings:items.length,priorRowsBytePreserved:true,sourceLinks:true,semanticRegressions:true,provisionalLevel4:true}));
