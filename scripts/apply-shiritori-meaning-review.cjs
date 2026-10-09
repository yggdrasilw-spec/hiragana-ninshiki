// Meanings and explicitly sourced display-name typos only. Every row has a review.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/meaning-review');
const source=fs.readFileSync(path.join(dir,'source.csv'),'utf8').trim().split(/\r?\n/);
const current=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/);
assert.equal(current.length,source.length,'Source and destination row counts differ');
const reviews=new Map();
for(const part of ['1','2','3','root','root-tail']){
  const file=path.join(dir,`review-${part}.jsonl`);
  for(const line of fs.readFileSync(file,'utf8').trim().split(/\r?\n/).filter(line=>line.trim())){
    const review=JSON.parse(line);
    // Older PowerShell batches serialized an omitted optional reason as null.
    if(review.status==='reviewed'&&review.reason==null)review.reason='';
    assert.ok(Number.isInteger(review.id)&&review.id>0&&review.id<source.length,'Invalid ID');
    assert.ok(!reviews.has(review.id),'Duplicate review ID '+review.id);
    assert.ok(['reviewed','needs-source'].includes(review.status),'Invalid status '+review.id);
    assert.ok(typeof review.meaning==='string'&&review.meaning.trim()&&!/[,\r\n]/.test(review.meaning),'Invalid meaning '+review.id);
    assert.ok(Array.isArray(review.sources)&&review.sources.every(url=>typeof url==='string'&&/^https?:\/\//.test(url)),'Invalid sources '+review.id);
    assert.ok(typeof review.reason==='string','Invalid reason '+review.id);
    if(review.status==='needs-source')assert.ok(review.reason.trim(),'Unresolved review needs a reason '+review.id);
    reviews.set(review.id,review);
  }
}
assert.equal(reviews.size,source.length-1,'Incomplete review; no rows will be applied');
for(const overrideName of ['source-overrides.json','audit-overrides.json']){
const overridesFile=path.join(dir,overrideName);
if(fs.existsSync(overridesFile)){
  const overrides=JSON.parse(fs.readFileSync(overridesFile,'utf8'));
  const overrideIds=new Set();
  for(const review of overrides){
    assert.ok(reviews.has(review.id)&&!overrideIds.has(review.id),'Invalid override ID '+review.id);
    assert.ok(typeof review.meaning==='string'&&review.meaning.trim()&&!/[,\r\n]/.test(review.meaning),'Invalid override meaning '+review.id);
    assert.ok(['reviewed','needs-source'].includes(review.status)&&typeof review.reason==='string'&&review.reason.trim(),'Invalid override status/reason '+review.id);
    assert.ok(Array.isArray(review.sources)&&review.sources.every(url=>typeof url==='string'&&/^https?:\/\//.test(url)),'Invalid override sources '+review.id);
    if(review.word!==undefined){
      assert.ok(review.id===2375&&review.word==='コモロ'&&review.status==='reviewed'&&review.sources.length,'Only the sourced Comoros typo is approved');
    }
    reviews.set(review.id,review);overrideIds.add(review.id);
  }
}
}
let changed=0;
const pending=[],changes=[];
const output=source.map((line,id)=>{
  if(!id)return line;
  const original=line.split(','),destination=current[id].split(','),review=reviews.get(id);
  assert.ok(review,'Missing review '+id);
  const expectedMetadata=original.slice();
  if(review.word&&destination[1]===review.word)expectedMetadata[1]=review.word;
  assert.deepEqual([destination[0],destination[1],destination[4]],[expectedMetadata[0],expectedMetadata[1],expectedMetadata[4]],'Vocabulary metadata differs '+id);
  // Image work can advance independently; preserve its current columns.
  for(const index of [3,5,6,7,8])original[index]=destination[index]??'';
  if(review.status==='needs-source'){
    pending.push({id,reading:original[0],word:original[1],level:Number(original[4]),meaning:original[2],suggestedMeaning:review.meaning,reason:review.reason,sources:review.sources});
  }else if(review.meaning!==original[2]){
    changed++;changes.push({id,reading:original[0],word:review.word||original[1],...(review.word?{beforeWord:original[1],afterWord:review.word}:{}),before:original[2],after:review.meaning,reason:review.reason,sources:review.sources});
    original[2]=review.meaning;
  }
  if(review.word)original[1]=review.word;
  return original.join(',');
});
const summary={sourceCommit:'aa8c295',rows:source.length-1,reviewed:reviews.size,changed,wordCorrections:[...reviews.values()].filter(review=>review.word).length,needsSource:pending.length,
  levels:[1,2,3].map(level=>({level,rows:source.slice(1).filter(line=>Number(line.split(',')[4])===level).length,
    changed:changes.filter(change=>Number(source[change.id].split(',')[4])===level).length,
    needsSource:pending.filter(row=>row.level===level).length}))};
fs.writeFileSync(path.join(root,'whitelist.csv'),output.join('\n')+'\n');
fs.writeFileSync(path.join(dir,'pending-sources.json'),JSON.stringify(pending,null,2)+'\n');
fs.writeFileSync(path.join(dir,'changes.json'),JSON.stringify(changes,null,2)+'\n');
fs.writeFileSync(path.join(dir,'summary.json'),JSON.stringify(summary,null,2)+'\n');
fs.writeFileSync(path.join(dir,'reviews.jsonl'),[...reviews.values()].sort((a,b)=>a.id-b.id).map(row=>JSON.stringify(row)).join('\n')+'\n');
const cell=value=>String(value).replace(/\|/g,'\\|').replace(/[\r\n]+/g,' ');
const lines=['# しりとり説明の全件レビュー結果','',
  `対象: ${summary.rows.toLocaleString()}行。変更: ${summary.changed.toLocaleString()}行。追加確認: ${summary.needsSource.toLocaleString()}行。`,
  '', `表示名の誤記修正: ${summary.wordCorrections}行（コロモ → コモロ）。読み・レベルを保持し、画像情報はmainの追加分と統合。`,
  '', '1文目を概要、2文目以降を補足とし、自動音声は概要だけ、詳細は任意のボタンで聞けるようにした。',
  '', '`reviewed` は編集レビュー済みを意味する。全ての事実が出典で独立検証済みという意味ではない。未解決の行は元の説明を維持し、候補の修正文と確認理由を記録した。',
  '', '| レベル | 対象行数 | 変更 | 追加確認 |','|---|---:|---:|---:|',
  ...summary.levels.map(row=>`| ${row.level} | ${row.rows} | ${row.changed} | ${row.needsSource} |`),
  '', '## 記録','',
  '- [全件のレビュー記録](../data/meaning-review/reviews.jsonl)',
  '- [変更前後と理由](../data/meaning-review/changes.json)',
  '- [追加確認が必要な語](../data/meaning-review/pending-sources.json)',
  '- [編集・音声の方針](shiritori-meaning-policy.md)',
  '- [追加監査の結果](shiritori-meaning-audit.md)',
  '', '## 変更例','', '| 語 | 元の説明 | 新しい説明 |','|---|---|---|',
  ...changes.filter(row=>row.before.replace(/[。\s]/g,'')!==row.after.replace(/[。\s]/g,'')).slice(0,20).map(row=>`| ${cell(row.word)} | ${cell(row.before)} | ${cell(row.after)} |`),
  '', '## 追加確認の例','', '| 語 | 確認が必要な点 |','|---|---|',
  ...pending.slice(0,30).map(row=>`| ${cell(row.word)} | ${cell(row.reason)} |`),''];
fs.writeFileSync(path.join(root,'docs/shiritori-meaning-review.md'),lines.join('\n'));
console.log(JSON.stringify(summary));
