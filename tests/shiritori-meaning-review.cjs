const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/meaning-review');
const source=fs.readFileSync(path.join(dir,'source.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(line=>line.split(','));
const current=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/).slice(1).map(line=>line.split(','));
const reviews=fs.readFileSync(path.join(dir,'reviews.jsonl'),'utf8').trim().split(/\r?\n/).map(JSON.parse);
assert.equal(reviews.length,source.length,'Every meaning has an explicit review');
assert.equal(current.length,source.length,'No vocabulary rows lost');
const ids=new Set();let changed=0,pending=0;
reviews.forEach(review=>{
  assert.ok(!ids.has(review.id),'Duplicate ID');ids.add(review.id);
  const before=source[review.id-1],after=current[review.id-1];assert.ok(before,'ID within range');
  const expected=before.slice();
  if(review.word){assert.equal(review.id,2375);assert.equal(review.word,'コモロ');assert.ok(review.sources.length);expected[1]=review.word;}
  assert.deepEqual(after.filter((_,i)=>i!==2),expected.filter((_,i)=>i!==2),'Reading, level and image remain paired; only sourced display typo allowed');
  assert.ok(Array.isArray(review.sources));
  if(review.status==='needs-source'){
    pending++;assert.ok(review.reason.trim());assert.equal(after[2],before[2],'Unverified suggestion is not silently accepted');
  }else{
    assert.equal(review.status,'reviewed');assert.equal(after[2],review.meaning,'Approved explanation used');
    if(after[2]!==before[2])changed++;
  }
});
assert.equal(ids.size,source.length);assert.ok(changed>0);
const summary=JSON.parse(fs.readFileSync(path.join(dir,'summary.json'),'utf8'));
assert.equal(summary.changed,changed);assert.equal(summary.needsSource,pending);
assert.equal(summary.wordCorrections,1);
assert.equal(current[2374][0],'こもろ');assert.equal(current[2374][1],'コモロ');assert.match(current[2374][2],/島国/);
assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'changes.json'),'utf8')).length,changed);
assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'pending-sources.json'),'utf8')).length,pending);
console.log(JSON.stringify({passed:true,rows:source.length,changed,pending}));
