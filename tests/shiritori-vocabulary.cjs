const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const crypto=require('node:crypto');
const policy=require('../shiritori-vocabulary.js');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
const ctx=vm.createContext({window:{},csv:fs.readFileSync(path.join(root,'whitelist.csv'),'utf8')});
vm.runInContext(fs.readFileSync(path.join(root,'shiritori-grade-policy.js'),'utf8'),ctx);
vm.runInContext(html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST =')),ctx);
const legacy=vm.runInContext('parseCSV(csv)',ctx),graded=vm.runInContext('parseCSV(csv,true)',ctx);
const review=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-grade-review.json'),'utf8'));
assert.equal(review.length,csvMeaningCount(ctx.csv));
function csvMeaningCount(csv){return csv.trim().split(/\r?\n/).length-1;}
assert.ok(review.every((row,index)=>row.id===index+1&&row.status==='assigned'&&row.reason&&row.level>=1&&row.level<=5),'Every current meaning has an explicit decision');
assert.equal(vm.runInContext('window.ShiritoriGradePolicy.sourceSha256',ctx),crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'whitelist.csv'))).digest('hex'));
assert.equal(legacy.length,graded.length);
let counts={};
for(let i=0;i<legacy.length;i++){
 const a=legacy[i],b=graded[i];
 for(const field of ['reading','words','meanings','imagequeries'])assert.deepEqual(a[field],b[field],'Grade policy must preserve all other data');
 assert.equal(b.level,Math.min(...b.meaningLevels));
 b.meaningLevels.forEach(l=>{assert.ok(l>=1&&l<=5);counts[l]=(counts[l]||0)+1;});
}
assert.equal(graded.find(r=>r.reading==='あきおおたちょう').level,4);
assert.equal(graded.find(r=>r.reading==='あいち').level,3);
const stone=graded.find(r=>r.reading==='いし');
assert.equal(stone.meaningLevels[stone.words.indexOf('石')],1);
assert.equal(stone.meaningLevels[stone.words.indexOf('意志')],3);
const senseLevel=(reading,word)=>{const row=graded.find(r=>r.reading===reading);assert.ok(row,reading);const i=row.words.indexOf(word);assert.ok(i>=0,word);return row.meaningLevels[i];};
for(const [reading,word] of [['あしあと','足跡'],['いろえんぴつ','色鉛筆'],['うわばき','上履き'],['かれー','カレー'],['おにごっこ','鬼ごっこ'],['おとしだま','お年玉'],['じかんわり','時間割'],['くく','九九'],['ずこう','図工'],['どっじぼーる','ドッジボール'],['のーと','ノート']])assert.equal(senseLevel(reading,word),1,word+' is familiar in early elementary life');
for(const [reading,word,level] of [['わりざん','割り算',2],['みりあんぺあ','mA',3],['かそくど','加速度',4],['はんどうたい','半導体',4],['のーと','ノート',1],['まいなん','マイナン',5],['こかこーら','コカ・コーラ',5]])assert.equal(senseLevel(reading,word),level);
const note=graded.find(r=>r.reading==='のーと');assert.equal(note.meaningLevels[note.words.indexOf('ノート')],1,'Notebook stays elementary');
assert.ok(note.meaningLevels.every((level,i)=>note.meanings[i].includes('冊子')?level===1:level===5),'Other notebook homophones stay separate at level 5');
assert.equal(policy.distance('りんこ','りんご'),1);
assert.equal(policy.distance('すかい','すいか'),1);
assert.equal(policy.distance('きうり','きゅうり'),1);
assert.equal(policy.distance('がっこお','がっこう'),1);
const suggestions=policy.suggestions('りんこ',graded,{level:1});
assert.ok(suggestions.some(r=>r.reading==='りんご'));
assert.equal(suggestions[0].reading,'りんご','Dakuten correction stays ahead of unrelated near words as the dictionary grows');
assert.ok(!policy.suggestions('りんこ',graded,{used:new Set(['りんご'])}).some(r=>r.reading==='りんご'));
assert.ok(policy.suggestions('かんご',graded,{tail:'り',level:1}).some(r=>r.reading==='りんご'),'Wrong first letter can be corrected to current tail');
assert.deepEqual(policy.suggestions('あ'.repeat(100),graded),[]);
assert.deepEqual(policy.suggestions('り',graded),[]);
// A missing or newly changed meaning is conservatively kept out of grade bands.
vm.runInContext('window.ShiritoriGradePolicy=undefined',ctx);
assert.ok(vm.runInContext('parseCSV(csv,true).every(r=>r.level===4)',ctx));
console.log(JSON.stringify({passed:true,meanings:Object.values(counts).reduce((a,b)=>a+b,0),counts,readings:graded.length}));
