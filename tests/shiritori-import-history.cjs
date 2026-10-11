const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),cp=require('node:child_process');
const root=path.resolve(__dirname,'..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'shiritori-history-'));
try{
  for(const file of ['scripts/import-shiritori-words.cjs','scripts/shiritori-correction-ledger.cjs','data/corrections/2026-10-11-ledger.json']){
    const dest=path.join(temp,file);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.copyFileSync(path.join(root,file),dest);
  }
  const current=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
  const history=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/history.json'),'utf8'));
  const first=history[0];
  const lines=current.trimEnd().split('\n');
  const baseline=lines.slice(0,-history.reduce((sum,h)=>sum+h.addedLines.length,0)).join('\n')+'\n';
  const target=path.join(temp,'whitelist.csv');fs.writeFileSync(target,baseline);
  const batch=path.join(temp,'batch.csv');
  fs.writeFileSync(batch,baseline.split('\n')[0]+'\n'+first.addedLines.join('\n')+'\n');
  fs.copyFileSync(path.join(root,first.batch.replace(/\.csv$/,'.review.json')),path.join(temp,'batch.review.json'));
  const run=(...args)=>cp.spawnSync(process.execPath,[path.join(temp,'scripts/import-shiritori-words.cjs'),batch,...args],{encoding:'utf8'});
  assert.notEqual(run().status,0,'Untracked insertion after reviewed correction is rejected');
  assert.equal(fs.readFileSync(target,'utf8'),baseline);
  assert.equal(run('--append','--validate-only').status,0);
  assert.equal(fs.readFileSync(target,'utf8'),baseline);
  const imported=run('--append');assert.equal(imported.status,0,imported.stderr);
  assert.equal(JSON.parse(imported.stdout).added,24);
  assert.ok(fs.readFileSync(target,'utf8').startsWith(baseline),'Existing row IDs and order unchanged');
  const restored=require(path.join(temp,'scripts/shiritori-correction-ledger.cjs')).historicalRows();
  assert.equal(restored.length,6191,'Restores the original pre-correction dictionary through both histories');
  assert.equal(JSON.parse(run('--append').stdout).added,0,'Repeated import is idempotent');
  const importedText=fs.readFileSync(target,'utf8');
  fs.writeFileSync(target,importedText.replace('放課後','不正変更'));
  assert.throws(()=>require(path.join(temp,'scripts/shiritori-correction-ledger.cjs')).historicalRows(),/after-state/,'Unrecorded tampering is detected');
  console.log(JSON.stringify({passed:true,appendHistory:true,stableIds:true,idempotent:true,tamperDetection:true}));
}finally{fs.rmSync(temp,{recursive:true,force:true});}
