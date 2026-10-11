// Preserve historical review tests while validating every subsequent approved edit.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
function historicalRows(){
  let text=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
  const importPath=path.join(root,'data/dictionary-imports/history.json');
  const imports=fs.existsSync(importPath)?JSON.parse(fs.readFileSync(importPath,'utf8')):[];
  for(const record of [...imports].reverse()){
    assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.afterSha256,'Imported dictionary matches recorded after-state');
    const lines=text.trimEnd().split(/\r?\n/);
    assert.deepEqual(lines.slice(-record.addedLines.length),record.addedLines,'Only reviewed appended rows are removed');
    text=lines.slice(0,-record.addedLines.length).join('\n')+'\n';
    assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.beforeSha256,'Import restores the prior dictionary exactly');
  }
  const lines=text.trim().split(/\r?\n/),heads=lines.shift().split(',');
  const current=lines.map(line=>Object.fromEntries(heads.map((h,i)=>[h,line.split(',')[i]||''])));
  const ledger=JSON.parse(fs.readFileSync(path.join(root,'data/corrections/2026-10-11-ledger.json'),'utf8'));
  assert.equal(crypto.createHash('sha256').update(text).digest('hex'),ledger.afterSha256,'Current dictionary matches the correction ledger');
  assert.equal(current.length,ledger.currentRows);
  const restored=new Array(ledger.sourceRows);
  ledger.currentOriginalIds.forEach((oid,i)=>{assert.ok(!restored[oid-1]);restored[oid-1]=current[i];});
  for(const change of ledger.changes){
    if(change.action==='edit')assert.deepEqual(restored[change.originalId-1],change.after,'Reviewed after-state '+change.originalId);
    else assert.equal(restored[change.originalId-1],undefined,'Only approved rows are removed');
    restored[change.originalId-1]=change.before;
  }
  assert.ok(restored.every(Boolean));
  const result=restored.map(r=>heads.map(h=>r[h]).join(','));
  assert.equal(crypto.createHash('sha256').update(heads.join(',')+'\n'+result.join('\n')+'\n').digest('hex'),ledger.beforeSha256,'All changes restore the original reviewed dictionary exactly');
  return result;
}
module.exports={historicalRows};
