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
console.log('Word segmentation, late marks, spatial ordering, small kana and limits passed.');
