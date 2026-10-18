const assert=require('node:assert/strict');
const engine=require('../shiritori-word-handwriting.js');
const stroke=(points)=>({points:points.map(([x,y])=>({x,y}))});
const left=stroke([[35,0],[0,45],[35,90]]),right=stroke([[145,0],[110,45],[145,90]]);
const plan=engine.plan([right,left]); // Spatial order, not drawing order.
const predictions=plan.segments.map(s=>[{ch:s.end-s.start===1?'く':'へ',p:s.end-s.start===1?.98:.05}]);
assert.equal(engine.decode(plan,predictions)[0].text,'くく');
// Detached strokes must be allowed to belong to one character (い / late dakuten).
const detached=engine.plan([stroke([[0,0],[0,70]]),stroke([[25,5],[30,65]])]);
assert.ok(detached.segments.some(s=>s.start===0&&s.end===2));
const marked=engine.plan([left,right,stroke([[37,0],[43,8]]),stroke([[48,0],[54,8]])]);
assert.ok(marked.segments.some(s=>s.indices.includes(0)&&s.indices.includes(2)&&s.indices.includes(3)&&!s.indices.includes(1)));
const small=engine.plan([left,stroke([[80,40],[65,65],[85,85]])]);
const smallSeg=small.segments.find(s=>s.indices.length===1&&s.indices[0]===1);
const smallChoices=engine.alternatives(smallSeg,[{ch:'や',p:.98}],small);
assert.equal(smallChoices[0].ch,'ゃ');assert.ok(smallChoices.some(c=>c.ch==='や'));
const same=engine.plan([left,right]);
assert.equal(engine.alternatives(same.segments[0],[{ch:'つ',p:.98}],same)[0].ch,'つ');
assert.deepEqual(engine.decode(engine.plan([]),[]),[]);
assert.throws(()=>engine.plan(Array.from({length:65},()=>left)),/too-many-strokes/);
assert.equal(engine.smallMap[engine.largeMap['っ']],'っ');
assert.equal(engine.smallMap[engine.largeMap['ッ']],'ッ');
assert.equal(engine.alternatives(smallSeg,[{ch:'ヤ',p:.98}],small)[0].ch,'ャ');
const kataPredictions=plan.segments.map(s=>[{ch:s.end-s.start===1?'ク':'ヘ',p:s.end-s.start===1?.98:.05}]);
assert.equal(engine.decode(plan,kataPredictions)[0].text,'クク');
console.log('Word segmentation, late marks, spatial ordering, small kana and limits passed.');

// A dictionary word outside the visual top five must still be offered first.
const ranked=Array.from({length:8},(_,i)=>({text:'候補'+i,score:10-i}));
assert.equal(engine.rankCandidates(ranked,text=>text==='候補6')[0].text,'候補6');
assert.deepEqual(engine.rankCandidates(ranked,()=>false),ranked.slice(0,5));
assert.deepEqual(engine.rankCandidates(ranked,text=>['候補6','候補2'].includes(text)).slice(0,2).map(r=>r.text),['候補2','候補6']);
const pairPredictions=plan.segments.map(s=>[{ch:'く',p:.7},{ch:'し',p:.3}]);
const dictionaryFirst=engine.decode(plan,pairPredictions,{isKnown:text=>text==='くし'});
assert.equal(dictionaryFirst[0].text,'くし');assert.equal(dictionaryFirst[0].chars.map(c=>c.ch).join(''),'くし');
console.log('Dictionary-first ordering preserves model candidates and stroke ranges.');

// Very narrow し is a likely left component only when tall ink follows nearby.
const componentStrokes=[stroke([[10,0],[8,70],[14,90]]),stroke([[48,0],[48,90],[40,100]]),stroke([[28,35],[72,35]])];
for(const letter of ['け','は']){
  const p=engine.plan(componentStrokes);
  const predictions=p.segments.map(s=>[{ch:s.start===0&&s.end===3?letter:s.start===0?'し':'は',p:s.start===0&&s.end===3?.25:.97}]);
  const candidates=engine.decode(p,predictions,{isKnown:()=>true});
  assert.equal(candidates[0].text,letter);
  assert.ok(candidates.some(c=>c.text==='しは'),'standalone interpretation remains available');
}
const thin=componentStrokes[0];
for(const strokes of [[thin],[thin,stroke([[150,0],[155,100]])]]){
  const p=engine.plan(strokes),s=p.segments.find(s=>s.start===0&&s.end===1);
  const candidate=engine.alternatives(s,[{ch:'し',p:.9}],p)[0];
  assert.equal(candidate.score,Math.log(.9)+.3-s.geometry,'lone or well-spaced thin し keeps its score');
}
const thinPlan=engine.plan(componentStrokes),thinSegment=thinPlan.segments.find(s=>s.start===0&&s.end===1);
assert.equal(engine.alternatives(thinSegment,[{ch:'シ',p:.9}],thinPlan)[0].score,Math.log(.9)+.3-thinSegment.geometry,'katakana シ is unaffected');

// Strong tiny い predictions must not detach upper-right dakuten from the body.
function markCase(base,voiced,markY=0,scale=1,dx=0,dy=0){
  const paths=[[[0,0],[0,90],[60,90],[60,0]],[[67,markY],[75,markY+12]],[[83,markY],[91,markY+12]]];
  const p=engine.plan(paths.map(points=>stroke(points.map(([x,y])=>[x*scale+dx,y*scale+dy]))));
  const ps=p.segments.map(s=>[{ch:s.start===0&&s.end===3?voiced:s.start===0?base:base==='カ'?'イ':'い',p:s.start===0&&s.end===3?.05:.97}]);
  return engine.decode(p,ps,{isKnown:()=>true});
}
for(const [base,voiced] of [['か','が'],['け','げ'],['は','ば']]){
  assert.equal(markCase(base,voiced)[0].text,voiced);
  assert.equal(markCase(base,voiced,0,2,150,80)[0].text,voiced,'scale and position independent');
  assert.notEqual(markCase(base,voiced,65)[0].text,voiced,'low small い is not dakuten');
}
assert.notEqual(markCase('カ','ガ')[0].text,'ガ','katakana ranking keeps its existing behavior');
const ordinaryI=engine.plan([stroke([[0,0],[0,90],[60,90],[60,0]]),stroke([[100,0],[100,75]]),stroke([[125,0],[130,70]])]);
const ordinaryPredictions=ordinaryI.segments.map(s=>[{ch:s.start===0?'か':'い',p:s.start===0&&s.end===1||s.start===1&&s.end===3?.99:.001}]);
assert.equal(engine.decode(ordinaryI,ordinaryPredictions)[0].text,'かい','full-height following い stays separate');
console.log('Hiragana-only thin し and upper-right dakuten ranking checks passed.');
