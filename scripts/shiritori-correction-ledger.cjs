// Preserve historical review tests while validating every subsequent approved edit.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
function undoImports(text,imports){
  for(const record of [...imports].reverse()){
    assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.afterSha256,'Imported dictionary matches recorded after-state');
    const lines=text.trimEnd().split(/\r?\n/);
    if(record.type==='vocabulary-corrections'){
      const restored=new Array(record.sourceRows);
      assert.equal(lines.length-1,record.currentOriginalIds.length);
      record.currentOriginalIds.forEach((oid,i)=>{assert.ok(!restored[oid-1]);restored[oid-1]=lines[i+1];});
      for(const edit of record.changes){
        assert.equal(restored[edit.originalId-1],edit.after,'Reviewed correction after-state');
        restored[edit.originalId-1]=edit.before;
      }
      assert.ok(restored.every(Boolean));
      text=lines[0]+'\n'+restored.join('\n')+'\n';
      assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.beforeSha256,'Corrections restore the prior dictionary exactly');
      continue;
    }
    if(record.type==='image-assets'){
      const seen=new Set();
      for(const edit of record.modifiedLines){
        assert.ok(Number.isInteger(edit.id)&&edit.id>0&&edit.id<lines.length&&!seen.has(edit.id),'Unique valid image row ID');
        seen.add(edit.id);
        const before=edit.before.split(','),after=edit.after.split(',');
        assert.equal(before.length,9);assert.equal(after.length,9);
        assert.deepEqual(after.slice(0,6),before.slice(0,6),'Image import preserves vocabulary and search fields');
        assert.equal(lines[edit.id],edit.after,'Reviewed image after-state');
        lines[edit.id]=edit.before;
      }
      text=lines.join('\n')+'\n';
      assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.beforeSha256,'Image import restores the prior dictionary exactly');
      continue;
    }
    assert.deepEqual(lines.slice(-record.addedLines.length),record.addedLines,'Only reviewed appended rows are removed');
    text=lines.slice(0,-record.addedLines.length).join('\n')+'\n';
    assert.equal(crypto.createHash('sha256').update(text).digest('hex'),record.beforeSha256,'Import restores the prior dictionary exactly');
  }
  return text;
}
function historicalRows(){
  const importPath=path.join(root,'data/dictionary-imports/history.json');
  const imports=fs.existsSync(importPath)?JSON.parse(fs.readFileSync(importPath,'utf8')):[];
  const text=undoImports(fs.readFileSync(path.join(root,'whitelist.csv'),'utf8'),imports);
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
module.exports={historicalRows,undoImports};
