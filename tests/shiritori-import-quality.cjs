const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),dir=fs.mkdtempSync(path.join(os.tmpdir(),'shiritori-import-'));
const target=path.join(root,'whitelist.csv'),before=fs.readFileSync(target,'utf8');
const batch=path.join(dir,'batch.csv'),review=path.join(dir,'batch.review.json');
const header=before.split('\n')[0];
function run(){return cp.spawnSync(process.execPath,[path.join(root,'scripts/import-shiritori-words.cjs'),batch,'--validate-only'],{encoding:'utf8'});}
try{
  fs.writeFileSync(batch,header+'\nてすとせんよう,試験専用,検査用の新しい語。,検査,1,,,,\n');
  assert.notEqual(run().status,0,'Unreviewed vocabulary rejected');
  const fixture={reading:'てすとせんよう',word:'試験専用',meaning:'検査用の新しい語。',lexicalSource:'テスト専用のレビュー記録',meaningReason:'概要と語義を確認',ageReason:'子供向けの説明を確認'};
  fs.writeFileSync(review,JSON.stringify([fixture]));assert.equal(run().status,0,'A documented review validates without changing production data');
  fixture.reading='あつい';fs.writeFileSync(batch,header+'\nあつい,試験専用,検査用の新しい語。,検査,1,,,,\n');fs.writeFileSync(review,JSON.stringify([fixture]));
  assert.notEqual(run().status,0,'Same reading requires separate-sense rationale');
  fixture.distinctSenseReason='同音異義語の確認を模したテスト';fs.writeFileSync(review,JSON.stringify([fixture]));assert.equal(run().status,0);
  const ledger=JSON.parse(fs.readFileSync(path.join(root,'data/corrections/2026-10-11-ledger.json'),'utf8'));
  const removed=ledger.changes.find(c=>c.originalId===215).before;
  fs.writeFileSync(batch,header+'\n'+header.split(',').map(k=>removed[k]).join(',')+'\n');fs.unlinkSync(review);
  const result=cp.spawnSync(process.execPath,[path.join(root,'scripts/import-shiritori-words.cjs'),batch],{encoding:'utf8'});
  assert.equal(result.status,0);assert.equal(JSON.parse(result.stdout).added,0,'Deleted vocabulary cannot return from old batches');
  assert.equal(fs.readFileSync(target,'utf8'),before,'Validation and stale imports leave production unchanged');
  console.log(JSON.stringify({passed:true,reviewGate:true,homonyms:true,deletedWords:true}));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
