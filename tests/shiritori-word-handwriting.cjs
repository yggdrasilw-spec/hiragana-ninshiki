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

// A dictionary word outside the visual top five must still be offered first.
const ranked=Array.from({length:8},(_,i)=>({text:'候補'+i,score:10-i}));
assert.equal(engine.rankCandidates(ranked,text=>text==='候補6')[0].text,'候補6');
assert.deepEqual(engine.rankCandidates(ranked,()=>false),ranked.slice(0,5));
assert.deepEqual(engine.rankCandidates(ranked,text=>['候補6','候補2'].includes(text)).slice(0,2).map(r=>r.text),['候補2','候補6']);
const pairPredictions=plan.segments.map(s=>[{ch:'く',p:.7},{ch:'し',p:.3}]);
const dictionaryFirst=engine.decode(plan,pairPredictions,{isKnown:text=>text==='くし'});
assert.equal(dictionaryFirst[0].text,'くし');assert.equal(dictionaryFirst[0].chars.map(c=>c.ch).join(''),'くし');
console.log('Dictionary-first ordering preserves model candidates and stroke ranges.');
